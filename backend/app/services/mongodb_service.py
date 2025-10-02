# backend/app/services/mongodb_service.py
# 2025-10-02 17:30, Claude 작성

"""
MongoDB 서비스

FAQ와 제품 정보를 MongoDB에 저장하고 조회하는 서비스입니다.

주요 기능:
1. FAQ CRUD
2. 제품 정보 CRUD
3. 검색 및 필터링
4. 통계 조회

컬렉션 구조:
- faqs: FAQ 데이터
- products: 제품 정보
- logs: 처리 로그
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, IndexModel
from pymongo.errors import DuplicateKeyError
import logging

logger = logging.getLogger(__name__)


class MongoDBService:
    """
    MongoDB 비동기 서비스 클래스
    
    motor를 사용한 비동기 MongoDB 연결을 관리합니다.
    
    Example:
        >>> service = MongoDBService("mongodb://localhost:27017", "csai_db")
        >>> await service.connect()
        >>> await service.store_faq(faq_data)
    """
    
    def __init__(self, connection_string: str, database_name: str):
        """
        MongoDB Service 초기화
        
        Args:
            connection_string: MongoDB 연결 문자열
            database_name: 데이터베이스 이름
        """
        self.connection_string = connection_string
        self.database_name = database_name
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
    
    async def connect(self):
        """
        MongoDB 연결
        
        연결 후 필요한 인덱스를 자동으로 생성합니다.
        """
        try:
            logger.info(f"MongoDB 연결 중: {self.database_name}")
            
            self.client = AsyncIOMotorClient(self.connection_string)
            self.db = self.client[self.database_name]
            
            # 연결 테스트
            await self.client.admin.command('ping')
            
            # 인덱스 생성
            await self._create_indexes()
            
            logger.info("✅ MongoDB 연결 성공!")
            
        except Exception as e:
            logger.error(f"❌ MongoDB 연결 실패: {e}")
            raise
    
    async def disconnect(self):
        """MongoDB 연결 종료"""
        if self.client:
            self.client.close()
            logger.info("MongoDB 연결 종료")
    
    async def _create_indexes(self):
        """
        필요한 인덱스 생성
        
        성능 최적화를 위한 인덱스를 생성합니다.
        """
        # FAQ 컬렉션 인덱스
        faq_indexes = [
            IndexModel([("inquiry_no", ASCENDING)], unique=True),
            IndexModel([("brand_channel", ASCENDING)]),
            IndexModel([("inquiry_category", ASCENDING)]),
            IndexModel([("answered", ASCENDING)]),
            IndexModel([("processing_status", ASCENDING)]),
            IndexModel([("inquiry_registration_date_time", DESCENDING)]),
            IndexModel([
                ("brand_channel", ASCENDING),
                ("inquiry_category", ASCENDING),
                ("answered", ASCENDING)
            ]),
        ]
        
        await self.db.faqs.create_indexes(faq_indexes)
        
        # 제품 컬렉션 인덱스
        product_indexes = [
            IndexModel([("product_id", ASCENDING)], unique=True),
            IndexModel([("brand_channel", ASCENDING)]),
            IndexModel([("product_name", ASCENDING)]),
            IndexModel([("tags", ASCENDING)]),
        ]
        
        await self.db.products.create_indexes(product_indexes)
        
        logger.info("인덱스 생성 완료") 
    
    # ==================== FAQ 관련 메서드 ====================
    
    async def store_faq(self, faq_data: Dict[str, Any]) -> bool:
        """
        FAQ 저장 (upsert)
        
        inquiry_no가 같으면 업데이트, 없으면 새로 생성합니다.
        
        Args:
            faq_data: FAQ 데이터 딕셔너리
            
        Returns:
            성공 여부
        """
        try:
            # 타임스탬프 추가
            now = datetime.now()
            faq_data['updated_at'] = now
            
            if 'created_at' not in faq_data:
                faq_data['created_at'] = now
            
            # processing_status 기본값
            if 'processing_status' not in faq_data:
                faq_data['processing_status'] = 'pending'
            
            # upsert (있으면 업데이트, 없으면 생성)
            result = await self.db.faqs.update_one(
                {'inquiry_no': faq_data['inquiry_no']},
                {'$set': faq_data},
                upsert=True
            )
            
            if result.upserted_id:
                logger.info(f"새 FAQ 저장: {faq_data['inquiry_no']}")
            else:
                logger.info(f"FAQ 업데이트: {faq_data['inquiry_no']}")
            
            return True
            
        except Exception as e:
            logger.error(f"FAQ 저장 실패 ({faq_data.get('inquiry_no')}): {e}")
            return False
    
    async def store_faqs_batch(self, faqs: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        FAQ 배치 저장
        
        Args:
            faqs: FAQ 데이터 리스트
            
        Returns:
            {'succeeded': int, 'failed': int}
        """
        succeeded = 0
        failed = 0
        
        for faq in faqs:
            if await self.store_faq(faq):
                succeeded += 1
            else:
                failed += 1
        
        logger.info(f"배치 저장 완료: 성공 {succeeded}, 실패 {failed}")
        
        return {
            'succeeded': succeeded,
            'failed': failed
        }
    
    async def get_faq(self, inquiry_no: int) -> Optional[Dict[str, Any]]:
        """
        FAQ 조회 (inquiry_no로)
        
        Args:
            inquiry_no: 문의 번호
            
        Returns:
            FAQ 데이터 또는 None
        """
        return await self.db.faqs.find_one({'inquiry_no': inquiry_no})
    
    async def get_pending_faqs(
        self,
        brand_channel: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        처리 대기 중인 FAQ 조회
        
        Args:
            brand_channel: 브랜드 필터 (선택)
            limit: 최대 개수
            
        Returns:
            FAQ 리스트
        """
        query = {
            'processing_status': 'pending',
            'answered': False
        }
        
        if brand_channel:
            query['brand_channel'] = brand_channel
        
        cursor = self.db.faqs.find(query).sort(
            'inquiry_registration_date_time', ASCENDING
        ).limit(limit)
        
        return await cursor.to_list(length=limit)
    
    async def search_faqs(
        self,
        category: Optional[str] = None,
        brand_channel: Optional[str] = None,
        answered: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        FAQ 검색
        
        Args:
            category: 카테고리 필터
            brand_channel: 브랜드 필터
            answered: 답변 여부 필터
            skip: 건너뛸 개수
            limit: 최대 개수
            
        Returns:
            FAQ 리스트
        """
        query = {}
        
        if category:
            query['inquiry_category'] = category
        
        if brand_channel:
            query['brand_channel'] = brand_channel
        
        if answered is not None:
            query['answered'] = answered
        
        cursor = self.db.faqs.find(query).sort(
            'inquiry_registration_date_time', DESCENDING
        ).skip(skip).limit(limit)
        
        return await cursor.to_list(length=limit)
    
    async def update_faq_status(
        self,
        inquiry_no: int,
        status: str,
        **kwargs
    ) -> bool:
        """
        FAQ 처리 상태 업데이트
        
        Args:
            inquiry_no: 문의 번호
            status: 새로운 상태
            **kwargs: 추가 업데이트 필드
            
        Returns:
            성공 여부
        """
        try:
            update_data = {
                'processing_status': status,
                'updated_at': datetime.now()
            }
            update_data.update(kwargs)
            
            result = await self.db.faqs.update_one(
                {'inquiry_no': inquiry_no},
                {'$set': update_data}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"FAQ 상태 업데이트 실패 ({inquiry_no}): {e}")
            return False
    
    # ==================== 제품 관련 메서드 ====================
    
    async def store_product(self, product_data: Dict[str, Any]) -> bool:
        """
        제품 정보 저장 (upsert)
        
        Args:
            product_data: 제품 데이터 딕셔너리
            
        Returns:
            성공 여부
        """
        try:
            now = datetime.now()
            product_data['updated_at'] = now
            
            if 'created_at' not in product_data:
                product_data['created_at'] = now
            
            result = await self.db.products.update_one(
                {'product_id': product_data['product_id']},
                {'$set': product_data},
                upsert=True
            )
            
            if result.upserted_id:
                logger.info(f"새 제품 저장: {product_data['product_id']}")
            else:
                logger.info(f"제품 업데이트: {product_data['product_id']}")
            
            return True
            
        except Exception as e:
            logger.error(f"제품 저장 실패 ({product_data.get('product_id')}): {e}")
            return False
    
    async def store_products_batch(
        self,
        products: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        제품 배치 저장
        
        Args:
            products: 제품 데이터 리스트
            
        Returns:
            {'succeeded': int, 'failed': int}
        """
        succeeded = 0
        failed = 0
        
        for product in products:
            if await self.store_product(product):
                succeeded += 1
            else:
                failed += 1
        
        logger.info(f"제품 배치 저장 완료: 성공 {succeeded}, 실패 {failed}")
        
        return {
            'succeeded': succeeded,
            'failed': failed
        }
    
    async def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        제품 조회 (product_id로)
        
        Args:
            product_id: 제품 ID
            
        Returns:
            제품 데이터 또는 None
        """
        return await self.db.products.find_one({'product_id': product_id})
    
    async def get_product_by_code(
        self,
        product_codes: List[str],
        brand_channel: str
    ) -> Optional[Dict[str, Any]]:
        """
        제품 코드로 제품 검색
        
        제품명이나 product_id에서 코드를 매칭합니다.
        
        Args:
            product_codes: 제품 코드 리스트 (예: ["K10", "PRO MAX"])
            brand_channel: 브랜드 채널
            
        Returns:
            제품 데이터 또는 None
        """
        # 코드를 모두 포함하는 정규식 생성
        # 예: ["K10", "PRO MAX"] → "K10.*PRO MAX"
        pattern = '.*'.join(product_codes)
        
        return await self.db.products.find_one({
            'brand_channel': brand_channel,
            'product_name': {'$regex': pattern, '$options': 'i'}
        })
    
    async def search_products(
        self,
        brand_channel: Optional[str] = None,
        tags: Optional[List[str]] = None,
        discontinued: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        제품 검색
        
        Args:
            brand_channel: 브랜드 필터
            tags: 태그 필터
            discontinued: 단종 여부 필터
            skip: 건너뛸 개수
            limit: 최대 개수
            
        Returns:
            제품 리스트
        """
        query = {}
        
        if brand_channel:
            query['brand_channel'] = brand_channel
        
        if tags:
            query['tags'] = {'$in': tags}
        
        if discontinued is not None:
            query['discontinued'] = discontinued
        
        cursor = self.db.products.find(query).skip(skip).limit(limit)
        
        return await cursor.to_list(length=limit)
    
    # ==================== 로그 관련 메서드 ====================
    
    async def log_processing(
        self,
        inquiry_no: int,
        stage: str,
        status: str,
        message: str = "",
        **metadata
    ):
        """
        처리 로그 기록
        
        Args:
            inquiry_no: 문의 번호
            stage: 처리 단계 (analyze, generate, review 등)
            status: 상태 (success, failed, pending)
            message: 로그 메시지
            **metadata: 추가 메타데이터
        """
        log_data = {
            'inquiry_no': inquiry_no,
            'stage': stage,
            'status': status,
            'message': message,
            'metadata': metadata,
            'timestamp': datetime.now()
        }
        
        await self.db.logs.insert_one(log_data)
    
    async def get_logs(
        self,
        inquiry_no: Optional[int] = None,
        stage: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        로그 조회
        
        Args:
            inquiry_no: 문의 번호 필터
            stage: 단계 필터
            limit: 최대 개수
            
        Returns:
            로그 리스트
        """
        query = {}
        
        if inquiry_no:
            query['inquiry_no'] = inquiry_no
        
        if stage:
            query['stage'] = stage
        
        cursor = self.db.logs.find(query).sort(
            'timestamp', DESCENDING
        ).limit(limit)
        
        return await cursor.to_list(length=limit)
    
    # ==================== 통계 관련 메서드 ====================
    
    async def get_faq_stats(
        self,
        brand_channel: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        FAQ 통계 조회
        
        Args:
            brand_channel: 브랜드 필터
            
        Returns:
            통계 데이터
        """
        query = {}
        if brand_channel:
            query['brand_channel'] = brand_channel
        
        total = await self.db.faqs.count_documents(query)
        answered = await self.db.faqs.count_documents({**query, 'answered': True})
        pending = await self.db.faqs.count_documents({
            **query,
            'processing_status': 'pending'
        })
        
        # 카테고리별 통계
        pipeline = [
            {'$match': query},
            {'$group': {
                '_id': '$inquiry_category',
                'count': {'$sum': 1}
            }}
        ]
        
        category_stats = {}
        async for doc in self.db.faqs.aggregate(pipeline):
            category_stats[doc['_id']] = doc['count']
        
        return {
            'total': total,
            'answered': answered,
            'unanswered': total - answered,
            'pending': pending,
            'by_category': category_stats
        }


# 싱글톤 인스턴스
_mongodb_service: Optional[MongoDBService] = None


def get_mongodb_service() -> MongoDBService:
    """
    MongoDB Service 싱글톤 인스턴스 반환
    
    FastAPI의 Depends에서 사용합니다.
    """
    global _mongodb_service
    if _mongodb_service is None:
        raise RuntimeError("MongoDB Service가 초기화되지 않았습니다")
    return _mongodb_service


def init_mongodb_service(connection_string: str, database_name: str):
    """
    MongoDB Service 초기화
    
    main.py에서 앱 시작 시 호출합니다.
    """
    global _mongodb_service
    _mongodb_service = MongoDBService(connection_string, database_name)
    return _mongodb_service
