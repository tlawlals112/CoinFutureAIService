"""
애플리케이션 설정 관리
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # 데이터베이스 설정
    database_url: str = Field(
        default="postgresql://username:password@localhost:5432/trading_db",
        env="DATABASE_URL"
    )
    
    # Redis 설정
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL"
    )
    
    # Binance API 설정
    binance_api_key: str = Field(env="BINANCE_API_KEY")
    binance_secret_key: str = Field(env="BINANCE_SECRET_KEY")
    binance_testnet: bool = Field(default=False, env="BINANCE_TESTNET")
    
    # LLM API 설정
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    google_api_key: Optional[str] = Field(default=None, env="GOOGLE_API_KEY")
    
    # Telegram Bot 설정
    telegram_bot_token: str = Field(env="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str = Field(env="TELEGRAM_CHAT_ID")
    
    # 거래 설정
    max_position_size: float = Field(default=0.1, env="MAX_POSITION_SIZE")
    max_daily_loss: float = Field(default=0.02, env="MAX_DAILY_LOSS")
    max_leverage: int = Field(default=20, env="MAX_LEVERAGE")
    stop_loss_percentage: float = Field(default=0.05, env="STOP_LOSS_PERCENTAGE")
    
    # 로깅 설정
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/trading_system.log", env="LOG_FILE")
    
    # 서버 설정
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # 모니터링 설정
    prometheus_port: int = Field(default=9090, env="PROMETHEUS_PORT")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# 전역 설정 인스턴스
settings = Settings()


# 거래소별 설정
EXCHANGE_CONFIG = {
    'binance': {
        'max_leverage': 125,
        'min_order_size': 0.001,
        'fee_maker': 0.0002,
        'fee_taker': 0.0004,
        'supported_symbols': [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT',
            'DOTUSDT', 'LINKUSDT', 'LTCUSDT', 'BCHUSDT', 'XRPUSDT'
        ]
    }
}

# 거래 한도 설정
TRADING_LIMITS = {
    'max_position_size': settings.max_position_size,
    'max_daily_loss': settings.max_daily_loss,
    'max_leverage': settings.max_leverage,
    'stop_loss_percentage': settings.stop_loss_percentage,
    'take_profit_percentage': 0.1,  # 10% 익절
    'max_open_positions': 5,  # 최대 5개 포지션
    'min_balance_threshold': 100  # 최소 잔고 100 USDT
}

# LLM 설정
LLM_CONFIG = {
    'gpt4': {
        'model': 'gpt-4-turbo-preview',
        'max_tokens': 1000,
        'temperature': 0.3,
        'weight': 0.5  # 앙상블 가중치
    },
    'claude': {
        'model': 'claude-3-sonnet-20240229',
        'max_tokens': 1000,
        'temperature': 0.3,
        'weight': 0.3
    },
    'perplexity': {
        'model': 'llama-3.1-sonar-small-128k-online',
        'max_tokens': 1000,
        'temperature': 0.3,
        'weight': 0.2
    }
}

# 알림 설정
NOTIFICATION_CONFIG = {
    'telegram': {
        'enabled': True,
        'chat_id': settings.telegram_chat_id,
        'bot_token': settings.telegram_bot_token,
        'notification_types': [
            'trade_execution',
            'profit_loss',
            'system_status',
            'risk_alert',
            'daily_report'
        ]
    }
} 