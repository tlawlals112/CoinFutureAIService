"""
거래 관련 데이터베이스 모델
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class SignalType(enum.Enum):
    """거래 신호 타입"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class PositionType(enum.Enum):
    """포지션 타입"""
    LONG = "LONG"
    SHORT = "SHORT"


class OrderType(enum.Enum):
    """주문 타입"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"


class OrderStatus(enum.Enum):
    """주문 상태"""
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class TradingSignal(Base):
    """거래 신호 모델"""
    __tablename__ = "trading_signals"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    signal_type = Column(Enum(SignalType), nullable=False)
    confidence = Column(Float, nullable=False)  # 0.0 ~ 1.0
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    leverage = Column(Integer, nullable=False, default=1)
    reasoning = Column(Text, nullable=True)
    llm_analysis = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    executed = Column(Boolean, default=False)
    
    # 관계
    trades = relationship("Trade", back_populates="signal")


class Trade(Base):
    """거래 기록 모델"""
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    signal_id = Column(Integer, nullable=True)
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)  # BUY, SELL
    order_type = Column(Enum(OrderType), nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    executed_price = Column(Float, nullable=True)
    status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    order_id = Column(String(100), nullable=True)  # 거래소 주문 ID
    fee = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    executed_at = Column(DateTime, nullable=True)
    
    # 관계
    signal = relationship("TradingSignal", back_populates="trades")
    position = relationship("Position", back_populates="trades")


class Position(Base):
    """포지션 모델"""
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    position_type = Column(Enum(PositionType), nullable=False)
    quantity = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=True)
    unrealized_pnl = Column(Float, nullable=True)
    realized_pnl = Column(Float, nullable=True)
    leverage = Column(Integer, nullable=False, default=1)
    margin_type = Column(String(20), nullable=False, default="ISOLATED")  # ISOLATED, CROSS
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    is_open = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    
    # 관계
    trades = relationship("Trade", back_populates="position")


class Portfolio(Base):
    """포트폴리오 모델"""
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    total_balance = Column(Float, nullable=False)
    available_balance = Column(Float, nullable=False)
    total_unrealized_pnl = Column(Float, nullable=True)
    total_realized_pnl = Column(Float, nullable=True)
    daily_pnl = Column(Float, nullable=True)
    weekly_pnl = Column(Float, nullable=True)
    monthly_pnl = Column(Float, nullable=True)
    win_rate = Column(Float, nullable=True)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MarketData(Base):
    """시장 데이터 모델"""
    __tablename__ = "market_data"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    
    # 기술적 지표
    rsi = Column(Float, nullable=True)
    macd = Column(Float, nullable=True)
    macd_signal = Column(Float, nullable=True)
    macd_histogram = Column(Float, nullable=True)
    bollinger_upper = Column(Float, nullable=True)
    bollinger_middle = Column(Float, nullable=True)
    bollinger_lower = Column(Float, nullable=True)
    sma_20 = Column(Float, nullable=True)
    sma_50 = Column(Float, nullable=True)
    ema_12 = Column(Float, nullable=True)
    ema_26 = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class LLMAnalysis(Base):
    """LLM 분석 결과 모델"""
    __tablename__ = "llm_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    llm_provider = Column(String(50), nullable=False)  # gpt4, claude, perplexity
    analysis_type = Column(String(50), nullable=False)  # market_analysis, risk_assessment, etc.
    input_data = Column(Text, nullable=True)
    output_data = Column(Text, nullable=False)
    confidence_score = Column(Float, nullable=True)
    processing_time = Column(Float, nullable=True)  # 초 단위
    cost = Column(Float, nullable=True)  # API 비용
    created_at = Column(DateTime, default=datetime.utcnow) 