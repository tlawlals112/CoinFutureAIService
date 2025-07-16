"""
GPT-4 Turbo 기반 투자 분석 엔진
"""

import json
import time
from typing import Dict, List, Optional, Any
from openai import OpenAI
from loguru import logger

from app.config import settings, LLM_CONFIG


class GPT4Engine:
    """GPT-4 Turbo 기반 투자 분석 엔진"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.config = LLM_CONFIG['gpt4']
        self.logger = logger.bind(name="gpt4_engine")
        
        # 투자 특화 프롬프트
        self.investment_prompt = """
당신은 전문 투자 분석가입니다. 다음 정보를 바탕으로 투자 결정을 내려주세요:

시장 데이터:
- 심볼: {symbol}
- 현재가: {current_price}
- 거래량: {volume}
- 24시간 변동률: {price_change_percent}%

기술적 지표:
- RSI: {rsi}
- MACD: {macd}
- MACD Signal: {macd_signal}
- Bollinger Upper: {bollinger_upper}
- Bollinger Lower: {bollinger_lower}
- SMA 20: {sma_20}
- SMA 50: {sma_50}

시장 상황:
- 추세: {trend}
- 변동성: {volatility}
- 거래량 추이: {volume_trend}

분석 결과를 다음 JSON 형식으로 응답해주세요:
{{
    "decision": "BUY/SELL/HOLD",
    "confidence": 0.0-1.0,
    "position_size": 1-10,
    "risk_level": 1-10,
    "expected_return": 0.0-1.0,
    "reasoning": "분석 근거",
    "stop_loss": "손절매 가격",
    "take_profit": "익절매 가격",
    "timeframe": "투자 기간"
}}
"""
        
    def analyze_market(self, market_data: Dict) -> Dict:
        """시장 분석 수행"""
        try:
            start_time = time.time()
            
            # 프롬프트 생성
            prompt = self._create_analysis_prompt(market_data)
            
            # GPT-4 API 호출
            response = self.client.chat.completions.create(
                model=self.config['model'],
                messages=[
                    {"role": "system", "content": "당신은 전문 투자 분석가입니다. 정확하고 객관적인 분석을 제공하세요."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.config['max_tokens'],
                temperature=self.config['temperature']
            )
            
            # 응답 파싱
            result = self._parse_response(response.choices[0].message.content)
            
            # 성능 로깅
            processing_time = time.time() - start_time
            self.logger.info(f"GPT-4 분석 완료 - 소요시간: {processing_time:.3f}초")
            
            # LLM 분석 결과 저장
            self._save_analysis_result(market_data['symbol'], prompt, response.choices[0].message.content, processing_time)
            
            return result
            
        except Exception as e:
            self.logger.error(f"GPT-4 분석 오류: {e}")
            return self._get_default_response()
            
    def _create_analysis_prompt(self, market_data: Dict) -> str:
        """분석 프롬프트 생성"""
        try:
            # 기술적 지표 계산
            technical_indicators = self._calculate_technical_indicators(market_data)
            
            # 시장 상황 분석
            market_situation = self._analyze_market_situation(market_data)
            
            # 프롬프트 변수 설정
            prompt_vars = {
                'symbol': market_data.get('symbol', 'UNKNOWN'),
                'current_price': market_data.get('close_price', 0),
                'volume': market_data.get('volume', 0),
                'price_change_percent': market_data.get('price_change_percent', 0),
                'rsi': technical_indicators.get('rsi', 0),
                'macd': technical_indicators.get('macd', 0),
                'macd_signal': technical_indicators.get('macd_signal', 0),
                'bollinger_upper': technical_indicators.get('bollinger_upper', 0),
                'bollinger_lower': technical_indicators.get('bollinger_lower', 0),
                'sma_20': technical_indicators.get('sma_20', 0),
                'sma_50': technical_indicators.get('sma_50', 0),
                'trend': market_situation.get('trend', 'NEUTRAL'),
                'volatility': market_situation.get('volatility', 'MEDIUM'),
                'volume_trend': market_situation.get('volume_trend', 'STABLE')
            }
            
            return self.investment_prompt.format(**prompt_vars)
            
        except Exception as e:
            self.logger.error(f"프롬프트 생성 오류: {e}")
            return self.investment_prompt.format(
                symbol='UNKNOWN',
                current_price=0,
                volume=0,
                price_change_percent=0,
                rsi=0,
                macd=0,
                macd_signal=0,
                bollinger_upper=0,
                bollinger_lower=0,
                sma_20=0,
                sma_50=0,
                trend='NEUTRAL',
                volatility='MEDIUM',
                volume_trend='STABLE'
            )
            
    def _calculate_technical_indicators(self, market_data: Dict) -> Dict:
        """기술적 지표 계산"""
        try:
            indicators = {}
            
            # RSI 분석
            rsi = market_data.get('rsi', 50)
            indicators['rsi'] = rsi
            indicators['rsi_signal'] = 'OVERSOLD' if rsi < 30 else 'OVERBOUGHT' if rsi > 70 else 'NEUTRAL'
            
            # MACD 분석
            macd = market_data.get('macd', 0)
            macd_signal = market_data.get('macd_signal', 0)
            indicators['macd'] = macd
            indicators['macd_signal'] = macd_signal
            indicators['macd_trend'] = 'BULLISH' if macd > macd_signal else 'BEARISH'
            
            # Bollinger Bands 분석
            current_price = market_data.get('close_price', 0)
            bb_upper = market_data.get('bollinger_upper', current_price)
            bb_lower = market_data.get('bollinger_lower', current_price)
            
            indicators['bollinger_upper'] = bb_upper
            indicators['bollinger_lower'] = bb_lower
            indicators['bb_position'] = 'UPPER' if current_price >= bb_upper else 'LOWER' if current_price <= bb_lower else 'MIDDLE'
            
            # 이동평균선 분석
            sma_20 = market_data.get('sma_20', current_price)
            sma_50 = market_data.get('sma_50', current_price)
            
            indicators['sma_20'] = sma_20
            indicators['sma_50'] = sma_50
            indicators['ma_trend'] = 'BULLISH' if sma_20 > sma_50 else 'BEARISH'
            
            return indicators
            
        except Exception as e:
            self.logger.error(f"기술적 지표 계산 오류: {e}")
            return {}
            
    def _analyze_market_situation(self, market_data: Dict) -> Dict:
        """시장 상황 분석"""
        try:
            situation = {}
            
            # 추세 분석
            price_change = market_data.get('price_change_percent', 0)
            if price_change > 5:
                situation['trend'] = 'STRONG_BULLISH'
            elif price_change > 1:
                situation['trend'] = 'BULLISH'
            elif price_change < -5:
                situation['trend'] = 'STRONG_BEARISH'
            elif price_change < -1:
                situation['trend'] = 'BEARISH'
            else:
                situation['trend'] = 'NEUTRAL'
                
            # 변동성 분석
            high_price = market_data.get('high_price', 0)
            low_price = market_data.get('low_price', 0)
            current_price = market_data.get('close_price', 0)
            
            if current_price > 0:
                volatility = (high_price - low_price) / current_price * 100
                if volatility > 10:
                    situation['volatility'] = 'HIGH'
                elif volatility > 5:
                    situation['volatility'] = 'MEDIUM'
                else:
                    situation['volatility'] = 'LOW'
            else:
                situation['volatility'] = 'UNKNOWN'
                
            # 거래량 추이
            volume = market_data.get('volume', 0)
            if volume > 1000000:
                situation['volume_trend'] = 'HIGH'
            elif volume > 100000:
                situation['volume_trend'] = 'MEDIUM'
            else:
                situation['volume_trend'] = 'LOW'
                
            return situation
            
        except Exception as e:
            self.logger.error(f"시장 상황 분석 오류: {e}")
            return {
                'trend': 'NEUTRAL',
                'volatility': 'MEDIUM',
                'volume_trend': 'STABLE'
            }
            
    def _parse_response(self, response_text: str) -> Dict:
        """GPT-4 응답 파싱"""
        try:
            # JSON 추출
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = response_text[start_idx:end_idx]
                result = json.loads(json_str)
                
                # 필수 필드 검증
                required_fields = ['decision', 'confidence', 'position_size', 'risk_level']
                for field in required_fields:
                    if field not in result:
                        result[field] = self._get_default_value(field)
                        
                return result
            else:
                self.logger.warning("JSON 응답을 찾을 수 없습니다.")
                return self._get_default_response()
                
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON 파싱 오류: {e}")
            return self._get_default_response()
        except Exception as e:
            self.logger.error(f"응답 파싱 오류: {e}")
            return self._get_default_response()
            
    def _get_default_response(self) -> Dict:
        """기본 응답 반환"""
        return {
            "decision": "HOLD",
            "confidence": 0.5,
            "position_size": 5,
            "risk_level": 5,
            "expected_return": 0.0,
            "reasoning": "분석 실패로 인한 보수적 결정",
            "stop_loss": None,
            "take_profit": None,
            "timeframe": "1H"
        }
        
    def _get_default_value(self, field: str):
        """필드별 기본값 반환"""
        defaults = {
            'decision': 'HOLD',
            'confidence': 0.5,
            'position_size': 5,
            'risk_level': 5,
            'expected_return': 0.0,
            'reasoning': '분석 불가',
            'stop_loss': None,
            'take_profit': None,
            'timeframe': '1H'
        }
        return defaults.get(field, None)
        
    def _save_analysis_result(self, symbol: str, input_data: str, output_data: str, processing_time: float):
        """분석 결과 저장"""
        try:
            from app.utils.database import get_db_session
            from app.models.trading_models import LLMAnalysis
            
            with get_db_session() as db:
                analysis = LLMAnalysis(
                    symbol=symbol,
                    timestamp=time.time(),
                    llm_provider='gpt4',
                    analysis_type='market_analysis',
                    input_data=input_data,
                    output_data=output_data,
                    processing_time=processing_time,
                    cost=0.0  # 비용 계산 로직 추가 필요
                )
                db.add(analysis)
                db.commit()
                
        except Exception as e:
            self.logger.error(f"분석 결과 저장 오류: {e}")
            
    def get_analysis_summary(self) -> Dict:
        """분석 요약 정보 조회"""
        return {
            'provider': 'GPT-4 Turbo',
            'model': self.config['model'],
            'weight': self.config['weight'],
            'status': 'active'
        } 