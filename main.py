#!/usr/bin/env python3
"""
주식 뉴스 텔레그램 봇 메인 실행 파일
StockNewsBot - 실시간 주식 뉴스를 텔레그램으로 전달하는 봇

사용법:
    python main.py

환경 변수 설정이 필요합니다:
    - TELEGRAM_BOT_TOKEN: 텔레그램 봇 토큰
    - 기타 설정은 config.env.example 참고
"""

import sys
import os
from loguru import logger
from dotenv import load_dotenv
from telegram import Update

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.bot.telegram_bot import StockNewsBot

def setup_logging():
    """로깅 설정"""
    # 기본 로거 제거
    logger.remove()
    
    # 콘솔 로깅 설정
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    # 파일 로깅 설정
    logger.add(
        "logs/stocknews_bot.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="1 day",
        retention="30 days",
        compression="zip"
    )

def check_environment():
    """필수 환경 변수 확인"""
    load_dotenv()
    
    required_vars = ["TELEGRAM_BOT_TOKEN"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"필수 환경 변수가 설정되지 않았습니다: {', '.join(missing_vars)}")
        logger.error("config.env.example 파일을 참고하여 .env 파일을 생성하세요.")
        return False
    
    return True

def main():
    """메인 함수"""
    print("🤖 StockNewsBot 시작 중...")
    
    # 로깅 설정
    setup_logging()
    
    # 환경 변수 확인
    if not check_environment():
        sys.exit(1)
    
    try:
        # 봇 인스턴스 생성 및 실행
        bot = StockNewsBot()
        logger.info("봇 초기화 완료, 실행 중...")
        
        # 봇 실행 (동기 방식)
        bot.app.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
        
    except KeyboardInterrupt:
        logger.info("사용자에 의해 봇이 중단되었습니다.")
    except Exception as e:
        logger.error(f"봇 실행 중 오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 봇이 안전하게 종료되었습니다.")
    except Exception as e:
        print(f"❌ 오류가 발생했습니다: {e}")
        sys.exit(1) 