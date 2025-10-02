# backend/app/schemas/answer.py
# 2025-10-02 17:05, Claude 작성

"""
답변 생성 관련 Pydantic 스키마

Claude를 이용한 답변 생성의 입출력을 정의합니다.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class AnswerGenerationRequest(BaseModel):
    """
    답변 생성 요청
    
    QuestionAnalyzer의 결과와 함께
    관련 FAQ, 제품 정보를 포함합니다.
    
    Example:
        {
            "inquiry_no": 313605440,
            "question_analysis": {...},  # QuestionAnalysisResponse
            "similar_faqs": [...],        # 유사한 FAQ 리스트
            "product_info": {...}         # 제품 정보
        }
    """
    
    inquiry_no: int = Field(..., description="문의 번호")
    
    # 원본 질문 정보
    title: str = Field(..., description="문의 제목")
    inquiry_content: str = Field(..., description="문의 내용")
    customer_name: str = Field(..., description="고객 이름")
    
    # 질문 분석 결과
    question_analysis: Dict[str, Any] = Field(
        ...,
        description="QuestionAnalysisResponse 데이터"
    )
    
    # 컨텍스트 정보
    similar_faqs: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="유사한 FAQ 리스트 (Weaviate에서 검색)"
    )
    
    product_info: Optional[Dict[str, Any]] = Field(
        None,
        description="제품 정보 (MongoDB에서 조회)"
    )
    
    # 추가 컨텍스트
    order_info: Optional[Dict[str, Any]] = Field(
        None,
        description="주문 정보 (있는 경우)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "inquiry_no": 313605440,
                "title": "반품 가능 여부",
                "inquiry_content": "개봉 후 반품이 가능한가요?",
                "customer_name": "이*영",
                "question_analysis": {
                    "category": "반품",
                    "complexity_score": 0.15,
                    "product_codes": ["K10"]
                },
                "similar_faqs": [
                    {
                        "inquiry_no": 313000001,
                        "title": "개봉 후 반품",
                        "answer_content": "개봉 후에도 반품이 가능합니다...",
                        "similarity": 0.92
                    }
                ],
                "product_info": {
                    "product_name": "키크론 K10 PRO MAX",
                    "specs": {...}
                }
            }
        }


class AnswerGenerationResponse(BaseModel):
    """
    답변 생성 응답
    
    Claude가 생성한 답변과 메타데이터를 포함합니다.
    
    Example:
        {
            "inquiry_no": 313605440,
            "answer_content": "안녕하세요 고객님...",
            "confidence_score": 0.85,
            "generated_at": "2025-10-02T17:00:00",
            "sources_used": ["FAQ_313000001", "PRODUCT_K10"],
            "review_required": false,
            "generation_time_ms": 2500
        }
    """
    
    inquiry_no: int = Field(..., description="문의 번호")
    
    # 생성된 답변
    answer_content: str = Field(..., description="생성된 답변 내용")
    
    # 메타데이터
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="답변 신뢰도 (0-1)"
    )
    
    generated_at: datetime = Field(
        default_factory=datetime.now,
        description="답변 생성 시각"
    )
    
    # 참고 자료
    sources_used: List[str] = Field(
        default_factory=list,
        description="답변 생성에 사용된 소스 ID 리스트"
    )
    
    similar_faq_count: int = Field(
        default=0,
        description="참고한 유사 FAQ 개수"
    )
    
    # 검수 필요 여부
    review_required: bool = Field(
        ...,
        description="CS 검수가 필요한지 여부"
    )
    
    review_reason: Optional[str] = Field(
        None,
        description="검수가 필요한 이유"
    )
    
    # 성능 메트릭
    generation_time_ms: int = Field(
        ...,
        description="답변 생성 소요 시간 (밀리초)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "inquiry_no": 313605440,
                "answer_content": "안녕하세요 고객님, 키크론 입니다.\n\n개봉 후에도 반품이 가능합니다...",
                "confidence_score": 0.85,
                "generated_at": "2025-10-02T17:00:00",
                "sources_used": ["FAQ_313000001", "PRODUCT_K10_PRO_MAX"],
                "similar_faq_count": 3,
                "review_required": False,
                "review_reason": None,
                "generation_time_ms": 2500
            }
        }


class CSReviewRequest(BaseModel):
    """
    CS 검수 요청
    
    생성된 답변을 CS 팀이 검수할 때 사용합니다.
    """
    
    inquiry_no: int = Field(..., description="문의 번호")
    
    action: str = Field(
        ...,
        description="검수 액션 (approve, modify, reject)",
        pattern="^(approve|modify|reject)$"
    )
    
    modified_answer: Optional[str] = Field(
        None,
        description="수정된 답변 (action=modify인 경우)"
    )
    
    reject_reason: Optional[str] = Field(
        None,
        description="거부 사유 (action=reject인 경우)"
    )
    
    reviewer_name: str = Field(..., description="검수자 이름")
    
    class Config:
        json_schema_extra = {
            "example": {
                "inquiry_no": 313605440,
                "action": "approve",
                "modified_answer": None,
                "reject_reason": None,
                "reviewer_name": "김CS"
            }
        }


class CSReviewResponse(BaseModel):
    """
    CS 검수 응답
    """
    
    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    inquiry_no: int = Field(..., description="문의 번호")
    final_status: str = Field(
        ...,
        description="최종 상태 (approved, pending, rejected)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "답변이 승인되었습니다",
                "inquiry_no": 313605440,
                "final_status": "approved"
            }
        }
