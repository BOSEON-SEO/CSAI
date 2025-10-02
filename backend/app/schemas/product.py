# backend/app/schemas/product.py
# 2025-10-02 16:55, Claude 작성

"""
제품 정보 관련 Pydantic 스키마

Spring에서 CSAI로 제품 정보를 전송할 때 사용하는 스키마입니다.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator


class ProductInput(BaseModel):
    """
    Spring에서 CSAI로 전송하는 제품 정보
    
    이 스키마는 products_keychron.csv 같은 제품 데이터를
    구조화한 형태입니다.
    
    Example:
        {
            "product_id": "K10_PRO_MAX",
            "brand_channel": "KEYCHRON",
            "product_name": "키크론 K10 PRO MAX 무선 기계식 키보드",
            "product_name_synonyms": ["K10 프로 맥스", "K10 PRO"],
            "price": "139000",
            "discontinued": false,
            "specs": {
                "keyboard_type": "기계식",
                "switch_options": ["바나나축", "적축", "갈축"],
                "connection_method": ["블루투스", "2.4GHz", "유선"],
                "battery_capacity": "4000mAh",
                ...
            }
        }
    """
    
    # 필수 필드
    product_id: str = Field(
        ...,
        description="제품 고유 ID (CSAI 내부용)",
        example="K10_PRO_MAX"
    )
    
    brand_channel: str = Field(
        ...,
        description="브랜드 채널",
        example="KEYCHRON"
    )
    
    product_name: str = Field(
        ...,
        description="제품명",
        example="키크론 K10 PRO MAX 무선 기계식 키보드"
    )
    
    # 선택 필드
    product_name_synonyms: List[str] = Field(
        default_factory=list,
        description="제품명 동의어 (검색용)",
        example=["K10 프로 맥스", "K10 PRO", "K10PRO MAX"]
    )
    
    price: Optional[str] = Field(
        None,
        description="가격 (문자열, 통화 정보 포함 가능)",
        example="139,000원"
    )
    
    discontinued: bool = Field(
        default=False,
        description="단종 여부"
    )
    
    release_date: Optional[str] = Field(
        None,
        description="출시일",
        example="2024-06"
    )
    
    # 제품 스펙 (유연한 구조)
    specs: Dict[str, Any] = Field(
        default_factory=dict,
        description="제품 스펙 (자유 형식)",
        example={
            "keyboard_type": "기계식",
            "switch_options": ["바나나축", "적축"],
            "connection_method": ["블루투스", "유선"],
            "battery_capacity": "4000mAh"
        }
    )
    
    # 태그 (검색 최적화)
    tags: List[str] = Field(
        default_factory=list,
        description="검색 태그",
        example=["무선", "블루투스", "기계식", "풀배열"]
    )
    
    # 특징 (FAQ 답변 생성용)
    features: List[str] = Field(
        default_factory=list,
        description="주요 특징",
        example=[
            "핫스왑 지원",
            "RGB 백라이트",
            "8000mAh 배터리"
        ]
    )
    
    # 호환성 정보
    compatibility: Dict[str, Any] = Field(
        default_factory=dict,
        description="호환성 정보",
        example={
            "os": ["Windows", "macOS", "Linux"],
            "devices": ["PC", "Mac", "iPad"]
        }
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "product_id": "K10_PRO_MAX",
                "brand_channel": "KEYCHRON",
                "product_name": "키크론 K10 PRO MAX 무선 기계식 키보드",
                "product_name_synonyms": ["K10 프로 맥스", "K10 PRO"],
                "price": "139,000원",
                "discontinued": False,
                "specs": {
                    "keyboard_type": "기계식",
                    "keyboard_layout": "풀배열",
                    "switch_options": ["바나나축", "적축", "갈축"],
                    "connection_method": ["블루투스", "2.4GHz", "유선"],
                    "battery_capacity": "4000mAh",
                    "hot_swap": True
                },
                "tags": ["무선", "블루투스", "기계식", "풀배열"],
                "features": [
                    "핫스왑 지원",
                    "RGB 백라이트",
                    "8000mAh 대용량 배터리"
                ]
            }
        }
    
    @validator('brand_channel')
    def validate_brand(cls, v):
        """브랜드 채널 검증"""
        valid_brands = ['KEYCHRON', 'GTGEAR', 'AIPER']
        if v not in valid_brands:
            raise ValueError(f'브랜드는 {valid_brands} 중 하나여야 합니다')
        return v


class ProductBatch(BaseModel):
    """
    제품 정보 배치 입력
    
    여러 제품을 한 번에 전송할 때 사용합니다.
    """
    products: List[ProductInput] = Field(
        ...,
        description="제품 리스트",
        min_items=1,
        max_items=500  # 한 번에 최대 500개
    )


class ProductResponse(BaseModel):
    """
    제품 정보 저장 응답
    """
    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    product_id: str = Field(..., description="처리된 제품 ID")
    stored_in_mongodb: bool = Field(..., description="MongoDB 저장 여부")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "제품 정보가 성공적으로 저장되었습니다",
                "product_id": "K10_PRO_MAX",
                "stored_in_mongodb": True
            }
        }


class ProductBatchResponse(BaseModel):
    """
    제품 정보 배치 저장 응답
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
                "total": 100,
                "succeeded": 98,
                "failed": 2,
                "errors": [
                    {
                        "product_id": "INVALID_PRODUCT",
                        "error": "필수 필드 누락"
                    }
                ]
            }
        }
