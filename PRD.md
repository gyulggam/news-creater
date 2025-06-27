# 주식 뉴스 텔레그램 봇 PRD (Product Requirements Document)

## 📋 프로젝트 개요

### 프로젝트명
**StockNewsBot** - 주식 뉴스 자동 수집 및 전달 텔레그램 봇

### 프로젝트 목표
Python을 활용하여 주식 관련 뉴스를 자동으로 수집하고 분석하여 텔레그램을 통해 사용자에게 실시간으로 전달하는 봇 서비스 구축

### 타겟 사용자
- 개인 주식 투자자
- 주식 투자 커뮤니티 운영자
- 실시간 주식 정보가 필요한 트레이더
- 주식 관련 뉴스를 모니터링하는 전문가

## 🎯 핵심 기능 요구사항

### 1. 뉴스 수집 및 분석
- **멀티 소스 뉴스 크롤링**: 네이버, 다음, 한경, 조선비즈, 이데일리 등
- **키워드 필터링**: 주식, 증시, 기업명, 종목코드 기반 필터링
- **중요도 분석**: AI/ML을 활용한 뉴스 중요도 자동 분류
- **중복 제거**: 동일 뉴스 중복 발송 방지

### 2. 텔레그램 봇 기능
- **실시간 뉴스 전송**: 중요 뉴스 즉시 전달
- **카테고리별 구독**: 증시, 개별 종목, 공시 등 선택적 구독
- **명령어 기반 상호작용**: 
  - `/start` - 봇 시작 및 설정
  - `/subscribe [종목코드]` - 특정 종목 구독
  - `/unsubscribe [종목코드]` - 구독 해제
  - `/status` - 현재 구독 상태 확인
  - `/search [키워드]` - 뉴스 검색
- **개인화 설정**: 알림 시간, 키워드 맞춤 설정

### 3. 스마트 필터링
- **종목별 분류**: 개별 종목 관련 뉴스 자동 분류
- **감정 분석**: 긍정/부정/중립 뉴스 분류
- **급등/급락 알림**: 주가 변동과 연관된 뉴스 우선 전송
- **공시 알림**: 중요 공시 정보 실시간 전달

### 4. 데이터 관리
- **사용자 구독 관리**: 개인별 관심 종목 및 설정 저장
- **뉴스 히스토리**: 발송된 뉴스 기록 관리
- **통계 및 분석**: 뉴스 발송 통계, 사용자 활동 분석

## 🛠 기술 스택

### Backend (Python)
- **Framework**: FastAPI 또는 Flask
- **크롤링**: BeautifulSoup4, Scrapy, Selenium
- **스케줄링**: APScheduler 또는 Celery
- **NLP/ML**: 
  - **형태소 분석**: KoNLPy (Okt, Komoran)
  - **감정 분석**: Transformers (KoBERT, KoGPT)
  - **텍스트 처리**: NLTK, spaCy

### 텔레그램 봇
- **봇 라이브러리**: python-telegram-bot
- **비동기 처리**: asyncio, aiohttp
- **메시지 포맷**: HTML/Markdown 리치 메시지

### 데이터베이스
- **메인 DB**: PostgreSQL (Supabase)
- **캐싱**: Redis
- **검색 엔진**: Elasticsearch (선택사항)

### 외부 API
- **주식 데이터**: 
  - 한국투자증권 API
  - 키움증권 API
  - Yahoo Finance API
- **뉴스 API**: 
  - 네이버 뉴스 API
  - 다음 뉴스 API
  - Google News API

### 인프라 및 배포
- **서버**: AWS EC2 또는 Google Cloud Platform
- **컨테이너**: Docker, Docker Compose
- **모니터링**: Prometheus + Grafana
- **로깅**: Python logging + ELK Stack

## 🎨 텔레그램 봇 UI/UX

