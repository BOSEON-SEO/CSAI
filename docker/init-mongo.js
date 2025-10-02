// ============================================================
// MongoDB 초기화 스크립트
// 투비네트웍스 글로벌 - CS AI 에이전트 프로젝트
// 
// 2025-10-02 11:00, Claude 작성
//
// 이 스크립트는 MongoDB 컨테이너가 처음 시작될 때 자동 실행됩니다.
// ============================================================

// csai 데이터베이스로 전환
db = db.getSiblingDB('csai');

// 1. csai 데이터베이스 전용 사용자 생성
db.createUser({
  user: 'csai_user',
  pwd: 'csai_password_2025',
  roles: [
    {
      role: 'readWrite',
      db: 'csai'
    }
  ]
});

print('✅ csai_user 생성 완료!');

// 2. 초기 컬렉션 생성 (빈 컬렉션이라도 생성해야 DB가 보임!)
db.createCollection('products');
db.createCollection('faqs');
db.createCollection('customers');
db.createCollection('logs');

print('✅ 초기 컬렉션 생성 완료!');

// 3. 인덱스 미리 생성
// products 컬렉션 인덱스
db.products.createIndex({ "product_id": 1 }, { unique: true });
db.products.createIndex({ "price": 1 });
db.products.createIndex({ "tags": 1 });
db.products.createIndex({ "release_date": -1 });
db.products.createIndex({ "product_name": "text", "tags": "text" });

print('✅ products 인덱스 생성 완료!');

// faqs 컬렉션 인덱스
db.faqs.createIndex({ "inquiry_no": 1 }, { unique: true });
db.faqs.createIndex({ "customer.id": 1 });
db.faqs.createIndex({ "processing_status": 1 });
db.faqs.createIndex({ "created_at": -1 });
db.faqs.createIndex({ "brand_channel": 1 });

print('✅ faqs 인덱스 생성 완료!');

// customers 컬렉션 인덱스
db.customers.createIndex({ "customer_id": 1 }, { unique: true });
db.customers.createIndex({ "email": 1 });

print('✅ customers 인덱스 생성 완료!');

// logs 컬렉션 인덱스 (TTL - 90일 후 자동 삭제)
db.logs.createIndex({ "created_at": 1 }, { expireAfterSeconds: 7776000 });

print('✅ logs 인덱스 생성 완료!');

// 4. 샘플 데이터 추가 (테스트용)
db.products.insertOne({
  "product_id": "SAMPLE-001",
  "product_name": "샘플 키보드 (초기화 테스트)",
  "price": 0,
  "discontinued": false,
  "release_date": new Date(),
  "specifications": {
    "switch_type": "샘플",
    "layout": "테스트"
  },
  "tags": ["sample", "test"],
  "created_at": new Date(),
  "updated_at": new Date()
});

print('✅ 샘플 데이터 추가 완료!');

print('');
print('='.repeat(60));
print('MongoDB 초기화 완료! 🎉');
print('='.repeat(60));
print('데이터베이스: csai');
print('사용자: csai_user');
print('컬렉션: products, faqs, customers, logs');
print('='.repeat(60));
