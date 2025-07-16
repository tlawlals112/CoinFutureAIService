"""
로깅 설정 및 관리
"""

import os
import sys
from pathlib import Path
from loguru import logger
from app.config import settings

# 로그 디렉토리 생성
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# 기본 로거 제거
logger.remove()

# 콘솔 로거 추가
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.log_level,
    colorize=True
)

# 파일 로거 추가
logger.add(
    settings.log_file,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level=settings.log_level,
    rotation="1 day",
    retention="30 days",
    compression="zip"
)

# 에러 로그 파일 추가
logger.add(
    "logs/error.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="ERROR",
    rotation="1 day",
    retention="90 days",
    compression="zip"
)

# 거래 로그 파일 추가
logger.add(
    "logs/trading.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="INFO",
    filter=lambda record: "trading" in record["name"].lower(),
    rotation="1 day",
    retention="30 days",
    compression="zip"
)

# LLM 로그 파일 추가
logger.add(
    "logs/llm.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="INFO",
    filter=lambda record: "llm" in record["name"].lower(),
    rotation="1 day",
    retention="30 days",
    compression="zip"
)


def get_logger(name: str):
    """특정 이름의 로거 반환"""
    return logger.bind(name=name)


def log_trade(symbol: str, action: str, quantity: float, price: float, **kwargs):
    """거래 로그 기록"""
    trade_logger = get_logger("trading")
    trade_logger.info(
        f"거래 실행 - 심볼: {symbol}, 액션: {action}, "
        f"수량: {quantity}, 가격: {price}, 추가정보: {kwargs}"
    )


def log_llm_request(provider: str, model: str, input_data: str, output_data: str, **kwargs):
    """LLM 요청 로그 기록"""
    llm_logger = get_logger("llm")
    llm_logger.info(
        f"LLM 요청 - 제공자: {provider}, 모델: {model}, "
        f"입력: {input_data[:100]}..., 출력: {output_data[:100]}..., 추가정보: {kwargs}"
    )


def log_error(error: Exception, context: str = ""):
    """에러 로그 기록"""
    error_logger = get_logger("error")
    error_logger.error(f"에러 발생 - 컨텍스트: {context}, 에러: {str(error)}")


def log_system_status(status: str, details: dict = None):
    """시스템 상태 로그 기록"""
    system_logger = get_logger("system")
    system_logger.info(f"시스템 상태: {status}, 상세정보: {details}")


def log_performance(operation: str, duration: float, **kwargs):
    """성능 로그 기록"""
    perf_logger = get_logger("performance")
    perf_logger.info(f"성능 측정 - 작업: {operation}, 소요시간: {duration:.3f}초, 추가정보: {kwargs}")


# 로거 초기화 완료 메시지
logger.info("로깅 시스템이 초기화되었습니다.")
logger.info(f"로그 레벨: {settings.log_level}")
logger.info(f"로그 파일: {settings.log_file}") 