### 메시지 포맷 디자인
```
📰 주식 뉴스 업데이트 (12월 19일 09:30)

🔥 주요 뉴스 5건:

1️⃣ [속보] 삼성전자 3분기 영업이익 277% 급증
   📈 긍정적 | ⏰ 08:45

2️⃣ SK하이닉스, HBM3E 양산 본격화 발표  
   📈 긍정적 | ⏰ 08:30

3️⃣ 현대차, 美 전기차 보조금 혜택 확대
   📊 중립 | ⏰ 08:15

4️⃣ 네이버, AI 검색 서비스 대폭 업그레이드
   📈 긍정적 | ⏰ 08:00

5️⃣ 카카오, 3분기 플랫폼 매출 성장세
   📈 긍정적 | ⏰ 07:45

💡 각 뉴스를 클릭하면 원문을 확인할 수 있습니다.
```

### 인터랙티브 버튼 (인라인 키보드)
뉴스 카드 하단에 표시되는 버튼들:

**뉴스 리스트 버튼 (각 뉴스별)**:
```
[1️⃣ 삼성전자 뉴스 보기] [2️⃣ SK하이닉스 뉴스 보기]
[3️⃣ 현대차 뉴스 보기]    [4️⃣ 네이버 뉴스 보기]
[5️⃣ 카카오 뉴스 보기]
```

**추가 액션 버튼**:
```
[🔄 새로고침] [⚙️ 설정] [📊 내 구독 현황]
```

- 각 번호 버튼 클릭 시 해당 뉴스 원문 URL로 이동
- Telegram의 InlineKeyboardButton 활용
- URL 타입 버튼으로 외부 링크 연결

### 알림 설정
- 평일 장중 시간대 집중 알림
- 주말/야간 중요 뉴스만 알림
- 사용자별 맞춤 알림 시간 설정

## 🔄 시스템 아키텍처

### 1. 뉴스 수집 파이프라인
```
뉴스 소스 → 크롤러 → 전처리 → 분류/분석 → 필터링 → 큐 저장
```

### 2. 메시지 전송 파이프라인
```
큐에서 가져오기 → 사용자 매칭 → 메시지 포맷팅 → 텔레그램 전송
```

### 3. 사용자 상호작용
```
텔레그램 명령어 → 봇 처리 → DB 업데이트 → 응답 메시지
```

## 📊 데이터베이스 스키마

```sql
-- 사용자 테이블
CREATE TABLE users (
    id BIGINT PRIMARY KEY,  -- 텔레그램 user_id
    username VARCHAR(100),
    first_name VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    notification_time TIME DEFAULT '09:00',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 뉴스 테이블
CREATE TABLE news (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    content TEXT,
    summary TEXT,
    url TEXT NOT NULL,
    source VARCHAR(50),
    category VARCHAR(30),
    stock_codes TEXT[], -- 관련 종목 코드들
    sentiment VARCHAR(20), -- positive, negative, neutral
    importance_score FLOAT,
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 구독 테이블
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT REFERENCES users(id),
    subscription_type VARCHAR(20), -- 'stock', 'category', 'keyword'
    value VARCHAR(100), -- 종목코드, 카테고리명, 키워드
    created_at TIMESTAMP DEFAULT NOW()
);

-- 발송 기록
CREATE TABLE sent_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT REFERENCES users(id),
    news_id UUID REFERENCES news(id),
    sent_at TIMESTAMP DEFAULT NOW()
);
```

## 🚀 개발 단계

### Phase 1 (1주) - 기본 봇 구축
- [x] 텔레그램 봇 생성 및 기본 설정
- [x] 기본 명령어 구현 (/start, /help)
- [x] 사용자 등록 및 DB 연동
- [x] 기본 메시지 전송 기능

### Phase 2 (2주) - 뉴스 수집 시스템
- [ ] 뉴스 사이트 크롤러 개발
- [ ] 뉴스 데이터 전처리 및 저장
- [ ] 기본 필터링 로직 구현
- [ ] 스케줄링 시스템 구축

### Phase 3 (2주) - 스마트 기능
- [ ] 종목 분류 및 매칭 시스템
- [ ] 감정 분석 모델 적용
- [ ] 구독 관리 시스템
- [ ] 개인화 알림 기능

### Phase 4 (1주) - 고도화 및 배포
- [ ] 성능 최적화 및 에러 처리
- [ ] 모니터링 시스템 구축
- [ ] 서버 배포 및 CI/CD 구축
- [ ] 사용자 테스트 및 피드백 반영

## 🎯 주요 기능 명세

