"""
알림 관련 데이터베이스 모델
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()


class NotificationType(enum.Enum):
    """알림 타입"""
    TRADE_EXECUTION = "TRADE_EXECUTION"
    PROFIT_LOSS = "PROFIT_LOSS"
    SYSTEM_STATUS = "SYSTEM_STATUS"
    RISK_ALERT = "RISK_ALERT"
    DAILY_REPORT = "DAILY_REPORT"
    WEEKLY_REPORT = "WEEKLY_REPORT"
    MONTHLY_REPORT = "MONTHLY_REPORT"


class NotificationStatus(enum.Enum):
    """알림 상태"""
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"


class NotificationChannel(enum.Enum):
    """알림 채널"""
    TELEGRAM = "TELEGRAM"
    EMAIL = "EMAIL"
    SMS = "SMS"


class Notification(Base):
    """알림 모델"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    notification_type = Column(Enum(NotificationType), nullable=False)
    channel = Column(Enum(NotificationChannel), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    data = Column(Text, nullable=True)  # JSON 형태의 추가 데이터
    status = Column(Enum(NotificationStatus), nullable=False, default=NotificationStatus.PENDING)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계
    history = relationship("NotificationHistory", back_populates="notification")


class NotificationHistory(Base):
    """알림 히스토리 모델"""
    __tablename__ = "notification_history"
    
    id = Column(Integer, primary_key=True, index=True)
    notification_id = Column(Integer, nullable=False)
    status = Column(Enum(NotificationStatus), nullable=False)
    error_message = Column(Text, nullable=True)
    response_data = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계
    notification = relationship("Notification", back_populates="history")


class NotificationTemplate(Base):
    """알림 템플릿 모델"""
    __tablename__ = "notification_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    template_name = Column(String(100), nullable=False, unique=True)
    notification_type = Column(Enum(NotificationType), nullable=False)
    channel = Column(Enum(NotificationChannel), nullable=False)
    title_template = Column(String(200), nullable=False)
    message_template = Column(Text, nullable=False)
    variables = Column(Text, nullable=True)  # JSON 형태의 변수 정의
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class NotificationSettings(Base):
    """알림 설정 모델"""
    __tablename__ = "notification_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, unique=True)
    telegram_enabled = Column(Boolean, default=True)
    telegram_chat_id = Column(String(100), nullable=True)
    email_enabled = Column(Boolean, default=False)
    email_address = Column(String(200), nullable=True)
    sms_enabled = Column(Boolean, default=False)
    phone_number = Column(String(20), nullable=True)
    
    # 알림 타입별 설정
    trade_execution_enabled = Column(Boolean, default=True)
    profit_loss_enabled = Column(Boolean, default=True)
    system_status_enabled = Column(Boolean, default=True)
    risk_alert_enabled = Column(Boolean, default=True)
    daily_report_enabled = Column(Boolean, default=True)
    weekly_report_enabled = Column(Boolean, default=True)
    monthly_report_enabled = Column(Boolean, default=True)
    
    # 알림 시간 설정
    quiet_hours_start = Column(String(5), nullable=True)  # HH:MM
    quiet_hours_end = Column(String(5), nullable=True)    # HH:MM
    timezone = Column(String(50), default="Asia/Seoul")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 