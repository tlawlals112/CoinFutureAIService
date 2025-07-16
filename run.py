#!/usr/bin/env python3
"""
AI 거래 시스템 실행 스크립트
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.config import settings
from app.utils.database import init_db
from app.services.ai_engine import AIEngine
from loguru import logger


def setup_logging():
    """로깅 설정"""
    logger.remove()  # 기본 핸들러 제거
    
    # 콘솔 출력
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    # 파일 출력
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logger.add(
        log_dir / "ai_trading_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="1 day",
        retention="30 days"
    )


def check_environment():
    """환경 설정 확인"""
    required_vars = [
        'BINANCE_API_KEY',
        'BINANCE_SECRET_KEY',
        'OPENAI_API_KEY',
        'ANTHROPIC_API_KEY',
        'TELEGRAM_BOT_TOKEN',
        'TELEGRAM_CHAT_ID'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not getattr(settings, var.lower(), None):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"필수 환경 변수가 설정되지 않았습니다: {', '.join(missing_vars)}")
        logger.info("env_example.txt 파일을 참고하여 .env 파일을 생성하세요.")
        return False
    
    return True


async def run_ai_trading():
    """AI 거래 실행"""
    try:
        logger.info("AI 거래 시스템을 시작합니다...")
        
        # 데이터베이스 초기화
        logger.info("데이터베이스 초기화 중...")
        init_db()
        logger.info("데이터베이스 초기화 완료")
        
        # AI 엔진 생성 및 시작
        logger.info("AI 엔진 초기화 중...")
        ai_engine = AIEngine()
        logger.info("AI 엔진 초기화 완료")
        
        # AI 거래 시작
        logger.info("AI 거래를 시작합니다...")
        await ai_engine.start_ai_trading()
        
    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단되었습니다.")
    except Exception as e:
        logger.error(f"AI 거래 실행 중 오류 발생: {e}")
        raise


def run_web_server():
    """웹 서버 실행"""
    try:
        import uvicorn
        logger.info("웹 서버를 시작합니다...")
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info"
        )
    except ImportError:
        logger.error("uvicorn이 설치되지 않았습니다. 'pip install uvicorn'을 실행하세요.")
    except Exception as e:
        logger.error(f"웹 서버 실행 중 오류 발생: {e}")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="AI 거래 시스템")
    parser.add_argument(
        "--mode",
        choices=["trading", "web", "both"],
        default="both",
        help="실행 모드 선택 (trading: AI 거래만, web: 웹 서버만, both: 둘 다)"
    )
    parser.add_argument(
        "--check-env",
        action="store_true",
        help="환경 설정만 확인"
    )
    
    args = parser.parse_args()
    
    # 로깅 설정
    setup_logging()
    
    # 환경 설정 확인
    if not check_environment():
        sys.exit(1)
    
    if args.check_env:
        logger.info("환경 설정이 올바르게 구성되었습니다.")
        return
    
    try:
        if args.mode == "trading":
            # AI 거래만 실행
            asyncio.run(run_ai_trading())
        elif args.mode == "web":
            # 웹 서버만 실행
            run_web_server()
        else:
            # 둘 다 실행 (별도 프로세스)
            import subprocess
            import threading
            
            def run_trading():
                asyncio.run(run_ai_trading())
            
            def run_web():
                run_web_server()
            
            # AI 거래를 별도 스레드에서 실행
            trading_thread = threading.Thread(target=run_trading, daemon=True)
            trading_thread.start()
            
            # 웹 서버를 메인 스레드에서 실행
            run_web()
            
    except KeyboardInterrupt:
        logger.info("프로그램이 중단되었습니다.")
    except Exception as e:
        logger.error(f"프로그램 실행 중 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 