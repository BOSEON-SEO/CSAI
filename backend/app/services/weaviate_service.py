# backend/app/services/weaviate_service.py
# 2025-10-02 17:45, Claude 작성
# 2025-10-02 15:50, Claude 업데이트 (Weaviate v4 API 수정 - data_type 필드명 변경)

"""
Weaviate 서비스

FAQ 벡터 검색을 위한 Weaviate 서비스입니다.

주요 기능:
1. FAQ 임베딩 생성 및 저장
2. 하이브리드 검색 (의미 검색 + 키워드 검색)
3. 유사 FAQ 찾기
4. 배치 업로드

컬렉션:
- FAQs: FAQ 벡터 데이터
"""

from typing import List, Optional, Dict, Any
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import Property, DataType
from weaviate.classes.query import MetadataQuery
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)


class WeaviateService:
    """
    Weaviate 서비스 클래스
    
    Sentence-BERT를 사용하여 FAQ를 임베딩하고
    Weaviate에 저장/검색하는 서비스입니다.
    
    Example:
        >>> service = WeaviateService("http://localhost:8080")
        >>> await service.connect()
        >>> await service.add_faq(faq_data)
        >>> results = await service.search_similar_faqs("배송 언제 오나요?")
    """
    
    FAQ_COLLECTION = "FAQs"
    
    def __init__(
        self,
        weaviate_url: str,
        model_name: str = 'jhgan/ko-sroberta-multitask',
        api_key: Optional[str] = None
    ):
        """
        Weaviate Service 초기화
        
        Args:
            weaviate_url: Weaviate 서버 URL
            model_name: Sentence-BERT 모델명
            api_key: Weaviate API 키 (클라우드 사용 시)
        """
        self.weaviate_url = weaviate_url
        self.api_key = api_key
        self.client: Optional[weaviate.WeaviateClient] = None
        
        # Sentence-BERT 모델 로드
        logger.info(f"Sentence-BERT 모델 로드 중: {model_name}")
        self.model = SentenceTransformer(model_name)
        logger.info("✅ Sentence-BERT 모델 로드 완료")
    
    async def connect(self):
        """
        Weaviate 연결
        
        연결 후 스키마를 확인하고 없으면 생성합니다.
        """
        try:
            logger.info(f"Weaviate 연결 중: {self.weaviate_url}")
            
            # 연결 설정
            if self.api_key:
                # 클라우드 인증
                self.client = weaviate.connect_to_wcs(
                    cluster_url=self.weaviate_url,
                    auth_credentials=Auth.api_key(self.api_key)
                )
            else:
                # 로컬 연결
                self.client = weaviate.connect_to_local(
                    host=self.weaviate_url.replace('http://', '').replace('https://', '').split(':')[0],
                    port=int(self.weaviate_url.split(':')[-1]) if ':' in self.weaviate_url else 8080
                )
            
            # 연결 확인
            if not self.client.is_ready():
                raise ConnectionError("Weaviate 서버에 연결할 수 없습니다")
            
            # 스키마 확인 및 생성
            await self._ensure_schema()
            
            logger.info("✅ Weaviate 연결 성공!")
            
        except Exception as e:
            logger.error(f"❌ Weaviate 연결 실패: {e}")
            raise
    
    async def disconnect(self):
        """Weaviate 연결 종료"""
        if self.client:
            self.client.close()
            logger.info("Weaviate 연결 종료")
    
    async def _ensure_schema(self):
        """
        스키마 확인 및 생성
        
        FAQs 컬렉션이 없으면 자동으로 생성합니다.
        """
        try:
            # 컬렉션 존재 확인
            if not self.client.collections.exists(self.FAQ_COLLECTION):
                logger.info(f"'{self.FAQ_COLLECTION}' 컬렉션 생성 중...")
                
                # FAQ 컬렉션 생성 (Weaviate v4 API)
                self.client.collections.create(
                    name=self.FAQ_COLLECTION,
                    description="고객 FAQ 벡터 저장소",
                    properties=[
                        Property(
                            name="inquiry_no",
                            data_type=DataType.INT,
                            description="문의 번호"
                        ),
                        Property(
                            name="brand_channel",
                            data_type=DataType.TEXT,
                            description="브랜드 채널"
                        ),
                        Property(
                            name="inquiry_category",
                            data_type=DataType.TEXT,
                            description="문의 카테고리"
                        ),
                        Property(
                            name="title",
                            data_type=DataType.TEXT,
                            description="문의 제목"
                        ),
                        Property(
                            name="inquiry_content",
                            data_type=DataType.TEXT,
                            description="문의 내용"
                        ),
                        Property(
                            name="answer_content",
                            data_type=DataType.TEXT,
                            description="답변 내용"
                        ),
                        Property(
                            name="product_name",
                            data_type=DataType.TEXT,
                            description="제품명"
                        ),
                        Property(
                            name="product_codes",
                            data_type=DataType.TEXT_ARRAY,
                            description="제품 코드 리스트"
                        ),
                    ],
                    # 벡터 설정 (우리가 직접 임베딩 생성)
                    vectorizer_config=None,
                )
                
                logger.info(f"✅ '{self.FAQ_COLLECTION}' 컬렉션 생성 완료")
            else:
                logger.info(f"'{self.FAQ_COLLECTION}' 컬렉션 이미 존재")
                
        except Exception as e:
            logger.error(f"스키마 생성 실패: {e}")
            raise
    
    def _create_embedding(self, text: str) -> List[float]:
        """
        텍스트 임베딩 생성
        
        Sentence-BERT를 사용하여 텍스트를 벡터로 변환합니다.
        
        Args:
            text: 임베딩할 텍스트
            
        Returns:
            임베딩 벡터 (리스트)
        """
        embedding = self.model.encode(text)
        return embedding.tolist()
    
    async def add_faq(
        self,
        inquiry_no: int,
        brand_channel: str,
        inquiry_category: str,
        title: str,
        inquiry_content: str,
        answer_content: Optional[str] = None,
        product_name: Optional[str] = None,
        product_codes: Optional[List[str]] = None
    ) -> bool:
        """
        FAQ 추가
        
        FAQ를 임베딩하여 Weaviate에 저장합니다.
        
        Args:
            inquiry_no: 문의 번호
            brand_channel: 브랜드 채널
            inquiry_category: 카테고리
            title: 제목
            inquiry_content: 문의 내용
            answer_content: 답변 내용 (선택)
            product_name: 제품명 (선택)
            product_codes: 제품 코드 (선택)
            
        Returns:
            성공 여부
        """
        try:
            # 임베딩할 텍스트 생성 (제목 + 내용)
            text_to_embed = f"{title} {inquiry_content}"
            
            # 임베딩 생성
            vector = self._create_embedding(text_to_embed)
            
            # Weaviate에 저장
            collection = self.client.collections.get(self.FAQ_COLLECTION)
            
            # 기존 데이터 확인 (inquiry_no로)
            from weaviate.classes.query import Filter
            
            existing = collection.query.fetch_objects(
                filters=Filter.by_property("inquiry_no").equal(inquiry_no),
                limit=1
            )
            
            if existing.objects:
                # 업데이트
                uuid = existing.objects[0].uuid
                collection.data.update(
                    uuid=uuid,
                    properties={
                        "brand_channel": brand_channel,
                        "inquiry_category": inquiry_category,
                        "title": title,
                        "inquiry_content": inquiry_content,
                        "answer_content": answer_content,
                        "product_name": product_name,
                        "product_codes": product_codes or [],
                    },
                    vector=vector
                )
                logger.info(f"FAQ 업데이트: {inquiry_no}")
            else:
                # 새로 생성
                collection.data.insert(
                    properties={
                        "inquiry_no": inquiry_no,
                        "brand_channel": brand_channel,
                        "inquiry_category": inquiry_category,
                        "title": title,
                        "inquiry_content": inquiry_content,
                        "answer_content": answer_content,
                        "product_name": product_name,
                        "product_codes": product_codes or [],
                    },
                    vector=vector
                )
                logger.info(f"FAQ 추가: {inquiry_no}")
            
            return True
            
        except Exception as e:
            logger.error(f"FAQ 추가 실패 ({inquiry_no}): {e}")
            return False
    
    async def add_faqs_batch(self, faqs: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        FAQ 배치 추가
        
        Args:
            faqs: FAQ 데이터 리스트
            
        Returns:
            {'succeeded': int, 'failed': int}
        """
        succeeded = 0
        failed = 0
        
        for faq in faqs:
            if await self.add_faq(
                inquiry_no=faq['inquiry_no'],
                brand_channel=faq['brand_channel'],
                inquiry_category=faq['inquiry_category'],
                title=faq['title'],
                inquiry_content=faq['inquiry_content'],
                answer_content=faq.get('answer_content'),
                product_name=faq.get('product_name'),
                product_codes=faq.get('product_codes', [])
            ):
                succeeded += 1
            else:
                failed += 1
        
        logger.info(f"배치 추가 완료: 성공 {succeeded}, 실패 {failed}")
        
        return {
            'succeeded': succeeded,
            'failed': failed
        }
    
    async def search_similar_faqs(
        self,
        query_text: str,
        brand_channel: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 5,
        min_similarity: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        유사 FAQ 검색 (벡터 검색)
        
        Args:
            query_text: 검색할 텍스트
            brand_channel: 브랜드 필터
            category: 카테고리 필터
            limit: 최대 개수
            min_similarity: 최소 유사도 (0-1)
            
        Returns:
            유사 FAQ 리스트
        """
        try:
            # 쿼리 임베딩 생성
            query_vector = self._create_embedding(query_text)
            
            # 컬렉션 가져오기
            collection = self.client.collections.get(self.FAQ_COLLECTION)
            
            # 필터 생성
            from weaviate.classes.query import Filter
            
            filters = None
            if brand_channel and category:
                filters = Filter.by_property("brand_channel").equal(brand_channel) & \
                          Filter.by_property("inquiry_category").equal(category)
            elif brand_channel:
                filters = Filter.by_property("brand_channel").equal(brand_channel)
            elif category:
                filters = Filter.by_property("inquiry_category").equal(category)
            
            # 벡터 검색
            response = collection.query.near_vector(
                near_vector=query_vector,
                limit=limit,
                return_metadata=MetadataQuery(distance=True),
                filters=filters
            )
            
            # 결과 변환
            results = []
            for obj in response.objects:
                # 거리를 유사도로 변환 (코사인 거리 → 유사도)
                # distance는 0에 가까울수록 유사 (0 = 완전 동일)
                similarity = 1 - obj.metadata.distance
                
                if similarity >= min_similarity:
                    results.append({
                        'inquiry_no': obj.properties['inquiry_no'],
                        'title': obj.properties['title'],
                        'inquiry_content': obj.properties['inquiry_content'],
                        'answer_content': obj.properties.get('answer_content'),
                        'brand_channel': obj.properties['brand_channel'],
                        'inquiry_category': obj.properties['inquiry_category'],
                        'product_name': obj.properties.get('product_name'),
                        'similarity': similarity
                    })
            
            logger.info(f"유사 FAQ 검색: {len(results)}개 발견 (최소 유사도: {min_similarity})")
            
            return results
            
        except Exception as e:
            logger.error(f"유사 FAQ 검색 실패: {e}")
            return []
    
    async def hybrid_search(
        self,
        query_text: str,
        keywords: List[str],
        brand_channel: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        하이브리드 검색 (벡터 + 키워드)
        
        의미 검색과 키워드 검색을 결합합니다.
        
        Args:
            query_text: 검색할 텍스트
            keywords: 키워드 리스트
            brand_channel: 브랜드 필터
            category: 카테고리 필터
            limit: 최대 개수
            
        Returns:
            검색 결과 리스트
        """
        try:
            # 쿼리 임베딩 생성
            query_vector = self._create_embedding(query_text)
            
            # 컬렉션 가져오기
            collection = self.client.collections.get(self.FAQ_COLLECTION)
            
            # 필터 생성
            from weaviate.classes.query import Filter
            
            filters = None
            if brand_channel and category:
                filters = Filter.by_property("brand_channel").equal(brand_channel) & \
                          Filter.by_property("inquiry_category").equal(category)
            elif brand_channel:
                filters = Filter.by_property("brand_channel").equal(brand_channel)
            elif category:
                filters = Filter.by_property("inquiry_category").equal(category)
            
            # 하이브리드 검색
            # alpha=0.5: 벡터 검색과 키워드 검색을 50:50으로
            response = collection.query.hybrid(
                query=query_text,
                vector=query_vector,
                alpha=0.5,  # 0=순수 키워드, 1=순수 벡터, 0.5=하이브리드
                limit=limit,
                return_metadata=MetadataQuery(score=True),
                filters=filters
            )
            
            # 결과 변환
            results = []
            for obj in response.objects:
                results.append({
                    'inquiry_no': obj.properties['inquiry_no'],
                    'title': obj.properties['title'],
                    'inquiry_content': obj.properties['inquiry_content'],
                    'answer_content': obj.properties.get('answer_content'),
                    'brand_channel': obj.properties['brand_channel'],
                    'inquiry_category': obj.properties['inquiry_category'],
                    'product_name': obj.properties.get('product_name'),
                    'score': obj.metadata.score  # 하이브리드 점수
                })
            
            logger.info(f"하이브리드 검색: {len(results)}개 발견")
            
            return results
            
        except Exception as e:
            logger.error(f"하이브리드 검색 실패: {e}")
            return []
    
    async def delete_faq(self, inquiry_no: int) -> bool:
        """
        FAQ 삭제
        
        Args:
            inquiry_no: 문의 번호
            
        Returns:
            성공 여부
        """
        try:
            collection = self.client.collections.get(self.FAQ_COLLECTION)
            
            # inquiry_no로 찾기
            from weaviate.classes.query import Filter
            
            result = collection.query.fetch_objects(
                filters=Filter.by_property("inquiry_no").equal(inquiry_no),
                limit=1
            )
            
            if result.objects:
                uuid = result.objects[0].uuid
                collection.data.delete_by_id(uuid)
                logger.info(f"FAQ 삭제: {inquiry_no}")
                return True
            else:
                logger.warning(f"FAQ를 찾을 수 없음: {inquiry_no}")
                return False
                
        except Exception as e:
            logger.error(f"FAQ 삭제 실패 ({inquiry_no}): {e}")
            return False
    
    async def get_total_count(self) -> int:
        """
        저장된 FAQ 총 개수 조회
        
        Returns:
            FAQ 개수
        """
        try:
            collection = self.client.collections.get(self.FAQ_COLLECTION)
            response = collection.aggregate.over_all(total_count=True)
            return response.total_count
        except Exception as e:
            logger.error(f"총 개수 조회 실패: {e}")
            return 0


# 싱글톤 인스턴스
_weaviate_service: Optional[WeaviateService] = None


def get_weaviate_service() -> WeaviateService:
    """
    Weaviate Service 싱글톤 인스턴스 반환
    
    FastAPI의 Depends에서 사용합니다.
    """
    global _weaviate_service
    if _weaviate_service is None:
        raise RuntimeError("Weaviate Service가 초기화되지 않았습니다")
    return _weaviate_service


def init_weaviate_service(
    weaviate_url: str,
    model_name: str = 'jhgan/ko-sroberta-multitask',
    api_key: Optional[str] = None
):
    """
    Weaviate Service 초기화
    
    main.py에서 앱 시작 시 호출합니다.
    """
    global _weaviate_service
    _weaviate_service = WeaviateService(weaviate_url, model_name, api_key)
    return _weaviate_service
