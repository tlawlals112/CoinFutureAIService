"""
API 라우터 정의
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional
import asyncio

from app.services.ai_engine import AIEngine
from app.services.data_collector import DataCollector
from app.services.trading_executor import TradingExecutor
from app.services.notification_service import NotificationService
from app.utils.database import get_db_session
from app.models.trading_models import Trade, Position, TradingSignal
from app.models.notification_models import Notification

# 라우터 생성
router = APIRouter(prefix="/api/v1", tags=["AI Trading API"])

# 서비스 인스턴스
ai_engine = AIEngine()
data_collector = DataCollector()
trading_executor = TradingExecutor()
notification_service = NotificationService()


# ==================== 시스템 제어 API ====================

@router.post("/system/start")
async def start_ai_trading():
    """AI 거래 시스템 시작"""
    try:
        await ai_engine.start_ai_trading()
        return {"success": True, "message": "AI 거래 시스템이 시작되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시스템 시작 실패: {str(e)}")


@router.post("/system/stop")
async def stop_ai_trading():
    """AI 거래 시스템 중지"""
    try:
        await ai_engine.stop_ai_trading()
        return {"success": True, "message": "AI 거래 시스템이 중지되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시스템 중지 실패: {str(e)}")


@router.get("/system/status")
async def get_system_status():
    """시스템 상태 조회"""
    try:
        status = await ai_engine.get_system_summary()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"상태 조회 실패: {str(e)}")


# ==================== 데이터 API ====================

@router.get("/data/market/{symbol}")
async def get_market_data(symbol: str):
    """특정 심볼의 시장 데이터 조회"""
    try:
        data = data_collector.get_latest_data(symbol)
        if not data:
            raise HTTPException(status_code=404, detail=f"{symbol} 데이터를 찾을 수 없습니다")
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 조회 실패: {str(e)}")


@router.get("/data/market")
async def get_all_market_data():
    """모든 심볼의 시장 데이터 조회"""
    try:
        data = data_collector.get_symbols_data()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 조회 실패: {str(e)}")


# ==================== AI 분석 API ====================

@router.post("/analysis/{symbol}")
async def analyze_symbol(symbol: str):
    """특정 심볼 AI 분석"""
    try:
        result = await ai_engine.analyze_single_symbol(symbol)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 실패: {str(e)}")


@router.get("/analysis/history")
async def get_analysis_history(limit: int = 100):
    """분석 히스토리 조회"""
    try:
        history = ai_engine.get_analysis_history(limit)
        return {"history": history, "count": len(history)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"히스토리 조회 실패: {str(e)}")


# ==================== 거래 API ====================

@router.get("/trading/positions")
async def get_positions():
    """현재 포지션 조회"""
    try:
        positions = trading_executor.get_positions()
        return {"positions": positions, "count": len(positions)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"포지션 조회 실패: {str(e)}")


@router.get("/trading/summary")
async def get_trading_summary():
    """거래 요약 정보 조회"""
    try:
        summary = trading_executor.get_trading_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"요약 조회 실패: {str(e)}")


@router.get("/trading/trades")
async def get_trade_history(limit: int = 100):
    """거래 히스토리 조회"""
    try:
        with get_db_session() as db:
            trades = db.query(Trade).order_by(Trade.created_at.desc()).limit(limit).all()
            
            return {
                "trades": [
                    {
                        "id": trade.id,
                        "symbol": trade.symbol,
                        "side": trade.side.value,
                        "quantity": trade.quantity,
                        "price": trade.price,
                        "status": trade.status.value,
                        "created_at": trade.created_at.isoformat(),
                        "executed_at": trade.executed_at.isoformat() if trade.executed_at else None
                    }
                    for trade in trades
                ],
                "count": len(trades)
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"거래 히스토리 조회 실패: {str(e)}")


# ==================== 알림 API ====================

@router.post("/notifications/send")
async def send_notification(notification_type: str, message: str, data: Dict = None):
    """알림 전송"""
    try:
        result = await notification_service.send_notification(notification_type, message, data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"알림 전송 실패: {str(e)}")


@router.get("/notifications/history")
async def get_notification_history(limit: int = 50):
    """알림 히스토리 조회"""
    try:
        history = notification_service.get_notification_history(limit)
        return {"history": history, "count": len(history)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"알림 히스토리 조회 실패: {str(e)}")


@router.get("/notifications/summary")
async def get_notification_summary():
    """알림 서비스 요약 정보 조회"""
    try:
        summary = notification_service.get_notification_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"알림 요약 조회 실패: {str(e)}")


# ==================== 관리 API ====================

@router.get("/admin/signals")
async def get_trading_signals(limit: int = 100):
    """거래 신호 조회"""
    try:
        with get_db_session() as db:
            signals = db.query(TradingSignal).order_by(TradingSignal.created_at.desc()).limit(limit).all()
            
            return {
                "signals": [
                    {
                        "id": signal.id,
                        "symbol": signal.symbol,
                        "signal_type": signal.signal_type.value,
                        "confidence": signal.confidence,
                        "price": signal.price,
                        "reasoning": signal.reasoning,
                        "created_at": signal.created_at.isoformat(),
                        "executed": signal.executed
                    }
                    for signal in signals
                ],
                "count": len(signals)
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"거래 신호 조회 실패: {str(e)}")


@router.get("/admin/notifications")
async def get_all_notifications(limit: int = 100):
    """모든 알림 조회"""
    try:
        with get_db_session() as db:
            notifications = db.query(Notification).order_by(Notification.created_at.desc()).limit(limit).all()
            
            return {
                "notifications": [
                    {
                        "id": notif.id,
                        "notification_type": notif.notification_type.value,
                        "channel": notif.channel.value,
                        "title": notif.title,
                        "status": notif.status.value,
                        "created_at": notif.created_at.isoformat(),
                        "sent_at": notif.sent_at.isoformat() if notif.sent_at else None
                    }
                    for notif in notifications
                ],
                "count": len(notifications)
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"알림 조회 실패: {str(e)}")


# ==================== 헬스체크 API ====================

@router.get("/health")
async def health_check():
    """시스템 헬스체크"""
    try:
        return {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z",
            "version": "1.0.0",
            "services": {
                "ai_engine": "active",
                "data_collector": "active",
                "trading_executor": "active",
                "notification_service": "active"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"헬스체크 실패: {str(e)}")


# ==================== 설정 API ====================

@router.get("/config")
async def get_config():
    """시스템 설정 조회"""
    try:
        from app.config import settings, LLM_CONFIG, TRADING_LIMITS, EXCHANGE_CONFIG, NOTIFICATION_CONFIG
        
        return {
            "settings": {
                "binance_testnet": settings.binance_testnet,
                "analysis_interval": 60,
                "max_position_size": TRADING_LIMITS['max_position_size'],
                "max_daily_loss": TRADING_LIMITS['max_daily_loss']
            },
            "llm_config": LLM_CONFIG,
            "trading_limits": TRADING_LIMITS,
            "exchange_config": EXCHANGE_CONFIG,
            "notification_config": NOTIFICATION_CONFIG
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"설정 조회 실패: {str(e)}")


# ==================== 통계 API ====================

@router.get("/stats/daily")
async def get_daily_stats():
    """일일 통계 조회"""
    try:
        # 오늘 거래 수
        with get_db_session() as db:
            from datetime import datetime, timedelta
            
            today = datetime.now().date()
            trades_today = db.query(Trade).filter(
                Trade.created_at >= today
            ).count()
            
            signals_today = db.query(TradingSignal).filter(
                TradingSignal.created_at >= today
            ).count()
            
            notifications_today = db.query(Notification).filter(
                Notification.created_at >= today
            ).count()
            
            return {
                "date": today.isoformat(),
                "trades": trades_today,
                "signals": signals_today,
                "notifications": notifications_today,
                "portfolio_summary": trading_executor.get_trading_summary()
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 조회 실패: {str(e)}")


@router.get("/stats/weekly")
async def get_weekly_stats():
    """주간 통계 조회"""
    try:
        # 이번 주 통계
        with get_db_session() as db:
            from datetime import datetime, timedelta
            
            today = datetime.now()
            week_start = today - timedelta(days=today.weekday())
            
            trades_weekly = db.query(Trade).filter(
                Trade.created_at >= week_start
            ).count()
            
            signals_weekly = db.query(TradingSignal).filter(
                TradingSignal.created_at >= week_start
            ).count()
            
            return {
                "week_start": week_start.date().isoformat(),
                "trades": trades_weekly,
                "signals": signals_weekly,
                "portfolio_summary": trading_executor.get_trading_summary()
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"주간 통계 조회 실패: {str(e)}") 