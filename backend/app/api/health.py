# 2025-09-30 17:45, Claude 작성
"""
Health Check API
시스템 상태 확인 엔드포인트
"""

from fastapi import APIRouter, HTTPException
from typing import Dict

router = APIRouter()


@router.get("/")
async def health_check() -> Dict[str, str]:
    """
    기본 헬스체크
    
    Returns:
        Dict: 서버 상태 정보
    """
    return {
        "status": "healthy",
        "service": "CS AI Agent API"
    }


@router.get("/detailed")
async def detailed_health_check() -> Dict[str, any]:
    """
    상세 헬스체크
    각 서비스(Weaviate, MongoDB, Redis) 연결 상태 확인
    
    TODO: Phase 1에서 실제 연결 체크 로직 구현
    
    Returns:
        Dict: 각 서비스별 상태
    """
    # TODO: 실제 서비스 연결 체크
    return {
        "status": "healthy",
        "services": {
            "weaviate": "not_configured",
            "mongodb": "not_configured",
            "redis": "not_configured",
            "claude_api": "not_configured"
        }
    }
