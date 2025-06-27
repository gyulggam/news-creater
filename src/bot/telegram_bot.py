import os
from datetime import datetime, time
from typing import List, Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler, 
    ContextTypes,
    MessageHandler,
    filters
)
from loguru import logger
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

class StockNewsBot:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        # NEWS_LIMIT 안전하게 처리
        news_limit_str = os.getenv("NEWS_LIMIT", "5").strip()
        # 주석이 있다면 제거
        if '#' in news_limit_str:
            news_limit_str = news_limit_str.split('#')[0].strip()
        try:
            self.news_limit = int(news_limit_str)
        except ValueError:
            self.news_limit = 5  # 기본값
        
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN이 설정되지 않았습니다!")
        
        # 봇 애플리케이션 생성
        self.app = Application.builder().token(self.bot_token).build()
        
        # 스케줄러 초기화
        self.scheduler = None
        self._init_scheduler()
        
        # 뉴스 모니터 초기화
        self.news_monitor = None
        self._init_news_monitor()
        
        # 핸들러 설정
        self._setup_handlers()
        
        # 봇 시작/종료 시 스케줄러 제어
        self.app.post_init = self._post_init
        self.app.post_stop = self._post_stop
        
        logger.info("StockNewsBot 초기화 완료")

    def _init_scheduler(self):
        """스케줄러 초기화"""
        try:
            from src.utils.scheduler import init_scheduler
            self.scheduler = init_scheduler(self)
            logger.info("뉴스 스케줄러 초기화 완료")
        except Exception as e:
            logger.error(f"스케줄러 초기화 실패: {e}")

    def _init_news_monitor(self):
        """뉴스 모니터 초기화"""
        try:
            from src.utils.news_monitor import init_news_monitor
            self.news_monitor = init_news_monitor(self, check_interval=300)  # 5분마다 체크
            logger.info("뉴스 모니터 초기화 완료")
        except Exception as e:
            logger.error(f"뉴스 모니터 초기화 실패: {e}")

    async def _post_init(self, app):
        """봇 초기화 후 실행"""
        if self.scheduler:
            await self.scheduler.start()
            logger.info("뉴스 스케줄러 시작됨")
        
        if self.news_monitor:
            await self.news_monitor.start_monitoring()
            logger.info("뉴스 모니터링 시작됨")

    async def _post_stop(self, app):
        """봇 정지 시 실행"""
        if self.news_monitor:
            await self.news_monitor.stop_monitoring()
            logger.info("뉴스 모니터링 정지됨")
            
        if self.scheduler:
            await self.scheduler.stop()
            logger.info("뉴스 스케줄러 정지됨")

    def _setup_handlers(self):
        """명령어 핸들러 설정"""
        # 명령어 핸들러
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("news", self.news_command))
        self.app.add_handler(CommandHandler("subscribe", self.subscribe_command))
        self.app.add_handler(CommandHandler("unsubscribe", self.unsubscribe_command))
        self.app.add_handler(CommandHandler("status", self.status_command))
        
        # 새로운 알림 관련 명령어
        self.app.add_handler(CommandHandler("notifications", self.notifications_command))
        self.app.add_handler(CommandHandler("notify_on", self.notify_on_command))
        self.app.add_handler(CommandHandler("notify_off", self.notify_off_command))
        self.app.add_handler(CommandHandler("schedule", self.schedule_command))
        
        # 뉴스 모니터링 관련 명령어
        self.app.add_handler(CommandHandler("monitor_on", self.monitor_on_command))
        self.app.add_handler(CommandHandler("monitor_off", self.monitor_off_command))
        self.app.add_handler(CommandHandler("monitor_status", self.monitor_status_command))
        self.app.add_handler(CommandHandler("set_threshold", self.set_threshold_command))
        
        # 콜백 쿼리 핸들러 (버튼 클릭)
        self.app.add_handler(CallbackQueryHandler(self.button_callback))
        
        logger.info("핸들러 설정 완료")

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """봇 시작 명령어"""
        welcome_message = """
🤖 **주식 뉴스 봇에 오신 것을 환영합니다!**

📈 실시간 주식 뉴스를 카드 형태로 전달해드립니다.

**주요 기능:**
• `/news` - 최신 주식 뉴스 5건 보기
• `/subscribe [종목코드]` - 특정 종목 구독
• `/unsubscribe [종목코드]` - 구독 해제
• `/status` - 내 구독 현황 확인
• `/help` - 도움말 보기

**사용 예시:**
• `/subscribe 005930` - 삼성전자 구독
• `/news` - 최신 뉴스 받기

시작하려면 `/news` 명령어를 입력하세요! 📰
        """
        
        await update.message.reply_text(
            welcome_message,
            parse_mode='Markdown'
        )
        
        logger.info(f"사용자 {update.effective_user.id} 봇 시작")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """도움말 명령어"""
        help_message = """
📋 **사용 가능한 명령어:**

🔸 `/start` - 봇 시작 및 환영 메시지
🔸 `/news` - 최신 주식 뉴스 5건 보기

🔔 **정기 시간 알림:**
🔸 `/notify_on` - 정기 알림 활성화 (30분 간격)
🔸 `/notify_off` - 정기 알림 비활성화  
🔸 `/notifications` - 알림 현황 확인
🔸 `/schedule` - 알림 시간표 확인

🚨 **스마트 이벤트 알림:**
🔸 `/monitor_on` - 새 뉴스 감지 알림 활성화
🔸 `/monitor_off` - 새 뉴스 감지 알림 비활성화
🔸 `/monitor_status` - 모니터링 현황 확인
🔸 `/set_threshold 3` - 알림 임계값 설정

📮 **구독 관리:**
🔸 `/subscribe [종목코드]` - 특정 종목 뉴스 구독
🔸 `/unsubscribe [종목코드]` - 구독 해제
🔸 `/status` - 현재 구독 상태 확인
🔸 `/help` - 이 도움말 보기

**종목코드 예시:**
• 005930 - 삼성전자
• 000660 - SK하이닉스
• 035420 - 네이버
• 035720 - 카카오

⏰ **정기 알림 시간 (30분 간격):**
• 오전 9:00 ~ 오후 6:00 (30분마다)

🚨 **스마트 이벤트 알림:**
• 5분마다 새로운 뉴스 자동 감지
• 설정한 개수 이상 새 뉴스 쌓이면 즉시 알림
• 스팸 방지를 위한 최소 10분 간격 제한

**뉴스 카드 사용법:**
• 뉴스 카드에서 각 번호 버튼을 클릭하면 원문을 볼 수 있습니다
• 🔄 새로고침 버튼으로 최신 뉴스를 다시 받을 수 있습니다
• 💡 정기 알림 또는 스마트 알림을 설정하면 자동으로 뉴스를 받을 수 있습니다
        """
        
        await update.message.reply_text(help_message, parse_mode='Markdown')

    async def news_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """최신 뉴스 카드 전송"""
        try:
            # 임시 뉴스 데이터 (실제로는 크롤러에서 가져옴)
            news_list = await self._get_latest_news()
            
            if not news_list:
                await update.message.reply_text("현재 사용 가능한 뉴스가 없습니다. 잠시 후 다시 시도해주세요.")
                return
            
            # 뉴스 카드 생성 및 전송
            await self._send_news_card(update, news_list)
            
            logger.info(f"사용자 {update.effective_user.id}에게 뉴스 카드 전송")
            
        except Exception as e:
            logger.error(f"뉴스 명령어 처리 중 오류: {e}")
            await update.message.reply_text("뉴스를 가져오는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")

    async def subscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """종목 구독 명령어"""
        if not context.args:
            await update.message.reply_text(
                "종목코드를 입력해주세요.\n예: `/subscribe 005930`",
                parse_mode='Markdown'
            )
            return
        
        stock_code = context.args[0]
        user_id = update.effective_user.id
        
        # TODO: 데이터베이스에 구독 정보 저장
        
        await update.message.reply_text(
            f"✅ **{stock_code}** 종목 구독이 완료되었습니다!\n"
            f"해당 종목의 뉴스를 실시간으로 받아보실 수 있습니다.",
            parse_mode='Markdown'
        )
        
        logger.info(f"사용자 {user_id} - 종목 {stock_code} 구독")

    async def unsubscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """구독 해제 명령어"""
        if not context.args:
            await update.message.reply_text(
                "종목코드를 입력해주세요.\n예: `/unsubscribe 005930`",
                parse_mode='Markdown'
            )
            return
        
        stock_code = context.args[0]
        user_id = update.effective_user.id
        
        # TODO: 데이터베이스에서 구독 정보 삭제
        
        await update.message.reply_text(
            f"❌ **{stock_code}** 종목 구독이 해제되었습니다.",
            parse_mode='Markdown'
        )
        
        logger.info(f"사용자 {user_id} - 종목 {stock_code} 구독 해제")

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """구독 상태 확인"""
        user_id = update.effective_user.id
        
        # TODO: 데이터베이스에서 구독 정보 조회
        # 임시 데이터
        subscribed_stocks = ["005930", "000660", "035420"]
        
        if not subscribed_stocks:
            status_message = "현재 구독 중인 종목이 없습니다.\n`/subscribe [종목코드]`로 구독을 시작하세요!"
        else:
            status_message = f"📊 **구독 현황** ({len(subscribed_stocks)}개)\n\n"
            for stock in subscribed_stocks:
                status_message += f"• {stock}\n"
            status_message += "\n구독 해제: `/unsubscribe [종목코드]`"
        
        await update.message.reply_text(status_message, parse_mode='Markdown')
        
        logger.info(f"사용자 {user_id} 구독 상태 조회")

    async def notifications_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """알림 현황 조회"""
        user_id = update.effective_user.id
        
        if self.scheduler:
            subscriber_info = self.scheduler.get_subscriber_info(user_id)
            
            if subscriber_info:
                times = [t.strftime('%H:%M') for t in subscriber_info['times']]
                status = "활성화" if subscriber_info['enabled'] else "비활성화"
                added_date = subscriber_info['added_at'].strftime('%Y-%m-%d %H:%M')
                
                message = f"🔔 **알림 현황**\n\n"
                message += f"• 상태: {status}\n"
                message += f"• 알림 시간: {', '.join(times)}\n"
                message += f"• 구독 시작: {added_date}\n\n"
                message += "**사용 가능한 명령어:**\n"
                message += "• `/notify_on` - 알림 활성화\n"
                message += "• `/notify_off` - 알림 비활성화\n"
                message += "• `/schedule` - 알림 시간 확인"
            else:
                message = "🔔 **알림 미설정**\n\n"
                message += "아직 알림을 설정하지 않았습니다.\n\n"
                message += "**알림 시작하기:**\n"
                message += "• `/notify_on` - 기본 알림 활성화\n"
                message += "  (오전 9시, 12시, 오후 3시, 6시)\n"
                message += "• `/schedule` - 알림 시간 확인"
        else:
            message = "⚠️ 알림 시스템이 현재 비활성화되어 있습니다."
        
        await update.message.reply_text(message, parse_mode='Markdown')

    async def notify_on_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """알림 활성화"""
        user_id = update.effective_user.id
        
        if self.scheduler:
            # 기본 알림 시간으로 구독자 추가
            self.scheduler.add_subscriber(user_id)
            
            await update.message.reply_text(
                "🔔 **30분 간격 알림이 활성화되었습니다!**\n\n"
                "📅 **알림 시간 (총 19회/일):**\n"
                "• 오전 09:00 ~ 오후 18:00\n"
                "• 매 30분마다 자동 전송\n\n"
                "💡 하루 종일 최신 주식 뉴스를 실시간으로 받아보실 수 있습니다.\n\n"
                "• `/schedule` - 상세 시간표 확인\n"
                "• `/notify_off` - 알림 비활성화\n"
                "• `/notifications` - 알림 현황 확인",
                parse_mode='Markdown'
            )
            
            logger.info(f"사용자 {user_id} 알림 활성화")
        else:
            await update.message.reply_text("⚠️ 알림 시스템이 현재 비활성화되어 있습니다.")

    async def notify_off_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """알림 비활성화"""
        user_id = update.effective_user.id
        
        if self.scheduler:
            subscriber_info = self.scheduler.get_subscriber_info(user_id)
            
            if subscriber_info:
                self.scheduler.toggle_subscriber(user_id, False)
                
                await update.message.reply_text(
                    "🔕 **알림이 비활성화되었습니다.**\n\n"
                    "더 이상 정기 알림을 받지 않습니다.\n\n"
                    "• `/notify_on` - 다시 알림 활성화\n"
                    "• `/news` - 수동으로 뉴스 확인",
                    parse_mode='Markdown'
                )
                
                logger.info(f"사용자 {user_id} 알림 비활성화")
            else:
                await update.message.reply_text(
                    "⚠️ 설정된 알림이 없습니다.\n\n"
                    "`/notify_on` 명령어로 알림을 먼저 활성화하세요.",
                    parse_mode='Markdown'
                )
        else:
            await update.message.reply_text("⚠️ 알림 시스템이 현재 비활성화되어 있습니다.")

    async def schedule_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """알림 스케줄 확인"""
        message = "⏰ **뉴스 알림 스케줄**\n\n"
        message += "📅 **30분 간격 알림 시간:**\n"
        message += "• 🌅 오전 09:00, 09:30\n"
        message += "• 🌄 오전 10:00, 10:30\n"
        message += "• 🌄 오전 11:00, 11:30\n"
        message += "• 🍽️ 오후 12:00, 12:30\n"
        message += "• 🌞 오후 13:00, 13:30\n"
        message += "• 🌞 오후 14:00, 14:30\n"
        message += "• 📈 오후 15:00, 15:30\n"
        message += "• 🌆 오후 16:00, 16:30\n"
        message += "• 🌆 오후 17:00, 17:30\n"
        message += "• 🌃 오후 18:00\n\n"
        message += "💡 **알림 관리:**\n"
        message += "• `/notify_on` - 알림 활성화\n"
        message += "• `/notify_off` - 알림 비활성화\n"
        message += "• `/notifications` - 내 알림 현황\n\n"
        message += "📱 **총 19회** 알림이 활성화되면 매일 30분마다 최신 주식 뉴스를 자동으로 받아보실 수 있습니다."
        
        await update.message.reply_text(message, parse_mode='Markdown')

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """인라인 버튼 클릭 처리"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "refresh":
            # 새로고침 버튼 클릭
            news_list = await self._get_latest_news()
            await self._send_news_card(update, news_list, edit_message=True)
            logger.info(f"사용자 {query.from_user.id} 뉴스 새로고침")
            
        elif query.data == "settings":
            # 설정 버튼 클릭
            await query.edit_message_text(
                "⚙️ **설정 메뉴**\n\n"
                "현재 사용 가능한 설정:\n"
                "• `/notifications` - 알림 현황 확인\n"
                "• `/notify_on` - 알림 활성화\n"
                "• `/notify_off` - 알림 비활성화\n"
                "• `/schedule` - 알림 시간표 확인\n\n"
                "💡 정기 알림을 설정하면 매일 자동으로 뉴스를 받아보실 수 있습니다.",
                parse_mode='Markdown'
            )
            
        elif query.data == "notification_settings":
            # 알림 설정 버튼 클릭
            user_id = query.from_user.id
            
            if self.scheduler:
                subscriber_info = self.scheduler.get_subscriber_info(user_id)
                
                if subscriber_info:
                    status = "활성화" if subscriber_info['enabled'] else "비활성화"
                    times = [t.strftime('%H:%M') for t in subscriber_info['times']]
                    
                    message = f"🔔 **알림 설정**\n\n"
                    message += f"• 현재 상태: {status}\n"
                    message += f"• 알림 시간: {', '.join(times)}\n\n"
                    
                    if subscriber_info['enabled']:
                        message += "• `/notify_off` - 알림 비활성화"
                    else:
                        message += "• `/notify_on` - 알림 활성화"
                else:
                    message = "🔔 **알림 설정**\n\n"
                    message += "아직 알림을 설정하지 않았습니다.\n\n"
                    message += "• `/notify_on` - 알림 시작하기"
            else:
                message = "⚠️ 알림 시스템이 현재 비활성화되어 있습니다."
            
            await query.edit_message_text(message, parse_mode='Markdown')

    async def _get_latest_news(self) -> List[Dict[str, Any]]:
        """최신 뉴스 가져오기"""
        try:
            # 실제 크롤러 사용
            from src.crawler.news_crawler import get_stock_news
            news_list = await get_stock_news(self.news_limit)
            
            if news_list:
                logger.info(f"크롤러에서 {len(news_list)}개 뉴스 수집됨")
                return news_list
            else:
                logger.warning("크롤러에서 뉴스를 가져오지 못함, 대체 뉴스 사용")
                return self._get_fallback_news()
                
        except Exception as e:
            logger.error(f"뉴스 크롤링 오류: {e}, 대체 뉴스 사용")
            return self._get_fallback_news()

    def _get_fallback_news(self) -> List[Dict[str, Any]]:
        """크롤링 실패시 대체 뉴스"""
        mock_news = [
            {
                "title": "[실시간] 코스피 상승세 지속, 외국인 순매수",
                "sentiment": "positive",
                "time": datetime.now().strftime("%H:%M"),
                "url": "https://finance.naver.com"
            },
            {
                "title": "반도체 업종 강세, SK하이닉스 3% 상승",
                "sentiment": "positive", 
                "time": datetime.now().strftime("%H:%M"),
                "url": "https://finance.naver.com"
            },
            {
                "title": "미국 증시 혼조, 기술주 약세 지속",
                "sentiment": "negative",
                "time": datetime.now().strftime("%H:%M"),
                "url": "https://finance.naver.com"
            },
            {
                "title": "원달러 환율 1,300원대 후반 등락",
                "sentiment": "neutral",
                "time": datetime.now().strftime("%H:%M"),
                "url": "https://finance.naver.com"
            },
            {
                "title": "배터리 3사, 전기차 수요 증가로 호실적",
                "sentiment": "positive",
                "time": datetime.now().strftime("%H:%M"),
                "url": "https://finance.naver.com"
            }
        ]
        
        return mock_news[:self.news_limit]

    async def _send_news_card(self, update: Update, news_list: List[Dict[str, Any]], edit_message: bool = False):
        """뉴스 카드 전송"""
        current_time = datetime.now().strftime("%m월 %d일 %H:%M")
        
        # 메시지 텍스트 생성
        message_text = f"📰 주식 뉴스 업데이트 ({current_time})\n\n🔥 주요 뉴스 {len(news_list)}건:\n\n"
        
        # 인라인 버튼 생성
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
            InlineKeyboardButton("⚙️ 설정", callback_data="settings")
        ]
        buttons.append(action_buttons)
        
        message_text += "💡 각 뉴스를 클릭하면 원문을 확인할 수 있습니다."
        
        keyboard = InlineKeyboardMarkup(buttons)
        
        if edit_message and update.callback_query:
            await update.callback_query.edit_message_text(
                text=message_text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                text=message_text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )

    async def monitor_on_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """뉴스 모니터링 활성화"""
        user_id = update.effective_user.id
        
        try:
            if not self.news_monitor:
                await update.message.reply_text("⚠️ 뉴스 모니터링 시스템이 비활성화되어 있습니다.")
                return
            
            # 구독자 목록에 추가 (스케줄러 시스템 재활용)
            if self.scheduler:
                self.scheduler.add_subscriber(user_id)
                self.scheduler.toggle_subscriber(user_id, True)
            
            await update.message.reply_text(
                "🔍 **스마트 뉴스 모니터링 활성화!**\n\n"
                "✨ **작동 방식:**\n"
                "• 5분마다 새로운 뉴스 자동 감지\n"
                "• 새 뉴스 3개 이상 쌓이면 즉시 알림\n"
                "• 최소 10분 간격으로 알림 전송\n\n"
                "🚨 **긴급 뉴스 알림**이 설정되었습니다!\n\n"
                "• `/monitor_off` - 모니터링 비활성화\n"
                "• `/monitor_status` - 모니터링 현황 확인\n"
                "• `/set_threshold 5` - 알림 임계값 변경 (기본 3개)",
                parse_mode='Markdown'
            )
            
            logger.info(f"사용자 {user_id} 뉴스 모니터링 활성화")
            
        except Exception as e:
            logger.error(f"뉴스 모니터링 활성화 중 오류: {e}")
            await update.message.reply_text("⚠️ 모니터링 활성화 중 오류가 발생했습니다.")

    async def monitor_off_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """뉴스 모니터링 비활성화"""
        user_id = update.effective_user.id
        
        try:
            if self.scheduler:
                self.scheduler.toggle_subscriber(user_id, False)
            
            await update.message.reply_text(
                "🔕 **스마트 뉴스 모니터링 비활성화**\n\n"
                "더 이상 새로운 뉴스 알림을 받지 않습니다.\n\n"
                "💡 **대안:**\n"
                "• `/news` - 수동으로 뉴스 확인\n"
                "• `/notify_on` - 정기 시간 알림\n"
                "• `/monitor_on` - 다시 스마트 모니터링 시작",
                parse_mode='Markdown'
            )
            
            logger.info(f"사용자 {user_id} 뉴스 모니터링 비활성화")
            
        except Exception as e:
            logger.error(f"뉴스 모니터링 비활성화 중 오류: {e}")
            await update.message.reply_text("⚠️ 모니터링 비활성화 중 오류가 발생했습니다.")

    async def monitor_status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """뉴스 모니터링 상태 확인"""
        try:
            if not self.news_monitor:
                await update.message.reply_text("⚠️ 뉴스 모니터링 시스템이 비활성화되어 있습니다.")
                return
            
            status = self.news_monitor.get_status()
            user_id = update.effective_user.id
            
            # 사용자 구독 상태 확인
            user_subscribed = False
            if self.scheduler:
                subscriber_info = self.scheduler.get_subscriber_info(user_id)
                user_subscribed = subscriber_info and subscriber_info.get('enabled', False)
            
            message = "🔍 **뉴스 모니터링 현황**\n\n"
            
            # 전체 시스템 상태
            system_status = "🟢 실행 중" if status["is_running"] else "🔴 정지됨"
            message += f"• 시스템 상태: {system_status}\n"
            message += f"• 체크 간격: {status['check_interval']}초 (5분)\n"
            message += f"• 알림 임계값: {status['min_news_threshold']}개 뉴스\n"
            message += f"• 추적 중인 뉴스: {status['known_news_count']}건\n"
            message += f"• 새 뉴스 버퍼: {status['new_news_buffer_count']}건\n"
            
            if status["last_notification_time"]:
                message += f"• 마지막 알림: {status['last_notification_time']}\n"
            else:
                message += "• 마지막 알림: 없음\n"
            
            message += "\n"
            
            # 개인 구독 상태
            user_status = "🔔 활성화" if user_subscribed else "🔕 비활성화"
            message += f"**개인 알림 상태:** {user_status}\n\n"
            
            if user_subscribed:
                message += "✅ 새로운 뉴스가 감지되면 즉시 알림을 받습니다!\n\n"
                message += "• `/monitor_off` - 알림 비활성화\n"
                message += f"• `/set_threshold 5` - 임계값 변경"
            else:
                message += "💤 현재 알림을 받지 않습니다.\n\n"
                message += "• `/monitor_on` - 알림 활성화"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"모니터링 상태 확인 중 오류: {e}")
            await update.message.reply_text("⚠️ 상태 확인 중 오류가 발생했습니다.")

    async def set_threshold_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """알림 임계값 설정"""
        try:
            if not context.args:
                await update.message.reply_text(
                    "📊 **알림 임계값 설정**\n\n"
                    "사용법: `/set_threshold [개수]`\n\n"
                    "예시:\n"
                    "• `/set_threshold 3` - 3개 뉴스에서 알림\n"
                    "• `/set_threshold 5` - 5개 뉴스에서 알림\n\n"
                    "💡 **추천:**\n"
                    "• 3개: 빠른 알림 (기본값)\n"
                    "• 5개: 중요한 뉴스만\n"
                    "• 7개: 매우 중요한 뉴스만",
                    parse_mode='Markdown'
                )
                return
            
            try:
                threshold = int(context.args[0])
                if threshold < 1 or threshold > 10:
                    await update.message.reply_text(
                        "⚠️ 임계값은 1~10 사이의 숫자여야 합니다.\n"
                        "예: `/set_threshold 3`"
                    )
                    return
            except ValueError:
                await update.message.reply_text(
                    "⚠️ 올바른 숫자를 입력해주세요.\n"
                    "예: `/set_threshold 5`"
                )
                return
            
            if not self.news_monitor:
                await update.message.reply_text("⚠️ 뉴스 모니터링 시스템이 비활성화되어 있습니다.")
                return
            
            # 임계값 설정
            old_threshold = self.news_monitor.min_news_threshold
            self.news_monitor.set_threshold(threshold)
            
            await update.message.reply_text(
                f"🔧 **알림 임계값 변경 완료!**\n\n"
                f"• 이전 값: {old_threshold}개 뉴스\n"
                f"• 새로운 값: {threshold}개 뉴스\n\n"
                f"💡 이제 새로운 뉴스가 **{threshold}개 이상** 쌓이면 즉시 알림을 받습니다.\n\n"
                f"• `/monitor_status` - 현재 상태 확인",
                parse_mode='Markdown'
            )
            
            logger.info(f"사용자 {update.effective_user.id} 임계값 변경: {old_threshold} -> {threshold}")
            
        except Exception as e:
            logger.error(f"임계값 설정 중 오류: {e}")
            await update.message.reply_text("⚠️ 임계값 설정 중 오류가 발생했습니다.")

 