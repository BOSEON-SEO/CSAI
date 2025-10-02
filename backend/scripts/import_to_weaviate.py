#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MongoDB → Weaviate 임베딩 임포트 스크립트
투비네트웍스 글로벌 - CS AI 에이전트 프로젝트

2025-10-02 17:50, Claude 작성

이 스크립트는 MongoDB에 저장된 FAQ 데이터를 읽어서
Sentence-BERT로 벡터 임베딩을 생성한 후 Weaviate에 저장합니다.

주요 작업:
1. MongoDB에서 FAQ 데이터 읽기
2. Sentence-BERT로 임베딩 생성 (768차원 벡터)
3. Weaviate에 벡터 + 메타데이터 저장
4. 진행 상황 로깅

사용법:
    # 모든 FAQ 임포트
    python import_to_weaviate.py --type faqs
    
    # 특정 브랜드만 임포트
    python import_to_weaviate.py --type faqs --brand KEYCHRON
    
    # 배치 크기 조정 (메모리 부족 시)
    python import_to_weaviate.py --type faqs --batch-size 50
"""

import sys
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import torch

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from pymongo import MongoClient
import weaviate
from weaviate.util import generate_uuid5
from sentence_transformers import SentenceTransformer


# ==================== 로깅 설정 ====================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== 설정 ====================

# MongoDB 설정
MONGO_URI = "mongodb://admin:csai_admin_2025@localhost:27017/"
MONGO_DATABASE = "csai"

# Weaviate 설정
WEAVIATE_URL = "http://localhost:8081"

# Sentence-BERT 모델
# 한국어 + 영어 멀티링구얼 모델 (768차원 벡터)
MODEL_NAME = "jhgan/ko-sroberta-multitask"


# ==================== 임베딩 생성기 ====================

class EmbeddingGenerator:
    """
    Sentence-BERT 임베딩 생성기
    
    텍스트를 768차원 벡터로 변환합니다.
    GPU가 있으면 자동으로 사용합니다 (RTX 3050).
    """
    
    def __init__(self, model_name: str = MODEL_NAME):
        """
        초기화
        
        Args:
            model_name: Sentence-BERT 모델 이름
        """
        logger.info(f"🤖 Sentence-BERT 모델 로딩: {model_name}")
        
        # GPU 사용 가능 여부 확인
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"  💻 디바이스: {device}")
        
        if device == "cuda":
            logger.info(f"  🎮 GPU: {torch.cuda.get_device_name(0)}")
        
        # 모델 로드
        self.model = SentenceTransformer(model_name, device=device)
        
        logger.info(f"  ✅ 모델 로드 완료! (임베딩 차원: 768)")
    
    def encode(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        텍스트 리스트를 벡터로 변환
        
        Args:
            texts: 텍스트 리스트
            batch_size: 배치 크기 (GPU 메모리에 따라 조정)
        
        Returns:
            벡터 리스트 (각 벡터는 768차원)
        """
        logger.info(f"  🔄 {len(texts)}개 텍스트 임베딩 생성 중... (배치 크기: {batch_size})")
        
        # 배치로 나눠서 처리
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_tensor=False,
            normalize_embeddings=True  # 코사인 유사도 계산 최적화
        )
        
        # numpy array → list 변환
        return embeddings.tolist()


# ==================== FAQ 임포터 ====================

