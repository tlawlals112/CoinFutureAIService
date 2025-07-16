"""
LLM 앙상블 기반 AI 분석 엔진
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from loguru import logger

from llm_models.ensemble_decision import EnsembleDecision
from app.services.data_collector import DataCollector
from app.services.trading_executor import TradingExecutor
from app.services.notification_service import NotificationService
from app.utils.database import get_db_session
from app.models.trading_models import TradingSignal


class AIEngine:
    """LLM 앙상블 기반 AI 분석 엔진"""
    
    def __init__(self):
        self.ensemble_decision = EnsembleDecision()
        self.data_collector = DataCollector()
        self.trading_executor = TradingExecutor()
        self.notification_service = NotificationService()
        self.logger = logger.bind(name="ai_engine")
        
        # 분석 주기 설정 (초 단위)
        self.analysis_interval = 60  # 1분마다 분석
        self.is_running = False
        
    async def start_ai_trading(self):
        """AI 거래 시작"""
        try:
            self.logger.info("AI 거래 시스템을 시작합니다.")
            self.is_running = True
            
            # 데이터 수집 시작
            self.data_collector.start()
            
            # 메인 루프 시작
            await self._main_trading_loop()
            
        except Exception as e:
            self.logger.error(f"AI 거래 시작 오류: {e}")
            await self._send_error_notification(str(e))
            
    async def stop_ai_trading(self):
        """AI 거래 중지"""
        try:
            self.logger.info("AI 거래 시스템을 중지합니다.")
            self.is_running = False
            
            # 데이터 수집 중지
            self.data_collector.stop()
            
        except Exception as e:
            self.logger.error(f"AI 거래 중지 오류: {e}")
            
    async def _main_trading_loop(self):
        """메인 거래 루프"""
        while self.is_running:
            try:
                # 시장 데이터 수집
                market_data = self._collect_market_data()
                
                if not market_data:
                    self.logger.warning("시장 데이터를 수집할 수 없습니다.")
                    await asyncio.sleep(self.analysis_interval)
                    continue
                    
                # AI 분석 수행
                analysis_result = await self._perform_ai_analysis(market_data)
                
                if analysis_result:
                    # 거래 신호 생성
                    trading_signal = self._generate_trading_signal(analysis_result, market_data)
                    
                    # 거래 신호 저장
                    self._save_trading_signal(trading_signal)
                    
                    # 거래 실행
                    trade_result = self.trading_executor.execute_trading_signal(trading_signal, market_data)
                    
                    # 알림 전송
                    await self._send_trading_notifications(trade_result, trading_signal)
                    
                    # 시스템 상태 업데이트
                    await self._update_system_status()
                    
                # 대기
                await asyncio.sleep(self.analysis_interval)
                
            except Exception as e:
                self.logger.error(f"메인 루프 오류: {e}")
                await self._send_error_notification(str(e))
                await asyncio.sleep(self.analysis_interval)
                
    def _collect_market_data(self) -> Optional[Dict]:
        """시장 데이터 수집"""
        try:
            # 모든 심볼의 최신 데이터 조회
            symbols_data = self.data_collector.get_symbols_data()
            
            if not symbols_data:
                return None
                
            # 가장 활발한 거래 심볼 선택 (예: BTCUSDT)
            target_symbol = 'BTCUSDT'
            market_data = symbols_data.get(target_symbol)
            
            if not market_data:
                # 첫 번째 사용 가능한 심볼 사용
                target_symbol = list(symbols_data.keys())[0]
                market_data = symbols_data[target_symbol]
                
            # 심볼 정보 추가
            market_data['symbol'] = target_symbol
            
            return market_data
            
        except Exception as e:
            self.logger.error(f"시장 데이터 수집 오류: {e}")
            return None
            
    async def _perform_ai_analysis(self, market_data: Dict) -> Optional[Dict]:
        """AI 분석 수행"""
        try:
            start_time = time.time()
            
            # 앙상블 의사결정 수행
            analysis_result = self.ensemble_decision.make_ensemble_decision(market_data)
            
            # 성능 로깅
            processing_time = time.time() - start_time
            self.logger.info(f"AI 분석 완료 - 소요시간: {processing_time:.3f}초")
            
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"AI 분석 오류: {e}")
            return None
            
    def _generate_trading_signal(self, analysis_result: Dict, market_data: Dict) -> Dict:
        """거래 신호 생성"""
        try:
            signal = {
                'symbol': market_data.get('symbol', 'UNKNOWN'),
                'decision': analysis_result.get('decision', 'HOLD'),
                'confidence': analysis_result.get('confidence', 0.5),
                'position_size': analysis_result.get('position_size', 5),
                'risk_level': analysis_result.get('risk_level', 5),
                'expected_return': analysis_result.get('expected_return', 0.0),
                'reasoning': analysis_result.get('reasoning', ''),
                'stop_loss': analysis_result.get('stop_loss'),
                'take_profit': analysis_result.get('take_profit'),
                'timeframe': analysis_result.get('timeframe', '1H'),
                'leverage': analysis_result.get('leverage', 1),
                'ensemble_details': analysis_result.get('ensemble_details', {}),
                'market_data': {
                    'price': market_data.get('close_price', 0),
                    'volume': market_data.get('volume', 0),
                    'rsi': market_data.get('rsi', 0),
                    'macd': market_data.get('macd', 0)
                }
            }
            
            return signal
            
        except Exception as e:
            self.logger.error(f"거래 신호 생성 오류: {e}")
            return {
                'symbol': market_data.get('symbol', 'UNKNOWN'),
                'decision': 'HOLD',
                'confidence': 0.0,
                'position_size': 0,
                'risk_level': 10,
                'reasoning': '신호 생성 실패'
            }
            
    def _save_trading_signal(self, signal: Dict):
        """거래 신호 저장"""
        try:
            with get_db_session() as db:
                trading_signal = TradingSignal(
                    symbol=signal['symbol'],
                    signal_type=signal['decision'],
                    confidence=signal['confidence'],
                    price=signal['market_data']['price'],
                    quantity=0,  # 거래 실행 시 계산
                    leverage=signal.get('leverage', 1),
                    reasoning=signal['reasoning'],
                    llm_analysis=signal.get('ensemble_details', {}),
                    created_at=datetime.now()
                )
                
                db.add(trading_signal)
                db.commit()
                
        except Exception as e:
            self.logger.error(f"거래 신호 저장 오류: {e}")
            
    async def _send_trading_notifications(self, trade_result: Dict, signal: Dict):
        """거래 알림 전송"""
        try:
            if trade_result.get('success'):
                # 거래 실행 알림
                trade_data = {
                    'symbol': signal['symbol'],
                    'action': signal['decision'],
                    'quantity': trade_result.get('quantity', 0),
                    'price': signal['market_data']['price'],
                    'confidence': signal['confidence']
                }
                
                await self.notification_service.send_trade_notification(trade_data)
                
                # 포트폴리오 상태 알림
                portfolio_data = self.trading_executor.get_trading_summary()
                await self.notification_service.send_portfolio_status(portfolio_data)
                
        except Exception as e:
            self.logger.error(f"거래 알림 전송 오류: {e}")
            
    async def _send_error_notification(self, error_message: str):
        """에러 알림 전송"""
        try:
            error_data = {
                'status': 'ERROR',
                'details': {
                    'error': error_message,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            await self.notification_service.send_system_status_notification(error_data)
            
        except Exception as e:
            self.logger.error(f"에러 알림 전송 오류: {e}")
            
    async def _update_system_status(self):
        """시스템 상태 업데이트"""
        try:
            # 시스템 상태 확인
            status_data = {
                'status': 'HEALTHY',
                'details': {
                    'data_collector': 'active',
                    'ai_engine': 'active',
                    'trading_executor': 'active',
                    'notification_service': 'active',
                    'last_update': datetime.now().isoformat()
                }
            }
            
            # 주기적으로 상태 알림 전송 (예: 1시간마다)
            current_hour = datetime.now().hour
            if current_hour % 1 == 0:  # 매시간
                await self.notification_service.send_system_status_notification(status_data)
                
        except Exception as e:
            self.logger.error(f"시스템 상태 업데이트 오류: {e}")
            
    async def analyze_single_symbol(self, symbol: str) -> Dict:
        """단일 심볼 분석"""
        try:
            # 시장 데이터 조회
            market_data = self.data_collector.get_latest_data(symbol)
            
            if not market_data:
                return {"error": "시장 데이터를 찾을 수 없습니다"}
                
            # AI 분석 수행
            analysis_result = await self._perform_ai_analysis(market_data)
            
            if not analysis_result:
                return {"error": "AI 분석에 실패했습니다"}
                
            return {
                "symbol": symbol,
                "analysis": analysis_result,
                "market_data": market_data,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"단일 심볼 분석 오류: {e}")
            return {"error": str(e)}
            
    async def get_system_summary(self) -> Dict:
        """시스템 요약 정보 조회"""
        try:
            return {
                'ai_engine': {
                    'status': 'active' if self.is_running else 'inactive',
                    'analysis_interval': self.analysis_interval,
                    'last_analysis': datetime.now().isoformat()
                },
                'data_collector': {
                    'status': 'active',
                    'symbols_count': len(self.data_collector.symbols),
                    'active_symbols': len(self.data_collector.data_cache)
                },
                'trading_executor': {
                    'status': 'active',
                    'positions': self.trading_executor.get_positions(),
                    'summary': self.trading_executor.get_trading_summary()
                },
                'notification_service': {
                    'status': 'active',
                    'summary': self.notification_service.get_notification_summary()
                },
                'ensemble_decision': {
                    'status': 'active',
                    'summary': self.ensemble_decision.get_ensemble_summary()
                }
            }
            
        except Exception as e:
            self.logger.error(f"시스템 요약 조회 오류: {e}")
            return {"error": str(e)}
            
    def get_analysis_history(self, limit: int = 100) -> List[Dict]:
        """분석 히스토리 조회"""
        try:
            with get_db_session() as db:
                signals = db.query(TradingSignal).order_by(
                    TradingSignal.created_at.desc()
                ).limit(limit).all()
                
                return [
                    {
                        'id': signal.id,
                        'symbol': signal.symbol,
                        'signal_type': signal.signal_type.value,
                        'confidence': signal.confidence,
                        'price': signal.price,
                        'reasoning': signal.reasoning,
                        'created_at': signal.created_at.isoformat(),
                        'executed': signal.executed
                    }
                    for signal in signals
                ]
                
        except Exception as e:
            self.logger.error(f"분석 히스토리 조회 오류: {e}")
            return [] 