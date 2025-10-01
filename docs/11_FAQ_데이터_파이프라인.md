# FAQ 데이터 파이프라인

**문서 버전**: 1.0  
**작성일**: 2025-10-01  
**작성자**: Claude  
**최종 업데이트**: 2025-10-01

---

## 📋 목차

1. [개요](#개요)
2. [전체 아키텍처](#전체-아키텍처)
3. [데이터 흐름](#데이터-흐름)
4. [각 단계 상세 설명](#각-단계-상세-설명)
5. [데이터베이스 스키마](#데이터베이스-스키마)
6. [스크립트 사용법](#스크립트-사용법)
7. [제약사항 및 해결방안](#제약사항-및-해결방안)
8. [운영 가이드](#운영-가이드)
9. [문제 해결](#문제-해결)

---

## 개요

### 목적

고객이 네이버 스마트스토어에 남긴 문의(FAQ)를 수집하고, CS 팀의 검수를 거쳐, AI 에이전트가 활용할 수 있는 형태로 변환하는 자동화 파이프라인입니다.

### 핵심 가치

| 문제점 | 해결방안 | 효과 |
|--------|----------|------|
| 문의 데이터가 분산 | 네이버 API로 자동 수집 | 데이터 중앙화 |
| CS 팀 수동 작업 부담 | Google Sheets 협업 | 작업 효율 향상 |
| AI가 학습할 데이터 부족 | MongoDB에 구조화된 FAQ 축적 | 답변 품질 개선 |

### 설계 원칙

1. **원본 데이터 보존**: MySQL에 네이버 API 원본을 그대로 저장
2. **인간 중심 워크플로우**: CS 팀이 익숙한 Google Sheets 사용
3. **단계별 추적 가능**: 각 문의가 어느 단계에 있는지 명확히 파악
4. **점진적 자동화**: 초기에는 수동 검수, 추후 완전 자동화로 확장

---

## 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                     네이버 스마트스토어                            │
│                  (고객 문의 발생 지점)                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ ① 폴링 방식 API 호출 (주기적)
                         │    GET /v1/pay-user/inquiries
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Python 백엔드                               │
│                 (NaverCommerceAPIService)                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ ② 원본 데이터 저장
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                        MySQL                                     │
│            (customer_inquiries 테이블)                           │
│     - 원본 데이터 보존                                           │
│     - processing_status 추적                                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ ③ 개발팀: 스크립트 실행
                         │    export_mysql_to_sheet.py
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Google Sheets                                 │
│              (CS 팀 협업 공간)                                   │
│     - 문의 내용 확인                                             │
│     - 답변 작성 (CS_답변 열)                                     │
│     - 검수 의견 기록                                             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ ④ CS팀: 전처리 완료 후
                         │    개발팀에게 알림
                         │
                         │ ⑤ 개발팀: 스크립트 실행
                         │    import_sheet_to_mongodb.py
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                      MongoDB                                     │
│                 (faqs 컬렉션)                                    │
│     - AI 에이전트가 참조하는 FAQ 데이터베이스                     │
│     - 벡터 검색을 위한 임베딩 저장 (추후)                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ ⑥ AI 에이전트가 FAQ 참조
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                   AI 에이전트 (Claude)                           │
│     - 새 문의 발생 시 유사 FAQ 검색                              │
│     - 답변 자동 생성 (검수 대기)                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 데이터 흐름

### 단계별 처리 상태

각 문의는 `processing_status` 필드로 현재 상태를 추적합니다.

| 상태 | 설명 | 다음 단계 |
|------|------|-----------|
| `pending` | MySQL에 저장됨, 아직 처리 안 됨 | Google Sheets 내보내기 |
| `exported_to_sheet` | Google Sheets로 내보냄 | CS 팀 검수 대기 |
| `cs_reviewed` | CS 팀 검수 완료 (수동 상태 변경) | MongoDB 동기화 |
| `synced_to_mongo` | MongoDB에 FAQ로 저장됨 | AI 에이전트 사용 가능 |

### 데이터 변환 과정

```
네이버 API 응답 (JSON)
    ↓
Pydantic 모델 (InquiryContent)
    ↓
SQLAlchemy ORM (CustomerInquiry)
    ↓
MySQL 테이블 (customer_inquiries)
    ↓
Google Sheets (2차원 배열)
    ↓ (CS 팀 검수)
MongoDB 문서 (FAQ 형식)
```

---

## 각 단계 상세 설명

### Step 1: 네이버 API 호출 및 MySQL 저장

**담당**: 개발팀 (자동화 예정)  
**빈도**: 매 10분마다 (cron job)  
**도구**: `NaverCommerceAPIService`

#### 실행 방법

```python
from app.services.naver_api_service import NaverCommerceAPIService
from sqlalchemy.orm import Session

service = NaverCommerceAPIService(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
    db_session=db_session
)

# 최근 7일간의 미답변 문의 수집
result = service.fetch_and_store_inquiries(
    days=7,
    answered=False  # 미답변만
)

print(f"새로 수집: {result['new_created']}개")
print(f"업데이트: {result['updated']}개")
```

#### 주요 로직

1. **인증**: OAuth2 Client Credentials로 액세스 토큰 발급
2. **페이징**: 200개씩 자동으로 모든 페이지 순회
3. **중복 방지**: `inquiry_no`로 기존 레코드 확인 후 upsert
4. **로그 기록**: `inquiry_processing_logs` 테이블에 처리 이력 저장

#### 제약사항

⚠️ **실시간 알림 API 없음**

네이버 Commerce API는 Webhook이나 실시간 알림 기능을 제공하지 않습니다. 따라서 우리는 **폴링(Polling) 방식**을 사용합니다.

**해결방안:**
- 10분마다 API를 호출하여 새 문의 확인
- `inquiryRegistrationDateTime`으로 최근 문의만 필터링
- API Rate Limit 준수 (정확한 제한은 네이버 문서 참조)

---

### Step 2: MySQL에서 Google Sheets로 내보내기

**담당**: 개발팀  
**빈도**: 일 1회 또는 필요 시  
**도구**: `scripts/faq/export_mysql_to_sheet.py`

#### 실행 방법

```bash
cd C:\workspace\CSAI\scripts\faq

python export_mysql_to_sheet.py \
  --db "mysql+pymysql://user:password@localhost/csai" \
  --credentials "C:\workspace\CSAI\config\google_credentials.json" \
  --sheet-id "1aB2cD3eF4gH5iJ6kL7mN8oP9qR0sT" \
  --limit 100
```

#### 파라미터

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--db` | MySQL 연결 문자열 | `mysql+pymysql://user:password@localhost/csai` |
| `--credentials` | Google Service Account JSON 경로 | `C:\workspace\CSAI\config\google_credentials.json` |
| `--sheet-id` | Google Sheets 스프레드시트 ID | (필수) |
| `--limit` | 최대 내보낼 문의 개수 | 100 |

#### Google Sheets 구조

스크립트가 생성하는 시트의 열 구조:

| 열 | 설명 | 편집 가능 |
|----|------|-----------|
| inquiry_no | 문의 번호 (고유 ID) | ❌ 읽기 전용 |
| category | 문의 유형 (상품, 배송 등) | ❌ 읽기 전용 |
| title | 문의 제목 | ❌ 읽기 전용 |
| inquiry_content | 문의 내용 | ❌ 읽기 전용 |
| inquiry_date | 문의 등록일 | ❌ 읽기 전용 |
| product_name | 제품명 | ❌ 읽기 전용 |
| product_option | 제품 옵션 | ❌ 읽기 전용 |
| customer_name | 고객명 | ❌ 읽기 전용 |
| customer_id | 고객 ID | ❌ 읽기 전용 |
| order_id | 주문 ID | ❌ 읽기 전용 |
| 처리상태 | 현재 처리 상태 | ❌ 읽기 전용 |
| **CS_답변** | **CS 팀이 작성할 답변** | ✅ **CS 팀 작성** |
| **AI_답변_검수** | **AI 답변에 대한 검수 의견** | ✅ **CS 팀 작성** |
| **비고** | **추가 메모** | ✅ **CS 팀 작성** |

#### CS 팀 작업 가이드

1. **Google Sheets 열기**: 개발팀이 공유한 스프레드시트 URL 접속
2. **최신 워크시트 확인**: `FAQ_20251001_143000` 형식의 최신 시트 선택
3. **문의 검토**: 각 행의 `inquiry_content` (문의 내용) 확인
4. **답변 작성**: `CS_답변` 열에 고객에게 보낼 답변 작성
   - 친절하고 명확한 톤 유지
   - 제품 스펙 참조 시 정확한 정보 확인
   - 길이 제한 없음 (상세하게 작성 가능)
5. **검수 의견 기록**: `AI_답변_검수` 열에 향후 AI 답변 개선을 위한 노트 기록 (선택)
6. **완료 알림**: 작업 완료 후 개발팀에게 Slack/Email로 알림

---

### Step 3: Google Sheets에서 MongoDB로 임포트

**담당**: 개발팀  
**빈도**: CS 팀 검수 완료 후  
**도구**: `scripts/faq/import_sheet_to_mongodb.py`

#### 실행 방법

```bash
cd C:\workspace\CSAI\scripts\faq

python import_sheet_to_mongodb.py \
  --credentials "C:\workspace\CSAI\config\google_credentials.json" \
  --mongodb-uri "mongodb://localhost:27017" \
  --mongodb-db "csai" \
  --mysql "mysql+pymysql://user:password@localhost/csai" \
  --sheet-id "1aB2cD3eF4gH5iJ6kL7mN8oP9qR0sT" \
  --worksheet "FAQ_20251001_143000"
```

#### 파라미터

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--credentials` | Google Service Account JSON 경로 | `C:\workspace\CSAI\config\google_credentials.json` |
| `--mongodb-uri` | MongoDB 연결 URI | `mongodb://localhost:27017` |
| `--mongodb-db` | MongoDB 데이터베이스 이름 | `csai` |
| `--mysql` | MySQL 연결 문자열 | `mysql+pymysql://user:password@localhost/csai` |
| `--sheet-id` | Google Sheets 스프레드시트 ID | (필수) |
| `--worksheet` | 워크시트 이름 | (필수) |

#### 변환 로직

Google Sheets의 각 행은 다음과 같은 MongoDB 문서로 변환됩니다:

```javascript
{
  faq_id: "FAQ-12345",
  inquiry_no: 12345,
  
  question: {
    text: "K10 PRO 키보드가 블루투스로 연결이 안 돼요",
    title: "블루투스 연결 문제",
    category: "상품",
    keywords: ["블루투스", "연결", "K10 PRO"]
  },
  
  answer: {
    text: "안녕하세요. K10 PRO 블루투스 연결 문제 해결 방법을 안내드립니다...",
    verified: true,
    verified_by: "CS팀",
    verified_at: ISODate("2025-10-01T15:30:00Z")
  },
  
  related_products: ["KB-0068"],
  
  context: {
    customer_name: "홍길동",
    order_id: "2025100112345",
    product_name: "Keychron K10 Pro",
    product_option: "갈축 (RGB)"
  },
  
  additional_info: {
    cs_review_notes: "펌웨어 업데이트 안내 추가",
    notes: "",
    related_faqs: []
  },
  
  stats: {
    view_count: 0,
    helpful_count: 0,
    not_helpful_count: 0
  },
  
  metadata: {
    created_at: ISODate("2025-10-01T15:30:00Z"),
    updated_at: ISODate("2025-10-01T15:30:00Z"),
    status: "active",
    source: "naver_smartstore",
    original_inquiry_date: "2025-09-30T10:15:00Z"
  }
}
```

---

## 데이터베이스 스키마

### MySQL: customer_inquiries

**목적**: 네이버 API 원본 데이터 보존 및 처리 상태 추적

```sql
CREATE TABLE customer_inquiries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    inquiry_no INT UNIQUE NOT NULL COMMENT '네이버 문의 번호',
    
    -- 문의 기본 정보
    category VARCHAR(50),
    title VARCHAR(500) NOT NULL,
    inquiry_content TEXT NOT NULL,
    inquiry_registration_date_time DATETIME NOT NULL,
    
    -- 답변 정보
    answered BOOLEAN NOT NULL DEFAULT FALSE,
    answer_content_id INT,
    answer_content TEXT,
    answer_template_no INT,
    answer_registration_date_time DATETIME,
    
    -- 주문 정보
    order_id VARCHAR(100) NOT NULL,
    product_no VARCHAR(100),
    product_order_id_list TEXT,
    product_name VARCHAR(500),
    product_order_option VARCHAR(500),
    
    -- 고객 정보
    customer_id VARCHAR(100),
    customer_name VARCHAR(100) NOT NULL,
    
    -- 처리 상태
    processing_status VARCHAR(50) NOT NULL DEFAULT 'pending',
    ai_answer_generated BOOLEAN NOT NULL DEFAULT FALSE,
    cs_reviewed BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- 타임스탬프
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_synced_from_naver DATETIME NOT NULL,
    
    INDEX idx_category_answered (category, answered),
    INDEX idx_status_created (processing_status, created_at),
    INDEX idx_inquiry_date (inquiry_registration_date_time)
);
```

### MongoDB: faqs 컬렉션

**목적**: AI 에이전트가 참조하는 검증된 FAQ 데이터베이스

```javascript
db.createCollection("faqs")

// 인덱스 생성
db.faqs.createIndex({ "inquiry_no": 1 }, { unique: true })
db.faqs.createIndex({ "question.category": 1 })
db.faqs.createIndex({ "question.keywords": 1 })
db.faqs.createIndex({ "related_products": 1 })
db.faqs.createIndex({ "metadata.status": 1 })

// 텍스트 검색 인덱스 (향후 벡터 검색으로 대체 예정)
db.faqs.createIndex({
  "question.text": "text",
  "answer.text": "text"
})
```

---

## 스크립트 사용법

### 초기 설정

#### 1. Google Service Account 생성

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. "API 및 서비스" → "라이브러리" → "Google Sheets API" 활성화
4. "사용자 인증 정보" → "서비스 계정 만들기"
5. JSON 키 다운로드 → `C:\workspace\CSAI\config\google_credentials.json`에 저장
6. 서비스 계정 이메일 주소 복사 (예: `csai@project.iam.gserviceaccount.com`)
7. Google Sheets 스프레드시트를 이 이메일과 공유 (편집자 권한)

#### 2. MySQL 데이터베이스 생성

```sql
CREATE DATABASE csai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE csai;

-- 테이블 생성 (위의 스키마 참조)
SOURCE C:\workspace\CSAI\backend\database\schema.sql;
```

#### 3. MongoDB 설정

```bash
# MongoDB 시작 (Docker 사용 시)
docker run -d -p 27017:27017 --name mongodb mongo:latest

# 또는 로컬 MongoDB 시작
mongod --dbpath C:\data\db
```

#### 4. Python 라이브러리 설치

```bash
cd C:\workspace\CSAI\backend
pip install -r requirements.txt
```

---

### 일일 운영 절차

#### 개발팀 작업

**오전 9시: 문의 수집 및 내보내기**

```bash
# 1. 최근 문의 수집 (최근 1일)
python -c "
from app.services.naver_api_service import NaverCommerceAPIService
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('mysql+pymysql://user:password@localhost/csai')
Session = sessionmaker(bind=engine)
db = Session()

service = NaverCommerceAPIService(
    client_id='YOUR_CLIENT_ID',
    client_secret='YOUR_CLIENT_SECRET',
    db_session=db
)

result = service.fetch_and_store_inquiries(days=1, answered=False)
print(f'수집 완료: {result}')
"

# 2. Google Sheets로 내보내기
cd C:\workspace\CSAI\scripts\faq
python export_mysql_to_sheet.py \
  --sheet-id "YOUR_SHEET_ID" \
  --limit 50

# 3. CS 팀에게 Slack/Email 알림
# "새로운 FAQ 50개가 Google Sheets에 업로드되었습니다. 검수 부탁드립니다."
```

**오후 5시: CS 검수 완료 후 MongoDB 동기화**

```bash
cd C:\workspace\CSAI\scripts\faq

python import_sheet_to_mongodb.py \
  --sheet-id "YOUR_SHEET_ID" \
  --worksheet "FAQ_20251001_090000"
```

#### CS 팀 작업

**오전 9시~오후 4시: FAQ 검수**

1. Google Sheets 스프레드시트 열기
2. 최신 워크시트 선택 (예: `FAQ_20251001_090000`)
3. 각 문의 검토 후 `CS_답변` 열에 답변 작성
4. 완료 후 개발팀에게 알림

---

## 제약사항 및 해결방안

### 1. 실시간 알림 미지원

**문제**: 네이버 Commerce API는 Webhook이나 Server-Sent Events를 제공하지 않음

**해결방안**:
- **폴링 방식**: 10분마다 API 호출 (cron job)
- **최적화**: `startSearchDate`를 현재 시간 - 20분으로 설정하여 최근 문의만 조회
- **비용 절감**: `answered=false` 파라미터로 미답변만 필터링

```python
# cron job 예시 (Linux/Mac)
# /etc/crontab 또는 crontab -e

*/10 * * * * cd /workspace/CSAI && python -m app.scripts.fetch_inquiries

# Windows Task Scheduler로 동일 작업 설정 가능
```

### 2. Google Sheets를 중간 단계로 사용하는 이유

**이유**:
1. **CS 팀 친숙도**: Excel/Sheets는 모든 팀원이 익숙한 도구
2. **협업 용이**: 여러 사람이 동시에 작업 가능, 변경 이력 자동 추적
3. **보안**: 데이터베이스 직접 접근보다 안전
4. **유연성**: 임의 열 추가, 필터링, 정렬 자유롭게 가능

**향후 개선 방향**:
- **Phase 4-5**: CS 팀 전용 웹 UI 개발 (Next.js + FastAPI)
- Google Sheets는 백업용으로 유지

### 3. 데이터 일관성 보장

**문제**: MySQL, Google Sheets, MongoDB 간 데이터 불일치 가능성

**해결방안**:
1. **단일 진실의 원천 (Source of Truth)**: MySQL의 `inquiry_no`를 기준으로 삼음
2. **상태 추적**: `processing_status`로 각 문의가 어느 단계인지 명확히 관리
3. **로그 기록**: `inquiry_processing_logs` 테이블에 모든 처리 이력 저장
4. **Upsert 전략**: MongoDB는 `inquiry_no`로 upsert하여 중복 방지

```python
# MongoDB upsert 예시
result = db.faqs.update_one(
    {'inquiry_no': inquiry_no},  # 조건
    {'$set': faq_document},      # 업데이트 내용
    upsert=True                   # 없으면 생성
)
```

---

## 운영 가이드

### 모니터링 포인트

#### 1. MySQL 상태 확인

```sql
-- 처리 대기 중인 문의 수
SELECT COUNT(*) AS pending_count
FROM customer_inquiries
WHERE processing_status = 'pending'
AND answered = FALSE;

-- 단계별 문의 분포
SELECT processing_status, COUNT(*) AS count
FROM customer_inquiries
GROUP BY processing_status;

-- 최근 1시간 내 동기화된 문의
SELECT COUNT(*) AS recently_synced
FROM customer_inquiries
WHERE last_synced_from_naver >= DATE_SUB(NOW(), INTERVAL 1 HOUR);
```

#### 2. MongoDB 상태 확인

```javascript
// FAQ 총 개수
db.faqs.countDocuments({ "metadata.status": "active" })

// 최근 생성된 FAQ (최근 24시간)
db.faqs.countDocuments({
  "metadata.created_at": {
    $gte: new Date(Date.now() - 24*60*60*1000)
  }
})

// 카테고리별 분포
db.faqs.aggregate([
  { $group: {
    _id: "$question.category",
    count: { $sum: 1 }
  }}
])
```

#### 3. 처리 실패 확인

```sql
-- 실패한 처리 로그 조회
SELECT 
    ipl.inquiry_no,
    ipl.stage,
    ipl.message,
    ipl.created_at,
    ci.title
FROM inquiry_processing_logs ipl
JOIN customer_inquiries ci ON ipl.inquiry_no = ci.inquiry_no
WHERE ipl.status = 'failed'
AND ipl.created_at >= DATE_SUB(NOW(), INTERVAL 1 DAY)
ORDER BY ipl.created_at DESC;
```

### 백업 전략

#### MySQL 백업

```bash
# 일일 백업 (cron: 매일 새벽 2시)
mysqldump -u user -p csai customer_inquiries inquiry_processing_logs \
  > backup_$(date +%Y%m%d).sql

# 백업 보관 (최근 30일)
find /backups -name "backup_*.sql" -mtime +30 -delete
```

#### MongoDB 백업

```bash
# 일일 백업
mongodump --db csai --collection faqs --out /backups/mongo_$(date +%Y%m%d)

# 백업 보관 (최근 30일)
find /backups -name "mongo_*" -mtime +30 -exec rm -rf {} \;
```

### 장애 복구

#### Scenario 1: Google Sheets 접근 불가

**증상**: `export_mysql_to_sheet.py` 실행 시 403 Forbidden 오류

**원인**:
1. Service Account 권한 문제
2. API 할당량 초과
3. 스프레드시트 공유 설정 문제

**해결**:
1. 스프레드시트가 Service Account 이메일과 공유되었는지 확인
2. Google Cloud Console에서 API 할당량 확인
3. Service Account JSON 키 재생성

#### Scenario 2: MongoDB 연결 실패

**증상**: `import_sheet_to_mongodb.py` 실행 시 Connection Timeout

**원인**:
1. MongoDB 서버 다운
2. 네트워크 문제
3. 인증 실패

**해결**:
```bash
# MongoDB 상태 확인
systemctl status mongod  # Linux
# 또는
docker ps | grep mongo   # Docker

# MongoDB 재시작
systemctl restart mongod  # Linux
# 또는
docker restart mongodb    # Docker

# 연결 테스트
mongo --host localhost --port 27017
```

#### Scenario 3: 네이버 API 인증 만료

**증상**: `NaverCommerceAPIService` 호출 시 401 Unauthorized

**원인**: Access Token 만료

**해결**:
```python
# 토큰 재발급 (자동으로 처리되지만 수동으로도 가능)
service = NaverCommerceAPIService(client_id, client_secret, db)
service.access_token = None  # 강제 재발급
token = service._get_access_token()
```

---

## 문제 해결

### 자주 묻는 질문 (FAQ)

**Q1. Google Sheets에 데이터가 중복으로 들어가요.**

A: `export_mysql_to_sheet.py`는 매번 새로운 워크시트를 생성합니다. 같은 문의를 중복으로 내보내지 않으려면:

```sql
-- MySQL에서 이미 내보낸 문의 확인
SELECT * FROM customer_inquiries
WHERE processing_status != 'pending';
```

스크립트는 `processing_status='pending'`인 문의만 내보내므로, 이미 내보낸 문의는 자동으로 제외됩니다.

**Q2. MongoDB에 FAQ가 저장되지 않아요.**

A: 다음을 확인하세요:

1. **CS_답변 열이 비어있지 않은지 확인**
   - `convert_to_faq_document()` 함수는 CS 답변이 있는 행만 처리합니다.

2. **inquiry_no가 유효한지 확인**
   - 숫자가 아닌 값이 있으면 건너뜁니다.

3. **로그 확인**
   ```bash
   # 스크립트 실행 시 출력되는 로그 확인
   python import_sheet_to_mongodb.py ... 2>&1 | tee import_log.txt
   ```

**Q3. 네이버 API에서 오래된 문의를 가져오고 싶어요.**

A: 네이버 API는 최대 **365일까지만 조회 가능**합니다.

```python
# 최근 30일 조회
service.fetch_and_store_inquiries(days=30)

# 최근 365일 조회 (최대)
service.fetch_and_store_inquiries(days=365)

# 365일보다 큰 값은 자동으로 365로 제한됩니다
service.fetch_and_store_inquiries(days=500)  # 실제로는 365일만 조회
```

**Q4. 특정 문의의 처리 상태를 추적하고 싶어요.**

A: MySQL 로그 테이블을 조회하세요:

```sql
SELECT 
    stage,
    status,
    message,
    created_at
FROM inquiry_processing_logs
WHERE inquiry_no = 12345
ORDER BY created_at ASC;
```

---

## 다음 단계

### Phase 1 완료 후 (현재)

- ✅ 네이버 API 연동
- ✅ MySQL 원본 데이터 저장
- ✅ Google Sheets 워크플로우
- ✅ MongoDB FAQ 데이터베이스

### Phase 2: 자동화 강화

- [ ] cron job으로 자동 수집 (10분마다)
- [ ] CS 팀 알림 자동화 (Slack Bot)
- [ ] 대시보드 개발 (처리 현황 실시간 모니터링)

### Phase 3: AI 답변 생성

- [ ] Claude를 사용한 초안 답변 자동 생성
- [ ] CS 팀은 검수만 수행 (생성은 AI가)
- [ ] 신뢰도 점수 기반 자동 승인/보류

### Phase 4: 완전 자동화

- [ ] CS 웹 UI 개발 (Google Sheets 대체)
- [ ] 고객에게 직접 답변 전송
- [ ] 지속적 학습 (CS 검수 → 파인튜닝)

---

**문서 끝**

이 문서에 대한 질문이나 개선 제안은 개발팀에게 연락주세요.
