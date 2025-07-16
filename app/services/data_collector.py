"""
실시간 시장 데이터 수집 서비스
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from binance.client import Client
from binance.websockets import BinanceSocketManager
from binance.exceptions import BinanceAPIException
import pandas as pd
import numpy as np
import ta
from loguru import logger

from app.config import settings, EXCHANGE_CONFIG
from app.utils.database import get_db_session
from app.models.trading_models import MarketData


class DataCollector:
    """실시간 시장 데이터 수집기"""
    
    def __init__(self):
        self.client = Client(
            settings.binance_api_key,
            settings.binance_secret_key,
            testnet=settings.binance_testnet
        )
        self.bm = BinanceSocketManager(self.client)
        self.connections = []
        self.symbols = EXCHANGE_CONFIG['binance']['supported_symbols']
        self.data_cache = {}
        self.logger = logger.bind(name="data_collector")
        
        # 기술적 지표 계산을 위한 데이터 저장
        self.klines_cache = {}
        
    def start(self):
        """데이터 수집 시작"""
        self.logger.info("데이터 수집 서비스를 시작합니다.")
        
        # WebSocket 연결 시작
        for symbol in self.symbols:
            self._start_symbol_stream(symbol)
            
        # REST API로 과거 데이터 수집
        self._collect_historical_data()
        
    def stop(self):
        """데이터 수집 중지"""
        self.logger.info("데이터 수집 서비스를 중지합니다.")
        
        # WebSocket 연결 종료
        for conn in self.connections:
            conn.close()
        self.connections.clear()
        
    def _start_symbol_stream(self, symbol: str):
        """특정 심볼의 WebSocket 스트림 시작"""
        try:
            # Kline/Candlestick 스트림
            conn_key = self.bm.start_kline_socket(
                symbol.lower(),
                self._process_kline_message,
                interval=Client.KLINE_INTERVAL_1MINUTE
            )
            self.connections.append(conn_key)
            
            # 24hr Ticker 스트림
            conn_key = self.bm.start_symbol_ticker_socket(
                symbol,
                self._process_ticker_message
            )
            self.connections.append(conn_key)
            
            self.logger.info(f"{symbol} 스트림이 시작되었습니다.")
            
        except Exception as e:
            self.logger.error(f"{symbol} 스트림 시작 실패: {e}")
            
    def _process_kline_message(self, msg):
        """Kline 메시지 처리"""
        try:
            if msg['e'] == 'kline':
                symbol = msg['s']
                kline = msg['k']
                
                # 캔들스틱 데이터 추출
                data = {
                    'symbol': symbol,
                    'timestamp': datetime.fromtimestamp(kline['t'] / 1000),
                    'open_price': float(kline['o']),
                    'high_price': float(kline['h']),
                    'low_price': float(kline['l']),
                    'close_price': float(kline['c']),
                    'volume': float(kline['v'])
                }
                
                # 기술적 지표 계산
                data = self._calculate_technical_indicators(data)
                
                # 데이터베이스에 저장
                self._save_market_data(data)
                
                # 캐시 업데이트
                self._update_cache(symbol, data)
                
        except Exception as e:
            self.logger.error(f"Kline 메시지 처리 오류: {e}")
            
    def _process_ticker_message(self, msg):
        """Ticker 메시지 처리"""
        try:
            symbol = msg['s']
            ticker_data = {
                'symbol': symbol,
                'price': float(msg['c']),
                'volume': float(msg['v']),
                'price_change': float(msg['p']),
                'price_change_percent': float(msg['P']),
                'timestamp': datetime.now()
            }
            
            # 캐시 업데이트
            self.data_cache[symbol] = ticker_data
            
        except Exception as e:
            self.logger.error(f"Ticker 메시지 처리 오류: {e}")
            
    def _calculate_technical_indicators(self, data: Dict) -> Dict:
        """기술적 지표 계산"""
        try:
            symbol = data['symbol']
            
            # 캐시된 데이터 가져오기
            if symbol not in self.klines_cache:
                self.klines_cache[symbol] = []
                
            # 새로운 데이터 추가
            self.klines_cache[symbol].append(data)
            
            # 최근 100개 데이터만 유지
            if len(self.klines_cache[symbol]) > 100:
                self.klines_cache[symbol] = self.klines_cache[symbol][-100:]
                
            # DataFrame 생성
            df = pd.DataFrame(self.klines_cache[symbol])
            
            if len(df) >= 20:  # 최소 데이터 필요
                # RSI 계산
                data['rsi'] = ta.momentum.RSIIndicator(df['close_price']).rsi().iloc[-1]
                
                # MACD 계산
                macd = ta.trend.MACD(df['close_price'])
                data['macd'] = macd.macd().iloc[-1]
                data['macd_signal'] = macd.macd_signal().iloc[-1]
                data['macd_histogram'] = macd.macd_diff().iloc[-1]
                
                # Bollinger Bands 계산
                bb = ta.volatility.BollingerBands(df['close_price'])
                data['bollinger_upper'] = bb.bollinger_hband().iloc[-1]
                data['bollinger_middle'] = bb.bollinger_mavg().iloc[-1]
                data['bollinger_lower'] = bb.bollinger_lband().iloc[-1]
                
                # 이동평균선 계산
                data['sma_20'] = ta.trend.SMAIndicator(df['close_price'], window=20).sma_indicator().iloc[-1]
                data['sma_50'] = ta.trend.SMAIndicator(df['close_price'], window=50).sma_indicator().iloc[-1]
                data['ema_12'] = ta.trend.EMAIndicator(df['close_price'], window=12).ema_indicator().iloc[-1]
                data['ema_26'] = ta.trend.EMAIndicator(df['close_price'], window=26).ema_indicator().iloc[-1]
                
        except Exception as e:
            self.logger.error(f"기술적 지표 계산 오류: {e}")
            
        return data
        
    def _save_market_data(self, data: Dict):
        """시장 데이터를 데이터베이스에 저장"""
        try:
            with get_db_session() as db:
                market_data = MarketData(**data)
                db.add(market_data)
                db.commit()
                
        except Exception as e:
            self.logger.error(f"시장 데이터 저장 오류: {e}")
            
    def _update_cache(self, symbol: str, data: Dict):
        """캐시 업데이트"""
        self.data_cache[symbol] = data
        
    def _collect_historical_data(self):
        """과거 데이터 수집"""
        self.logger.info("과거 데이터 수집을 시작합니다.")
        
        for symbol in self.symbols:
            try:
                # 최근 100개 캔들스틱 데이터 수집
                klines = self.client.get_klines(
                    symbol=symbol,
                    interval=Client.KLINE_INTERVAL_1MINUTE,
                    limit=100
                )
                
                for kline in klines:
                    data = {
                        'symbol': symbol,
                        'timestamp': datetime.fromtimestamp(kline[0] / 1000),
                        'open_price': float(kline[1]),
                        'high_price': float(kline[2]),
                        'low_price': float(kline[3]),
                        'close_price': float(kline[4]),
                        'volume': float(kline[5])
                    }
                    
                    # 기술적 지표 계산
                    data = self._calculate_technical_indicators(data)
                    
                    # 데이터베이스에 저장
                    self._save_market_data(data)
                    
                self.logger.info(f"{symbol} 과거 데이터 수집 완료")
                
            except Exception as e:
                self.logger.error(f"{symbol} 과거 데이터 수집 실패: {e}")
                
    def get_latest_data(self, symbol: str) -> Optional[Dict]:
        """최신 데이터 조회"""
        return self.data_cache.get(symbol)
        
    def get_symbols_data(self) -> Dict[str, Dict]:
        """모든 심볼의 최신 데이터 조회"""
        return self.data_cache.copy()
        
    def get_historical_data(self, symbol: str, limit: int = 100) -> List[Dict]:
        """과거 데이터 조회"""
        try:
            with get_db_session() as db:
                market_data = db.query(MarketData).filter(
                    MarketData.symbol == symbol
                ).order_by(
                    MarketData.timestamp.desc()
                ).limit(limit).all()
                
                return [
                    {
                        'symbol': data.symbol,
                        'timestamp': data.timestamp,
                        'open_price': data.open_price,
                        'high_price': data.high_price,
                        'low_price': data.low_price,
                        'close_price': data.close_price,
                        'volume': data.volume,
                        'rsi': data.rsi,
                        'macd': data.macd,
                        'bollinger_upper': data.bollinger_upper,
                        'bollinger_lower': data.bollinger_lower,
                        'sma_20': data.sma_20,
                        'sma_50': data.sma_50
                    }
                    for data in market_data
                ]
                
        except Exception as e:
            self.logger.error(f"과거 데이터 조회 오류: {e}")
            return []
            
    def get_market_summary(self) -> Dict:
        """시장 요약 정보 조회"""
        summary = {
            'total_symbols': len(self.symbols),
            'active_symbols': len(self.data_cache),
            'last_update': datetime.now().isoformat(),
            'symbols': {}
        }
        
        for symbol in self.symbols:
            if symbol in self.data_cache:
                data = self.data_cache[symbol]
                summary['symbols'][symbol] = {
                    'price': data.get('close_price', 0),
                    'volume': data.get('volume', 0),
                    'rsi': data.get('rsi', 0),
                    'timestamp': data.get('timestamp', datetime.now()).isoformat()
                }
                
        return summary 