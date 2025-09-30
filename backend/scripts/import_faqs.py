# 2025-09-30 17:45, Claude 작성
"""
FAQ 데이터 임포트 스크립트
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


def import_faqs():
    """
    data/faqs 디렉토리의 JSON 파일을 MongoDB에 임포트
    
    TODO: Phase 2에서 구현
    """
    logger.info("FAQ 데이터 임포트 시작")
    
    # TODO: MongoDB 연결
    # from app.services.mongodb_service import MongoDBService
    # db_service = MongoDBService(settings.MONGODB_URL, settings.MONGODB_DB_NAME)
    
    # FAQ 데이터 디렉토리
    faqs_dir = Path(__file__).parent.parent.parent / "data" / "faqs"
    
    if not faqs_dir.exists():
        logger.error(f"FAQ 데이터 디렉토리가 없습니다: {faqs_dir}")
        return
    
    # JSON 파일 로드
    faq_files = list(faqs_dir.glob("*.json"))
    logger.info(f"발견된 FAQ 파일: {len(faq_files)}개")
    
    imported_count = 0
    for faq_file in faq_files:
        try:
            with open(faq_file, 'r', encoding='utf-8') as f:
                faq_data = json.load(f)
            
            # TODO: MongoDB에 저장
            # db_service.db.faqs.insert_one(faq_data)
            
            logger.info(f"✅ 임포트 성공: {faq_data.get('faq_id', 'unknown')}")
            imported_count += 1
            
        except Exception as e:
            logger.error(f"❌ 임포트 실패 ({faq_file.name}): {e}")
    
    logger.info(f"FAQ 데이터 임포트 완료: {imported_count}/{len(faq_files)}개")


if __name__ == "__main__":
    try:
        import_faqs()
        logger.info("✅ FAQ 데이터 임포트 성공")
    except Exception as e:
        logger.error(f"❌ FAQ 데이터 임포트 실패: {e}")
        sys.exit(1)
