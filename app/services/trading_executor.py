"""
Binance API를 사용한 거래 실행 서비스
"""

import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
from loguru import logger

from app.config import settings, TRADING_LIMITS, EXCHANGE_CONFIG
from app.utils.database import get_db_session
from app.models.trading_models import Trade, Position, TradingSignal
from app.utils.logger import log_trade


class TradingExecutor:
    """Binance 거래 실행 서비스"""
    
    def __init__(self):
        self.client = Client(
            settings.binance_api_key,
            settings.binance_secret_key,
            testnet=settings.binance_testnet
        )
        self.logger = logger.bind(name="trading_executor")
        self.trading_limits = TRADING_LIMITS
        self.exchange_config = EXCHANGE_CONFIG['binance']
        
    def execute_trading_signal(self, signal: Dict, market_data: Dict) -> Dict:
        """거래 신호 실행"""
        try:
            # 거래 신호 검증
            if not self._validate_signal(signal):
                return {"success": False, "error": "거래 신호 검증 실패"}
                
            # 리스크 체크
            if not self._check_risk_limits(signal):
                return {"success": False, "error": "리스크 한도 초과"}
                
            # 계좌 잔고 확인
            account_info = self._get_account_info()
            if not self._check_balance(signal, account_info):
                return {"success": False, "error": "잔고 부족"}
                
            # 거래 실행
            trade_result = self._execute_trade(signal, market_data)
            
            # 거래 기록 저장
            self._save_trade_record(signal, trade_result, market_data)
            
            # 포지션 업데이트
            self._update_position(signal, trade_result, market_data)
            
            return trade_result
            
        except Exception as e:
            self.logger.error(f"거래 실행 오류: {e}")
            return {"success": False, "error": str(e)}
            
    def _validate_signal(self, signal: Dict) -> bool:
        """거래 신호 검증"""
        try:
            required_fields = ['decision', 'confidence', 'position_size', 'risk_level']
            
            for field in required_fields:
                if field not in signal:
                    self.logger.error(f"필수 필드 누락: {field}")
                    return False
                    
            # 의사결정 유효성 검사
            valid_decisions = ['BUY', 'SELL', 'HOLD']
            if signal['decision'] not in valid_decisions:
                self.logger.error(f"잘못된 의사결정: {signal['decision']}")
                return False
                
            # 신뢰도 검사
            confidence = signal.get('confidence', 0)
            if confidence < 0.3:  # 30% 미만 신뢰도는 거래하지 않음
                self.logger.warning(f"신뢰도가 너무 낮음: {confidence}")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"신호 검증 오류: {e}")
            return False
            
    def _check_risk_limits(self, signal: Dict) -> bool:
        """리스크 한도 체크"""
        try:
            # 일일 손실 한도 체크
            daily_pnl = self._get_daily_pnl()
            max_daily_loss = self.trading_limits['max_daily_loss']
            
            if daily_pnl < -max_daily_loss:
                self.logger.warning(f"일일 손실 한도 초과: {daily_pnl}")
                return False
                
            # 포지션 크기 체크
            position_size = signal.get('position_size', 5)
            max_position_size = self.trading_limits['max_position_size']
            
            if position_size > max_position_size * 10:  # 1-10 스케일을 퍼센트로 변환
                self.logger.warning(f"포지션 크기 한도 초과: {position_size}")
                return False
                
            # 리스크 레벨 체크
            risk_level = signal.get('risk_level', 5)
            if risk_level > 8:  # 리스크 레벨이 너무 높으면 거래하지 않음
                self.logger.warning(f"리스크 레벨이 너무 높음: {risk_level}")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"리스크 체크 오류: {e}")
            return False
            
    def _get_account_info(self) -> Dict:
        """계좌 정보 조회"""
        try:
            account_info = self.client.futures_account()
            return account_info
        except Exception as e:
            self.logger.error(f"계좌 정보 조회 오류: {e}")
            return {}
            
    def _check_balance(self, signal: Dict, account_info: Dict) -> bool:
        """잔고 확인"""
        try:
            # USDT 잔고 확인
            balances = account_info.get('assets', [])
            usdt_balance = 0
            
            for balance in balances:
                if balance['asset'] == 'USDT':
                    usdt_balance = float(balance['availableBalance'])
                    break
                    
            # 최소 잔고 체크
            min_balance = self.trading_limits['min_balance_threshold']
            if usdt_balance < min_balance:
                self.logger.warning(f"잔고 부족: {usdt_balance} USDT")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"잔고 확인 오류: {e}")
            return False
            
    def _execute_trade(self, signal: Dict, market_data: Dict) -> Dict:
        """실제 거래 실행"""
        try:
            symbol = market_data.get('symbol', 'BTCUSDT')
            decision = signal.get('decision', 'HOLD')
            position_size = signal.get('position_size', 5)
            
            if decision == 'HOLD':
                return {"success": True, "action": "HOLD", "message": "거래 보류"}
                
            # 거래 수량 계산
            quantity = self._calculate_quantity(signal, market_data)
            
            # 주문 타입 결정
            order_type = 'MARKET'  # 시장가 주문
            
            # 거래 방향 결정
            side = 'BUY' if decision == 'BUY' else 'SELL'
            
            # 레버리지 설정
            leverage = min(signal.get('leverage', 1), self.exchange_config['max_leverage'])
            self._set_leverage(symbol, leverage)
            
            # 주문 실행
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type=order_type,
                quantity=quantity
            )
            
            # 거래 로그
            log_trade(
                symbol=symbol,
                action=decision,
                quantity=quantity,
                price=market_data.get('close_price', 0),
                order_id=order.get('orderId'),
                confidence=signal.get('confidence', 0)
            )
            
            return {
                "success": True,
                "action": decision,
                "order": order,
                "quantity": quantity,
                "price": market_data.get('close_price', 0),
                "leverage": leverage
            }
            
        except BinanceAPIException as e:
            self.logger.error(f"Binance API 오류: {e}")
            return {"success": False, "error": f"API 오류: {e}"}
        except BinanceOrderException as e:
            self.logger.error(f"주문 오류: {e}")
            return {"success": False, "error": f"주문 오류: {e}"}
        except Exception as e:
            self.logger.error(f"거래 실행 오류: {e}")
            return {"success": False, "error": str(e)}
            
    def _calculate_quantity(self, signal: Dict, market_data: Dict) -> float:
        """거래 수량 계산"""
        try:
            # 계좌 잔고 조회
            account_info = self._get_account_info()
            usdt_balance = 0
            
            for balance in account_info.get('assets', []):
                if balance['asset'] == 'USDT':
                    usdt_balance = float(balance['availableBalance'])
                    break
                    
            # 포지션 크기 계산 (총 자산의 퍼센트)
            position_size_percent = signal.get('position_size', 5) / 10.0  # 1-10을 0-1로 변환
            max_position_size = self.trading_limits['max_position_size']
            
            # 실제 사용할 자금 계산
            available_amount = usdt_balance * min(position_size_percent, max_position_size)
            
            # 현재 가격
            current_price = market_data.get('close_price', 0)
            
            if current_price <= 0:
                return 0.001  # 최소 수량
                
            # 수량 계산
            quantity = available_amount / current_price
            
            # 최소 주문 수량 체크
            min_quantity = self.exchange_config['min_order_size']
            if quantity < min_quantity:
                quantity = min_quantity
                
            # 소수점 자릿수 조정 (Binance 요구사항)
            quantity = round(quantity, 3)
            
            return quantity
            
        except Exception as e:
            self.logger.error(f"수량 계산 오류: {e}")
            return 0.001  # 최소 수량
            
    def _set_leverage(self, symbol: str, leverage: int):
        """레버리지 설정"""
        try:
            self.client.futures_change_leverage(symbol=symbol, leverage=leverage)
            self.logger.info(f"{symbol} 레버리지 설정: {leverage}배")
        except Exception as e:
            self.logger.error(f"레버리지 설정 오류: {e}")
            
    def _get_daily_pnl(self) -> float:
        """일일 손익 조회"""
        try:
            # 최근 24시간 거래 내역 조회
            trades = self.client.futures_account_trades()
            
            daily_pnl = 0.0
            current_time = time.time()
            one_day_ago = current_time - (24 * 60 * 60)
            
            for trade in trades:
                trade_time = trade['time'] / 1000  # 밀리초를 초로 변환
                if trade_time > one_day_ago:
                    realized_pnl = float(trade.get('realizedPnl', 0))
                    daily_pnl += realized_pnl
                    
            return daily_pnl
            
        except Exception as e:
            self.logger.error(f"일일 손익 조회 오류: {e}")
            return 0.0
            
    def _save_trade_record(self, signal: Dict, trade_result: Dict, market_data: Dict):
        """거래 기록 저장"""
        try:
            with get_db_session() as db:
                trade = Trade(
                    symbol=market_data.get('symbol', 'UNKNOWN'),
                    side=trade_result.get('action', 'HOLD'),
                    order_type='MARKET',
                    quantity=trade_result.get('quantity', 0),
                    price=market_data.get('close_price', 0),
                    executed_price=trade_result.get('price', 0),
                    status='FILLED' if trade_result.get('success') else 'REJECTED',
                    order_id=trade_result.get('order', {}).get('orderId'),
                    created_at=datetime.now()
                )
                
                if trade_result.get('success'):
                    trade.executed_at = datetime.now()
                    
                db.add(trade)
                db.commit()
                
        except Exception as e:
            self.logger.error(f"거래 기록 저장 오류: {e}")
            
    def _update_position(self, signal: Dict, trade_result: Dict, market_data: Dict):
        """포지션 업데이트"""
        try:
            if not trade_result.get('success') or trade_result.get('action') == 'HOLD':
                return
                
            with get_db_session() as db:
                # 기존 포지션 조회
                existing_position = db.query(Position).filter(
                    Position.symbol == market_data.get('symbol'),
                    Position.is_open == True
                ).first()
                
                if existing_position:
                    # 기존 포지션 업데이트
                    if trade_result.get('action') == 'SELL':
                        existing_position.is_open = False
                        existing_position.closed_at = datetime.now()
                        existing_position.realized_pnl = self._calculate_realized_pnl(existing_position, trade_result)
                else:
                    # 새 포지션 생성
                    if trade_result.get('action') == 'BUY':
                        new_position = Position(
                            symbol=market_data.get('symbol', 'UNKNOWN'),
                            position_type='LONG',
                            quantity=trade_result.get('quantity', 0),
                            entry_price=trade_result.get('price', 0),
                            current_price=trade_result.get('price', 0),
                            leverage=trade_result.get('leverage', 1),
                            margin_type='ISOLATED',
                            is_open=True,
                            created_at=datetime.now()
                        )
                        db.add(new_position)
                        
                db.commit()
                
        except Exception as e:
            self.logger.error(f"포지션 업데이트 오류: {e}")
            
    def _calculate_realized_pnl(self, position: Position, trade_result: Dict) -> float:
        """실현 손익 계산"""
        try:
            entry_price = position.entry_price
            exit_price = trade_result.get('price', 0)
            quantity = position.quantity
            
            if position.position_type == 'LONG':
                return (exit_price - entry_price) * quantity
            else:
                return (entry_price - exit_price) * quantity
                
        except Exception as e:
            self.logger.error(f"실현 손익 계산 오류: {e}")
            return 0.0
            
    def get_positions(self) -> List[Dict]:
        """현재 포지션 조회"""
        try:
            with get_db_session() as db:
                positions = db.query(Position).filter(Position.is_open == True).all()
                
                return [
                    {
                        'symbol': pos.symbol,
                        'position_type': pos.position_type.value,
                        'quantity': pos.quantity,
                        'entry_price': pos.entry_price,
                        'current_price': pos.current_price,
                        'unrealized_pnl': pos.unrealized_pnl,
                        'leverage': pos.leverage,
                        'created_at': pos.created_at.isoformat()
                    }
                    for pos in positions
                ]
                
        except Exception as e:
            self.logger.error(f"포지션 조회 오류: {e}")
            return []
            
    def get_trading_summary(self) -> Dict:
        """거래 요약 정보 조회"""
        try:
            account_info = self._get_account_info()
            
            return {
                'total_balance': float(account_info.get('totalWalletBalance', 0)),
                'available_balance': float(account_info.get('availableBalance', 0)),
                'total_unrealized_pnl': float(account_info.get('totalUnrealizedProfit', 0)),
                'daily_pnl': self._get_daily_pnl(),
                'positions_count': len(self.get_positions()),
                'last_update': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"거래 요약 조회 오류: {e}")
            return {} 