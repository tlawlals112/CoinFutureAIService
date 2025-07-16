"""
데이터베이스 연결 및 세션 관리
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from contextlib import contextmanager
from typing import Generator
from loguru import logger

from app.config import settings

# 데이터베이스 엔진 생성
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.debug
)

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 베이스 클래스
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """데이터베이스 세션 생성"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"데이터베이스 세션 오류: {e}")
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """컨텍스트 매니저를 사용한 데이터베이스 세션"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"데이터베이스 세션 오류: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """데이터베이스 초기화"""
    try:
        # 모든 테이블 생성
        from app.models.trading_models import Base as TradingBase
        from app.models.notification_models import Base as NotificationBase
        
        TradingBase.metadata.create_all(bind=engine)
        NotificationBase.metadata.create_all(bind=engine)
        
        logger.info("데이터베이스 테이블이 성공적으로 생성되었습니다.")
    except Exception as e:
        logger.error(f"데이터베이스 초기화 오류: {e}")
        raise


def check_db_connection() -> bool:
    """데이터베이스 연결 확인"""
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        logger.info("데이터베이스 연결이 정상입니다.")
        return True
    except Exception as e:
        logger.error(f"데이터베이스 연결 오류: {e}")
        return False


def get_db_info():
    """데이터베이스 정보 조회"""
    try:
        with engine.connect() as connection:
            # PostgreSQL 버전 확인
            result = connection.execute("SELECT version()")
            version = result.fetchone()[0]
            
            # 테이블 목록 확인
            result = connection.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = [row[0] for row in result.fetchall()]
            
            return {
                "version": version,
                "tables": tables,
                "connection_status": "connected"
            }
    except Exception as e:
        logger.error(f"데이터베이스 정보 조회 오류: {e}")
        return {
            "version": "unknown",
            "tables": [],
            "connection_status": "error",
            "error": str(e)
        } 