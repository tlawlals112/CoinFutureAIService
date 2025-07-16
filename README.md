# AI 거래 시스템 🤖📈

LLM 앙상블 기반 암호화폐 자동 거래 시스템입니다. GPT-4, Claude 3.5 Sonnet, Perplexity API를 조합하여 실시간 시장 분석과 자동 거래를 수행합니다.

## 🚀 주요 기능

### 🤖 AI 분석 엔진
- **다중 LLM 앙상블**: GPT-4, Claude 3.5 Sonnet, Perplexity API 조합
- **실시간 시장 분석**: 기술적 지표, 뉴스 감정 분석
- **자동 의사결정**: 매수/매도/홀드 신호 생성
- **리스크 관리**: 포지션 크기, 손절매, 익절매 자동 설정

### 📊 데이터 수집
- **실시간 시장 데이터**: Binance API를 통한 실시간 가격, 거래량
- **기술적 지표**: RSI, MACD, Bollinger Bands, 이동평균선
- **뉴스 데이터**: Perplexity API를 통한 뉴스 감정 분석

### 💰 거래 실행
- **자동 거래**: AI 신호에 따른 자동 매수/매도
- **리스크 제한**: 일일 손실 한도, 포지션 크기 제한
- **레버리지 거래**: 선물 거래 지원
- **실시간 모니터링**: 포지션, 손익 실시간 추적

### 📱 알림 시스템
- **Telegram Bot**: 실시간 거래 알림
- **다양한 알림**: 거래 실행, 수익/손실, 시스템 상태
- **일일 리포트**: 거래 성과 요약

### 🌐 웹 API
- **RESTful API**: FastAPI 기반 웹 인터페이스
- **실시간 모니터링**: 시스템 상태, 포지션, 거래 히스토리
- **설정 관리**: 거래 파라미터, 알림 설정

## 🏗️ 시스템 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Collector│    │   AI Engine     │    │ Trading Executor│
│                 │    │                 │    │                 │
│ • Binance API   │───▶│ • GPT-4         │───▶│ • Order Execution│
│ • Market Data   │    │ • Claude 3.5    │    │ • Risk Management│
│ • Technical     │    │ • Perplexity    │    │ • Position Mgmt │
│   Indicators    │    │ • Ensemble      │    │                 │
└─────────────────┘    │   Decision      │    └─────────────────┘
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │Notification     │
                       │Service          │
                       │                 │
                       │ • Telegram Bot  │
                       │ • Real-time     │
                       │   Alerts        │
                       └─────────────────┘
```

## 📋 요구사항

### 시스템 요구사항
- Python 3.8+
- SQLite 데이터베이스
- 인터넷 연결

### API 키 요구사항
- **Binance API**: 거래소 API 키 (실제 거래용)
- **OpenAI API**: GPT-4 사용을 위한 API 키
- **Anthropic API**: Claude 3.5 Sonnet 사용을 위한 API 키
- **Telegram Bot**: 알림 전송을 위한 봇 토큰

## 🛠️ 설치 및 설정

### 1. 저장소 클론
```bash
git clone <repository-url>
cd ai-trading-system
```

### 2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정
```bash
cp env_example.txt .env
```

`.env` 파일을 편집하여 필요한 API 키들을 설정하세요:

```env
# Binance API 설정
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET_KEY=your_binance_secret_key
BINANCE_TESTNET=true

# LLM API 설정
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
GOOGLE_API_KEY=your_google_api_key