class FAQImporter:
    """
    MongoDB → Weaviate FAQ 임포터
    
    FAQ 데이터를 읽어서 임베딩을 생성하고 Weaviate에 저장합니다.
    """
    
    def __init__(
        self,
        mongo_uri: str,
        mongo_database: str,
        weaviate_url: str,
        embedding_generator: EmbeddingGenerator
    ):
        """
        초기화
        
        Args:
            mongo_uri: MongoDB 연결 URI
            mongo_database: MongoDB 데이터베이스 이름
            weaviate_url: Weaviate URL
            embedding_generator: 임베딩 생성기
        """
        self.embedding_generator = embedding_generator
        
        # MongoDB 연결
        logger.info("🔌 MongoDB 연결 중...")
        self.mongo_client = MongoClient(mongo_uri)
        self.mongo_db = self.mongo_client[mongo_database]
        logger.info("  ✅ MongoDB 연결 성공!")
        
        # Weaviate 연결
        logger.info("🔌 Weaviate 연결 중...")
        self.weaviate_client = weaviate.connect_to_local(
            host="localhost",
            port=8081,
            grpc_port=50051
        )
        
        if not self.weaviate_client.is_ready():
            raise ConnectionError("Weaviate가 준비되지 않았습니다")
        
        logger.info("  ✅ Weaviate 연결 성공!")
    
    def prepare_faq_text(self, faq: Dict[str, Any]) -> str:
        """
        FAQ 문서를 하나의 텍스트로 결합
        
        질문 제목 + 질문 내용 + 답변을 결합하여
        임베딩 생성용 텍스트를 만듭니다.
        
        Args:
            faq: MongoDB FAQ 문서
        
        Returns:
            결합된 텍스트
        """
        parts = []
        
        # 제목
        if faq.get('title'):
            parts.append(faq['title'])
        
        # 질문 내용
        if faq.get('inquiry_content'):
            parts.append(faq['inquiry_content'])
        
        # 답변
        if faq.get('answer_content'):
            parts.append(faq['answer_content'])
        
        # 공백으로 결합
        return ' '.join(parts).strip()
    
    def import_faqs(
        self,
        brand_filter: str = None,
        batch_size: int = 100,
        limit: int = None
    ) -> Dict[str, int]:
        """
        FAQ 데이터를 Weaviate에 임포트
        
        Args:
            brand_filter: 브랜드 필터 (예: "KEYCHRON")
            batch_size: 배치 크기
            limit: 임포트할 최대 개수 (테스트용)
        
        Returns:
            {'imported': int, 'failed': int}
        """
        logger.info("=" * 70)
        logger.info("📦 FAQ → Weaviate 임포트 시작")
        logger.info("=" * 70)
        
        # MongoDB에서 FAQ 읽기
        query = {}
        if brand_filter:
            query['brand_channel'] = brand_filter.upper()
        
        logger.info(f"\n[1/4] MongoDB에서 FAQ 읽기...")
        if brand_filter:
            logger.info(f"  🏷️  브랜드 필터: {brand_filter}")
        
        cursor = self.mongo_db.faqs.find(query)
        
        if limit:
            cursor = cursor.limit(limit)
            logger.info(f"  ⚠️  테스트 모드: 최대 {limit}개만 임포트")
        
        faqs = list(cursor)
        logger.info(f"  ✅ {len(faqs)}개 FAQ 로드 완료")
        
        if not faqs:
            logger.warning("  ⚠️  임포트할 FAQ가 없습니다!")
            return {'imported': 0, 'failed': 0}
        
        # 텍스트 준비
        logger.info(f"\n[2/4] FAQ 텍스트 준비 중...")
        texts = []
        metadata_list = []
        
        for faq in faqs:
            # 텍스트 결합
            combined_text = self.prepare_faq_text(faq)
            texts.append(combined_text)
            
            # 메타데이터 준비
            metadata = {
                'faq_id': faq.get('faq_id', f"FAQ-{faq['inquiry_no']}"),
                'inquiry_no': faq['inquiry_no'],
                'mongodb_id': str(faq['_id']),
                'brand_channel': faq.get('brand_channel', ''),
                'category': faq.get('inquiry_category', ''),
                'combined_text': combined_text,
                'answered': faq.get('answered', False),
                'created_at': faq.get('created_at', datetime.now())
            }
            metadata_list.append(metadata)
        
        logger.info(f"  ✅ {len(texts)}개 텍스트 준비 완료")
        
        # 임베딩 생성
        logger.info(f"\n[3/4] 임베딩 생성 중...")
        embeddings = self.embedding_generator.encode(texts, batch_size=batch_size)
        logger.info(f"  ✅ {len(embeddings)}개 임베딩 생성 완료")
        
        # Weaviate에 저장
        logger.info(f"\n[4/4] Weaviate에 저장 중...")
        
        collection = self.weaviate_client.collections.get("FAQ")
        
        imported = 0
        failed = 0
        
        # 배치로 나눠서 저장
        for i in range(0, len(faqs), batch_size):
            batch_metadata = metadata_list[i:i+batch_size]
            batch_vectors = embeddings[i:i+batch_size]
            
            try:
                # 배치 insert
                with collection.batch.dynamic() as batch:
                    for metadata, vector in zip(batch_metadata, batch_vectors):
                        # UUID 생성 (faq_id 기반)
                        uuid = generate_uuid5(metadata['faq_id'])
                        
                        batch.add_object(
                            properties=metadata,
                            vector=vector,
                            uuid=uuid
                        )
                
                imported += len(batch_metadata)
                
                # 진행 상황 출력
                if imported % 100 == 0 or imported == len(faqs):
                    logger.info(f"  → {imported}/{len(faqs)} 완료...")
                
            except Exception as e:
                failed += len(batch_metadata)
                logger.error(f"  ❌ 배치 저장 실패: {e}")
        
        # 결과 출력
        logger.info("\n" + "=" * 70)
        logger.info("📊 임포트 결과")
        logger.info("=" * 70)
        logger.info(f"  ✅ 성공: {imported:>5}개")
        logger.info(f"  ❌ 실패: {failed:>5}개")
        logger.info("=" * 70)
        
        return {
            'imported': imported,
            'failed': failed
        }
    
    def close(self):
        """연결 종료"""
        self.mongo_client.close()
        self.weaviate_client.close()
        logger.info("🔌 연결 종료")


# ==================== 메인 함수 ====================

def main():
    """메인 실행 함수"""
    
    parser = argparse.ArgumentParser(
        description='MongoDB FAQ 데이터를 Weaviate에 임포트',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--type',
        default='faqs',
        choices=['faqs', 'products'],
        help='임포트할 데이터 타입'
    )
    
    parser.add_argument(
        '--brand',
        help='브랜드 필터 (예: KEYCHRON)'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='배치 크기 (기본값: 100)'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        help='임포트할 최대 개수 (테스트용)'
    )
    
    args = parser.parse_args()
    
    try:
        # 임베딩 생성기 초기화
        embedding_generator = EmbeddingGenerator(MODEL_NAME)
        
        # 임포터 초기화
        importer = FAQImporter(
            mongo_uri=MONGO_URI,
            mongo_database=MONGO_DATABASE,
            weaviate_url=WEAVIATE_URL,
            embedding_generator=embedding_generator
        )
        
        # FAQ 임포트
        if args.type == 'faqs':
            result = importer.import_faqs(
                brand_filter=args.brand,
                batch_size=args.batch_size,
                limit=args.limit
            )
        
        # 성공 여부 반환
        success = result['failed'] == 0
        
        if success:
            logger.info("\n✅ 모든 작업 완료!")
        else:
            logger.warning(f"\n⚠️  일부 실패: {result['failed']}개")
        
        return success
        
    except Exception as e:
        logger.error(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        importer.close()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
