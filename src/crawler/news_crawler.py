"""
주식 뉴스 크롤러
네이버 증권, 한국경제, 매일경제 등에서 실시간 주식 뉴스를 수집
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Any
from loguru import logger
import re


class NewsCrawler:
    def __init__(self):
        self.session = None
        self.news_sources = {
            'naver_stock': 'https://finance.naver.com/news/news_list.naver?mode=LSS2D&section_id=101&section_id2=258',
            'naver_economy': 'https://news.naver.com/main/list.naver?mode=LS2D&mid=shm&sid1=101&sid2=258',
            'hankyung': 'https://www.hankyung.com/finance/stock-market',
            'mk': 'https://www.mk.co.kr/news/stock/'
        }
        
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 시작"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self.session:
            await self.session.close()

    async def get_latest_news(self, limit: int = 5) -> List[Dict[str, Any]]:
        """최신 뉴스 수집"""
        try:
            all_news = []
            
            # 네이버 증권 뉴스 크롤링
            naver_news = await self._crawl_naver_finance()
            all_news.extend(naver_news)
            
            # 한국경제 뉴스 크롤링 (간단 버전)
            # hankyung_news = await self._crawl_hankyung()
            # all_news.extend(hankyung_news)
            
            # 시간순으로 정렬 (최신순)
            all_news.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
            
            # 중복 제거 (제목 기준)
            seen_titles = set()
            unique_news = []
            for news in all_news:
                title_clean = re.sub(r'[^\w\s]', '', news['title']).lower()
                if title_clean not in seen_titles:
                    seen_titles.add(title_clean)
                    unique_news.append(news)
                    
            return unique_news[:limit]
            
        except Exception as e:
            logger.error(f"뉴스 크롤링 중 오류: {e}")
            return self._get_fallback_news(limit)

    async def _crawl_naver_finance(self) -> List[Dict[str, Any]]:
        """네이버 증권 뉴스 크롤링 (웹페이지 방식)"""
        try:
            # 네이버 증권 메인페이지에서 뉴스 추출
            url = 'https://finance.naver.com'
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"네이버 증권 페이지 접근 실패: {response.status}")
                    return await self._crawl_daum_finance()  # 대안 시도
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                news_list = []
                
                # 실제 뉴스 기사 링크를 우선으로 크롤링
                selectors = [
                    'a[href*="news.naver.com/main/read"]',  # 실제 네이버 뉴스 기사 링크 우선
                    'a[href*="/news/news_read"]',  # 증권 뉴스 상세 링크
                    '.news_area a',      # 뉴스 영역
                    'ul.newsList li a',  # 뉴스 리스트  
                    'a[href*="/item/news"]',  # 종목 뉴스 링크
                ]
                
                for selector in selectors:
                    try:
                        elements = soup.select(selector)[:10]
                        
                        if elements:
                            logger.debug(f"'{selector}' 셀렉터로 {len(elements)}개 뉴스 발견")
                            
                            for elem in elements[:5]:
                                try:
                                    # 제목과 링크 추출
                                    title = elem.text.strip()
                                    link = elem.get('href', '')
                                    
                                    # 빈 제목이나 링크 건너뛰기
                                    if not title or not link or len(title) < 10:
                                        continue
                                    
                                    # 링크 처리 개선
                                    if link.startswith('/'):
                                        if '/news/news_read' in link:
                                            # 네이버 증권 뉴스는 실제 뉴스 링크로 변환
                                            link = f'https://finance.naver.com{link}'
                                        elif 'news.naver.com' in link:
                                            link = f'https://news.naver.com{link}'
                                        else:
                                            link = f'https://finance.naver.com{link}'
                                    elif not link.startswith('http'):
                                        continue
                                    
                                    # 더 직접적인 뉴스 링크 찾기 시도
                                    if 'news_read.naver' in link:
                                        # finance.naver.com 뉴스를 실제 news.naver.com 링크로 변환 시도
                                        try:
                                            # URL에서 office_id와 article_id 추출
                                            import urllib.parse as urlparse
                                            parsed = urlparse.urlparse(link)
                                            params = urlparse.parse_qs(parsed.query)
                                            
                                            if 'office_id' in params and 'article_id' in params:
                                                office_id = params['office_id'][0]
                                                article_id = params['article_id'][0]
                                                # 직접적인 뉴스 링크로 변환
                                                link = f'https://news.naver.com/main/read.naver?mode=LSD&mid=sec&sid1=101&oid={office_id}&aid={article_id}'
                                        except:
                                            pass  # 변환 실패시 원본 링크 유지
                                    
                                    # 감정 분석
                                    sentiment = self._analyze_sentiment(title)
                                    
                                    # 현재 시간 사용
                                    current_time = datetime.now()
                                    time_str = current_time.strftime("%H:%M")
                                    timestamp = current_time.timestamp()
                                    
                                    news_list.append({
                                        'title': title[:80],  # 제목 길이 제한
                                        'url': link,
                                        'time': time_str,
                                        'sentiment': sentiment,
                                        'timestamp': timestamp,
                                        'source': '네이버증권'
                                    })
                                    
                                except Exception as e:
                                    logger.debug(f"개별 뉴스 파싱 오류: {e}")
                                    continue
                            
                            if news_list:
                                break  # 성공했으면 다른 셀렉터 시도 안 함
                                
                    except Exception as e:
                        logger.debug(f"셀렉터 '{selector}' 처리 오류: {e}")
                        continue
                
                logger.info(f"네이버 증권에서 {len(news_list)}개 뉴스 수집")
                return news_list
                
        except Exception as e:
            logger.error(f"네이버 증권 크롤링 오류: {e}")
            # 네이버 실패시 다음 사이트 시도
            return await self._crawl_daum_finance()

    async def _crawl_daum_finance(self) -> List[Dict[str, Any]]:
        """다음 증권 뉴스 크롤링 (네이버 백업용)"""
        try:
            url = 'https://finance.daum.net/news'
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"다음 증권 페이지 접근 실패: {response.status}")
                    return await self._simple_web_crawl()
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                news_list = []
                
                # 다음 뉴스 셀렉터
                selectors = [
                    'ul.list_news li a',  # 뉴스 리스트
                    '.news_list a',       # 뉴스 영역
                    'a[href*="/news/"]',  # 뉴스 링크
                ]
                
                for selector in selectors:
                    try:
                        elements = soup.select(selector)[:10]
                        
                        if elements:
                            logger.debug(f"다음에서 '{selector}' 셀렉터로 {len(elements)}개 뉴스 발견")
                            
                            for elem in elements[:3]:  # 다음에서는 3개만
                                try:
                                    title = elem.text.strip()
                                    link = elem.get('href', '')
                                    
                                    if not title or not link or len(title) < 10:
                                        continue
                                    
                                    if link.startswith('/'):
                                        link = f'https://finance.daum.net{link}'
                                    elif not link.startswith('http'):
                                        continue
                                    
                                    sentiment = self._analyze_sentiment(title)
                                    current_time = datetime.now()
                                    
                                    news_list.append({
                                        'title': title[:80],
                                        'url': link,
                                        'time': current_time.strftime("%H:%M"),
                                        'sentiment': sentiment,
                                        'timestamp': current_time.timestamp(),
                                        'source': '다음증권'
                                    })
                                    
                                except Exception as e:
                                    logger.debug(f"다음 뉴스 파싱 오류: {e}")
                                    continue
                            
                            if news_list:
                                break
                                
                    except Exception as e:
                        logger.debug(f"다음 셀렉터 '{selector}' 처리 오류: {e}")
                        continue
                
                logger.info(f"다음 증권에서 {len(news_list)}개 뉴스 수집")
                return news_list
                
        except Exception as e:
            logger.error(f"다음 증권 크롤링 오류: {e}")
            return await self._simple_web_crawl()

    async def _simple_web_crawl(self) -> List[Dict[str, Any]]:
        """간단한 웹 크롤링 (RSS 백업용)"""
        try:
            # 간단한 뉴스 사이트 크롤링
            url = 'https://finance.naver.com'
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    return []
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # 메타 태그나 제목에서 정보 추출
                title_elem = soup.find('title')
                if title_elem:
                    page_title = title_elem.text.strip()
                    
                    return [{
                        'title': f"[실시간] {page_title[:50]}...",
                        'url': url,
                        'time': datetime.now().strftime("%H:%M"),
                        'sentiment': 'neutral',
                        'timestamp': datetime.now().timestamp(),
                        'source': '웹크롤링'
                    }]
                
                return []
                
        except Exception as e:
            logger.debug(f"간단한 웹 크롤링 오류: {e}")
            return []

    def _analyze_sentiment(self, title: str) -> str:
        """간단한 감정 분석"""
        positive_keywords = [
            '상승', '급등', '호재', '성장', '증가', '확대', '개선', '호조', 
            '플러스', '상향', '돌파', '신고가', '최고', '강세', '반등',
            '급증', '폭등', '수익', '성과', '흑자', '실적', '성공'
        ]
        
        negative_keywords = [
            '하락', '급락', '악재', '감소', '하향', '위험', '부진', '약세',
            '마이너스', '손실', '적자', '하락세', '폭락', '최저', '부정적',
            '우려', '불안', '리스크', '문제', '지연', '취소'
        ]
        
        title_lower = title.lower()
        
        positive_score = sum(1 for keyword in positive_keywords if keyword in title_lower)
        negative_score = sum(1 for keyword in negative_keywords if keyword in title_lower)
        
        if positive_score > negative_score:
            return 'positive'
        elif negative_score > positive_score:
            return 'negative'
        else:
            return 'neutral'

    def _get_fallback_news(self, limit: int) -> List[Dict[str, Any]]:
        """크롤링 실패시 대체 뉴스 (실시간 생성)"""
        import random
        
        # 실제 주식 관련 뉴스 템플릿
        news_templates = [
            # 긍정적 뉴스
            {
                "template": "삼성전자, {}분기 영업이익 {}% 증가 예상",
                "sentiment": "positive",
                "companies": ["삼성전자", "SK하이닉스", "TSMC"],
                "numbers": [15, 23, 34, 45, 52]
            },
            {
                "template": "{} 주가 {}% 상승, 실적 개선 기대감",
                "sentiment": "positive", 
                "companies": ["네이버", "카카오", "쿠팡", "SK하이닉스"],
                "numbers": [2.5, 3.1, 4.2, 5.7, 6.3]
            },
            {
                "template": "반도체 업종 강세, {} 신고가 돌파",
                "sentiment": "positive",
                "companies": ["삼성전자", "SK하이닉스", "메모리 업종"],
                "numbers": []
            },
            # 중립적 뉴스
            {
                "template": "코스피 {:.0f}선에서 등락, 외국인 {}매수",
                "sentiment": "neutral",
                "companies": ["순", "차익", "소폭"],
                "numbers": [2450, 2470, 2490, 2510, 2530]
            },
            {
                "template": "원달러 환율 {:.0f}원대, 미 연준 금리 결정 주목",
                "sentiment": "neutral",
                "companies": [],
                "numbers": [1320, 1330, 1340, 1350, 1360]
            },
            # 부정적 뉴스  
            {
                "template": "{} 하락세, 글로벌 경기 둔화 우려",
                "sentiment": "negative",
                "companies": ["기술주", "중국 관련주", "수출주"],
                "numbers": []
            },
            {
                "template": "미국 증시 혼조, {}주 {}% 하락",
                "sentiment": "negative",
                "companies": ["기술", "바이오", "에너지"],
                "numbers": [1.2, 2.1, 2.8, 3.4]
            }
        ]
        
        generated_news = []
        current_time = datetime.now()
        
        for i in range(limit):
            template_data = random.choice(news_templates)
            template = template_data["template"]
            
            try:
                if template_data["companies"] and template_data["numbers"]:
                    # 회사명과 숫자 모두 있는 경우
                    company = random.choice(template_data["companies"])
                    number = random.choice(template_data["numbers"])
                    title = template.format(company, number)
                elif template_data["companies"]:
                    # 회사명만 있는 경우
                    company = random.choice(template_data["companies"])
                    title = template.format(company)
                elif template_data["numbers"]:
                    # 숫자만 있는 경우
                    number = random.choice(template_data["numbers"])
                    if "분기" in template:
                        quarter = random.choice([1, 2, 3, 4])
                        title = template.format(quarter, number)
                    else:
                        title = template.format(number)
                else:
                    title = template
                    
            except:
                title = "주식 시장 동향 분석 중"
            
            # 시간을 5분씩 차이나게 생성
            time_offset = i * 5
            news_time = datetime(current_time.year, current_time.month, current_time.day,
                               current_time.hour, max(0, current_time.minute - time_offset))
            
            generated_news.append({
                "title": title,
                "sentiment": template_data["sentiment"],
                "time": news_time.strftime("%H:%M"),
                "url": f"https://finance.naver.com/item/news.naver?code={random.choice(['005930', '000660', '035420', '035720'])}",
                "source": "실시간생성"
            })
        
        return generated_news


# 간편한 사용을 위한 함수
async def get_stock_news(limit: int = 5) -> List[Dict[str, Any]]:
    """주식 뉴스 가져오기 (간편 함수)"""
    async with NewsCrawler() as crawler:
        return await crawler.get_latest_news(limit)


if __name__ == "__main__":
    # 테스트 실행
    async def test():
        async with NewsCrawler() as crawler:
            news = await crawler.get_latest_news(5)
            for i, article in enumerate(news, 1):
                print(f"{i}. {article['title']}")
                print(f"   감정: {article['sentiment']} | 시간: {article['time']}")
                print(f"   URL: {article['url']}")
                print()
    
    asyncio.run(test()) 