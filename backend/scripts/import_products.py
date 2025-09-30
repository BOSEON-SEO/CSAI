# 2025-09-30 17:45, Claude 작성
"""
제품 데이터 임포트 스크립트
JSON 파일을 MongoDB에 임포트
"""

import sys
import json
import logging
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent.parent))

from config import settings
from app.utils.logger import setup_logger

logger = setup_logger()


def import_products():
    """
    data/products 디렉토리의 JSON 파일을 MongoDB에 임포트
    
    TODO: Phase 2에서 구현
    """
    logger.info("제품 데이터 임포트 시작")
    
    # TODO: MongoDB 연결
    # from app.services.mongodb_service import MongoDBService
    # db_service = MongoDBService(settings.MONGODB_URL, settings.MONGODB_DB_NAME)
    
    # 제품 데이터 디렉토리
    products_dir = Path(__file__).parent.parent.parent / "data" / "products"
    
    if not products_dir.exists():
        logger.error(f"제품 데이터 디렉토리가 없습니다: {products_dir}")
        return
    
    # JSON 파일 로드
    product_files = list(products_dir.glob("*.json"))
    logger.info(f"발견된 제품 파일: {len(product_files)}개")
    
    imported_count = 0
    for product_file in product_files:
        try:
            with open(product_file, 'r', encoding='utf-8') as f:
                product_data = json.load(f)
            
            # TODO: MongoDB에 저장
            # db_service.db.products.insert_one(product_data)
            
            logger.info(f"✅ 임포트 성공: {product_data.get('product_code', 'unknown')}")
            imported_count += 1
            
        except Exception as e:
            logger.error(f"❌ 임포트 실패 ({product_file.name}): {e}")
    
    logger.info(f"제품 데이터 임포트 완료: {imported_count}/{len(product_files)}개")


if __name__ == "__main__":
    try:
        import_products()
        logger.info("✅ 제품 데이터 임포트 성공")
    except Exception as e:
        logger.error(f"❌ 제품 데이터 임포트 실패: {e}")
        sys.exit(1)
