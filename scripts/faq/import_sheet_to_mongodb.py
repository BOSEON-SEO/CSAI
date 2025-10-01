"""
Google Sheets에서 MongoDB로 FAQ 데이터 임포트

2025-10-01 15:00, Claude 작성

이 스크립트는 CS 팀이 전처리를 완료한 Google Sheets 데이터를 읽어서
MongoDB에 FAQ 형식으로 저장합니다. 이 데이터는 AI 에이전트가 
고객 문의에 답변할 때 사용됩니다.

워크플로우:
1. Google Sheets API로 전처리된 시트 읽기
2. 각 행을 FAQ 문서 형식으로 변환
3. 관련 제품 정보 조회 및 연결
4. MongoDB faqs 컬렉션에 저장
5. MySQL의 processing_status를 'synced_to_mongo'로 업데이트

사용법:
    python import_sheet_to_mongodb.py --sheet-id YOUR_SHEET_ID --worksheet "FAQ_20251001"
"""

import argparse
import sys
import re
from datetime import datetime
from typing import List, Dict, Any, Optional

# Google Sheets API
from google.oauth2 import service_account
from googleapiclient.discovery import build

# MongoDB
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

# MySQL (상태 업데이트용)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 프로젝트 모델 임포트
sys.path.append('C:\\workspace\\CSAI\\backend')
from app.models.database import CustomerInquiry, InquiryProcessingLog


