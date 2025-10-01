"""
네이버 스마트스토어 Commerce API 응답 모델

2025-10-01 14:00, Claude 작성

이 모듈은 네이버 커머스 API의 고객 문의 조회 응답을 
Python 객체로 매핑하기 위한 Pydantic 모델들을 정의합니다.

API 문서: https://apicenter.commerce.naver.com/docs/commerce-api/current/get-customer-inquiry-pay-user
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class InquiryContent(BaseModel):
    """
    고객 문의 내용 구조체
    
    네이버 스마트스토어에서 받은 개별 문의의 상세 정보를 담는 모델입니다.
    이 모델은 API 응답의 content 배열 안에 있는 각 문의 항목을 표현합니다.
    """
    
    inquiry_no: int = Field(..., alias="inquiryNo", description="문의 번호 (고유 식별자)")
    
    category: Optional[str] = Field(
        None, 
        description="문의 유형 (상품, 배송, 반품, 교환, 환불, 기타)"
    )
    
    title: str = Field(..., description="문의 제목")
    
    inquiry_content: str = Field(
        ..., 
        alias="inquiryContent", 
        description="문의 내용"
    )
    
    inquiry_registration_date_time: datetime = Field(
        ..., 
        alias="inquiryRegistrationDateTime",
        description="문의 등록 일시"
    )
    
    # 답변 관련 필드들
    answer_content_id: Optional[int] = Field(
        None, 
        alias="answerContentId",
        description="최근 문의 답변 ID"
    )
    
    answer_content: Optional[str] = Field(
        None,
        alias="answerContent", 
        description="최근 문의 답변 내용"
    )
    
    answer_template_no: Optional[int] = Field(
        None,
        alias="answerTemplateNo",
        description="최근 문의 답변 템플릿 번호"
    )
    
    answer_registration_date_time: Optional[datetime] = Field(
        None,
        alias="answerRegistrationDateTime",
        description="최근 문의 답변 등록 일시"
    )
    
    answered: bool = Field(..., description="문의 답변 여부")
    
    # 주문 관련 필드들
    order_id: str = Field(..., alias="orderId", description="주문 ID")
    
    product_no: Optional[str] = Field(
        None,
        alias="productNo",
        description="상품번호"
    )
    
    product_order_id_list: Optional[str] = Field(
        None,
        alias="productOrderIdList",
        description="상품 주문 ID 목록 (쉼표로 구분)"
    )
    
    product_name: Optional[str] = Field(
        None,
        alias="productName",
        description="상품명"
    )
    
    product_order_option: Optional[str] = Field(
        None,
        alias="productOrderOption",
        description="상품 주문 옵션"
    )
    
    # 고객 정보
    customer_id: Optional[str] = Field(
        None,
        alias="customerId",
        description="구매자 ID"
    )
    
    customer_name: str = Field(
        ...,
        alias="customerName",
        description="구매자 이름"
    )
    
    class Config:
        """Pydantic 설정"""
        populate_by_name = True  # alias와 필드명 둘 다 허용
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SortInfo(BaseModel):
    """정렬 정보"""
    sorted: bool = Field(..., description="정렬 여부")
    unsorted: bool = Field(..., description="미정렬 여부")
    empty: bool = Field(..., description="비어있는지 여부")


class PageableInfo(BaseModel):
    """
    페이징 정보
    
    Spring의 Pageable 표준 응답 구조를 따릅니다.
    """
    page_number: int = Field(..., alias="pageNumber", description="현재 페이지 번호 (0부터 시작)")
    page_size: int = Field(..., alias="pageSize", description="페이지 크기")
    sort: SortInfo = Field(..., description="정렬 정보")
    offset: int = Field(..., description="오프셋")
    paged: bool = Field(..., description="페이징 여부")
    unpaged: bool = Field(..., description="비페이징 여부")
    
    class Config:
        populate_by_name = True


class NaverInquiryResponse(BaseModel):
    """
    네이버 고객 문의 조회 API 응답
    
    GET /v1/pay-user/inquiries 엔드포인트의 전체 응답 구조입니다.
    Spring의 Page<T> 표준 응답 형식을 따릅니다.
    
    Example:
        >>> response = NaverInquiryResponse.parse_obj(api_response)
        >>> for inquiry in response.content:
        >>>     print(f"문의 #{inquiry.inquiry_no}: {inquiry.title}")
    """
    
    # 페이징 메타데이터
    total_pages: int = Field(..., alias="totalPages", description="전체 페이지 수")
    total_elements: int = Field(..., alias="totalElements", description="전체 요소 수")
    
    number: int = Field(..., description="현재 페이지 번호")
    size: int = Field(..., description="페이지 크기")
    number_of_elements: int = Field(
        ..., 
        alias="numberOfElements",
        description="현재 페이지의 요소 수"
    )
    
    # 페이지 상태
    first: bool = Field(..., description="첫 페이지 여부")
    last: bool = Field(..., description="마지막 페이지 여부")
    empty: bool = Field(..., description="비어있는지 여부")
    
    # 정렬 및 페이징 정보
    pageable: PageableInfo = Field(..., description="페이징 정보")
    sort: SortInfo = Field(..., description="정렬 정보")
    
    # 실제 데이터
    content: List[InquiryContent] = Field(
        ..., 
        description="문의 내용 목록"
    )
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def get_unanswered_inquiries(self) -> List[InquiryContent]:
        """
        미답변 문의만 필터링해서 반환
        
        Returns:
            미답변 문의 리스트
        """
        return [inquiry for inquiry in self.content if not inquiry.answered]
    
    def get_product_inquiries(self) -> List[InquiryContent]:
        """
        상품 관련 문의만 필터링해서 반환
        
        Returns:
            상품 카테고리 문의 리스트
        """
        return [
            inquiry for inquiry in self.content 
            if inquiry.category == "상품"
        ]
