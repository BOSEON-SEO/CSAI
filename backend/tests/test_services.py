# backend/tests/test_services.py
# 2025-10-02 18:15, Claude 작성

"""
MongoDB와 Weaviate Service 테스트

루트 디렉토리의 docker-compose.yml 사용
- Weaviate: localhost:8081 (8080은 Spring이 사용 중)
- MongoDB: localhost:27017

사용법:
    python tests/test_services.py
"""

import asyncio
import sys
import os

# 경로 설정
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.mongodb_service import MongoDBService
from app.services.weaviate_service import WeaviateService


async def test_mongodb():
    """MongoDB Service 테스트"""
    print("\n" + "="*70)
    print("MongoDB Service 테스트")
    print("="*70 + "\n")
    
    # 연결 (루트 docker-compose.yml 설정 사용)
    mongo = MongoDBService(
        connection_string="mongodb://admin:csai_admin_2025@localhost:27017",
        database_name="csai"
    )
    
    try:
        await mongo.connect()
        
        # 테스트 FAQ 데이터
        test_faq = {
            'inquiry_no': 999999,
            'brand_channel': 'KEYCHRON',
            'inquiry_category': '배송',
            'title': '테스트 문의',
            'inquiry_content': '배송 언제 오나요?',
            'customer_name': '테스트',
            'order_id': 'TEST123',
            'answered': False
        }
        
        # 1. FAQ 저장 테스트
        print("1. FAQ 저장 테스트...")
        success = await mongo.store_faq(test_faq)
        print(f"   결과: {'✅ 성공' if success else '❌ 실패'}")
        
        # 2. FAQ 조회 테스트
        print("\n2. FAQ 조회 테스트...")
        faq = await mongo.get_faq(999999)
        if faq:
            print(f"   ✅ 조회 성공: {faq['title']}")
        else:
            print("   ❌ 조회 실패")
        
        # 3. 통계 조회 테스트
        print("\n3. 통계 조회 테스트...")
        stats = await mongo.get_faq_stats()
        print(f"   총 FAQ: {stats['total']}개")
        print(f"   답변 완료: {stats['answered']}개")
        print(f"   대기 중: {stats['pending']}개")
        
        # 정리
        print("\n4. 테스트 데이터 정리...")
        await mongo.db.faqs.delete_one({'inquiry_no': 999999})
        print("   ✅ 정리 완료")
        
        await mongo.disconnect()
        print("\n✅ MongoDB 테스트 완료!\n")
        
    except Exception as e:
        print(f"\n❌ MongoDB 테스트 실패: {e}\n")
        import traceback
        traceback.print_exc()


async def test_weaviate():
    """Weaviate Service 테스트"""
    print("\n" + "="*70)
    print("Weaviate Service 테스트")
    print("="*70 + "\n")
    
    # 연결 (포트 8081 사용 - Spring의 8080과 충돌 방지)
    weaviate = WeaviateService(
        weaviate_url="http://localhost:8081"
    )
    
    try:
        await weaviate.connect()
        
        # 테스트 FAQ 데이터
        test_faqs = [
            {
                'inquiry_no': 999991,
                'brand_channel': 'KEYCHRON',
                'inquiry_category': '배송',
                'title': '배송 문의',
                'inquiry_content': '배송 언제 오나요?',
                'answer_content': '배송은 영업일 기준 2-3일 소요됩니다'
            },
            {
                'inquiry_no': 999992,
                'brand_channel': 'KEYCHRON',
                'inquiry_category': '반품',
                'title': '반품 가능 여부',
                'inquiry_content': '개봉 후 반품 가능한가요?',
                'answer_content': '개봉 후에도 반품이 가능합니다',
                'product_name': '키크론 K10 PRO MAX',
                'product_codes': ['K10', 'PRO MAX']
            },
            {
                'inquiry_no': 999993,
                'brand_channel': 'KEYCHRON',
                'inquiry_category': '상품',
                'title': '키보드 블루투스 연결',
                'inquiry_content': 'K10 키보드 블루투스가 안 연결돼요',
                'answer_content': '토글 스위치를 BT로 변경 후 FN+1을 5초간 눌러주세요',
                'product_name': '키크론 K10 PRO MAX',
                'product_codes': ['K10', 'PRO MAX']
            }
        ]
        
        # 1. FAQ 배치 추가 테스트
        print("1. FAQ 배치 추가 테스트...")
        result = await weaviate.add_faqs_batch(test_faqs)
        print(f"   성공: {result['succeeded']}개")
        print(f"   실패: {result['failed']}개")
        
        # 2. 총 개수 확인
        print("\n2. 총 개수 확인...")
        total = await weaviate.get_total_count()
        print(f"   총 FAQ: {total}개")
        
        # 3. 유사 FAQ 검색 테스트
        print("\n3. 유사 FAQ 검색 테스트...")
        print("   검색어: '배송이 얼마나 걸리나요?'")
        
        similar_faqs = await weaviate.search_similar_faqs(
            query_text="배송이 얼마나 걸리나요?",
            brand_channel="KEYCHRON",
            limit=3,
            min_similarity=0.5
        )
        
        print(f"   결과: {len(similar_faqs)}개 발견\n")
        for i, faq in enumerate(similar_faqs, 1):
            print(f"   [{i}] 유사도: {faq['similarity']:.2f}")
            print(f"       제목: {faq['title']}")
            print(f"       내용: {faq['inquiry_content'][:50]}...")
            print()
        
        # 4. 하이브리드 검색 테스트
        print("4. 하이브리드 검색 테스트...")
        print("   검색어: 'K10 키보드 문제'")
        
        hybrid_results = await weaviate.hybrid_search(
            query_text="K10 키보드 문제",
            keywords=["K10", "키보드"],
            brand_channel="KEYCHRON",
            limit=3
        )
        
        print(f"   결과: {len(hybrid_results)}개 발견\n")
        for i, faq in enumerate(hybrid_results, 1):
            print(f"   [{i}] 점수: {faq['score']:.2f}")
            print(f"       제목: {faq['title']}")
            print(f"       제품: {faq.get('product_name', 'N/A')}")
            print()
        
        # 정리
        print("5. 테스트 데이터 정리...")
        for faq in test_faqs:
            await weaviate.delete_faq(faq['inquiry_no'])
        print("   ✅ 정리 완료")
        
        await weaviate.disconnect()
        print("\n✅ Weaviate 테스트 완료!\n")
        
    except Exception as e:
        print(f"\n❌ Weaviate 테스트 실패: {e}\n")
        import traceback
        traceback.print_exc()