class SheetToMongoDBImporter:
    """
    Google Sheets에서 MongoDB로 FAQ를 임포트하는 클래스
    
    CS 팀이 검수한 데이터를 AI 에이전트가 사용할 수 있는
    MongoDB 문서 형식으로 변환하고 저장합니다.
    """
    
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    
    def __init__(
        self,
        google_credentials_path: str,
        mongodb_uri: str,
        mongodb_database: str,
        mysql_connection_string: str
    ):
        """
        초기화
        
        Args:
            google_credentials_path: Google Service Account JSON 파일 경로
            mongodb_uri: MongoDB 연결 URI
            mongodb_database: MongoDB 데이터베이스 이름
            mysql_connection_string: MySQL 연결 문자열
        """
        # Google Sheets API 인증
        self.credentials = service_account.Credentials.from_service_account_file(
            google_credentials_path,
            scopes=self.SCOPES
        )
        self.sheets_service = build('sheets', 'v4', credentials=self.credentials)
        
        # MongoDB 연결
        self.mongo_client = MongoClient(mongodb_uri)
        self.mongo_db = self.mongo_client[mongodb_database]
        self.faqs_collection = self.mongo_db['faqs']
        self.products_collection = self.mongo_db['products']
        
        # MySQL 연결 (상태 업데이트용)
        engine = create_engine(mysql_connection_string)
        Session = sessionmaker(bind=engine)
        self.mysql_db = Session()
    
    def read_sheet_data(
        self,
        spreadsheet_id: str,
        worksheet_name: str
    ) -> List[Dict[str, Any]]:
        """
        Google Sheets에서 데이터 읽기
        
        Args:
            spreadsheet_id: 스프레드시트 ID
            worksheet_name: 워크시트 이름
            
        Returns:
            딕셔너리 리스트 (각 행이 하나의 딕셔너리)
        """
        range_name = f"{worksheet_name}!A:N"  # A부터 N열까지
        
        result = self.sheets_service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        
        if not values:
            return []
        
        # 첫 행은 헤더
        headers = values[0]
        data = []
        
        # 나머지 행들을 딕셔너리로 변환
        for row in values[1:]:
            # 행의 길이가 헤더보다 짧으면 빈 문자열로 채움
            row_data = row + [''] * (len(headers) - len(row))
            row_dict = dict(zip(headers, row_data))
            data.append(row_dict)
        
        return data
    
    def extract_product_ids_from_text(self, text: str) -> List[str]:
        """
        텍스트에서 제품 ID 추출
        
        제품명이나 문의 내용에서 우리가 정의한 제품 ID 패턴을 찾습니다.
        예: "KB-0068", "K10 PRO"
        
        Args:
            text: 분석할 텍스트
            
        Returns:
            제품 ID 리스트
        """
        if not text:
            return []
        
        product_ids = []
        
        # KB-숫자 패턴 매칭
        kb_pattern = r'KB-\d{4}'
        kb_matches = re.findall(kb_pattern, text, re.IGNORECASE)
        product_ids.extend(kb_matches)
        
        # MongoDB에서 제품명으로 검색
        # 예: "K10 PRO"가 텍스트에 있으면 해당 제품 찾기
        products = self.products_collection.find({}, {'product_id': 1, 'model_name': 1})
        
        for product in products:
            model_name = product.get('model_name', '')
            if model_name and model_name.lower() in text.lower():
                product_ids.append(product['product_id'])
        
        # 중복 제거
        return list(set(product_ids))
    
    def convert_to_faq_document(
        self,
        row: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        시트의 행을 MongoDB FAQ 문서로 변환
        
        Args:
            row: 시트의 한 행 (딕셔너리)
            
        Returns:
            MongoDB FAQ 문서 또는 None (변환 실패 시)
        """
        # 필수 필드 확인
        inquiry_no = row.get('inquiry_no', '')
        if not inquiry_no:
            return None
        
        try:
            inquiry_no = int(inquiry_no)
        except (ValueError, TypeError):
            return None
        
        # CS팀이 작성한 답변 확인
        cs_answer = row.get('CS_답변', '').strip()
        if not cs_answer:
            # 답변이 없으면 건너뛰기
            return None
        
        # 질문 텍스트
        question_text = row.get('inquiry_content', '').strip()
        if not question_text:
            return None
        
        # 제품 ID 추출
        product_name = row.get('product_name', '')
        product_option = row.get('product_option', '')
        combined_text = f"{product_name} {product_option} {question_text}"
        
        related_products = self.extract_product_ids_from_text(combined_text)
        
        # FAQ 문서 생성
        faq_doc = {
            'faq_id': f"FAQ-{inquiry_no}",
            'inquiry_no': inquiry_no,  # 원본 문의 번호 보존
            
            # 질문
            'question': {
                'text': question_text,
                'title': row.get('title', ''),
                'category': row.get('category', '기타'),
                'keywords': self._extract_keywords(question_text)
            },
            
            # 답변
            'answer': {
                'text': cs_answer,
                'verified': True,
                'verified_by': 'CS팀',
                'verified_at': datetime.now()
            },
            
            # 관련 제품
            'related_products': related_products,
            
            # 고객 및 주문 정보 (참고용)
            'context': {
                'customer_name': row.get('customer_name', ''),
                'order_id': row.get('order_id', ''),
                'product_name': product_name,
                'product_option': product_option
            },
            
            # 추가 정보
            'additional_info': {
                'cs_review_notes': row.get('AI_답변_검수', ''),
                'notes': row.get('비고', ''),
                'related_faqs': []
            },
            
            # 통계 (초기값)
            'stats': {
                'view_count': 0,
                'helpful_count': 0,
                'not_helpful_count': 0
            },
            
            # 메타데이터
            'metadata': {
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'status': 'active',
                'source': 'naver_smartstore',
                'original_inquiry_date': row.get('inquiry_date', '')
            }
        }
        
        return faq_doc
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        텍스트에서 키워드 추출 (간단한 버전)
        
        나중에 더 정교한 NLP 기반 키워드 추출로 교체 가능
        
        Args:
            text: 분석할 텍스트
            
        Returns:
            키워드 리스트
        """
        # 일반적인 제품 관련 키워드
        common_keywords = [
            '배터리', '연결', '블루투스', 'USB', '충전', '스위치',
            '키캡', '소음', '호환', '드라이버', '펌웨어', '불량',
            '배송', '교환', '환불', '반품', 'LED', 'RGB'
        ]
        
        keywords = []
        text_lower = text.lower()
        
        for keyword in common_keywords:
            if keyword.lower() in text_lower:
                keywords.append(keyword)
        
        return keywords
    
    def import_to_mongodb(
        self,
        spreadsheet_id: str,
        worksheet_name: str
    ) -> Dict[str, Any]:
        """
        Google Sheets 데이터를 MongoDB로 임포트
        
        Args:
            spreadsheet_id: 스프레드시트 ID
            worksheet_name: 워크시트 이름
            
        Returns:
            처리 결과 딕셔너리
        """
        print(f"시트 읽기 중: {worksheet_name}")
        rows = self.read_sheet_data(spreadsheet_id, worksheet_name)
        print(f"→ {len(rows)}개 행을 읽었습니다.")
        print()
        
        imported_count = 0
        updated_count = 0
        skipped_count = 0
        failed_count = 0
        
        for idx, row in enumerate(rows, start=2):  # 2부터 시작 (1은 헤더)
            try:
                # FAQ 문서로 변환
                faq_doc = self.convert_to_faq_document(row)
                
                if faq_doc is None:
                    skipped_count += 1
                    continue
                
                inquiry_no = faq_doc['inquiry_no']
                
                # MongoDB에 저장 (upsert)
                result = self.faqs_collection.update_one(
                    {'inquiry_no': inquiry_no},
                    {'$set': faq_doc},
                    upsert=True
                )
                
                if result.upserted_id:
                    imported_count += 1
                    print(f"  ✓ [{idx}] 새 FAQ 생성: #{inquiry_no}")
                else:
                    updated_count += 1
                    print(f"  ↻ [{idx}] FAQ 업데이트: #{inquiry_no}")
                
                # MySQL 상태 업데이트
                mysql_inquiry = self.mysql_db.query(CustomerInquiry).filter(
                    CustomerInquiry.inquiry_no == inquiry_no
                ).first()
                
                if mysql_inquiry:
                    mysql_inquiry.processing_status = 'synced_to_mongo'
                    mysql_inquiry.cs_reviewed = True
                    
                    # 로그 기록
                    log = InquiryProcessingLog(
                        inquiry_no=inquiry_no,
                        stage='synced',
                        status='success',
                        message='Synced to MongoDB from Google Sheets'
                    )
                    self.mysql_db.add(log)
                
                self.mysql_db.commit()
                
            except Exception as e:
                failed_count += 1
                print(f"  ✗ [{idx}] 실패: {e}")
                self.mysql_db.rollback()
        
        print()
        print("=" * 60)
        print("임포트 완료!")
        print(f"  - 새로 생성: {imported_count}개")
        print(f"  - 업데이트: {updated_count}개")
        print(f"  - 건너뜀: {skipped_count}개")
        print(f"  - 실패: {failed_count}개")
        print("=" * 60)
        
        return {
            'success': True,
            'imported': imported_count,
            'updated': updated_count,
            'skipped': skipped_count,
            'failed': failed_count
        }


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description='Google Sheets FAQ 데이터를 MongoDB로 임포트'
    )
    parser.add_argument(
        '--credentials',
        default='C:\\workspace\\CSAI\\config\\google_credentials.json',
        help='Google Service Account JSON 파일 경로'
    )
    parser.add_argument(
        '--mongodb-uri',
        default='mongodb://localhost:27017',
        help='MongoDB 연결 URI'
    )
    parser.add_argument(
        '--mongodb-db',
        default='csai',
        help='MongoDB 데이터베이스 이름'
    )
    parser.add_argument(
        '--mysql',
        default='mysql+pymysql://user:password@localhost/csai',
        help='MySQL 연결 문자열'
    )
    parser.add_argument(
        '--sheet-id',
        required=True,
        help='Google Sheets 스프레드시트 ID'
    )
    parser.add_argument(
        '--worksheet',
        required=True,
        help='워크시트 이름'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Google Sheets → MongoDB 임포트 시작")
    print("=" * 60)
    print()
    
    try:
        importer = SheetToMongoDBImporter(
            google_credentials_path=args.credentials,
            mongodb_uri=args.mongodb_uri,
            mongodb_database=args.mongodb_db,
            mysql_connection_string=args.mysql
        )
        
        result = importer.import_to_mongodb(
            spreadsheet_id=args.sheet_id,
            worksheet_name=args.worksheet
        )
        
        if result['success']:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ 치명적 오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
