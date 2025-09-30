# 2025-09-30 17:45, Claude 작성
"""
Weaviate 초기화 스크립트
스키마 생성 및 설정
"""

import sys
import logging
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent.parent))

from config import settings
from app.utils.logger import setup_logger

logger = setup_logger()


def create_weaviate_schema():
    """
    Weaviate 스키마 생성
    
    클래스:
    - FAQ: FAQ 임베딩 저장
    
    TODO: Phase 1에서 구현
    """
    logger.info("Weaviate 스키마 생성 시작")
    
    # TODO: Weaviate 클라이언트 연결
    # import weaviate
    # client = weaviate.Client(url=settings.WEAVIATE_URL)
    
    # TODO: FAQ 클래스 스키마 정의
    faq_schema = {
        "class": "FAQ",
        "description": "고객 FAQ 임베딩",
        "vectorizer": "none",  # 외부 임베딩 사용 (Sentence-BERT)
        "properties": [
            {
                "name": "faq_id",
                "dataType": ["string"],
                "description": "FAQ 고유 ID"
            },
            {
                "name": "category",
                "dataType": ["string"],
                "description": "FAQ 카테고리"
            },
            {
                "name": "question",
                "dataType": ["text"],
                "description": "질문 텍스트"
            },
            {
                "name": "keywords",
                "dataType": ["string[]"],
                "description": "키워드 리스트"
            }
        ]
    }
    
    # TODO: 스키마 생성
    # client.schema.create_class(faq_schema)
    
    logger.info("Weaviate 스키마 생성 완료")


if __name__ == "__main__":
    try:
        create_weaviate_schema()
        logger.info("✅ Weaviate 초기화 성공")
    except Exception as e:
        logger.error(f"❌ Weaviate 초기화 실패: {e}")
        sys.exit(1)
