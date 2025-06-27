"""
뉴스 모니터링 모듈
새로운 뉴스가 3개 이상 쌓이면 자동으로 알림을 전송하는 시스템
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Set
from loguru import logger
import hashlib


class NewsMonitor:
    def __init__(self, bot_instance, check_interval: int = 300):  # 5분마다 체크
        self.bot = bot_instance
        self.check_interval = check_interval  # 체크 간격 (초)
        self.known_news_hashes: Set[str] = set()  # 알려진 뉴스 해시
        self.new_news_buffer: List[Dict[str, Any]] = []  # 새 뉴스 버퍼
        self.min_news_threshold = 3  # 최소 뉴스 개수 임계값
        self.is_running = False
        self.monitor_task = None
        self.last_notification_time = None
        self.min_notification_interval = 600  # 최소 알림 간격 (10분)
        
    def _generate_news_hash(self, news: Dict[str, Any]) -> str:
        """뉴스 고유 해시 생성"""
        # 제목과 시간을 조합해서 고유 해시 생성
        content = f"{news.get('title', '')}{news.get('time', '')}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def start_monitoring(self):
        """뉴스 모니터링 시작"""
        if self.is_running:
            logger.warning("뉴스 모니터링이 이미 실행 중입니다")
            return
        
        self.is_running = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info(f"🔍 뉴스 모니터링 시작 - {self.check_interval}초마다 체크, {self.min_news_threshold}개 이상 새 뉴스시 알림")
    
    async def stop_monitoring(self):
        """뉴스 모니터링 중지"""
        self.is_running = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("🛑 뉴스 모니터링 중지됨")
    
    async def _monitoring_loop(self):
        """뉴스 모니터링 메인 루프"""
        try:
            # 첫 실행시 기존 뉴스들로 해시 초기화
            await self._initialize_known_news()
            
            while self.is_running:
                try:
                    await self._check_for_new_news()
                    await asyncio.sleep(self.check_interval)
                except Exception as e:
                    logger.error(f"뉴스 모니터링 중 오류: {e}")
                    await asyncio.sleep(60)  # 오류시 1분 대기
                    
        except asyncio.CancelledError:
            logger.info("뉴스 모니터링 루프 취소됨")
        except Exception as e:
            logger.error(f"뉴스 모니터링 루프 오류: {e}")
    
    async def _initialize_known_news(self):
        """기존 뉴스로 해시 초기화"""
        try:
            from src.crawler.news_crawler import get_stock_news
            current_news = await get_stock_news(20)  # 더 많은 뉴스로 초기화
            
            for news in current_news:
                news_hash = self._generate_news_hash(news)
                self.known_news_hashes.add(news_hash)
            
            logger.info(f"📋 기존 뉴스 {len(self.known_news_hashes)}개로 모니터링 초기화")
            
        except Exception as e:
            logger.error(f"뉴스 초기화 오류: {e}")
    
    async def _check_for_new_news(self):
        """새로운 뉴스 확인"""
        try:
            from src.crawler.news_crawler import get_stock_news
            current_news = await get_stock_news(10)
            
            if not current_news:
                return
            
            new_news_count = 0
            new_news_list = []
            
            # 새로운 뉴스 감지
            for news in current_news:
                news_hash = self._generate_news_hash(news)
                
                if news_hash not in self.known_news_hashes:
                    # 새로운 뉴스 발견!
                    self.known_news_hashes.add(news_hash)
                    new_news_list.append(news)
                    new_news_count += 1
            
            if new_news_count > 0:
                logger.info(f"🆕 새로운 뉴스 {new_news_count}개 감지")
                self.new_news_buffer.extend(new_news_list)
                
                # 임계값 도달 확인
                if len(self.new_news_buffer) >= self.min_news_threshold:
                    await self._send_new_news_notification()
            
        except Exception as e:
            logger.error(f"새 뉴스 확인 중 오류: {e}")
    
    async def _send_new_news_notification(self):
        """새 뉴스 알림 전송"""
        try:
            # 최소 알림 간격 체크
            current_time = datetime.now()
            if (self.last_notification_time and 
                (current_time - self.last_notification_time).total_seconds() < self.min_notification_interval):
                logger.info(f"⏰ 최소 알림 간격({self.min_notification_interval}초) 미충족, 알림 지연")
                return
            
            # 활성 구독자 확인
            if not self.bot.scheduler:
                logger.warning("스케줄러가 없어서 구독자 확인 불가")
                return
            
            active_subscribers = []
            for user_id, info in self.bot.scheduler.subscribers.items():
                if info.get('enabled', True):
                    active_subscribers.append(user_id)
            
            if not active_subscribers:
                logger.info("📭 활성 구독자가 없어서 알림 전송 안함")
                self.new_news_buffer.clear()  # 버퍼 비우기
                return
            
            # 새 뉴스 알림 전송
            news_count = len(self.new_news_buffer)
            logger.info(f"🚨 긴급 뉴스 알림 전송: {news_count}개 뉴스, {len(active_subscribers)}명에게")
            
            success_count = 0
            for user_id in active_subscribers:
                try:
                    await self._send_urgent_news_to_user(user_id, self.new_news_buffer[:5])  # 최대 5개
                    success_count += 1
                    await asyncio.sleep(0.1)  # API 제한 고려
                except Exception as e:
                    logger.error(f"사용자 {user_id}에게 긴급 알림 전송 실패: {e}")
            
            logger.info(f"🚨 긴급 뉴스 알림 완료: {success_count}/{len(active_subscribers)}명")
            
            # 버퍼 비우기 및 시간 업데이트
            self.new_news_buffer.clear()
            self.last_notification_time = current_time
            
        except Exception as e:
            logger.error(f"새 뉴스 알림 전송 중 오류: {e}")
    
    async def _send_urgent_news_to_user(self, user_id: int, news_list: List[Dict[str, Any]]):
        """특정 사용자에게 긴급 뉴스 전송"""
        try:
            current_time = datetime.now().strftime("%m월 %d일 %H:%M")
            message_text = f"🚨 **긴급 뉴스 알림** ({current_time})\n\n"
            message_text += f"📈 **새로운 주요 뉴스 {len(news_list)}건 감지!**\n\n"
            
            # 인라인 버튼 생성
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            buttons = []
            
            for i, news in enumerate(news_list, 1):
                # 감정 분석 아이콘
                sentiment_icon = "📈" if news["sentiment"] == "positive" else "📉" if news["sentiment"] == "negative" else "📊"
                sentiment_text = "긍정적" if news["sentiment"] == "positive" else "부정적" if news["sentiment"] == "negative" else "중립"
                
                # 메시지 텍스트에 뉴스 추가
                message_text += f"{i}️⃣ {news['title']}\n   {sentiment_icon} {sentiment_text} | ⏰ {news['time']}\n\n"
                
                # 각 뉴스별 버튼 생성
                button_text = f"{i}️⃣ 뉴스 보기"
                buttons.append([InlineKeyboardButton(button_text, url=news["url"])])
            
            # 추가 액션 버튼
            action_buttons = [
                InlineKeyboardButton("🔄 새로고침", callback_data="refresh"),
                InlineKeyboardButton("⚙️ 알림설정", callback_data="notification_settings")
            ]
            buttons.append(action_buttons)
            
            message_text += "💡 각 뉴스를 클릭하면 원문을 확인할 수 있습니다.\n"
            message_text += "🔍 새로운 뉴스가 감지되어 즉시 알림을 보내드렸습니다."
            
            keyboard = InlineKeyboardMarkup(buttons)
            
            # 봇을 통해 메시지 전송
            await self.bot.app.bot.send_message(
                chat_id=user_id,
                text=message_text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"사용자 {user_id}에게 긴급 뉴스 전송 중 오류: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """모니터링 상태 반환"""
        return {
            "is_running": self.is_running,
            "check_interval": self.check_interval,
            "known_news_count": len(self.known_news_hashes),
            "new_news_buffer_count": len(self.new_news_buffer),
            "min_news_threshold": self.min_news_threshold,
            "last_notification_time": self.last_notification_time.strftime("%Y-%m-%d %H:%M:%S") if self.last_notification_time else None
        }
    
    def set_threshold(self, threshold: int):
        """알림 임계값 변경"""
        self.min_news_threshold = threshold
        logger.info(f"🔧 알림 임계값 변경: {threshold}개 뉴스")


# 전역 뉴스 모니터 인스턴스
news_monitor = None

def init_news_monitor(bot_instance, check_interval: int = 300):
    """뉴스 모니터 초기화"""
    global news_monitor
    news_monitor = NewsMonitor(bot_instance, check_interval)
    return news_monitor 