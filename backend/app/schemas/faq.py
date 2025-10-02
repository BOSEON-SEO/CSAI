# backend/app/schemas/faq.py
# 2025-10-02 16:50, Claude 작성

"""
FAQ 관련 Pydantic 스키마

Spring에서 CSAI로 FAQ 데이터를 전송할 때 사용하는 스키마입니다.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator


class FAQInput(BaseModel):
    """
    Spring에서 CSAI로 전송하는 개별 FAQ 데이터
    
    이 스키마는 Spring이 네이버 API에서 가져온 데이터를
    CSAI가 이해할 수 있는 형식으로 변환한 것입니다.
    
    Example:
        {
            "inquiry_no": 313605440,
            "brand_channel": "KEYCHRON",
            "inquiry_category": "반품",
            "title": "반품 가능 여부",
            "inquiry_content": "해당 제품으로 주문해서...",
            "inquiry_registration_date_time": "2025-09-08T14:27:04",
            "customer_id": "wjsr****",
            "customer_name": "이*영",
            "order_id": "2025090465815541",
            "product_name": "키크론 V10 PRO MAX 블루투스...",
            "product_order_option": "쉘 화이트, 바나나축",
            "answered": false
        }
    """
    
    # 필수 필드
    inquiry_no: int = Field(
        ..., 
        description="네이버 문의 번호 (고유 식별자)",
        example=313605440
    )
    
    brand_channel: str = Field(
        ...,
        description="브랜드 채널 (KEYCHRON, GTGEAR, AIPER)",
        example="KEYCHRON"
    )
    
    inquiry_category: str = Field(
        ...,
        description="문의 카테고리 (반품, 배송, 교환, 상품, 환불, 기타)",
        example="반품"
    )
    
    title: str = Field(
        ...,
        description="문의 제목",
        max_length=500,
        example="반품 가능 여부"
    )
    
    inquiry_content: str = Field(
        ...,
        description="문의 내용 (실제 고객 질문)",
        example="개봉 후 반품이 가능한가요?"
    )
    
    inquiry_registration_date_time: datetime = Field(
        ...,
        description="문의 등록 일시"
    )
    
    customer_name: str = Field(
        ...,
        description="고객 이름 (마스킹됨)",
        example="이*영"
    )
    
    order_id: str = Field(
        ...,
        description="주문 ID",
        example="2025090465815541"
    )
    
    answered: bool = Field(
        ...,
        description="답변 완료 여부"
    )
    
    # 선택 필드
    customer_id: Optional[str] = Field(
        None,
        description="고객 ID (마스킹됨)",
        example="wjsr****"
    )
    
    product_name: Optional[str] = Field(
        None,
        description="상품명",
        example="키크론 V10 PRO MAX 블루투스 인체공학 키보드"
    )
    
    product_order_option: Optional[str] = Field(
        None,
        description="상품 주문 옵션",
        example="쉘 화이트, 바나나축"
    )
    
    naver_product_no: Optional[str] = Field(
        None,
        description="네이버 상품 번호"
    )
    
    answer_content: Optional[str] = Field(
        None,
        description="기존 답변 내용 (있는 경우)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "inquiry_no": 313605440,
                "brand_channel": "KEYCHRON",
                "inquiry_category": "반품",
                "title": "반품 가능 여부",
                "inquiry_content": "개봉 후 반품이 가능한가요?",
                "inquiry_registration_date_time": "2025-09-08T14:27:04",
                "customer_id": "wjsr****",
                "customer_name": "이*영",
                "order_id": "2025090465815541",
                "product_name": "키크론 V10 PRO MAX",
                "product_order_option": "쉘 화이트, 바나나축",
                "answered": False
            }
        }
    
    @validator('inquiry_category')
    def validate_category(cls, v):
        """카테고리 검증"""
        valid_categories = ['반품', '배송', '교환', '상품', '환불', '기타']
        if v not in valid_categories:
            raise ValueError(f'카테고리는 {valid_categories} 중 하나여야 합니다')
        return v
    
    @validator('brand_channel')
    def validate_brand(cls, v):
        """브랜드 채널 검증"""
        valid_brands = ['KEYCHRON', 'GTGEAR', 'AIPER']
        if v not in valid_brands:
            raise ValueError(f'브랜드는 {valid_brands} 중 하나여야 합니다')
        return v


class FAQBatch(BaseModel):
    """
    FAQ 배치 입력 (여러 개를 한 번에)
    
    Spring이 여러 FAQ를 한 번에 전송할 때 사용합니다.
    
    Example:
        {
            "faqs": [
                {...},  # FAQInput
                {...},  # FAQInput
            ]
        }
    """
    faqs: List[FAQInput] = Field(
        ...,
        description="FAQ 리스트",
        min_items=1,
        max_items=1000  # 한 번에 최대 1000개
    )


class FAQResponse(BaseModel):
    """
    FAQ 저장 응답
    
    CSAI가 Spring에게 보내는 응답입니다.
    """
    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    inquiry_no: int = Field(..., description="처리된 문의 번호")
    stored_in_mongodb: bool = Field(..., description="MongoDB 저장 여부")
    stored_in_weaviate: bool = Field(..., description="Weaviate 저장 여부")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "FAQ가 성공적으로 저장되었습니다",
                "inquiry_no": 313605440,
                "stored_in_mongodb": True,
                "stored_in_weaviate": True
            }
        }


class FAQBatchResponse(BaseModel):
    """
    FAQ 배치 저장 응답
    """
    success: bool = Field(..., description="전체 성공 여부")
    total: int = Field(..., description="전체 개수")
    succeeded: int = Field(..., description="성공 개수")
    failed: int = Field(..., description="실패 개수")
    errors: List[dict] = Field(
        default_factory=list,
        description="실패한 항목들의 에러 정보"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "total": 10,
                "succeeded": 9,
                "failed": 1,
                "errors": [
                    {
                        "inquiry_no": 313605441,
                        "error": "중복된 inquiry_no"
                    }
                ]
            }
        }
