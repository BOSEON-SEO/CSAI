# 05. 기술 스택 - NoSQL 데이터베이스 (MongoDB)

**작성일**: 2025-09-30  
**최종 업데이트**: 2025-10-02 10:05, Claude 업데이트  
**Phase**: Phase 0 설계 완료, Phase 2 데이터 준비 완료

---

## 📋 목차

1. [개요](#개요)
2. [선정 이유](#선정-이유)
3. [MongoDB 특징](#mongodb-특징)
4. [스키마 설계](#스키마-설계)
5. [구현 상태](#구현-상태)
6. [다음 단계](#다음-단계)

---

## 개요

### MongoDB란?

**MongoDB**는 문서 지향(Document-Oriented) NoSQL 데이터베이스로, JSON 형태의 유연한 스키마를 제공합니다.

**공식 사이트**: https://www.mongodb.com/

### 프로젝트에서의 역할

```
Weaviate (벡터 검색)                MongoDB (실제 데이터)
       ↓                                   ↓
FAQ ID: [123, 456, 789]              FAQ 전체 내용
       ↓                                   ↓
유사도 점수만 제공                   제목, 질문, 답변, 메타데이터
       ↓                                   ↓
    ─────────────── 함께 사용 ───────────────
                      ↓
            Claude에게 전달하여 답변 생성
```

**핵심**: MongoDB는 "실제 책장" 역할 → Weaviate가 찾은 책의 내용을 보여줌

---

## 선정 이유

### 후보 NoSQL DB 비교표

| DB | 가변 스키마 | 트랜잭션 | 쿼리 | 집계 | 비용 | 선정 |
|----|------------|---------|------|------|------|------|
| **MongoDB** | ✅ 완벽 | ✅ ACID | ✅ 강력 | ✅ 강력 | 무료 | ✅ |
| PostgreSQL | ❌ 고정 | ✅ | ✅ | ✅ | 무료 | ❌ |
| DynamoDB | ✅ | ⚠️ 제한적 | ⚠️ 제한적 | ❌ | 유료 | ❌ |
| Firestore | ✅ | ✅ | ⚠️ 제한적 | ❌ | 유료 | ❌ |
| Redis | ❌ Key-Value | ❌ | ❌ | ❌ | 무료 | ❌ |

### 1. 가변 스키마 완벽 지원 ✨

**문제 상황**:
```
블루투스 키보드:
  - bluetooth_version: "5.1"
  - bluetooth_runtime: "200시간"
  - battery_capacity: "4000mAh"

유선 키보드:
  - bluetooth_version: 없음!
  - bluetooth_runtime: 없음!
  - battery_capacity: 없음!

→ PostgreSQL(관계형 DB): NULL 값 많이 발생, 비효율적
→ MongoDB: 필요한 필드만 저장, 효율적! ✅
```

**MongoDB 예시**:
```json
// 블루투스 키보드
{
  "product_id": "KB-001",
  "product_name": "K10 PRO MAX",
  "connectivity": {
    "bluetooth": {
      "version": "5.1",
      "runtime": "200시간"
    },
    "usb": {
      "type": "Type-C"
    }
  },
  "battery": {
    "capacity": "4000mAh",
    "charging_time": "4시간"
  }
}

// 유선 키보드 (bluetooth, battery 필드 없음 → OK!)
{
  "product_id": "KB-002",
  "product_name": "C2 PRO",
  "connectivity": {
    "usb": {
      "type": "Type-C"
    }
  }
}
```

**장점**:
- 제품별 다른 구조 OK
- NULL 값 저장 안함 (스토리지 절약)
- 스키마 변경 자유로움

### 2. 트랜잭션 지원 (ACID)

**시나리오**: CS 사원이 AI 답변 승인

```javascript
// MongoDB 트랜잭션
session.startTransaction();

try {
  // 1. FAQ 답변 업데이트
  await db.faqs.updateOne(
    { _id: faq_id },
    { $set: { answer_content: approved_answer, answered: true } }
  );
  
  // 2. 처리 로그 저장
  await db.logs.insertOne({
    faq_id: faq_id,
    action: "approved",
    reviewer: "CS-001",
    timestamp: new Date()
  });
  
  // 3. 통계 업데이트
  await db.stats.updateOne(
    { date: today },
    { $inc: { approved_count: 1 } }
  );
  
  await session.commitTransaction();  // 모두 성공 시 커밋
  
} catch (error) {
  await session.abortTransaction();  // 하나라도 실패 시 롤백
}
```

**장점**:
- 데이터 일관성 보장
- 부분 실패 시 모두 롤백
- 신뢰성 높은 시스템

### 3. 강력한 쿼리 및 집계

#### 복잡한 조건 검색
```javascript
// 예: 미응답 FAQ 중 KEYCHRON 제품, 기술 카테고리, 최근 7일
db.faqs.find({
  brand_channel: "KEYCHRON",
  inquiry_category: "기술지원",
  answered: false,
  created_at: { $gte: new Date(Date.now() - 7*24*60*60*1000) }
}).sort({ created_at: -1 });
```

#### 비즈니스 인사이트 추출 (Aggregation)
```javascript
// 예: 브랜드별 월별 문의 통계
db.faqs.aggregate([
  {
    $match: {
      created_at: {
        $gte: new Date("2025-10-01"),
        $lt: new Date("2025-11-01")
      }
    }
  },
  {
    $group: {
      _id: {
        brand: "$brand_channel",
        category: "$inquiry_category"
      },
      count: { $sum: 1 },
      answered_count: {
        $sum: { $cond: ["$answered", 1, 0] }
      }
    }
  },
  {
    $sort: { count: -1 }
  }
]);

// 결과:
// [
//   { _id: {brand: "KEYCHRON", category: "기술지원"}, count: 45, answered_count: 40 },
//   { _id: {brand: "KEYCHRON", category: "배송"}, count: 30, answered_count: 28 },
//   ...
// ]
```

**활용**:
- CS 팀 성과 분석
- 자주 묻는 질문 파악
- 제품별 문제점 분석
- 비즈니스 의사결정 지원

### 4. Weaviate와의 완벽한 협업

```
┌─────────────────┐         ┌─────────────────┐
│    Weaviate     │         │    MongoDB      │
│  (벡터 검색)     │         │  (데이터 저장)   │
├─────────────────┤         ├─────────────────┤
│ FAQ ID 저장     │◄────────│ FAQ ID 생성     │
│ 임베딩 벡터 저장 │         │ 전체 내용 저장   │
│ 유사도 계산      │────────►│ ID로 조회       │
└─────────────────┘         └─────────────────┘
         ↓                           ↓
    빠른 검색 (50ms)          상세 정보 (10ms)
         ↓                           ↓
              Claude에게 전달 (함께 사용)
```

**역할 분담**:
- **Weaviate**: 의미 검색, 유사 FAQ ID 반환
- **MongoDB**: 실제 FAQ 내용, 고객 정보, 제품 스펙 반환

### 5. 비용 효율성

```
셀프호스팅 (Docker):
  MongoDB 7.0        $0/월
  
클라우드 (Atlas):
  512MB (개발)       $0/월 (Free Tier)
  2GB (프로덕션)     $9/월
  
우리 선택: Docker 셀프호스팅 → $0/월 ✅
```

---

## MongoDB 특징

### 1. BSON 형식

**BSON** = Binary JSON
- JSON보다 빠른 파싱
- 더 많은 데이터 타입 지원

```python
{
  "_id": ObjectId("670123abc..."),        # MongoDB 고유 ID
  "inquiry_no": "313605440",
  "created_at": ISODate("2025-09-08T14:27:04Z"),  # Date 타입
  "answered": True,                       # Boolean
  "metadata": { ... }                     # Nested 객체
}
```

### 2. 인덱싱

**단일 필드 인덱스**:
```javascript
db.faqs.createIndex({ inquiry_no: 1 });  // 오름차순
db.faqs.createIndex({ created_at: -1 }); // 내림차순 (최신순)
```

**복합 인덱스**:
```javascript
// 브랜드 + 카테고리로 자주 검색
db.faqs.createIndex({
  brand_channel: 1,
  inquiry_category: 1,
  created_at: -1
});
```

**텍스트 인덱스** (전문 검색):
```javascript
db.faqs.createIndex({
  title: "text",
  inquiry_content: "text"
});

// 사용
db.faqs.find({ $text: { $search: "블루투스 연결" } });
```

### 3. 샤딩 (Sharding)

**수평 확장 (Scale-Out)**:
```
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Shard 1  │  │ Shard 2  │  │ Shard 3  │
│ 0~30만건  │  │ 30~60만건 │  │ 60~100만건│
└──────────┘  └──────────┘  └──────────┘
       ↑            ↑            ↑
    ───────────────────────────────
              Mongos Router
```

**우리 프로젝트**:
- 초기: 단일 서버로 충분
- 확장 시: 샤딩으로 수평 확장 가능

### 4. 레플리카 셋 (Replica Set)

**고가용성 (High Availability)**:
```
┌─────────┐     ┌─────────┐     ┌─────────┐
│ Primary │────►│Secondary│────►│Secondary│
│ (쓰기)   │     │ (읽기)   │     │ (백업)   │
└─────────┘     └─────────┘     └─────────┘
     ↓
Primary 장애 시
     ↓
Secondary 하나가 자동으로 Primary 승격 ✅
```

---

## 스키마 설계

### 1. products 컬렉션

```javascript
{
  "_id": ObjectId("..."),
  "product_id": "KC-K10-PRO-MAX-001",     // 제품 고유 ID
  "brand_channel": "KEYCHRON",
  "product_name": "K10 PRO MAX 무선 기계식 키보드",
  "product_name_synonyms": "K10PRO, K10 프로맥스",  // 검색 동의어
  
  // 가격 정보
  "price": 159000,
  "discontinued": false,
  "release_date": "2024-03-15",
  
  // 제품 사양 (제품마다 다름!)
  "keyboard_layout": "풀배열",
  "keyboard_type": "기계식",
  "switch_options": ["저소음 적축", "저소음 바나나축"],
  "connection_method": "블루투스 5.1 + 2.4GHz + USB-C",
  "bluetooth_runtime": "200시간",
  "battery_capacity": "4000mAh",
  "hot_swap_socket": true,
  
  // 메타데이터
  "created_at": ISODate("..."),
  "updated_at": ISODate("...")
}
```

**인덱스**:
```javascript
db.products.createIndex({ product_id: 1 }, { unique: true });
db.products.createIndex({ brand_channel: 1, product_name: 1 });
db.products.createIndex({ product_name: "text", product_name_synonyms: "text" });
```

### 2. faqs 컬렉션

```javascript
{
  "_id": ObjectId("..."),
  "faq_id": "FAQ-KEYCHRON-001",           // 고유 ID (Weaviate 매핑용)
  "inquiry_no": "313605440",              // 네이버 문의 번호
  
  // 브랜드 및 분류
  "brand_channel": "KEYCHRON",
  "internal_product_code": "KC-K10-PRO-MAX-001",
  "inquiry_category": "기술지원",         // 상품/배송/반품/교환/환불/기타
  
  // 질문
  "title": "블루투스 연결 안됨",
  "inquiry_content": "K10 PRO MAX 블루투스로 연결이 안되는데 어떻게 해야하나요?",
  "inquiry_registration_date_time": ISODate("2025-09-08T14:27:04Z"),
  
  // 고객 정보
  "customer_id": "wjsr********",
  "customer_name": "이*영",
  "order_id": "2025090465815541",
  
  // 답변
  "answer_content": "안녕하세요 고객님 키크론 입니다...",
  "answered": true,
  "ai_answer_generated": false,           // AI가 생성한 답변 여부
  "cs_reviewed": false,                   // CS 검수 완료 여부
  "processing_status": "pending",         // pending/approved/rejected
  
  // 메타데이터
  "created_at": ISODate("..."),
  "updated_at": ISODate("...")
}
```

**인덱스**:
```javascript
db.faqs.createIndex({ faq_id: 1 }, { unique: true });
db.faqs.createIndex({ inquiry_no: 1 }, { unique: true });
db.faqs.createIndex({
  brand_channel: 1,
  inquiry_category: 1,
  answered: 1,
  created_at: -1
});
db.faqs.createIndex({ title: "text", inquiry_content: "text" });
```

### 3. customers 컬렉션

```javascript
{
  "_id": ObjectId("..."),
  "customer_id": "wjsr********",          // 네이버 고객 ID
  "customer_name": "이*영",
  
  // 주문 이력
  "orders": [
    {
      "order_id": "2025090465815541",
      "product_id": "KC-K10-PRO-MAX-001",
      "order_date": ISODate("2025-09-08"),
      "status": "completed"
    }
  ],
  
  // 문의 이력
  "inquiry_count": 3,
  "last_inquiry_date": ISODate("2025-09-08"),
  
  // 메타데이터
  "created_at": ISODate("..."),
  "updated_at": ISODate("...")
}
```

### 4. logs 컬렉션

```javascript
{
  "_id": ObjectId("..."),
  "faq_id": "FAQ-KEYCHRON-001",
  "action": "ai_answer_generated",        // 또는 cs_reviewed, approved, rejected
  "reviewer": "CS-001",                   // CS 사원 ID
  "timestamp": ISODate("..."),
  
  // AI 답변 정보
  "ai_confidence_score": 0.85,
  "similar_faq_ids": ["FAQ-002", "FAQ-015"],
  "processing_time_ms": 2500,
  
  // 검수 정보
  "review_notes": "답변 내용 일부 수정",
  "original_answer": "...",
  "modified_answer": "..."
}
```

---

## 구현 상태

### ✅ Phase 1: 인프라 구축 완료 (2025-10-01)

```bash
# Docker Compose로 MongoDB 실행
docker-compose up -d mongodb

# 서비스 확인
docker ps | grep mongo
# mongodb    Up    0.0.0.0:27017->27017/tcp
```

**설치된 서비스**:
- MongoDB v7.0
- 포트: 27017
- 관리자 계정: admin / csai_admin_2025
- 데이터베이스: csai_database

### ✅ Phase 2: 스키마 설계 및 데이터 준비 완료 (2025-10-01~02)

**완료된 작업**:
1. ✅ MongoDB 4개 컬렉션 스키마 설계
2. ✅ 제품 데이터 160개 준비 (products_keychron.csv)
3. ✅ FAQ 데이터 100건 수집 (네이버 API)
4. ✅ 통합 임포트 스크립트 작성 (import_data.py)

**데이터 현황**:
```
products: 0건 (임포트 대기 중)
faqs: 0건 (임포트 대기 중)
customers: 0건
logs: 0건
```

### 🔄 Phase 3: 데이터 임포트 (즉시 진행)

**다음 작업**:
```bash
# 1. 제품 데이터 임포트
cd C:\workspace\CSAI\backend\scripts
python import_data.py --type products --source ../../data/raw/products_keychron.csv --brand KEYCHRON

# 2. FAQ 데이터 임포트
python import_data.py --type faqs --source ../../data/raw/faq_data_sample.csv

# 3. MongoDB Express에서 확인
# http://localhost:8082
```

---

## 다음 단계

### Phase 3 작업 계획 (2025-10-02 ~ 11-03)

#### 1주차: 데이터 임포트 및 검증
1. ✅ 스크립트 준비 완료 (import_data.py)
2. 제품 데이터 160개 MongoDB 임포트
3. FAQ 데이터 100건 MongoDB 임포트
4. 인덱스 자동 생성 확인
5. 데이터 무결성 검증

#### 2주차: MongoDBService 구현
```python
# backend/app/services/mongodb_service.py

class MongoDBService:
    async def get_product_by_id(self, product_id: str) -> Dict:
        """제품 정보 조회"""
        product = await self.db.products.find_one({"product_id": product_id})
        return product
    
    async def get_faqs_by_ids(self, faq_ids: List[str]) -> List[Dict]:
        """FAQ 목록 조회 (Weaviate에서 받은 ID들)"""
        faqs = await self.db.faqs.find(
            {"faq_id": {"$in": faq_ids}}
        ).to_list(length=None)
        return faqs
    
    async def get_customer_info(self, customer_id: str) -> Dict:
        """고객 정보 조회"""
        customer = await self.db.customers.find_one({"customer_id": customer_id})
        return customer
    
    async def save_answer_log(self, log_data: Dict):
        """답변 로그 저장"""
        await self.db.logs.insert_one(log_data)
```

#### 3~4주차: 통합 및 최적화
- [ ] FastAPI 엔드포인트 연동
- [ ] 쿼리 성능 최적화
- [ ] 집계 파이프라인 구현 (통계)
- [ ] 백업 및 복구 절차 수립

---

## 참고 자료

### 공식 문서
- MongoDB 공식 사이트: https://www.mongodb.com/
- Python 드라이버 (Motor): https://motor.readthedocs.io/
- 집계 파이프라인: https://www.mongodb.com/docs/manual/aggregation/

### 프로젝트 관련 문서
- [02. 시스템 아키텍처](./02_시스템_아키텍처.md)
- [04. 벡터 DB (Weaviate)](./04_기술스택_벡터DB.md)
- [07. 데이터 모델 설계](./07_데이터_모델_설계.md)
- [개발 계획](./09_개발_계획.md)

---

**문서 작성**: 2025-09-30, Claude  
**최종 업데이트**: 2025-10-02 10:05, Claude  
**다음 업데이트**: Phase 3 데이터 임포트 완료 시
