#!/usr/bin/env python3
# backend/scripts/import_data.py
# 2025-10-02 09:00, Claude 작성

"""
통합 데이터 임포트 스크립트

CSV/JSON 데이터를 MongoDB에 임포트하는 통합 스크립트입니다.
기존 mongodb_service.py와 import_products.py의 기능을 통합했습니다.

주요 기능:
1. CSV 파일 읽기 및 파싱
2. JSON 파일 읽기
3. MongoDB 연결 및 데이터 삽입
4. 중복 데이터 처리 (upsert)
5. 진행 상황 로깅

사용법:
    # 제품 데이터 임포트
    python import_data.py --type products --source ../data/raw/products_keychron.csv
    
    # FAQ 데이터 임포트
    python import_data.py --type faqs --source ../data/raw/faq_data_sample.csv
    
    # 특정 브랜드만 임포트
    python import_data.py --type products --source ../data/raw/products_keychron.csv --brand KEYCHRON
"""

import sys
import json
import csv
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, IndexModel


# ==================== 로깅 설정 ====================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(project_root / 'logs' / 'import_data.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


# ==================== 데이터 로더 ====================

class DataLoader:
    """
    데이터 파일 로더
    
    CSV, JSON 파일을 읽어서 딕셔너리 리스트로 변환합니다.
    """
    
    @staticmethod
    def load_csv(filepath: Path, encoding: str = 'utf-8') -> List[Dict[str, Any]]:
        """
        CSV 파일 로드
        
        Args:
            filepath: CSV 파일 경로
            encoding: 파일 인코딩
            
        Returns:
            데이터 리스트
        """
        logger.info(f"📄 CSV 파일 로드 중: {filepath}")
        
        data = []
        with open(filepath, 'r', encoding=encoding) as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 빈 문자열을 None으로 변환
                cleaned_row = {
                    k: (v if v.strip() else None) if isinstance(v, str) else v
                    for k, v in row.items()
                }
                data.append(cleaned_row)
        
        logger.info(f"✅ {len(data)}개 행 로드 완료")
        return data
    
    @staticmethod
    def load_json(filepath: Path, encoding: str = 'utf-8') -> List[Dict[str, Any]]:
        """
        JSON 파일 로드
        
        Args:
            filepath: JSON 파일 경로
            encoding: 파일 인코딩
            
        Returns:
            데이터 리스트 또는 단일 데이터를 리스트로 감싼 것
        """
        logger.info(f"📄 JSON 파일 로드 중: {filepath}")
        
        with open(filepath, 'r', encoding=encoding) as f:
            data = json.load(f)
        
        # 단일 객체면 리스트로 감싸기
        if isinstance(data, dict):
            data = [data]
        
        logger.info(f"✅ {len(data)}개 항목 로드 완료")
        return data


# ==================== 데이터 변환기 ====================

