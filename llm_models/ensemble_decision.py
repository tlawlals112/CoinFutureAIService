"""
다중 LLM 앙상블 의사결정 시스템
"""

import json
import time
from typing import Dict, List, Optional, Any
from loguru import logger

from .gpt4_engine import GPT4Engine
from .claude_engine import ClaudeEngine
from .perplexity_engine import PerplexityEngine
from app.config import LLM_CONFIG


class EnsembleDecision:
    """다중 LLM 앙상블 의사결정 시스템"""
    
    def __init__(self):
        self.gpt4_engine = GPT4Engine()
        self.claude_engine = ClaudeEngine()
        self.perplexity_engine = PerplexityEngine()
        self.logger = logger.bind(name="ensemble_decision")
        
        # 가중치 설정
        self.weights = {
            'gpt4': LLM_CONFIG['gpt4']['weight'],
            'claude': LLM_CONFIG['claude']['weight'],
            'perplexity': LLM_CONFIG['perplexity']['weight']
        }
        
    def make_ensemble_decision(self, market_data: Dict) -> Dict:
        """앙상블 의사결정 수행"""
        try:
            start_time = time.time()
            
            # 각 LLM의 분석 수행
            gpt4_result = self.gpt4_engine.analyze_market(market_data)
            claude_result = self.claude_engine.analyze_market(market_data)
            
            # 뉴스 감정 분석
            symbol = market_data.get('symbol', 'UNKNOWN')
            current_price = market_data.get('close_price', 0)
            perplexity_result = self.perplexity_engine.analyze_news_sentiment(symbol, current_price)
            
            # 앙상블 의사결정 생성
            final_decision = self._combine_analyses(
                gpt4_result, claude_result, perplexity_result
            )
            
            # 성능 로깅
            processing_time = time.time() - start_time
            self.logger.info(f"앙상블 의사결정 완료 - 소요시간: {processing_time:.3f}초")
            
            return final_decision
            
        except Exception as e:
            self.logger.error(f"앙상블 의사결정 오류: {e}")
            return self._get_default_response()
            
    def _combine_analyses(self, gpt4_result: Dict, claude_result: Dict, perplexity_result: Dict) -> Dict:
        """여러 분석 결과를 종합"""
        try:
            # 의사결정 가중 평균 계산
            decision_scores = self._calculate_decision_scores(gpt4_result, claude_result, perplexity_result)
            
            # 신뢰도 가중 평균 계산
            confidence = self._calculate_weighted_confidence(gpt4_result, claude_result, perplexity_result)
            
            # 포지션 크기 가중 평균 계산
            position_size = self._calculate_weighted_position_size(gpt4_result, claude_result, perplexity_result)
            
            # 리스크 레벨 가중 평균 계산
            risk_level = self._calculate_weighted_risk_level(gpt4_result, claude_result, perplexity_result)
            
            # 최종 의사결정
            final_decision = self._determine_final_decision(decision_scores, confidence)
            
            # 종합 분석 결과
            result = {
                "decision": final_decision,
                "confidence": confidence,
                "position_size": position_size,
                "risk_level": risk_level,
                "expected_return": self._calculate_expected_return(gpt4_result, claude_result, perplexity_result),
                "reasoning": self._combine_reasoning(gpt4_result, claude_result, perplexity_result),
                "stop_loss": self._determine_stop_loss(gpt4_result, claude_result),
                "take_profit": self._determine_take_profit(gpt4_result, claude_result),
                "timeframe": self._determine_timeframe(gpt4_result, claude_result),
                "ensemble_details": {
                    "gpt4_decision": gpt4_result.get('decision', 'HOLD'),
                    "claude_decision": claude_result.get('decision', 'HOLD'),
                    "perplexity_sentiment": perplexity_result.get('sentiment', 'NEUTRAL'),
                    "decision_scores": decision_scores
                }
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"분석 결과 종합 오류: {e}")
            return self._get_default_response()
            
    def _calculate_decision_scores(self, gpt4_result: Dict, claude_result: Dict, perplexity_result: Dict) -> Dict:
        """의사결정 점수 계산"""
        scores = {
            'BUY': 0.0,
            'SELL': 0.0,
            'HOLD': 0.0
        }
        
        # GPT-4 의사결정
        gpt4_decision = gpt4_result.get('decision', 'HOLD')
        gpt4_confidence = gpt4_result.get('confidence', 0.5)
        scores[gpt4_decision] += gpt4_confidence * self.weights['gpt4']
        
        # Claude 의사결정
        claude_decision = claude_result.get('decision', 'HOLD')
        claude_confidence = claude_result.get('confidence', 0.5)
        scores[claude_decision] += claude_confidence * self.weights['claude']
        
        # Perplexity 감정 분석
        sentiment = perplexity_result.get('sentiment', 'NEUTRAL')
        sentiment_confidence = perplexity_result.get('confidence', 0.5)
        
        if sentiment == 'POSITIVE':
            scores['BUY'] += sentiment_confidence * self.weights['perplexity']
        elif sentiment == 'NEGATIVE':
            scores['SELL'] += sentiment_confidence * self.weights['perplexity']
        else:
            scores['HOLD'] += sentiment_confidence * self.weights['perplexity']
            
        return scores
        
    def _calculate_weighted_confidence(self, gpt4_result: Dict, claude_result: Dict, perplexity_result: Dict) -> float:
        """가중 평균 신뢰도 계산"""
        total_confidence = 0.0
        total_weight = 0.0
        
        # GPT-4 신뢰도
        gpt4_confidence = gpt4_result.get('confidence', 0.5)
        total_confidence += gpt4_confidence * self.weights['gpt4']
        total_weight += self.weights['gpt4']
        
        # Claude 신뢰도
        claude_confidence = claude_result.get('confidence', 0.5)
        total_confidence += claude_confidence * self.weights['claude']
        total_weight += self.weights['claude']
        
        # Perplexity 신뢰도
        perplexity_confidence = perplexity_result.get('confidence', 0.5)
        total_confidence += perplexity_confidence * self.weights['perplexity']
        total_weight += self.weights['perplexity']
        
        return total_confidence / total_weight if total_weight > 0 else 0.5
        
    def _calculate_weighted_position_size(self, gpt4_result: Dict, claude_result: Dict, perplexity_result: Dict) -> int:
        """가중 평균 포지션 크기 계산"""
        total_size = 0.0
        total_weight = 0.0
        
        # GPT-4 포지션 크기
        gpt4_size = gpt4_result.get('position_size', 5)
        total_size += gpt4_size * self.weights['gpt4']
        total_weight += self.weights['gpt4']
        
        # Claude 포지션 크기
        claude_size = claude_result.get('position_size', 5)
        total_size += claude_size * self.weights['claude']
        total_weight += self.weights['claude']
        
        # Perplexity는 포지션 크기 없으므로 중간값 사용
        total_size += 5 * self.weights['perplexity']
        total_weight += self.weights['perplexity']
        
        return round(total_size / total_weight) if total_weight > 0 else 5
        
    def _calculate_weighted_risk_level(self, gpt4_result: Dict, claude_result: Dict, perplexity_result: Dict) -> int:
        """가중 평균 리스크 레벨 계산"""
        total_risk = 0.0
        total_weight = 0.0
        
        # GPT-4 리스크 레벨
        gpt4_risk = gpt4_result.get('risk_level', 5)
        total_risk += gpt4_risk * self.weights['gpt4']
        total_weight += self.weights['gpt4']
        
        # Claude 리스크 레벨
        claude_risk = claude_result.get('risk_level', 5)
        total_risk += claude_risk * self.weights['claude']
        total_weight += self.weights['claude']
        
        # Perplexity 리스크 레벨 (뉴스 기반)
        perplexity_risk = self._calculate_news_based_risk(perplexity_result)
        total_risk += perplexity_risk * self.weights['perplexity']
        total_weight += self.weights['perplexity']
        
        return round(total_risk / total_weight) if total_weight > 0 else 5
        
    def _calculate_news_based_risk(self, perplexity_result: Dict) -> int:
        """뉴스 기반 리스크 계산"""
        sentiment = perplexity_result.get('sentiment', 'NEUTRAL')
        market_impact = perplexity_result.get('market_impact', 'LOW')
        
        # 감정에 따른 기본 리스크
        base_risk = {
            'POSITIVE': 3,
            'NEUTRAL': 5,
            'NEGATIVE': 7
        }.get(sentiment, 5)
        
        # 시장 영향도에 따른 조정
        impact_multiplier = {
            'HIGH': 1.5,
            'MEDIUM': 1.0,
            'LOW': 0.8
        }.get(market_impact, 1.0)
        
        return min(10, max(1, round(base_risk * impact_multiplier)))
        
    def _determine_final_decision(self, decision_scores: Dict, confidence: float) -> str:
        """최종 의사결정"""
        # 가장 높은 점수의 의사결정 선택
        best_decision = max(decision_scores, key=decision_scores.get)
        best_score = decision_scores[best_decision]
        
        # 신뢰도가 낮으면 HOLD로 조정
        if confidence < 0.6:
            return 'HOLD'
            
        # 점수 차이가 적으면 HOLD로 조정
        second_best = sorted(decision_scores.values(), reverse=True)[1]
        if best_score - second_best < 0.1:
            return 'HOLD'
            
        return best_decision
        
    def _calculate_expected_return(self, gpt4_result: Dict, claude_result: Dict, perplexity_result: Dict) -> float:
        """예상 수익률 계산"""
        total_return = 0.0
        total_weight = 0.0
        
        # GPT-4 예상 수익률
        gpt4_return = gpt4_result.get('expected_return', 0.0)
        total_return += gpt4_return * self.weights['gpt4']
        total_weight += self.weights['gpt4']
        
        # Claude 예상 수익률
        claude_return = claude_result.get('expected_return', 0.0)
        total_return += claude_return * self.weights['claude']
        total_weight += self.weights['claude']
        
        # Perplexity 기반 수익률 (감정 분석)
        sentiment_return = self._calculate_sentiment_return(perplexity_result)
        total_return += sentiment_return * self.weights['perplexity']
        total_weight += self.weights['perplexity']
        
        return total_return / total_weight if total_weight > 0 else 0.0
        
    def _calculate_sentiment_return(self, perplexity_result: Dict) -> float:
        """감정 분석 기반 수익률 계산"""
        sentiment = perplexity_result.get('sentiment', 'NEUTRAL')
        
        return {
            'POSITIVE': 0.05,  # 5% 상승 예상
            'NEUTRAL': 0.0,    # 변화 없음
            'NEGATIVE': -0.05  # 5% 하락 예상
        }.get(sentiment, 0.0)
        
    def _combine_reasoning(self, gpt4_result: Dict, claude_result: Dict, perplexity_result: Dict) -> str:
        """분석 근거 종합"""
        reasoning_parts = []
        
        # GPT-4 근거
        gpt4_reasoning = gpt4_result.get('reasoning', '')
        if gpt4_reasoning:
            reasoning_parts.append(f"GPT-4: {gpt4_reasoning}")
            
        # Claude 근거
        claude_reasoning = claude_result.get('reasoning', '')
        if claude_reasoning:
            reasoning_parts.append(f"Claude: {claude_reasoning}")
            
        # Perplexity 근거
        perplexity_summary = perplexity_result.get('summary', '')
        if perplexity_summary:
            reasoning_parts.append(f"뉴스: {perplexity_summary}")
            
        return " | ".join(reasoning_parts) if reasoning_parts else "앙상블 분석"
        
    def _determine_stop_loss(self, gpt4_result: Dict, claude_result: Dict) -> Optional[float]:
        """손절매 가격 결정"""
        gpt4_stop = gpt4_result.get('stop_loss')
        claude_stop = claude_result.get('stop_loss')
        
        if gpt4_stop and claude_stop:
            # 두 값의 평균
            return (float(gpt4_stop) + float(claude_stop)) / 2
        elif gpt4_stop:
            return float(gpt4_stop)
        elif claude_stop:
            return float(claude_stop)
        else:
            return None
            
    def _determine_take_profit(self, gpt4_result: Dict, claude_result: Dict) -> Optional[float]:
        """익절매 가격 결정"""
        gpt4_take = gpt4_result.get('take_profit')
        claude_take = claude_result.get('take_profit')
        
        if gpt4_take and claude_take:
            # 두 값의 평균
            return (float(gpt4_take) + float(claude_take)) / 2
        elif gpt4_take:
            return float(gpt4_take)
        elif claude_take:
            return float(claude_take)
        else:
            return None
            
    def _determine_timeframe(self, gpt4_result: Dict, claude_result: Dict) -> str:
        """투자 기간 결정"""
        gpt4_timeframe = gpt4_result.get('timeframe', '1H')
        claude_timeframe = claude_result.get('timeframe', '1H')
        
        # 더 짧은 기간 선택 (빠른 대응)
        timeframes = {
            '1M': 1, '5M': 5, '15M': 15, '30M': 30,
            '1H': 60, '4H': 240, '1D': 1440
        }
        
        gpt4_minutes = timeframes.get(gpt4_timeframe, 60)
        claude_minutes = timeframes.get(claude_timeframe, 60)
        
        selected_minutes = min(gpt4_minutes, claude_minutes)
        
        # 분을 시간/일로 변환
        if selected_minutes < 60:
            return f"{selected_minutes}M"
        elif selected_minutes < 1440:
            hours = selected_minutes // 60
            return f"{hours}H"
        else:
            days = selected_minutes // 1440
            return f"{days}D"
            
    def _get_default_response(self) -> Dict:
        """기본 응답 반환"""
        return {
            "decision": "HOLD",
            "confidence": 0.5,
            "position_size": 5,
            "risk_level": 5,
            "expected_return": 0.0,
            "reasoning": "앙상블 분석 실패",
            "stop_loss": None,
            "take_profit": None,
            "timeframe": "1H",
            "ensemble_details": {
                "gpt4_decision": "HOLD",
                "claude_decision": "HOLD",
                "perplexity_sentiment": "NEUTRAL",
                "decision_scores": {"BUY": 0.0, "SELL": 0.0, "HOLD": 1.0}
            }
        }
        
    def get_ensemble_summary(self) -> Dict:
        """앙상블 시스템 요약 정보 조회"""
        return {
            'system': 'Ensemble Decision System',
            'models': {
                'gpt4': self.gpt4_engine.get_analysis_summary(),
                'claude': self.claude_engine.get_analysis_summary(),
                'perplexity': self.perplexity_engine.get_analysis_summary()
            },
            'weights': self.weights,
            'status': 'active'
        } 