import os
from datetime import datetime
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
        self._setup_handlers()
        
        logger.info("StockNewsBot 초기화 완료")

    def _setup_handlers(self):
        """명령어 핸들러 설정"""
        # 명령어 핸들러
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("news", self.news_command))
        self.app.add_handler(CommandHandler("subscribe", self.subscribe_command))
        self.app.add_handler(CommandHandler("unsubscribe", self.unsubscribe_command))
        self.app.add_handler(CommandHandler("status", self.status_command))
        
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
🔸 `/subscribe [종목코드]` - 특정 종목 뉴스 구독
🔸 `/unsubscribe [종목코드]` - 구독 해제
🔸 `/status` - 현재 구독 상태 확인
🔸 `/help` - 이 도움말 보기

**종목코드 예시:**
• 005930 - 삼성전자
• 000660 - SK하이닉스
• 035420 - 네이버
• 035720 - 카카오

**뉴스 카드 사용법:**
• 뉴스 카드에서 각 번호 버튼을 클릭하면 원문을 볼 수 있습니다
• 🔄 새로고침 버튼으로 최신 뉴스를 다시 받을 수 있습니다
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
                "• 알림 시간 설정 (개발 예정)\n"
                "• 키워드 설정 (개발 예정)\n\n"
                "설정을 변경하려면 명령어를 사용하세요.",
                parse_mode='Markdown'
            )

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

 