# Telegram Bot 설정
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# 데이터베이스 설정
DATABASE_URL=sqlite:///ai_trading.db
```

### 5. 환경 설정 확인
```bash
python run.py --check-env
```

## 🚀 실행 방법

### 전체 시스템 실행 (AI 거래 + 웹 서버)
```bash
python run.py --mode both
```

### AI 거래만 실행
```bash
python run.py --mode trading
```

### 웹 서버만 실행
```bash
python run.py --mode web
```

### 개발 서버 실행
```bash
python main.py
```

## 📊 웹 인터페이스

시스템이 실행되면 다음 URL에서 웹 인터페이스에 접근할 수 있습니다:

- **메인 페이지**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **시스템 상태**: http://localhost:8000/status

## 🔧 API 엔드포인트

### 시스템 제어
- `POST /api/v1/system/start` - AI 거래 시작
- `POST /api/v1/system/stop` - AI 거래 중지
- `GET /api/v1/system/status` - 시스템 상태 조회

### 데이터 조회
- `GET /api/v1/data/market/{symbol}` - 특정 심볼 시장 데이터
- `GET /api/v1/data/market` - 모든 심볼 시장 데이터

### AI 분석
- `POST /api/v1/analysis/{symbol}` - 특정 심볼 AI 분석
- `GET /api/v1/analysis/history` - 분석 히스토리

### 거래 관리
- `GET /api/v1/trading/positions` - 현재 포지션 조회
- `GET /api/v1/trading/summary` - 거래 요약 정보
- `GET /api/v1/trading/trades` - 거래 히스토리

### 알림 관리
- `POST /api/v1/notifications/send` - 알림 전송
- `GET /api/v1/notifications/history` - 알림 히스토리
- `GET /api/v1/notifications/summary` - 알림 서비스 요약

### 통계 및 관리
- `GET /api/v1/stats/daily` - 일일 통계
- `GET /api/v1/stats/weekly` - 주간 통계
- `GET /api/v1/config` - 시스템 설정 조회

## ⚙️ 설정 옵션

### 거래 제한 설정
```python
TRADING_LIMITS = {
    'max_position_size': 0.1,  # 최대 포지션 크기 (10%)
    'max_daily_loss': 1000,    # 일일 최대 손실 (USDT)
    'min_balance_threshold': 100  # 최소 잔고 임계값
}
```

### LLM 가중치 설정
```python
LLM_CONFIG = {
    'gpt4': {'weight': 0.4, 'model': 'gpt-4-turbo-preview'},
    'claude': {'weight': 0.4, 'model': 'claude-3-5-sonnet-20241022'},
    'perplexity': {'weight': 0.2, 'model': 'llama-3.1-8b-instruct'}
}
```

### 알림 설정
```python
NOTIFICATION_CONFIG = {
    'telegram': {
        'notification_types': [
            'TRADE_EXECUTION',
            'PROFIT_LOSS',
            'SYSTEM_STATUS',
            'RISK_ALERT'
        ]
    }
}
```

## 📈 성능 모니터링

### 로그 파일
- **위치**: `logs/ai_trading_YYYY-MM-DD.log`
- **레벨**: DEBUG, INFO, WARNING, ERROR
- **보관**: 30일

### 주요 지표
- **거래 성공률**: AI 신호의 정확도
- **수익률**: 총 수익/손실
- **리스크 지표**: 최대 손실, 변동성
- **시스템 성능**: API 응답 시간, 처리 속도

## 🔒 보안 고려사항

### API 키 보안
- **환경 변수 사용**: API 키를 코드에 하드코딩하지 마세요
- **테스트넷 사용**: 개발 시 Binance 테스트넷 사용
- **권한 제한**: 최소한의 권한만 부여

### 리스크 관리
- **자금 관리**: 전체 자금의 일정 비율만 사용
- **손절매**: 자동 손절매 설정
- **모니터링**: 실시간 포지션 모니터링

## 🐛 문제 해결

### 일반적인 문제

#### 1. API 키 오류
```
Error: Invalid API key
```
**해결**: `.env` 파일에서 API 키를 확인하고 올바르게 설정하세요.

#### 2. 데이터베이스 오류
```
Error: Database connection failed
```
**해결**: 데이터베이스 파일 권한을 확인하고 다시 초기화하세요.

#### 3. Telegram 알림 실패
```
Error: Telegram bot token invalid
```
**해결**: 봇 토큰과 채팅 ID를 확인하세요.

### 로그 확인
```bash
tail -f logs/ai_trading_$(date +%Y-%m-%d).log
```

## 🤝 기여하기

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## ⚠️ 면책 조항

이 소프트웨어는 교육 및 연구 목적으로만 제공됩니다. 실제 거래에 사용할 경우 모든 위험은 사용자가 부담합니다. 암호화폐 거래는 높은 위험을 수반하며, 투자 원금 손실이 발생할 수 있습니다.

## 📞 지원

문제가 발생하거나 질문이 있으시면 이슈를 생성해 주세요.

---

**⚠️ 주의**: 이 시스템은 실제 자금으로 거래를 수행합니다. 충분한 테스트 후 사용하시기 바랍니다. 