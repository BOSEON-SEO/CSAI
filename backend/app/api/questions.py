# 2025-09-30 17:45, Claude 작성
"""
Questions API
질문 접수 및 처리 엔드포인트
"""

from fastapi import APIRouter, HTTPException
from typing import Dict

router = APIRouter()


@router.post("/analyze")
async def analyze_question(question: Dict[str, str]) -> Dict[str, any]:
    """
    질문 분석 및 답변 생성
    
    TODO: Phase 3에서 구현
    
    Args:
        question: 질문 데이터
        
    Returns:
        Dict: 분석 결과 및 답변
    """
    # TODO: QuestionAnalyzer 호출
    # TODO: WeaviateService로 유사 FAQ 검색
    # TODO: MongoDBService로 제품 정보 조회
    # TODO: ConfidenceScorer로 신뢰도 평가
    # TODO: ClaudeService로 답변 생성
    
    return {
        "question_id": "temp_id",
        "status": "not_implemented",
        "message": "Phase 3에서 구현 예정"
    }


@router.get("/{question_id}")
async def get_question_status(question_id: str) -> Dict[str, any]:
    """
    질문 처리 상태 조회
    
    TODO: Phase 3에서 구현
    
    Args:
        question_id: 질문 ID
        
    Returns:
        Dict: 질문 상태 정보
    """
    return {
        "question_id": question_id,
        "status": "not_implemented"
    }
