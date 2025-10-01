"""
MySQL 데이터베이스 모델 - 고객 문의

2025-10-01 14:15, Claude 작성

이 모듈은 네이버 API에서 받은 고객 문의 데이터를 MySQL에 저장하기 위한
SQLAlchemy ORM 모델을 정의합니다.

설계 원칙:
1. 네이버 API 원본 데이터를 최대한 그대로 보존
2. 나중에 문제 발생 시 원본 데이터로 복구 가능하도록 설계
3. 타임스탬프를 통한 데이터 추적 가능
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class CustomerInquiry(Base):
    """
    고객 문의 테이블
    
    네이버 스마트스토어 API에서 받은 고객 문의를 그대로 저장합니다.
    이 테이블은 "source of truth"로 작동하며, 모든 원본 데이터를 보존합니다.
    
    테이블명: customer_inquiries
    """
    
    __tablename__ = 'customer_inquiries'
    
    # 기본 키 (자동 증가)
    id = Column(
        Integer, 
        primary_key=True, 
        autoincrement=True,
        comment="내부 시퀀스 ID"
    )
    
    # 네이버 문의 번호 (고유)
    inquiry_no = Column(
        Integer,
        nullable=False,
        unique=True,
        index=True,
        comment="네이버 문의 번호 (고유 식별자)"
    )
    
    # 문의 기본 정보
    category = Column(
        String(50),
        nullable=True,
        index=True,
        comment="문의 유형 (상품, 배송, 반품, 교환, 환불, 기타)"
    )
    
    title = Column(
        String(500),
        nullable=False,
        comment="문의 제목"
    )
    
    inquiry_content = Column(
        Text,
        nullable=False,
        comment="문의 내용"
    )
    
    inquiry_registration_date_time = Column(
        DateTime,
        nullable=False,
        index=True,
        comment="문의 등록 일시"
    )
    
    # 답변 정보
    answered = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="답변 완료 여부"
    )
    
    answer_content_id = Column(
        Integer,
        nullable=True,
        comment="최근 문의 답변 ID"
    )
    
    answer_content = Column(
        Text,
        nullable=True,
        comment="최근 문의 답변 내용"
    )
    
    answer_template_no = Column(
        Integer,
        nullable=True,
        comment="답변 템플릿 번호"
    )
    
    answer_registration_date_time = Column(
        DateTime,
        nullable=True,
        comment="답변 등록 일시"
    )
    
    # 주문 관련 정보
    order_id = Column(
        String(100),
        nullable=False,
        index=True,
        comment="주문 ID"
    )
    
    product_no = Column(
        String(100),
        nullable=True,
        index=True,
        comment="상품번호"
    )
    
    product_order_id_list = Column(
        Text,
        nullable=True,
        comment="상품 주문 ID 목록 (쉼표 구분)"
    )
    
    product_name = Column(
        String(500),
        nullable=True,
        comment="상품명"
    )
    
    product_order_option = Column(
        String(500),
        nullable=True,
        comment="상품 주문 옵션"
    )
    
    # 고객 정보
    customer_id = Column(
        String(100),
        nullable=True,
        index=True,
        comment="구매자 ID"
    )
    
    customer_name = Column(
        String(100),
        nullable=False,
        comment="구매자 이름"
    )
    
    # 처리 상태 추적
    processing_status = Column(
        String(50),
        nullable=False,
        default='pending',
        index=True,
        comment="처리 상태 (pending, exported_to_sheet, cs_reviewed, synced_to_mongo)"
    )
    
    ai_answer_generated = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="AI 답변 생성 여부"
    )
    
    cs_reviewed = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="CS팀 검수 완료 여부"
    )
    
    # 타임스탬프
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        comment="레코드 생성 시간"
    )
    
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
        comment="레코드 수정 시간"
    )
    
    # API 동기화 정보
    last_synced_from_naver = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        comment="네이버 API에서 마지막으로 가져온 시간"
    )
    
    # 복합 인덱스 정의
    __table_args__ = (
        Index('idx_category_answered', 'category', 'answered'),
        Index('idx_status_created', 'processing_status', 'created_at'),
        Index('idx_inquiry_date', 'inquiry_registration_date_time'),
        {'comment': '네이버 스마트스토어 고객 문의 원본 데이터'}
    )
    
    def __repr__(self):
        return (
            f"<CustomerInquiry("
            f"inquiry_no={self.inquiry_no}, "
            f"title='{self.title[:30]}...', "
            f"answered={self.answered}"
            f")>"
        )
    
    def to_dict(self):
        """
        딕셔너리로 변환
        
        Google Sheet나 MongoDB로 내보낼 때 사용합니다.
        """
        return {
            'inquiry_no': self.inquiry_no,
            'category': self.category,
            'title': self.title,
            'inquiry_content': self.inquiry_content,
            'inquiry_registration_date_time': self.inquiry_registration_date_time.isoformat() if self.inquiry_registration_date_time else None,
            'answered': self.answered,
            'answer_content': self.answer_content,
            'answer_registration_date_time': self.answer_registration_date_time.isoformat() if self.answer_registration_date_time else None,
            'order_id': self.order_id,
            'product_no': self.product_no,
            'product_name': self.product_name,
            'product_order_option': self.product_order_option,
            'customer_id': self.customer_id,
            'customer_name': self.customer_name,
            'processing_status': self.processing_status,
            'ai_answer_generated': self.ai_answer_generated,
            'cs_reviewed': self.cs_reviewed,
        }


class InquiryProcessingLog(Base):
    """
    문의 처리 로그 테이블
    
    각 문의가 어떤 단계를 거쳤는지 추적합니다.
    문제 발생 시 디버깅에 유용합니다.
    
    테이블명: inquiry_processing_logs
    """
    
    __tablename__ = 'inquiry_processing_logs'
    
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    
    inquiry_no = Column(
        Integer,
        nullable=False,
        index=True,
        comment="문의 번호"
    )
    
    stage = Column(
        String(100),
        nullable=False,
        comment="처리 단계 (fetched, exported, reviewed, synced)"
    )
    
    status = Column(
        String(50),
        nullable=False,
        comment="상태 (success, failed, pending)"
    )
    
    message = Column(
        Text,
        nullable=True,
        comment="로그 메시지 또는 에러 메시지"
    )
    
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        index=True,
        comment="로그 생성 시간"
    )
    
    __table_args__ = (
        Index('idx_inquiry_stage', 'inquiry_no', 'stage'),
        {'comment': '문의 처리 과정 추적 로그'}
    )
    
    def __repr__(self):
        return (
            f"<InquiryProcessingLog("
            f"inquiry_no={self.inquiry_no}, "
            f"stage='{self.stage}', "
            f"status='{self.status}'"
            f")>"
        )