async def test_integration():
    """통합 테스트 (MongoDB + Weaviate)"""
    print("\n" + "="*70)
    print("통합 테스트 (MongoDB + Weaviate)")
    print("="*70 + "\n")
    
    # 서비스 초기화
    mongo = MongoDBService(
        connection_string="mongodb://admin:csai_admin_2025@localhost:27017",
        database_name="csai"
    )
    
    weaviate = WeaviateService(
        weaviate_url="http://localhost:8081"
    )
    
    try:
        await mongo.connect()
        await weaviate.connect()
        
        # 테스트 시나리오: Spring에서 FAQ 전송
        print("시나리오: Spring → CSAI FAQ 전송\n")
        
        faq_from_spring = {
            'inquiry_no': 999999,
            'brand_channel': 'KEYCHRON',
            'inquiry_category': '반품',
            'title': '반품 요청',
            'inquiry_content': 'K10 PRO MAX 키보드 반품하고 싶어요. 개봉했는데 가능한가요?',
            'customer_name': '김고객',
            'order_id': 'TEST999',
            'product_name': '키크론 K10 PRO MAX 무선 기계식 키보드',
            'product_order_option': '쉘 화이트, 바나나축',
            'answered': False
        }
        
        # 1. MongoDB에 저장
        print("1. MongoDB에 저장...")
        mongo_success = await mongo.store_faq(faq_from_spring)
        print(f"   {'✅ 성공' if mongo_success else '❌ 실패'}")
        
        # 2. Weaviate에 임베딩 저장
        print("\n2. Weaviate에 임베딩 저장...")
        weaviate_success = await weaviate.add_faq(
            inquiry_no=faq_from_spring['inquiry_no'],
            brand_channel=faq_from_spring['brand_channel'],
            inquiry_category=faq_from_spring['inquiry_category'],
            title=faq_from_spring['title'],
            inquiry_content=faq_from_spring['inquiry_content'],
            product_name=faq_from_spring.get('product_name'),
            product_codes=['K10', 'PRO MAX']
        )
        print(f"   {'✅ 성공' if weaviate_success else '❌ 실패'}")
        
        # 3. 유사 FAQ 검색 (답변 생성 전 단계)
        print("\n3. 유사 FAQ 검색 (답변 생성용)...")
        similar = await weaviate.search_similar_faqs(
            query_text=faq_from_spring['inquiry_content'],
            brand_channel=faq_from_spring['brand_channel'],
            category=faq_from_spring['inquiry_category'],
            limit=3,
            min_similarity=0.6
        )
        
        print(f"   {len(similar)}개의 유사 FAQ 발견")
        for i, faq in enumerate(similar, 1):
            print(f"   [{i}] 유사도 {faq['similarity']:.2f}: {faq['title']}")
        
        # 4. MongoDB에서 원본 데이터 조회
        print("\n4. MongoDB에서 원본 데이터 조회...")
        original = await mongo.get_faq(999999)
        if original:
            print(f"   ✅ 조회 성공")
            print(f"   제목: {original['title']}")
            print(f"   상태: {original['processing_status']}")
        
        # 정리
        print("\n5. 테스트 데이터 정리...")
        await mongo.db.faqs.delete_one({'inquiry_no': 999999})
        await weaviate.delete_faq(999999)
        print("   ✅ 정리 완료")
        
        await mongo.disconnect()
        await weaviate.disconnect()
        
        print("\n✅ 통합 테스트 완료!\n")
        
    except Exception as e:
        print(f"\n❌ 통합 테스트 실패: {e}\n")
        import traceback
        traceback.print_exc()


async def main():
    """메인 테스트 함수"""
    print("\n" + "🧪"*35)
    print("MongoDB & Weaviate Service 테스트 시작")
    print("🧪"*35)
    
    print("\n📌 연결 정보:")
    print("   - Weaviate: http://localhost:8081")
    print("   - MongoDB: mongodb://localhost:27017")
    print("   - 루트 docker-compose.yml 사용\n")
    
    try:
        # MongoDB 테스트
        await test_mongodb()
        
        # Weaviate 테스트
        await test_weaviate()
        
        # 통합 테스트
        await test_integration()
        
        print("="*70)
        print("🎉 모든 테스트 완료!")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}\n")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())
