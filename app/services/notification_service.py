"""
Telegram Bot 알림 서비스
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from telegram import Bot
from telegram.error import TelegramError
from loguru import logger

from app.config import settings, NOTIFICATION_CONFIG
from app.utils.database import get_db_session
from app.models.notification_models import Notification, NotificationHistory, NotificationStatus


class NotificationService:
    """Telegram Bot 알림 서비스"""
    
    def __init__(self):
        self.bot = Bot(token=settings.telegram_bot_token)
        self.chat_id = settings.telegram_chat_id
        self.logger = logger.bind(name="notification_service")
        self.config = NOTIFICATION_CONFIG['telegram']
        
    async def send_notification(self, notification_type: str, message: str, data: Dict = None) -> Dict:
        """알림 전송"""
        try:
            # 알림 설정 확인
            if not self._is_notification_enabled(notification_type):
                return {"success": False, "error": "알림이 비활성화되어 있습니다"}
                
            # 알림 템플릿 생성
            title, formatted_message = self._create_notification_template(notification_type, message, data)
            
            # Telegram 메시지 전송
            result = await self._send_telegram_message(title, formatted_message)
            
            # 알림 기록 저장
            self._save_notification_record(notification_type, title, formatted_message, result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"알림 전송 오류: {e}")
            return {"success": False, "error": str(e)}
            
    async def send_trade_notification(self, trade_data: Dict) -> Dict:
        """거래 알림 전송"""
        try:
            symbol = trade_data.get('symbol', 'UNKNOWN')
            action = trade_data.get('action', 'UNKNOWN')
            quantity = trade_data.get('quantity', 0)
            price = trade_data.get('price', 0)
            confidence = trade_data.get('confidence', 0)
            
            message = f"🔔 거래 실행 알림\n\n"
            message += f"📊 심볼: {symbol}\n"
            message += f"🎯 액션: {action}\n"
            message += f"📈 수량: {quantity}\n"
            message += f"💰 가격: ${price:,.2f}\n"
            message += f"🎯 신뢰도: {confidence:.1%}\n"
            message += f"⏰ 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            return await self.send_notification('TRADE_EXECUTION', message, trade_data)
            
        except Exception as e:
            self.logger.error(f"거래 알림 전송 오류: {e}")
            return {"success": False, "error": str(e)}
            
    async def send_profit_loss_notification(self, pnl_data: Dict) -> Dict:
        """수익/손실 알림 전송"""
        try:
            symbol = pnl_data.get('symbol', 'UNKNOWN')
            pnl = pnl_data.get('pnl', 0)
            pnl_percent = pnl_data.get('pnl_percent', 0)
            position_type = pnl_data.get('position_type', 'UNKNOWN')
            
            emoji = "📈" if pnl > 0 else "📉"
            status = "수익" if pnl > 0 else "손실"
            
            message = f"{emoji} {status} 알림\n\n"
            message += f"📊 심볼: {symbol}\n"
            message += f"📈 포지션: {position_type}\n"
            message += f"💰 {status}: ${pnl:,.2f}\n"
            message += f"📊 비율: {pnl_percent:.2f}%\n"
            message += f"⏰ 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            return await self.send_notification('PROFIT_LOSS', message, pnl_data)
            
        except Exception as e:
            self.logger.error(f"수익/손실 알림 전송 오류: {e}")
            return {"success": False, "error": str(e)}
            
    async def send_system_status_notification(self, status_data: Dict) -> Dict:
        """시스템 상태 알림 전송"""
        try:
            status = status_data.get('status', 'UNKNOWN')
            details = status_data.get('details', {})
            
            emoji = "🟢" if status == 'HEALTHY' else "🟡" if status == 'WARNING' else "🔴"
            
            message = f"{emoji} 시스템 상태 알림\n\n"
            message += f"📊 상태: {status}\n"
            message += f"⏰ 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            if details:
                message += "📋 상세 정보:\n"
                for key, value in details.items():
                    message += f"• {key}: {value}\n"
                    
            return await self.send_notification('SYSTEM_STATUS', message, status_data)
            
        except Exception as e:
            self.logger.error(f"시스템 상태 알림 전송 오류: {e}")
            return {"success": False, "error": str(e)}
            
    async def send_risk_alert_notification(self, risk_data: Dict) -> Dict:
        """리스크 알림 전송"""
        try:
            risk_level = risk_data.get('risk_level', 'UNKNOWN')
            risk_type = risk_data.get('risk_type', 'UNKNOWN')
            details = risk_data.get('details', '')
            
            emoji = "⚠️" if risk_level == 'HIGH' else "⚡" if risk_level == 'MEDIUM' else "ℹ️"
            
            message = f"{emoji} 리스크 알림\n\n"
            message += f"🚨 리스크 레벨: {risk_level}\n"
            message += f"📊 리스크 타입: {risk_type}\n"
            message += f"⏰ 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            if details:
                message += f"📋 상세 정보:\n{details}"
                
            return await self.send_notification('RISK_ALERT', message, risk_data)
            
        except Exception as e:
            self.logger.error(f"리스크 알림 전송 오류: {e}")
            return {"success": False, "error": str(e)}
            
    async def send_daily_report_notification(self, report_data: Dict) -> Dict:
        """일일 리포트 알림 전송"""
        try:
            total_trades = report_data.get('total_trades', 0)
            winning_trades = report_data.get('winning_trades', 0)
            losing_trades = report_data.get('losing_trades', 0)
            total_pnl = report_data.get('total_pnl', 0)
            win_rate = report_data.get('win_rate', 0)
            
            emoji = "📈" if total_pnl > 0 else "📉"
            
            message = f"{emoji} 일일 거래 리포트\n\n"
            message += f"📊 총 거래: {total_trades}건\n"
            message += f"✅ 승리: {winning_trades}건\n"
            message += f"❌ 패배: {losing_trades}건\n"
            message += f"🎯 승률: {win_rate:.1f}%\n"
            message += f"💰 총 손익: ${total_pnl:,.2f}\n"
            message += f"📅 날짜: {datetime.now().strftime('%Y-%m-%d')}"
            
            return await self.send_notification('DAILY_REPORT', message, report_data)
            
        except Exception as e:
            self.logger.error(f"일일 리포트 알림 전송 오류: {e}")
            return {"success": False, "error": str(e)}
            
    def _is_notification_enabled(self, notification_type: str) -> bool:
        """알림 활성화 여부 확인"""
        try:
            enabled_types = self.config.get('notification_types', [])
            return notification_type in enabled_types
        except Exception as e:
            self.logger.error(f"알림 활성화 확인 오류: {e}")
            return True  # 기본적으로 활성화
            
    def _create_notification_template(self, notification_type: str, message: str, data: Dict = None) -> tuple:
        """알림 템플릿 생성"""
        try:
            # 알림 타입별 이모지
            emoji_map = {
                'TRADE_EXECUTION': '🔔',
                'PROFIT_LOSS': '💰',
                'SYSTEM_STATUS': '⚙️',
                'RISK_ALERT': '⚠️',
                'DAILY_REPORT': '📊',
                'WEEKLY_REPORT': '📈',
                'MONTHLY_REPORT': '📋'
            }
            
            emoji = emoji_map.get(notification_type, '📢')
            title = f"{emoji} AI 거래 시스템 알림"
            
            return title, message
            
        except Exception as e:
            self.logger.error(f"알림 템플릿 생성 오류: {e}")
            return "📢 알림", message
            
    async def _send_telegram_message(self, title: str, message: str) -> Dict:
        """Telegram 메시지 전송"""
        try:
            full_message = f"{title}\n\n{message}"
            
            # 메시지 길이 제한 (Telegram 제한: 4096자)
            if len(full_message) > 4000:
                full_message = full_message[:4000] + "\n\n... (메시지가 잘렸습니다)"
                
            result = await self.bot.send_message(
                chat_id=self.chat_id,
                text=full_message,
                parse_mode='HTML'
            )
            
            return {
                "success": True,
                "message_id": result.message_id,
                "chat_id": result.chat_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except TelegramError as e:
            self.logger.error(f"Telegram 전송 오류: {e}")
            return {"success": False, "error": f"Telegram 오류: {e}"}
        except Exception as e:
            self.logger.error(f"메시지 전송 오류: {e}")
            return {"success": False, "error": str(e)}
            
    def _save_notification_record(self, notification_type: str, title: str, message: str, result: Dict):
        """알림 기록 저장"""
        try:
            with get_db_session() as db:
                notification = Notification(
                    notification_type=notification_type,
                    channel='TELEGRAM',
                    title=title,
                    message=message,
                    data=json.dumps(result),
                    status=NotificationStatus.SENT if result.get('success') else NotificationStatus.FAILED,
                    sent_at=datetime.now() if result.get('success') else None,
                    created_at=datetime.now()
                )
                
                db.add(notification)
                db.commit()
                
                # 알림 히스토리 저장
                history = NotificationHistory(
                    notification_id=notification.id,
                    status=notification.status,
                    response_data=json.dumps(result),
                    created_at=datetime.now()
                )
                
                db.add(history)
                db.commit()
                
        except Exception as e:
            self.logger.error(f"알림 기록 저장 오류: {e}")
            
    async def send_portfolio_status(self, portfolio_data: Dict) -> Dict:
        """포트폴리오 상태 알림 전송"""
        try:
            total_balance = portfolio_data.get('total_balance', 0)
            available_balance = portfolio_data.get('available_balance', 0)
            total_unrealized_pnl = portfolio_data.get('total_unrealized_pnl', 0)
            positions_count = portfolio_data.get('positions_count', 0)
            
            message = f"📊 포트폴리오 상태\n\n"
            message += f"💰 총 잔고: ${total_balance:,.2f}\n"
            message += f"💳 사용 가능: ${available_balance:,.2f}\n"
            message += f"📈 미실현 손익: ${total_unrealized_pnl:,.2f}\n"
            message += f"📋 활성 포지션: {positions_count}개\n"
            message += f"⏰ 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            return await self.send_notification('SYSTEM_STATUS', message, portfolio_data)
            
        except Exception as e:
            self.logger.error(f"포트폴리오 상태 알림 전송 오류: {e}")
            return {"success": False, "error": str(e)}
            
    def get_notification_history(self, limit: int = 50) -> List[Dict]:
        """알림 히스토리 조회"""
        try:
            with get_db_session() as db:
                notifications = db.query(Notification).order_by(
                    Notification.created_at.desc()
                ).limit(limit).all()
                
                return [
                    {
                        'id': notif.id,
                        'type': notif.notification_type.value,
                        'title': notif.title,
                        'status': notif.status.value,
                        'created_at': notif.created_at.isoformat(),
                        'sent_at': notif.sent_at.isoformat() if notif.sent_at else None
                    }
                    for notif in notifications
                ]
                
        except Exception as e:
            self.logger.error(f"알림 히스토리 조회 오류: {e}")
            return []
            
    def get_notification_summary(self) -> Dict:
        """알림 서비스 요약 정보 조회"""
        return {
            'service': 'Telegram Notification Service',
            'enabled': True,
            'chat_id': self.chat_id,
            'notification_types': self.config.get('notification_types', []),
            'status': 'active'
        } 