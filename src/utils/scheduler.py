"""
스케줄러 모듈
주기적으로 뉴스를 전송하고 사용자 알림을 관리하는 기능
"""

import asyncio
from datetime import datetime, time
from typing import List, Dict, Any, Callable
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger


class NewsScheduler:
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.scheduler = AsyncIOScheduler()
        self.subscribers = {}  # user_id: {times: [time_list], enabled: bool}
        # 30분 간격 알림 시간 설정
        self.default_times = [
            time(9, 0),   # 오전 9시
            time(9, 30),  # 오전 9시 30분
            time(10, 0),  # 오전 10시
            time(10, 30), # 오전 10시 30분
            time(11, 0),  # 오전 11시
            time(11, 30), # 오전 11시 30분
            time(12, 0),  # 오후 12시
            time(12, 30), # 오후 12시 30분
            time(13, 0),  # 오후 1시
            time(13, 30), # 오후 1시 30분
            time(14, 0),  # 오후 2시
            time(14, 30), # 오후 2시 30분
            time(15, 0),  # 오후 3시
            time(15, 30), # 오후 3시 30분
            time(16, 0),  # 오후 4시
            time(16, 30), # 오후 4시 30분
            time(17, 0),  # 오후 5시
            time(17, 30), # 오후 5시 30분
            time(18, 0),  # 오후 6시
        ]
        
    async def start(self):
        """스케줄러 시작"""
        try:
            # 기본 뉴스 전송 스케줄 설정
            self._setup_default_schedules()
            
            self.scheduler.start()
            logger.info("뉴스 스케줄러 시작됨")
            
        except Exception as e:
            logger.error(f"스케줄러 시작 오류: {e}")
    
    async def stop(self):
        """스케줄러 중지"""
        try:
            self.scheduler.shutdown()
            logger.info("뉴스 스케줄러 중지됨")
        except Exception as e:
            logger.error(f"스케줄러 중지 오류: {e}")
    
    def _setup_default_schedules(self):
        """30분 간격 뉴스 전송 스케줄 설정"""
        logger.info("📅 30분 간격 뉴스 알림 스케줄 설정 중...")
        
        # 30분 간격 알림 스케줄 추가
        for schedule_time in self.default_times:
            self.scheduler.add_job(
                self._send_scheduled_news,
                CronTrigger(hour=schedule_time.hour, minute=schedule_time.minute),
                id=f"news_{schedule_time.hour}_{schedule_time.minute}",
                name=f"뉴스 전송 {schedule_time.strftime('%H:%M')}",
                replace_existing=True
            )
            logger.info(f"⏰ 뉴스 알림 스케줄 추가: {schedule_time.strftime('%H:%M')}")
        
        logger.info(f"✅ 총 {len(self.default_times)}개 알림 시간 설정 완료 (30분 간격)")
    
    async def _send_scheduled_news(self):
        """스케줄된 뉴스 전송"""
        try:
            current_time = datetime.now().strftime("%H:%M")
            logger.info(f"스케줄된 뉴스 전송 시작: {current_time}")
            
            # 활성화된 구독자들에게 뉴스 전송
            active_subscribers = self._get_active_subscribers_for_time(current_time)
            
            if not active_subscribers:
                logger.info("현재 시간에 알림을 받을 구독자가 없습니다")
                return
            
            # 최신 뉴스 가져오기
            from src.crawler.news_crawler import get_stock_news
            news_list = await get_stock_news(5)
            
            if not news_list:
                logger.warning("스케줄된 뉴스 전송: 뉴스를 가져올 수 없음")
                return
            
            # 각 구독자에게 뉴스 전송
            success_count = 0
            for user_id in active_subscribers:
                try:
                    await self._send_news_to_user(user_id, news_list)
                    success_count += 1
                    # 봇 API 제한을 위해 잠시 대기
                    await asyncio.sleep(0.1)
                except Exception as e:
                    logger.error(f"사용자 {user_id}에게 뉴스 전송 실패: {e}")
            
            logger.info(f"스케줄된 뉴스 전송 완료: {success_count}/{len(active_subscribers)}명")
            
        except Exception as e:
            logger.error(f"스케줄된 뉴스 전송 중 오류: {e}")
    
    async def _send_news_to_user(self, user_id: int, news_list: List[Dict[str, Any]]):
        """특정 사용자에게 뉴스 전송"""
        try:
            # 뉴스 카드 생성
            current_time = datetime.now().strftime("%m월 %d일 %H:%M")
            message_text = f"📰 주식 뉴스 알림 ({current_time})\n\n🔥 주요 뉴스 {len(news_list)}건:\n\n"
            
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
            
            message_text += "💡 각 뉴스를 클릭하면 원문을 확인할 수 있습니다.\n📲 정기 알림을 받고 계십니다."
            
            keyboard = InlineKeyboardMarkup(buttons)
            
            # 봇을 통해 메시지 전송
            await self.bot.app.bot.send_message(
                chat_id=user_id,
                text=message_text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"사용자 {user_id}에게 뉴스 전송 중 오류: {e}")
            raise
    
    def _get_active_subscribers_for_time(self, current_time: str) -> List[int]:
        """현재 시간에 알림을 받을 활성 구독자 목록"""
        # 활성화된 구독자들만 반환
        active_subscribers = []
        
        for user_id, info in self.subscribers.items():
            if info.get('enabled', True):  # enabled가 없으면 기본값 True
                active_subscribers.append(user_id)
        
        if active_subscribers:
            logger.info(f"🔔 알림 대상 구독자: {len(active_subscribers)}명 - {active_subscribers}")
        else:
            logger.info("📭 현재 활성화된 구독자가 없습니다. /notify_on 명령어로 알림을 활성화하세요.")
        
        return active_subscribers
    
    def add_subscriber(self, user_id: int, notification_times: List[time] = None):
        """구독자 추가"""
        if notification_times is None:
            notification_times = self.default_times
        
        self.subscribers[user_id] = {
            'times': notification_times,
            'enabled': True,
            'added_at': datetime.now()
        }
        
        logger.info(f"구독자 추가: {user_id}, 알림시간: {[t.strftime('%H:%M') for t in notification_times]}")
    
    def remove_subscriber(self, user_id: int):
        """구독자 제거"""
        if user_id in self.subscribers:
            del self.subscribers[user_id]
            logger.info(f"구독자 제거: {user_id}")
    
    def update_subscriber_times(self, user_id: int, notification_times: List[time]):
        """구독자 알림 시간 업데이트"""
        if user_id in self.subscribers:
            self.subscribers[user_id]['times'] = notification_times
            logger.info(f"구독자 {user_id} 알림시간 업데이트: {[t.strftime('%H:%M') for t in notification_times]}")
    
    def toggle_subscriber(self, user_id: int, enabled: bool):
        """구독자 알림 활성화/비활성화"""
        if user_id in self.subscribers:
            self.subscribers[user_id]['enabled'] = enabled
            status = "활성화" if enabled else "비활성화"
            logger.info(f"구독자 {user_id} 알림 {status}")
    
    def get_subscriber_info(self, user_id: int) -> Dict[str, Any]:
        """구독자 정보 조회"""
        return self.subscribers.get(user_id, None)
    
    def get_all_subscribers(self) -> Dict[int, Dict[str, Any]]:
        """모든 구독자 정보 조회"""
        return self.subscribers.copy()


# 전역 스케줄러 인스턴스 (나중에 봇에서 사용)
news_scheduler = None

def init_scheduler(bot_instance):
    """스케줄러 초기화"""
    global news_scheduler
    news_scheduler = NewsScheduler(bot_instance)
    return news_scheduler 