"""
AI 거래 시스템 메인 애플리케이션
"""

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio
import threading
from loguru import logger

from app.config import settings
from app.api.routes import router
from app.services.ai_engine import AIEngine
from app.utils.database import init_db


# 전역 AI 엔진 인스턴스
ai_engine = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시 실행
    logger.info("AI 거래 시스템을 시작합니다...")
    
    # 데이터베이스 초기화
    try:
        init_db()
        logger.info("데이터베이스 초기화 완료")
    except Exception as e:
        logger.error(f"데이터베이스 초기화 실패: {e}")
    
    # AI 엔진 초기화
    global ai_engine
    ai_engine = AIEngine()
    logger.info("AI 엔진 초기화 완료")
    
    yield
    
    # 종료 시 실행
    logger.info("AI 거래 시스템을 종료합니다...")
    if ai_engine:
        await ai_engine.stop_ai_trading()


# FastAPI 애플리케이션 생성
app = FastAPI(
    title="AI 거래 시스템",
    description="LLM 앙상블 기반 암호화폐 자동 거래 시스템",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(router)


# 루트 엔드포인트
@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "AI 거래 시스템에 오신 것을 환영합니다!",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


# 전역 예외 처리
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """전역 예외 처리"""
    logger.error(f"전역 예외 발생: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "내부 서버 오류가 발생했습니다."}
    )


# AI 거래 시작 엔드포인트
@app.post("/start-trading")
async def start_trading():
    """AI 거래 시작"""
    global ai_engine
    if not ai_engine:
        raise HTTPException(status_code=500, detail="AI 엔진이 초기화되지 않았습니다")
    
    try:
        # 별도 스레드에서 AI 거래 시작
        def run_ai_trading():
            asyncio.run(ai_engine.start_ai_trading())
        
        thread = threading.Thread(target=run_ai_trading, daemon=True)
        thread.start()
        
        return {"success": True, "message": "AI 거래가 시작되었습니다"}
    except Exception as e:
        logger.error(f"AI 거래 시작 실패: {e}")
        raise HTTPException(status_code=500, detail=f"AI 거래 시작 실패: {str(e)}")


# AI 거래 중지 엔드포인트
@app.post("/stop-trading")
async def stop_trading():
    """AI 거래 중지"""
    global ai_engine
    if not ai_engine:
        raise HTTPException(status_code=500, detail="AI 엔진이 초기화되지 않았습니다")
    
    try:
        await ai_engine.stop_ai_trading()
        return {"success": True, "message": "AI 거래가 중지되었습니다"}
    except Exception as e:
        logger.error(f"AI 거래 중지 실패: {e}")
        raise HTTPException(status_code=500, detail=f"AI 거래 중지 실패: {str(e)}")


# 시스템 상태 엔드포인트
@app.get("/status")
async def get_status():
    """시스템 상태 조회"""
    global ai_engine
    if not ai_engine:
        return {"status": "initializing", "message": "시스템 초기화 중"}
    
    try:
        status = await ai_engine.get_system_summary()
        return status
    except Exception as e:
        logger.error(f"상태 조회 실패: {e}")
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    # 개발 서버 실행
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 