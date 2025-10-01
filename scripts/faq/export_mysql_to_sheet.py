"""
MySQL에서 Google Sheets로 FAQ 데이터 내보내기

2025-10-01 14:45, Claude 작성

이 스크립트는 MySQL 데이터베이스에 저장된 고객 문의를 읽어서
Google Sheets로 내보냅니다. CS 팀은 이 시트에서 데이터를 확인하고
필요한 전처리 작업을 수행합니다.

워크플로우:
1. MySQL에서 processing_status='pending'인 미답변 문의 조회
2. Google Sheets API로 스프레드시트 생성 또는 기존 시트에 추가
3. 각 문의의 status를 'exported_to_sheet'로 업데이트

사용법:
    python export_mysql_to_sheet.py --limit 100 --sheet-id YOUR_SHEET_ID
"""

import argparse
import sys
from datetime import datetime
from typing import List, Dict, Any

# Google Sheets API 라이브러리
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# SQLAlchemy 설정
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 프로젝트 모델 임포트
sys.path.append('C:\\workspace\\CSAI\\backend')
from app.models.database import CustomerInquiry, InquiryProcessingLog


class MySQLToSheetExporter:
    """
    MySQL에서 Google Sheets로 데이터를 내보내는 클래스
    
    Google Sheets API를 사용하여 MySQL 데이터를 스프레드시트로 복사합니다.
    """
    
    # Google Sheets API 스코프
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    
    def __init__(
        self,
        db_connection_string: str,
        google_credentials_path: str
    ):
        """
        초기화
        
        Args:
            db_connection_string: MySQL 연결 문자열 
                                 (예: 'mysql+pymysql://user:pass@localhost/dbname')
            google_credentials_path: Google Service Account JSON 파일 경로
        """
        # 데이터베이스 연결
        self.engine = create_engine(db_connection_string)
        Session = sessionmaker(bind=self.engine)
        self.db = Session()
        
        # Google Sheets API 인증
        self.credentials = service_account.Credentials.from_service_account_file(
            google_credentials_path,
            scopes=self.SCOPES
        )
        self.sheets_service = build('sheets', 'v4', credentials=self.credentials)
    
    def get_pending_inquiries(self, limit: int = 100) -> List[CustomerInquiry]:
        """
        처리 대기 중인 문의 조회
        
        Args:
            limit: 최대 조회 개수
            
        Returns:
            CustomerInquiry 리스트
        """
        return self.db.query(CustomerInquiry).filter(
            CustomerInquiry.processing_status == 'pending',
            CustomerInquiry.answered == False
        ).order_by(
            CustomerInquiry.inquiry_registration_date_time.desc()
        ).limit(limit).all()
    
    def prepare_sheet_data(
        self,
        inquiries: List[CustomerInquiry]
    ) -> List[List[Any]]:
        """
        Google Sheets에 쓸 수 있는 형식으로 데이터 변환
        
        Args:
            inquiries: CustomerInquiry 리스트
            
        Returns:
            2차원 배열 (행과 열)
        """
        # 헤더 행
        headers = [
            'inquiry_no',
            'category',
            'title',
            'inquiry_content',
            'inquiry_date',
            'product_name',
            'product_option',
            'customer_name',
            'customer_id',
            'order_id',
            '처리상태',
            'CS_답변',  # CS팀이 작성할 열
            'AI_답변_검수',  # CS팀 검수 의견
            '비고'  # 추가 메모
        ]
        
        # 데이터 행들
        rows = [headers]
        
        for inquiry in inquiries:
            row = [
                inquiry.inquiry_no,
                inquiry.category or '',
                inquiry.title,
                inquiry.inquiry_content,
                inquiry.inquiry_registration_date_time.strftime('%Y-%m-%d %H:%M:%S'),
                inquiry.product_name or '',
                inquiry.product_order_option or '',
                inquiry.customer_name,
                inquiry.customer_id or '',
                inquiry.order_id,
                inquiry.processing_status,
                '',  # CS 답변 (비어있음 - CS팀이 작성)
                '',  # AI 답변 검수 (비어있음)
                ''   # 비고 (비어있음)
            ]
            rows.append(row)
        
        return rows
    
    def export_to_sheet(
        self,
        sheet_id: str,
        inquiries: List[CustomerInquiry],
        worksheet_name: str = None
    ) -> Dict[str, Any]:
        """
        Google Sheets로 데이터 내보내기
        
        Args:
            sheet_id: Google Sheets 스프레드시트 ID
            inquiries: 내보낼 문의 리스트
            worksheet_name: 워크시트 이름 (None이면 날짜 기반 자동 생성)
            
        Returns:
            결과 딕셔너리
        """
        if not inquiries:
            return {
                'success': True,
                'exported_count': 0,
                'message': '내보낼 문의가 없습니다.'
            }
        
        # 워크시트 이름 생성
        if worksheet_name is None:
            worksheet_name = f"FAQ_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # 데이터 준비
            data = self.prepare_sheet_data(inquiries)
            
            # 새 워크시트 추가
            add_sheet_request = {
                'addSheet': {
                    'properties': {
                        'title': worksheet_name
                    }
                }
            }
            
            batch_update_request = {'requests': [add_sheet_request]}
            self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=sheet_id,
                body=batch_update_request
            ).execute()
            
            # 데이터 쓰기
            range_name = f"{worksheet_name}!A1"
            body = {
                'values': data
            }
            
            result = self.sheets_service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            # 헤더 행 서식 설정 (굵게, 배경색)
            format_request = {
                'requests': [
                    {
                        'repeatCell': {
                            'range': {
                                'sheetId': self._get_sheet_id(sheet_id, worksheet_name),
                                'startRowIndex': 0,
                                'endRowIndex': 1
                            },
                            'cell': {
                                'userEnteredFormat': {
                                    'backgroundColor': {
                                        'red': 0.9,
                                        'green': 0.9,
                                        'blue': 0.9
                                    },
                                    'textFormat': {
                                        'bold': True
                                    }
                                }
                            },
                            'fields': 'userEnteredFormat(backgroundColor,textFormat)'
                        }
                    }
                ]
            }
            
            self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=sheet_id,
                body=format_request
            ).execute()
            
            # MySQL 상태 업데이트
            for inquiry in inquiries:
                inquiry.processing_status = 'exported_to_sheet'
                
                # 로그 기록
                log = InquiryProcessingLog(
                    inquiry_no=inquiry.inquiry_no,
                    stage='exported',
                    status='success',
                    message=f'Exported to Google Sheets: {worksheet_name}'
                )
                self.db.add(log)
            
            self.db.commit()
            
            print(f"✅ 성공: {len(inquiries)}개 문의를 '{worksheet_name}' 시트로 내보냈습니다.")
            print(f"   스프레드시트 URL: https://docs.google.com/spreadsheets/d/{sheet_id}")
            
            return {
                'success': True,
                'exported_count': len(inquiries),
                'worksheet_name': worksheet_name,
                'spreadsheet_url': f'https://docs.google.com/spreadsheets/d/{sheet_id}'
            }
            
        except HttpError as e:
            self.db.rollback()
            print(f"❌ Google Sheets API 오류: {e}")
            return {
                'success': False,
                'exported_count': 0,
                'error': str(e)
            }
        except Exception as e:
            self.db.rollback()
            print(f"❌ 예상치 못한 오류: {e}")
            return {
                'success': False,
                'exported_count': 0,
                'error': str(e)
            }
    
    def _get_sheet_id(self, spreadsheet_id: str, sheet_name: str) -> int:
        """
        워크시트의 내부 ID 조회
        
        Args:
            spreadsheet_id: 스프레드시트 ID
            sheet_name: 워크시트 이름
            
        Returns:
            워크시트 ID (정수)
        """
        spreadsheet = self.sheets_service.spreadsheets().get(
            spreadsheetId=spreadsheet_id
        ).execute()
        
        for sheet in spreadsheet['sheets']:
            if sheet['properties']['title'] == sheet_name:
                return sheet['properties']['sheetId']
        
        raise ValueError(f"워크시트 '{sheet_name}'를 찾을 수 없습니다.")


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description='MySQL FAQ 데이터를 Google Sheets로 내보내기'
    )
    parser.add_argument(
        '--db',
        default='mysql+pymysql://user:password@localhost/csai',
        help='MySQL 연결 문자열'
    )
    parser.add_argument(
        '--credentials',
        default='C:\\workspace\\CSAI\\config\\google_credentials.json',
        help='Google Service Account JSON 파일 경로'
    )
    parser.add_argument(
        '--sheet-id',
        required=True,
        help='Google Sheets 스프레드시트 ID'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=100,
        help='최대 내보낼 문의 개수'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("MySQL → Google Sheets 내보내기 시작")
    print("=" * 60)
    print()
    
    try:
        exporter = MySQLToSheetExporter(
            db_connection_string=args.db,
            google_credentials_path=args.credentials
        )
        
        # 대기 중인 문의 조회
        print(f"처리 대기 중인 문의 조회 중... (최대 {args.limit}개)")
        inquiries = exporter.get_pending_inquiries(limit=args.limit)
        print(f"→ {len(inquiries)}개 문의를 찾았습니다.")
        print()
        
        if not inquiries:
            print("내보낼 문의가 없습니다.")
            return
        
        # Google Sheets로 내보내기
        result = exporter.export_to_sheet(
            sheet_id=args.sheet_id,
            inquiries=inquiries
        )
        
        if result['success']:
            print()
            print("=" * 60)
            print("내보내기 완료!")
            print(f"  - 내보낸 문의: {result['exported_count']}개")
            print(f"  - 워크시트: {result['worksheet_name']}")
            print(f"  - URL: {result['spreadsheet_url']}")
            print("=" * 60)
        else:
            print()
            print("=" * 60)
            print("내보내기 실패")
            print(f"  - 오류: {result.get('error', '알 수 없는 오류')}")
            print("=" * 60)
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ 치명적 오류: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