### 뉴스 수집 및 처리
```python
# 뉴스 크롤링 예시
class NewsCollector:
    def __init__(self):
        self.sources = ['naver', 'daum', 'hankyung', 'chosunbiz']
    
    async def collect_news(self, keywords: List[str]) -> List[News]:
        # 멀티 소스에서 뉴스 수집
        pass
    
    def analyze_sentiment(self, content: str) -> str:
        # 감정 분석 (긍정/부정/중립)
        pass
    
    def extract_stock_codes(self, content: str) -> List[str]:
        # 종목코드 추출
        pass
```

### 텔레그램 봇 구현 예시
```python
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import asyncio

# 뉴스 카드 전송 기능
async def send_news_card(bot, chat_id, news_list):
    # 뉴스 리스트 메시지 포맷팅
    message_text = "📰 주식 뉴스 업데이트 (12월 19일 09:30)\n\n🔥 주요 뉴스 5건:\n\n"
    
    buttons = []
    for i, news in enumerate(news_list[:5], 1):
        # 메시지 텍스트에 뉴스 추가
        sentiment_icon = "📈" if news.sentiment == "positive" else "📉" if news.sentiment == "negative" else "📊"
        message_text += f"{i}️⃣ {news.title}\n   {sentiment_icon} {news.sentiment} | ⏰ {news.time}\n\n"
        
        # 인라인 버튼 생성 (원문 링크)
        button_text = f"{i}️⃣ 뉴스 보기"
        buttons.append([InlineKeyboardButton(button_text, url=news.url)])
    
    # 추가 액션 버튼
    action_buttons = [
        InlineKeyboardButton("🔄 새로고침", callback_data="refresh"),
        InlineKeyboardButton("⚙️ 설정", callback_data="settings")
    ]
    buttons.append(action_buttons)
    
    message_text += "💡 각 뉴스를 클릭하면 원문을 확인할 수 있습니다."
    
    keyboard = InlineKeyboardMarkup(buttons)
    await bot.send_message(chat_id=chat_id, text=message_text, reply_markup=keyboard)

# 봇 명령어 처리
@bot.message_handler(commands=['subscribe'])
def subscribe_stock(message):
    # 종목 구독 처리
    pass

@bot.message_handler(commands=['news'])
async def get_latest_news(message):
    # 최신 뉴스 카드 전송
    news_list = await collect_latest_news()
    await send_news_card(bot, message.chat.id, news_list)
```

## 📈 성공 지표

### 사용자 지표
- **활성 사용자**: 100명 (1개월 내)
- **메시지 오픈율**: 80% 이상
- **구독 유지율**: 주간 70% 이상

### 기술 지표
- **뉴스 수집 주기**: 5분 간격
- **메시지 전송 속도**: 평균 1초 이내
- **봇 응답 시간**: 평균 500ms 이하

### 품질 지표
- **뉴스 정확도**: 중복 뉴스 5% 이하
- **관련성 점수**: 사용자 만족도 4.0/5.0 이상
- **시스템 가동률**: 99.5% 이상

## 🔒 보안 및 운영

### 보안 사항
- **API 키 관리**: 환경 변수로 안전한 키 관리
- **사용자 데이터 보호**: 개인정보 최소 수집
- **Rate Limiting**: 스팸 방지 및 API 호출 제한

### 운영 고려사항
- **로그 관리**: 체계적인 로깅 시스템
- **에러 처리**: 장애 발생 시 자동 복구
- **백업**: 일일 DB 백업 및 복구 시스템

## 💡 확장 가능성

### 추가 기능 아이디어
- **AI 뉴스 요약**: GPT를 활용한 뉴스 요약
- **차트 분석**: 주가 차트와 뉴스 연관 분석
- **그룹 봇**: 투자 그룹 채팅용 봇 기능
- **웹 대시보드**: 통계 및 관리 웹 인터페이스

### 수익화 방안
- **프리미엄 구독**: 고급 분석 기능
- **API 제공**: 다른 서비스에 뉴스 데이터 제공
- **맞춤형 봇**: 기업용 맞춤 뉴스 봇 제작

---

**문서 작성일**: 2024년 12월
**작성자**: 개발팀
**버전**: v2.0 (Telegram Bot) 