# backend/app/schemas/question.py
# 2025-10-02 17:00, Claude 작성

"""
질문 분석 관련 Pydantic 스키마

QuestionAnalyzer의 입출력을 정의합니다.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class QuestionAnalysisRequest(BaseModel):
    """
    질문 분석 요청
    
    이 스키마는 FAQInput과 유사하지만,
    분석에 필요한 필드만 포함합니다.
    
    Example:
        {
            "inquiry_no": 313605440,
            "brand_channel": "KEYCHRON",
            "inquiry_category": "반품",
            "title": "반품 가능 여부",
            "inquiry_content": "개봉 후 반품이 가능한가요?",
            "product_name": "키크론 K10 PRO MAX",
            "product_order_option": "쉘 화이트, 바나나축"
        }
    """
    
    inquiry_no: int = Field(..., description="문의 번호")
    brand_channel: str = Field(..., description="브랜드 채널")
    inquiry_category: str = Field(..., description="문의 카테고리")
    title: str = Field(..., description="문의 제목")
    inquiry_content: str = Field(..., description="문의 내용")
    
    product_name: Optional[str] = Field(None, description="제품명")
    product_order_option: Optional[str] = Field(None, description="주문 옵션")
    
    class Config:
        json_schema_extra = {
            "example": {
                "inquiry_no": 313605440,
                "brand_channel": "KEYCHRON",
                "inquiry_category": "반품",
                "title": "반품 가능 여부",
                "inquiry_content": "개봉 후 반품이 가능한가요?",
                "product_name": "키크론 K10 PRO MAX",
                "product_order_option": "쉘 화이트, 바나나축"
            }
        }


class QuestionAnalysisResponse(BaseModel):
    """
    질문 분석 응답
    
    QuestionAnalyzer의 분석 결과를 담습니다.
    
    Example:
        {
            "inquiry_no": 313605440,
            "category": "반품",
            "brand_channel": "KEYCHRON",
            "product_codes": ["K10", "PRO MAX"],
            "product_color": "쉘 화이트",
            "product_switch": "바나나축",
            "keywords": ["반품", "개봉"],
            "tech_terms": [],
            "complexity_score": 0.15,
            "confidence_score": null,
            "should_answer": null
        }
    """
    
    inquiry_no: int = Field(..., description="문의 번호")
    
    # 기본 분류 정보
    category: str = Field(..., description="카테고리")
    brand_channel: str = Field(..., description="브랜드 채널")
    
    # 제품 정보
    product_codes: List[str] = Field(
        default_factory=list,
        description="제품 코드 리스트"
    )
    product_color: Optional[str] = Field(None, description="색상")
    product_switch: Optional[str] = Field(None, description="스위치 타입")
    
    # 분석 결과
    keywords: List[str] = Field(
        default_factory=list,
        description="추출된 키워드"
    )
    tech_terms: List[str] = Field(
        default_factory=list,
        description="기술 용어"
    )
    complexity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="복잡도 점수 (0-1)"
    )
    
    # 신뢰도 평가 (ConfidenceScorer 실행 후 채워짐)
    confidence_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="신뢰도 점수 (0-1)"
    )
    should_answer: Optional[bool] = Field(
        None,
        description="AI가 답변해야 하는지 여부"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "inquiry_no": 313605440,
                "category": "반품",
                "brand_channel": "KEYCHRON",
                "product_codes": ["K10", "PRO MAX"],
                "product_color": "쉘 화이트",
                "product_switch": "바나나축",
                "keywords": ["반품", "개봉"],
                "tech_terms": [],
                "complexity_score": 0.15,
                "confidence_score": 0.85,
                "should_answer": True
            }
        }
