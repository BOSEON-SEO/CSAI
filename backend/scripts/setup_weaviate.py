#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Weaviate 초기 설정 스크립트
투비네트웍스 글로벌 - CS AI 에이전트 프로젝트

2025-10-02 17:40, Claude 작성

이 스크립트는 Weaviate Vector Database의 스키마를 설정합니다.
FAQ와 제품 정보를 벡터로 저장하기 위한 클래스를 생성합니다.

주요 작업:
1. Weaviate 연결 확인
2. FAQ 클래스 스키마 생성
3. Product 클래스 스키마 생성 (선택)
4. 인덱스 설정

사용법:
    python setup_weaviate.py
"""

import sys
import logging
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import weaviate
from weaviate.classes.config import Configure, Property, DataType


# ==================== 로깅 설정 ====================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== 설정 ====================

WEAVIATE_URL = "http://localhost:8081"  # docker-compose.yml 참고


# ==================== Weaviate 스키마 ====================

def create_faq_schema(client: weaviate.WeaviateClient):
    """
    FAQ 클래스 스키마 생성
    
    FAQ 문서를 벡터로 저장하기 위한 클래스를 정의합니다.
    
    Args:
        client: Weaviate 클라이언트
    """
    logger.info("📋 FAQ 클래스 스키마 생성 중...")
    
    try:
        # 기존 클래스가 있으면 삭제 (재생성)
        if client.collections.exists("FAQ"):
            client.collections.delete("FAQ")
            logger.info("  ♻️  기존 FAQ 클래스 삭제")
        
        # FAQ 클래스 생성
        client.collections.create(
            name="FAQ",
            description="고객 문의 FAQ - 질문과 답변을 벡터로 저장",
            
            # 벡터 인덱스 설정
            vectorizer_config=Configure.Vectorizer.none(),  # 우리가 직접 벡터 제공
            
            # 프로퍼티 정의
            properties=[
                Property(
                    name="faq_id",
                    data_type=DataType.TEXT,
                    description="FAQ 고유 ID (예: FAQ-302260746)",
                    index_filterable=True,
                    index_searchable=False
                ),
                Property(
                    name="inquiry_no",
                    data_type=DataType.INT,
                    description="문의 번호 (네이버 스토어)",
                    index_filterable=True,
                    index_searchable=False
                ),
                Property(
                    name="mongodb_id",
                    data_type=DataType.TEXT,
                    description="MongoDB 문서 _id (상세 조회용)",
                    index_filterable=True,
                    index_searchable=False
                ),
                Property(
                    name="brand_channel",
                    data_type=DataType.TEXT,
                    description="브랜드 채널 (KEYCHRON, GTGEAR, AIPER)",
                    index_filterable=True,
                    index_searchable=False
                ),
                Property(
                    name="category",
                    data_type=DataType.TEXT,
                    description="문의 카테고리 (배송, 반품, 상품 등)",
                    index_filterable=True,
                    index_searchable=False
                ),
                Property(
                    name="combined_text",
                    data_type=DataType.TEXT,
                    description="질문 + 답변 결합 텍스트 (벡터 생성 원본)",
                    index_filterable=False,
                    index_searchable=True  # 전문 검색 가능
                ),
                Property(
                    name="answered",
                    data_type=DataType.BOOL,
                    description="답변 완료 여부",
                    index_filterable=True,
                    index_searchable=False
                ),
                Property(
                    name="created_at",
                    data_type=DataType.DATE,
                    description="생성 일시",
                    index_filterable=True,
                    index_searchable=False
                )
            ]
        )
        
        logger.info("  ✅ FAQ 클래스 생성 완료!")
        
    except Exception as e:
        logger.error(f"  ❌ FAQ 클래스 생성 실패: {e}")
        raise


def create_product_schema(client: weaviate.WeaviateClient):
    """
    Product 클래스 스키마 생성 (선택 사항)
    
    제품 정보를 벡터로 저장하기 위한 클래스를 정의합니다.
    FAQ 검색 시 관련 제품을 함께 찾을 수 있습니다.
    
    Args:
        client: Weaviate 클라이언트
    """
    logger.info("📋 Product 클래스 스키마 생성 중...")
    
    try:
        # 기존 클래스가 있으면 삭제
        if client.collections.exists("Product"):
            client.collections.delete("Product")
            logger.info("  ♻️  기존 Product 클래스 삭제")
        
        # Product 클래스 생성
        client.collections.create(
            name="Product",
            description="제품 정보 - 제품명과 스펙을 벡터로 저장",
            
            vectorizer_config=Configure.Vectorizer.none(),
            
            properties=[
                Property(
                    name="product_id",
                    data_type=DataType.TEXT,
                    description="제품 고유 ID",
                    index_filterable=True,
                    index_searchable=False
                ),
                Property(
                    name="mongodb_id",
                    data_type=DataType.TEXT,
                    description="MongoDB 문서 _id",
                    index_filterable=True,
                    index_searchable=False
                ),
                Property(
                    name="brand_channel",
                    data_type=DataType.TEXT,
                    description="브랜드 채널",
                    index_filterable=True,
                    index_searchable=False
                ),
                Property(
                    name="product_name",
                    data_type=DataType.TEXT,
                    description="제품명",
                    index_filterable=False,
                    index_searchable=True
                ),
                Property(
                    name="combined_text",
                    data_type=DataType.TEXT,
                    description="제품명 + 스펙 결합 텍스트",
                    index_filterable=False,
                    index_searchable=True
                ),
                Property(
                    name="discontinued",
                    data_type=DataType.BOOL,
                    description="단종 여부",
                    index_filterable=True,
                    index_searchable=False
                )
            ]
        )
        
        logger.info("  ✅ Product 클래스 생성 완료!")
        
    except Exception as e:
        logger.error(f"  ❌ Product 클래스 생성 실패: {e}")
        raise


# ==================== 메인 함수 ====================

def main():
    """메인 실행 함수"""
    
    logger.info("=" * 70)
    logger.info("🚀 Weaviate 초기 설정 시작")
    logger.info("=" * 70)
    
    # Weaviate 연결
    logger.info(f"\n[1/4] Weaviate 연결 중: {WEAVIATE_URL}")
    
    try:
        client = weaviate.connect_to_local(
            host="localhost",
            port=8081,
            grpc_port=50051
        )
        
        # 연결 확인
        if client.is_ready():
            logger.info("  ✅ Weaviate 연결 성공!")
        else:
            raise ConnectionError("Weaviate가 준비되지 않았습니다")
        
    except Exception as e:
        logger.error(f"  ❌ Weaviate 연결 실패: {e}")
        logger.error("\n💡 해결 방법:")
        logger.error("  1. Docker 컨테이너 확인: docker-compose ps")
        logger.error("  2. Weaviate 재시작: docker-compose restart weaviate")
        logger.error("  3. 로그 확인: docker-compose logs weaviate")
        return False
    
    try:
        # FAQ 스키마 생성
        logger.info("\n[2/4] FAQ 클래스 스키마 생성")
        create_faq_schema(client)
        
        # Product 스키마 생성
        logger.info("\n[3/4] Product 클래스 스키마 생성")
        create_product_schema(client)
        
        # 스키마 확인
        logger.info("\n[4/4] 생성된 클래스 확인")
        
        collections = client.collections.list_all()
        logger.info(f"  📋 총 {len(collections)} 개 클래스:")
        for collection_name in collections:
            logger.info(f"    - {collection_name}")
        
        # 성공
        logger.info("\n" + "=" * 70)
        logger.info("✅ Weaviate 초기 설정 완료!")
        logger.info("=" * 70)
        logger.info("\n다음 단계:")
        logger.info("  1. Sentence-BERT 모델 설정")
        logger.info("  2. MongoDB → Weaviate 데이터 임포트")
        logger.info("  3. 검색 테스트")
        logger.info("=" * 70)
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ 스키마 생성 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        client.close()
        logger.info("\n🔌 Weaviate 연결 종료")


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
