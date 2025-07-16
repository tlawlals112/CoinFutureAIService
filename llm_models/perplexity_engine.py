"""
Perplexity API 기반 뉴스 및 시장 감정 분석 엔진
"""

import json
import time
import httpx
from typing import Dict, List, Optional, Any
from loguru import logger

from app.config import settings, LLM_CONFIG


class PerplexityEngine:
    """Perplexity API 기반 뉴스 및 시장 감정 분석 엔진"""
    
    def __init__(self):
        self.api_key = settings.google_api_key  # Perplexity API 키로 변경 필요
        self.config = LLM_CONFIG['perplexity']
        self.logger = logger.bind(name="perplexity_engine")
        self.base_url = "https://api.perplexity.ai"
        
        # 뉴스 분석 프롬프트
        self.news_analysis_prompt = """
다음 암호화폐 심볼에 대한 최신 뉴스와 시장 감정을 분석해주세요:

심볼: {symbol}
현재가: {current_price}

다음 JSON 형식으로 응답해주세요:
{{
    "sentiment": "POSITIVE/NEGATIVE/NEUTRAL",
    "confidence": 0.0-1.0,
    "key_news": ["주요 뉴스 1", "주요 뉴스 2"],
    "market_impact": "HIGH/MEDIUM/LOW",
    "trend_prediction": "BULLISH/BEARISH/NEUTRAL",
    "risk_factors": ["리스크 요소 1", "리스크 요소 2"],
    "opportunities": ["기회 요소 1", "기회 요소 2"],
    "summary": "전체 요약"
}}
"""
        
    def analyze_news_sentiment(self, symbol: str, current_price: float) -> Dict:
        """뉴스 감정 분석 수행"""
        try:
            start_time = time.time()
            
            # 프롬프트 생성
            prompt = self.news_analysis_prompt.format(
                symbol=symbol,
                current_price=current_price
            )
            
            # Perplexity API 호출
            response = self._call_perplexity_api(prompt)
            
            # 응답 파싱
            result = self._parse_response(response)
            
            # 성능 로깅
            processing_time = time.time() - start_time
            self.logger.info(f"Perplexity 뉴스 분석 완료 - 소요시간: {processing_time:.3f}초")
            
            # LLM 분석 결과 저장
            self._save_analysis_result(symbol, prompt, response, processing_time)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Perplexity 뉴스 분석 오류: {e}")
            return self._get_default_response()
            
    def _call_perplexity_api(self, prompt: str) -> str:
        """Perplexity API 호출"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.config['model'],
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": self.config['max_tokens'],
                "temperature": self.config['temperature']
            }
            
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data
                )
                response.raise_for_status()
                
                result = response.json()
                return result['choices'][0]['message']['content']
                
        except Exception as e:
            self.logger.error(f"Perplexity API 호출 오류: {e}")
            raise
            
    def _parse_response(self, response_text: str) -> Dict:
        """Perplexity 응답 파싱"""
        try:
            # JSON 추출
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = response_text[start_idx:end_idx]
                result = json.loads(json_str)
                
                # 필수 필드 검증
                required_fields = ['sentiment', 'confidence', 'key_news', 'market_impact']
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
            "sentiment": "NEUTRAL",
            "confidence": 0.5,
            "key_news": ["분석 실패"],
            "market_impact": "LOW",
            "trend_prediction": "NEUTRAL",
            "risk_factors": ["분석 불가"],
            "opportunities": ["분석 불가"],
            "summary": "뉴스 분석에 실패했습니다."
        }
        
    def _get_default_value(self, field: str):
        """필드별 기본값 반환"""
        defaults = {
            'sentiment': 'NEUTRAL',
            'confidence': 0.5,
            'key_news': ['분석 불가'],
            'market_impact': 'LOW',
            'trend_prediction': 'NEUTRAL',
            'risk_factors': ['분석 불가'],
            'opportunities': ['분석 불가'],
            'summary': '분석 불가'
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
                    llm_provider='perplexity',
                    analysis_type='news_sentiment',
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
            'provider': 'Perplexity API',
            'model': self.config['model'],
            'weight': self.config['weight'],
            'status': 'active'
        }
        
    def analyze_multiple_symbols(self, symbols: List[str], prices: Dict[str, float]) -> Dict[str, Dict]:
        """여러 심볼에 대한 뉴스 분석"""
        results = {}
        
        for symbol in symbols:
            try:
                current_price = prices.get(symbol, 0)
                result = self.analyze_news_sentiment(symbol, current_price)
                results[symbol] = result
                
                # API 호출 간격 조절
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"{symbol} 뉴스 분석 실패: {e}")
                results[symbol] = self._get_default_response()
                
        return results 