class DataTransformer:
    """
    데이터 변환기
    
    원본 데이터를 MongoDB 스키마에 맞게 변환합니다.
    """
    
    @staticmethod
    def transform_product(raw_data: Dict[str, Any], brand_channel: str) -> Dict[str, Any]:
        """
        제품 데이터 변환
        
        Args:
            raw_data: 원본 CSV/JSON 데이터
            brand_channel: 브랜드 채널명
            
        Returns:
            변환된 제품 데이터
        """
        # 필수 필드
        product = {
            'product_id': str(raw_data.get('id', '')),
            'brand_channel': brand_channel.upper(),
            'product_name': raw_data.get('product_name', ''),
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        # 선택 필드 (있으면 추가)
        optional_fields = [
            'product_name_synonyms', 'price', 'discontinued', 'release_date',
            'key_binding', 'tags', 'features', 'keyboard_layout', 'keyboard_type',
            'switch_options', 'multi_media_key_count', 'main_frame_material',
            'key_cap_profile', 'stabilizer', 'reinforcing_plate', 'n_key_rollover',
            'plug_and_play', 'polling_rate', 'support_platforms', 'battery_capacity',
            'bluetooth_runtime', 'backlight_pattern', 'connection_method',
            'supports_2_4ghz', 'dynamic_keystroke', 'hot_swap_socket', 'rapid_trigger',
            'size', 'height_including_key_cap', 'height_not_including_key_cap',
            'package_contents', 'warranty_period', 'weight', 'color', 'color_details'
        ]
        
        for field in optional_fields:
            value = raw_data.get(field)
            if value is not None:
                # Boolean 변환
                if field == 'discontinued':
                    product[field] = str(value).lower() in ('true', '1', 'yes', 't')
                # 태그는 리스트로 변환
                elif field == 'tags' and isinstance(value, str):
                    product[field] = [tag.strip() for tag in value.split(',') if tag.strip()]
                else:
                    product[field] = value
        
        return product
    
    @staticmethod
    def transform_faq(raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        FAQ 데이터 변환
        
        Args:
            raw_data: 원본 CSV/JSON 데이터
            
        Returns:
            변환된 FAQ 데이터
        """
        # 날짜 파싱
        try:
            reg_date = datetime.strptime(
                raw_data.get('inquiry_registration_date_time', ''),
                '%Y-%m-%d %H:%M:%S'
            )
        except:
            reg_date = datetime.now()
        
        faq = {
            'inquiry_no': int(raw_data.get('inquiry_no', 0)),
            'brand_channel': raw_data.get('brand_channel', '').upper(),
            'internal_product_code': raw_data.get('internal_product_code', ''),
            'inquiry_category': raw_data.get('inquiry_category', ''),
            'title': raw_data.get('title', ''),
            'inquiry_content': raw_data.get('inquiry_content', ''),
            'inquiry_registration_date_time': reg_date,
            'customer_id': raw_data.get('customer_id', ''),
            'customer_name': raw_data.get('customer_name', ''),
            'order_id': raw_data.get('order_id', ''),
            'naver_product_no': raw_data.get('naver_product_no', ''),
            'product_name': raw_data.get('product_name', ''),
            'product_order_option': raw_data.get('product_order_option', ''),
            'answer_content': raw_data.get('answer_content', ''),
            'answered': raw_data.get('answered', 'false').lower() in ('true', '1', 'yes', 't'),
            'ai_answer_generated': raw_data.get('ai_answer_generated', 'false').lower() in ('true', '1', 'yes', 't'),
            'cs_reviewed': raw_data.get('cs_reviewed', 'false').lower() in ('true', '1', 'yes', 't'),
            'processing_status': raw_data.get('processing_status', 'pending'),
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        return faq


# ==================== MongoDB 임포터 ====================

class MongoDBImporter:
    """
    MongoDB 데이터 임포터
    
    데이터를 MongoDB에 삽입하고 관리합니다.
    """
    
    def __init__(self, connection_string: str, database_name: str):
        """
        초기화
        
        Args:
            connection_string: MongoDB 연결 문자열
            database_name: 데이터베이스 이름
        """
        self.connection_string = connection_string
        self.database_name = database_name
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
    
    async def connect(self):
        """MongoDB 연결"""
        logger.info(f"🔌 MongoDB 연결 중: {self.database_name}")
        
        try:
            self.client = AsyncIOMotorClient(self.connection_string)
            self.db = self.client[self.database_name]
            
            # 연결 테스트
            await self.client.admin.command('ping')
            
            logger.info("✅ MongoDB 연결 성공!")
            
        except Exception as e:
            logger.error(f"❌ MongoDB 연결 실패: {e}")
            raise
    
    async def disconnect(self):
        """MongoDB 연결 종료"""
        if self.client:
            self.client.close()
            logger.info("🔌 MongoDB 연결 종료")
    
    async def ensure_indexes(self, collection_name: str):
        """
        인덱스 생성
        
        Args:
            collection_name: 컬렉션 이름
        """
        logger.info(f"🔧 {collection_name} 인덱스 생성 중...")
        
        if collection_name == 'products':
            indexes = [
                IndexModel([("product_id", ASCENDING)], unique=True),
                IndexModel([("brand_channel", ASCENDING)]),
                IndexModel([("product_name", ASCENDING)]),
            ]
            await self.db.products.create_indexes(indexes)
        
        elif collection_name == 'faqs':
            indexes = [
                IndexModel([("inquiry_no", ASCENDING)], unique=True),
                IndexModel([("brand_channel", ASCENDING)]),
                IndexModel([("inquiry_category", ASCENDING)]),
                IndexModel([("answered", ASCENDING)]),
                IndexModel([("processing_status", ASCENDING)]),
            ]
            await self.db.faqs.create_indexes(indexes)
        
        logger.info(f"✅ {collection_name} 인덱스 생성 완료")
    
    async def import_products(
        self,
        products: List[Dict[str, Any]],
        brand_filter: Optional[str] = None
    ) -> Dict[str, int]:
        """
        제품 데이터 임포트
        
        Args:
            products: 제품 데이터 리스트
            brand_filter: 브랜드 필터 (선택)
            
        Returns:
            {'inserted': int, 'updated': int, 'failed': int}
        """
        logger.info(f"📦 제품 데이터 임포트 시작: {len(products)}개")
        
        # 인덱스 생성
        await self.ensure_indexes('products')
        
        inserted = 0
        updated = 0
        failed = 0
        
        for product in products:
            # 브랜드 필터링
            if brand_filter and product.get('brand_channel') != brand_filter.upper():
                continue
            
            try:
                result = await self.db.products.update_one(
                    {'product_id': product['product_id']},
                    {'$set': product},
                    upsert=True
                )
                
                if result.upserted_id:
                    inserted += 1
                    logger.debug(f"  ➕ 새 제품: {product['product_name']}")
                elif result.modified_count > 0:
                    updated += 1
                    logger.debug(f"  🔄 업데이트: {product['product_name']}")
                
            except Exception as e:
                failed += 1
                logger.error(f"  ❌ 실패 ({product.get('product_id')}): {e}")
        
        logger.info(f"✅ 제품 임포트 완료: 추가 {inserted}, 업데이트 {updated}, 실패 {failed}")
        
        return {
            'inserted': inserted,
            'updated': updated,
            'failed': failed
        }
    
    async def import_faqs(
        self,
        faqs: List[Dict[str, Any]],
        brand_filter: Optional[str] = None
    ) -> Dict[str, int]:
        """
        FAQ 데이터 임포트
        
        Args:
            faqs: FAQ 데이터 리스트
            brand_filter: 브랜드 필터 (선택)
            
        Returns:
            {'inserted': int, 'updated': int, 'failed': int}
        """
        logger.info(f"💬 FAQ 데이터 임포트 시작: {len(faqs)}개")
        
        # 인덱스 생성
        await self.ensure_indexes('faqs')
        
        inserted = 0
        updated = 0
        failed = 0
        
        for faq in faqs:
            # 브랜드 필터링
            if brand_filter and faq.get('brand_channel') != brand_filter.upper():
                continue
            
            try:
                result = await self.db.faqs.update_one(
                    {'inquiry_no': faq['inquiry_no']},
                    {'$set': faq},
                    upsert=True
                )
                
                if result.upserted_id:
                    inserted += 1
                    logger.debug(f"  ➕ 새 FAQ: {faq['inquiry_no']}")
                elif result.modified_count > 0:
                    updated += 1
                    logger.debug(f"  🔄 업데이트: {faq['inquiry_no']}")
                
            except Exception as e:
                failed += 1
                logger.error(f"  ❌ 실패 ({faq.get('inquiry_no')}): {e}")
        
        logger.info(f"✅ FAQ 임포트 완료: 추가 {inserted}, 업데이트 {updated}, 실패 {failed}")
        
        return {
            'inserted': inserted,
            'updated': updated,
            'failed': failed
        }


# ==================== 메인 함수 ====================

async def main():
    """메인 실행 함수"""
    
    # 인자 파싱
    parser = argparse.ArgumentParser(
        description='CSV/JSON 데이터를 MongoDB에 임포트',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 제품 데이터 임포트
  python import_data.py --type products --source ../data/raw/products_keychron.csv --brand KEYCHRON
  
  # FAQ 데이터 임포트
  python import_data.py --type faqs --source ../data/raw/faq_data_sample.csv
  
  # JSON 파일 임포트
  python import_data.py --type products --source ../data/products/keychron_products.json
        """
    )
    
    parser.add_argument(
        '--type',
        required=True,
        choices=['products', 'faqs'],
        help='임포트할 데이터 타입'
    )
    
    parser.add_argument(
        '--source',
        required=True,
        help='소스 파일 경로 (CSV 또는 JSON)'
    )
    
    parser.add_argument(
        '--brand',
        default='KEYCHRON',
        help='브랜드 채널명 (기본값: KEYCHRON)'
    )
    
    parser.add_argument(
        '--mongodb-url',
        default='mongodb://csai_user:csai_password_2025@localhost:27017/csai',
        help='MongoDB 연결 문자열'
    )
    
    parser.add_argument(
        '--database',
        default='csai',
        help='데이터베이스 이름'
    )
    
    parser.add_argument(
        '--filter-brand',
        help='특정 브랜드만 임포트 (선택)'
    )
    
    args = parser.parse_args()
    
    # 파일 경로 확인
    source_path = Path(args.source)
    if not source_path.exists():
        logger.error(f"❌ 파일을 찾을 수 없습니다: {source_path}")
        sys.exit(1)
    
    # 데이터 로드
    loader = DataLoader()
    
    if source_path.suffix == '.csv':
        raw_data = loader.load_csv(source_path)
    elif source_path.suffix == '.json':
        raw_data = loader.load_json(source_path)
    else:
        logger.error(f"❌ 지원하지 않는 파일 형식: {source_path.suffix}")
        sys.exit(1)
    
    if not raw_data:
        logger.error("❌ 데이터가 비어있습니다")
        sys.exit(1)
    
    # 데이터 변환
    transformer = DataTransformer()
    
    if args.type == 'products':
        transformed_data = [
            transformer.transform_product(item, args.brand)
            for item in raw_data
        ]
    else:  # faqs
        transformed_data = [
            transformer.transform_faq(item)
            for item in raw_data
        ]
    
    logger.info(f"🔄 {len(transformed_data)}개 데이터 변환 완료")
    
    # MongoDB 임포트
    importer = MongoDBImporter(args.mongodb_url, args.database)
    
    try:
        await importer.connect()
        
        if args.type == 'products':
            result = await importer.import_products(
                transformed_data,
                brand_filter=args.filter_brand
            )
        else:  # faqs
            result = await importer.import_faqs(
                transformed_data,
                brand_filter=args.filter_brand
            )
        
        # 결과 출력
        logger.info("=" * 60)
        logger.info("📊 임포트 결과 요약")
        logger.info("=" * 60)
        logger.info(f"  ➕ 추가됨:   {result['inserted']:>5}개")
        logger.info(f"  🔄 업데이트: {result['updated']:>5}개")
        logger.info(f"  ❌ 실패:     {result['failed']:>5}개")
        logger.info("=" * 60)
        
        if result['failed'] > 0:
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"❌ 임포트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        await importer.disconnect()
    
    logger.info("✅ 모든 작업 완료!")


if __name__ == "__main__":
    asyncio.run(main())
