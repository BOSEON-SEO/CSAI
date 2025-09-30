# 2025-09-30 17:45, Claude 작성
"""
FAQ 임베딩 생성 스크립트
Sentence-BERT로 FAQ 임베딩 생성 후 Weaviate 업로드
"""

import sys
import logging
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent.parent))

from config import settings
from app.utils.logger import setup_logger

logger = setup_logger()


def create_embeddings():
    """
    MongoDB의 FAQ를 읽어서 임베딩 생성 후 Weaviate 업로드
    
    TODO: Phase 2에서 구현
    """
    logger.info("FAQ 임베딩 생성 시작")
    
    # TODO: MongoDB에서 FAQ 조회
    # from app.services.mongodb_service import MongoDBService
    # db_service = MongoDBService(settings.MONGODB_URL, settings.MONGODB_DB_NAME)
    # faqs = db_service.db.faqs.find()
    
    # TODO: Sentence-BERT 모델 로드
    # from sentence_transformers import SentenceTransformer
    # model = SentenceTransformer('jhgan/ko-sroberta-multitask')
    
    # TODO: Weaviate 서비스
    # from app.services.weaviate_service import WeaviateService
    # weaviate_service = WeaviateService(settings.WEAVIATE_URL)
    
    processed_count = 0
    # TODO: 각 FAQ에 대해
    # for faq in faqs:
    #     # 임베딩 생성
    #     question_text = faq['question']
    #     embedding = model.encode(question_text)
    #     
    #     # Weaviate 업로드
    #     weaviate_service.upload_faq(
    #         faq_id=faq['faq_id'],
    #         text=question_text,
    #         metadata=faq
    #     )
    #     
    #     processed_count += 1
    #     if processed_count % 10 == 0:
    #         logger.info(f"진행 중... {processed_count}개 처리됨")
    
    logger.info(f"FAQ 임베딩 생성 완료: {processed_count}개")


if __name__ == "__main__":
    try:
        create_embeddings()
        logger.info("✅ FAQ 임베딩 생성 성공")
    except Exception as e:
        logger.error(f"❌ FAQ 임베딩 생성 실패: {e}")
        sys.exit(1)
