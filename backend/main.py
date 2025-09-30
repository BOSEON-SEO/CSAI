# 2025-09-30 17:45, Claude 작성
"""
FastAPI 메인 진입점
애플리케이션 초기화 및 라우터 등록
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# TODO: Phase 3에서 라우터 임포트 추가
# from app.api import health, questions, reviews, stats

app = FastAPI(
    title="투비네트웍스 CS AI Agent API",
    description="FAQ 자동 응답 시스템",
    version="1.0.0"
)

# CORS 설정 (프론트엔드 연동용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js 개발 서버
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """
    루트 엔드포인트
    API 상태 확인
    """
    return {
        "message": "CS AI Agent API",
        "version": "1.0.0",
        "status": "running"
    }


# TODO: Phase 3에서 라우터 등록
# app.include_router(health.router, prefix="/health", tags=["Health"])
# app.include_router(questions.router, prefix="/api/questions", tags=["Questions"])
# app.include_router(reviews.router, prefix="/api/reviews", tags=["Reviews"])
# app.include_router(stats.router, prefix="/api/stats", tags=["Statistics"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # 개발 모드: 코드 변경 시 자동 재시작
    )
