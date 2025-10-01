"""
네이버 Commerce API 서비스

2025-10-01 14:30, Claude 작성

이 모듈은 네이버 스마트스토어 Commerce API를 호출하고
받은 데이터를 MySQL 데이터베이스에 저장하는 서비스를 제공합니다.

주요 기능:
1. 네이버 API 인증 및 호출
2. 페이징 처리를 통한 대량 데이터 수집
3. MySQL에 원본 데이터 저장
4. 중복 방지 및 업데이트 처리
"""

import requests
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..models.naver_api import NaverInquiryResponse, InquiryContent
from ..models.database import CustomerInquiry, InquiryProcessingLog


class NaverCommerceAPIService:
    """
    네이버 커머스 API 서비스 클래스
    
    네이버 스마트스토어 API와 통신하여 고객 문의를 가져오고
    데이터베이스에 저장하는 모든 로직을 담당합니다.
    
    Example:
        >>> service = NaverCommerceAPIService(client_id, client_secret)
        >>> service.fetch_and_store_inquiries(days=7)
    """
    
    BASE_URL = "https://api.commerce.naver.com/external"
    INQUIRIES_ENDPOINT = "/v1/pay-user/inquiries"
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        db_session: Session
    ):
        """
        초기화
        
        Args:
            client_id: 네이버 API 클라이언트 ID
            client_secret: 네이버 API 클라이언트 시크릿
            db_session: SQLAlchemy 데이터베이스 세션
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.db = db_session
        self.access_token = None
    
    def _get_access_token(self) -> str:
        """
        OAuth2 액세스 토큰 발급
        
        네이버 커머스 API는 OAuth2 Client Credentials 방식을 사용합니다.
        토큰은 일정 시간 유효하므로 캐싱하여 재사용합니다.
        
        Returns:
            액세스 토큰 문자열
            
        Raises:
            requests.HTTPError: 토큰 발급 실패 시
        """
        # 이미 토큰이 있으면 재사용 (실제로는 만료 시간 체크 필요)
        if self.access_token:
            return self.access_token
        
        token_url = f"{self.BASE_URL}/v1/oauth2/token"
        
        response = requests.post(
            token_url,
            data={
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': 'client_credentials'
            },
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        response.raise_for_status()
        token_data = response.json()
        self.access_token = token_data['access_token']
        
        return self.access_token
    
    def fetch_inquiries(
        self,
        start_date: str,
        end_date: str,
        page: int = 1,
        size: int = 200,
        answered: Optional[bool] = None
    ) -> NaverInquiryResponse:
        """
        고객 문의 조회
        
        Args:
            start_date: 검색 시작일 (yyyy-MM-dd)
            end_date: 검색 종료일 (yyyy-MM-dd)
            page: 페이지 번호 (1부터 시작)
            size: 페이지 크기 (10~200)
            answered: 답변 여부 필터 (None이면 전체)
            
        Returns:
            NaverInquiryResponse 객체
            
        Raises:
            requests.HTTPError: API 호출 실패 시
        """
        token = self._get_access_token()
        url = f"{self.BASE_URL}{self.INQUIRIES_ENDPOINT}"
        
        params = {
            'startSearchDate': start_date,
            'endSearchDate': end_date,
            'page': page,
            'size': size
        }
        
        if answered is not None:
            params['answered'] = 'true' if answered else 'false'
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        
        # Pydantic 모델로 파싱
        return NaverInquiryResponse.parse_obj(response.json())
    
    def save_inquiry(self, inquiry: InquiryContent) -> CustomerInquiry:
        """
        개별 문의를 데이터베이스에 저장
        
        이미 존재하는 inquiry_no면 업데이트하고,
        없으면 새로 생성합니다.
        
        Args:
            inquiry: InquiryContent 객체
            
        Returns:
            저장된 CustomerInquiry 엔티티
        """
        # 기존 레코드 확인
        existing = self.db.query(CustomerInquiry).filter(
            CustomerInquiry.inquiry_no == inquiry.inquiry_no
        ).first()
        
        if existing:
            # 업데이트
            existing.category = inquiry.category
            existing.title = inquiry.title
            existing.inquiry_content = inquiry.inquiry_content
            existing.answered = inquiry.answered
            existing.answer_content = inquiry.answer_content
            existing.answer_content_id = inquiry.answer_content_id
            existing.answer_template_no = inquiry.answer_template_no
            existing.answer_registration_date_time = inquiry.answer_registration_date_time
            existing.last_synced_from_naver = datetime.now()
            
            db_inquiry = existing
        else:
            # 새로 생성
            db_inquiry = CustomerInquiry(
                inquiry_no=inquiry.inquiry_no,
                category=inquiry.category,
                title=inquiry.title,
                inquiry_content=inquiry.inquiry_content,
                inquiry_registration_date_time=inquiry.inquiry_registration_date_time,
                answered=inquiry.answered,
                answer_content_id=inquiry.answer_content_id,
                answer_content=inquiry.answer_content,
                answer_template_no=inquiry.answer_template_no,
                answer_registration_date_time=inquiry.answer_registration_date_time,
                order_id=inquiry.order_id,
                product_no=inquiry.product_no,
                product_order_id_list=inquiry.product_order_id_list,
                product_name=inquiry.product_name,
                product_order_option=inquiry.product_order_option,
                customer_id=inquiry.customer_id,
                customer_name=inquiry.customer_name,
                processing_status='pending',
                last_synced_from_naver=datetime.now()
            )
            self.db.add(db_inquiry)
        
        try:
            self.db.commit()
            self.db.refresh(db_inquiry)
            
            # 처리 로그 기록
            log = InquiryProcessingLog(
                inquiry_no=inquiry.inquiry_no,
                stage='fetched',
                status='success',
                message='Successfully fetched from Naver API'
            )
            self.db.add(log)
            self.db.commit()
            
        except IntegrityError as e:
            self.db.rollback()
            raise e
        
        return db_inquiry
    
    def fetch_and_store_inquiries(
        self,
        days: int = 7,
        answered: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        최근 N일간의 문의를 가져와서 데이터베이스에 저장
        
        페이징을 자동으로 처리하여 모든 데이터를 가져옵니다.
        네이버 API는 최대 365일까지만 조회 가능합니다.
        
        Args:
            days: 조회할 일수 (기본 7일)
            answered: 답변 여부 필터 (None이면 전체)
            
        Returns:
            처리 결과 딕셔너리
            {
                'total_fetched': int,  # 가져온 총 문의 수
                'new_created': int,    # 새로 생성된 문의 수
                'updated': int,        # 업데이트된 문의 수
                'failed': int          # 실패한 문의 수
            }
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 네이버 API는 최대 365일까지만 조회 가능
        if days > 365:
            days = 365
            start_date = end_date - timedelta(days=365)
        
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        total_fetched = 0
        new_created = 0
        updated = 0
        failed = 0
        page = 1
        
        print(f"문의 조회 시작: {start_date_str} ~ {end_date_str}")
        
        while True:
            try:
                # API 호출
                response = self.fetch_inquiries(
                    start_date=start_date_str,
                    end_date=end_date_str,
                    page=page,
                    size=200,  # 최대 크기
                    answered=answered
                )
                
                # 데이터가 없으면 종료
                if not response.content:
                    break
                
                print(f"페이지 {page}: {len(response.content)}개 문의 처리 중...")
                
                # 각 문의 저장
                for inquiry in response.content:
                    try:
                        # 기존 레코드 확인
                        existing = self.db.query(CustomerInquiry).filter(
                            CustomerInquiry.inquiry_no == inquiry.inquiry_no
                        ).first()
                        
                        self.save_inquiry(inquiry)
                        
                        if existing:
                            updated += 1
                        else:
                            new_created += 1
                        
                        total_fetched += 1
                        
                    except Exception as e:
                        print(f"문의 #{inquiry.inquiry_no} 저장 실패: {e}")
                        failed += 1
                        
                        # 실패 로그 기록
                        log = InquiryProcessingLog(
                            inquiry_no=inquiry.inquiry_no,
                            stage='fetched',
                            status='failed',
                            message=str(e)
                        )
                        self.db.add(log)
                        self.db.commit()
                
                # 마지막 페이지면 종료
                if response.last:
                    break
                
                page += 1
                
            except requests.HTTPError as e:
                print(f"API 호출 실패: {e}")
                break
        
        result = {
            'total_fetched': total_fetched,
            'new_created': new_created,
            'updated': updated,
            'failed': failed
        }
        
        print(f"\n처리 완료:")
        print(f"  - 총 가져온 문의: {total_fetched}개")
        print(f"  - 새로 생성: {new_created}개")
        print(f"  - 업데이트: {updated}개")
        print(f"  - 실패: {failed}개")
        
        return result
    
    def get_pending_inquiries(self, limit: int = 100) -> List[CustomerInquiry]:
        """
        처리 대기 중인 문의 조회
        
        processing_status가 'pending'인 문의들을 가져옵니다.
        이 문의들은 아직 Google Sheet로 내보내지 않은 것들입니다.
        
        Args:
            limit: 최대 조회 개수
            
        Returns:
            CustomerInquiry 리스트
        """
        return self.db.query(CustomerInquiry).filter(
            CustomerInquiry.processing_status == 'pending',
            CustomerInquiry.answered == False  # 미답변만
        ).order_by(
            CustomerInquiry.inquiry_registration_date_time.asc()
        ).limit(limit).all()
