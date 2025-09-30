# 2025-09-30 17:45, Claude 작성
"""
Statistics API
통계 및 대시보드 데이터 제공
"""

from fastapi import APIRouter
from typing import Dict

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_stats() -> Dict[str, any]:
    """
    대시보드 통계 조회
    
    TODO: Phase 4에서 구현
    
    Returns:
        Dict: 대시보드 통계 데이터
    """
    return {
        "total_questions": 0,
        "auto_answered": 0,
        "pending_review": 0,
        "approved": 0,
        "rejected": 0,
        "avg_response_time": 0,
        "confidence_distribution": {},
        "message": "Phase 4에서 구현 예정"
    }


@router.get("/performance")
async def get_performance_metrics() -> Dict[str, any]:
    """
    성능 지표 조회
    
    TODO: Phase 5에서 구현
    
    Returns:
        Dict: 성능 메트릭
    """
    return {
        "avg_processing_time": 0,
        "accuracy_rate": 0,
        "approval_rate": 0,
        "message": "Phase 5에서 구현 예정"
    }
