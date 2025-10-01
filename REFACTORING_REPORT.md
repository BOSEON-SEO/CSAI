# 네이버 문의 관리 API 리팩토링 완료 보고서

**작성일**: 2025-10-01 22:40  
**작성자**: Claude  
**프로젝트**: 투비네트웍스 글로벌 CS AI 에이전트

---

## 📋 리팩토링 개요

네이버 스마트스토어의 고객 문의를 수집하고 관리하는 Spring Boot API를 리팩토링했습니다. 
기존 코드의 구조는 유지하되, 제안된 개선사항들을 모두 반영하여 즉시 실행 가능한 상태로 만들었습니다.

---

## ✅ 수정된 파일 목록

### 1. DTO 계층 (4개 파일)

#### `CustomerInquiryDTO.java`
- **경로**: `com.tbnws.gtgear.support.tbnws_admin_back.dto.naver.commerce.inquiry.CustomerInquiryDTO`
- **변경사항**:
  - `@Builder` 어노테이션 추가 (객체 생성 편의성 향상)
  - Jackson 어노테이션 추가 (`@JsonProperty`, `@JsonFormat`)
  - 네이버 API JSON 응답과 정확한 매핑 지원
  - 모든 필드에 상세한 JavaDoc 주석 추가

#### `InquiryPatchResult.java`
- **경로**: `com.tbnws.gtgear.support.tbnws_admin_back.dto.naver.commerce.inquiry.InquiryPatchResult`
- **변경사항**:
  - `@Builder` 어노테이션 추가
  - 필드명 개선 (`newInserted`, `updated` 명확화)
  - `success()`, `error()` 정적 팩토리 메서드 추가
  - 처리 시간 정보 추가 (`processingTimeMs`)

#### `InquiryListResponseDTO.java`
- **경로**: `com.tbnws.gtgear.support.tbnws_admin_back.dto.naver.commerce.inquiry.InquiryListResponseDTO`
- **변경사항**:
  - `@Builder` 어노테이션 추가
  - 페이징 메타 정보 완비 (`hasNext`, `hasPrevious`, `totalPages`)
  - 모든 필드에 명확한 설명 추가

#### `CustomerInquiryPatchResultDTO.java`
- **경로**: `com.tbnws.gtgear.support.tbnws_admin_back.dto.naver.commerce.inquiry.CustomerInquiryPatchResultDTO`
- **상태**: `@Deprecated` 마킹
- **이유**: `InquiryPatchResult`로 대체됨

---

### 2. Service 계층 (1개 파일)

#### `NaverInquiryService.java`
- **경로**: `com.tbnws.gtgear.support.tbnws_admin_back.service.naver.NaverInquiryService`
- **주요 개선사항**:

**1. 상수 정의**
```java
private static final String INQUIRY_API_URL = "...";
private static final DateTimeFormatter DATE_FORMAT = ...;
private static final DateTimeFormatter ISO_DATETIME_FORMAT = ...;
```

**2. 메서드 시그니처 명확화**
- `getCustomerInquiries()`: 네이버 API 호출 전담
- `patchInquiries()`: DB 동기화 전담 (@Transactional 적용)
- `getInquiries()`: 페이징 조회 전담 (@Transactional(readOnly = true))

**3. 에러 핸들링 강화**
- try-catch 블록으로 모든 예외 처리
- 상세한 로깅 추가 (DEBUG, INFO, ERROR 레벨 구분)
- NaverApiException을 통한 명확한 에러 전파

**4. 코드 가독성 향상**
- 각 메서드에 상세한 JavaDoc 주석
- 단계별 주석 추가 (// 1. ... // 2. ... 형식)
- 복잡한 로직을 별도 메서드로 분리 (`shouldUpdate()`, `mapStoreToBrandChannel()`)

---

### 3. Controller 계층 (1개 파일)

#### `NaverController.java`
- **경로**: `com.tbnws.gtgear.support.tbnws_admin_back.controller.NaverController`
- **주요 개선사항**:

**1. 엔드포인트 명확화**
```
PATCH /api/naver/{storeName}/inquiries  → 네이버 API에서 문의 수집
GET   /api/naver/{storeName}/inquiries  → DB에서 문의 조회
```

**2. 파라미터 검증 강화**
- `validatePatchParameters()`: PATCH 요청 검증
- `validateGetParameters()`: GET 요청 검증
- 네이버 API 제약사항 준수 (페이지 크기 10~200, 조회 기간 최대 365일)

**3. 상세한 JavaDoc 추가**
- API 사용 예시
- 쿼리 파라미터 설명
- 응답 예시 (JSON 형식)

**4. 에러 응답 개선**
- 4xx: 파라미터 검증 실패 → BAD_REQUEST
- 5xx: 서버 에러 → INTERNAL_SERVER_ERROR
- 모든 경우에 적절한 응답 DTO 반환

---

### 4. MyBatis Mapper (1개 파일)

#### `CustomerInquiryMapper.xml`
- **경로**: `src/main/resources/mapper/naver/CustomerInquiryMapper.xml`
- **주요 개선사항**:

**1. Namespace 수정**
- **변경 전**: \`naver.customerInquiry\` (백틱 포함 - 에러 발생)
- **변경 후**: `naver.customerInquiry`

**2. DTO 경로 업데이트**
```xml
<resultMap ... type="com.tbnws.gtgear.support.tbnws_admin_back.dto.naver.commerce.inquiry.CustomerInquiryDTO">
```

**3. 메서드 ID 명확화**
- `insertInquiry` → `insertCustomerInquiry` (DAO 메서드명과 일치)
- `updateCustomerInquiry` 추가

**4. 주요 쿼리 정리**
- `selectInquiryByNo`: 단일 문의 조회
- `insertCustomerInquiry`: 새 문의 삽입
- `updateCustomerInquiry`: 기존 문의 업데이트
- `selectInquiriesWithPaging`: 페이징된 문의 목록 조회 (필터 지원)
- `countInquiries`: 전체 문의 개수 조회
- `batchInsertInquiries`: 배치 삽입 (성능 최적화용)

---

## 🔧 핵심 개선사항

### 1. 일관된 네이밍 컨벤션
- DTO 파일들: `*DTO.java` 또는 명사형 이름
- Service 메서드: 동사 + 명사 형태 (`getInquiries`, `patchInquiries`)
- Mapper 쿼리 ID: `select*`, `insert*`, `update*`, `delete*` 접두사 사용

### 2. 명확한 책임 분리
- **Controller**: 파라미터 검증, HTTP 응답 처리
- **Service**: 비즈니스 로직, 트랜잭션 관리
- **DAO**: MyBatis 연결
- **Mapper**: SQL 쿼리 정의

### 3. 에러 핸들링 강화
```java
try {
    // 비즈니스 로직
} catch (HttpClientErrorException e) {
    // HTTP 에러 처리
} catch (Exception e) {
    // 기타 예외 처리
}
```

### 4. 로깅 개선
```java
logger.info("[문의 동기화 시작] ...");   // 작업 시작
logger.debug("[네이버 API 호출] ...");     // 상세 정보
logger.warn("[파라미터 검증 실패] ...");   // 경고
logger.error("[문의 동기화 실패] ...");    // 에러
```

### 5. Builder 패턴 활용
```java
InquiryPatchResult result = InquiryPatchResult.builder()
    .success(true)
    .totalFetched(150)
    .newInserted(30)
    .build();
```

---

## 🚀 실행 방법

### 1. 사전 준비

**application.yml 설정 확인**
```yaml
tbnws:
  naver:
    commerce:
      oauth_token_url: https://api.commerce.naver.com/external/v1/oauth2/token
      application:
        keychron:
          id: ${KEYCHRON_CLIENT_ID}
          secret: ${KEYCHRON_CLIENT_SECRET}
        gtgear:
          id: ${GTGEAR_CLIENT_ID}
          secret: ${GTGEAR_CLIENT_SECRET}
        aiper:
          id: ${AIPER_CLIENT_ID}
          secret: ${AIPER_CLIENT_SECRET}
```

**데이터베이스 테이블 확인**
- `customer_inquiries` 테이블이 생성되어 있어야 함
- 모든 컬럼 (brand_channel, processing_status 등) 포함 확인

---

### 2. API 테스트

#### 테스트 1: 문의 수집 (PATCH)
```bash
# 키크론 스토어의 최근 10개 미답변 문의 수집
curl -X PATCH "http://localhost:8080/api/naver/keychron/inquiries?size=10&answered=false" \
  -H "Authorization: Bearer YOUR_SESSION_TOKEN"
```

**예상 응답**:
```json
{
  "success": true,
  "totalFetched": 10,
  "newInserted": 3,
  "updated": 2,
  "errors": 0,
  "startTime": "2025-10-01T22:00:00",
  "endTime": "2025-10-01T22:00:05",
  "processingTimeMs": 5000
}
```

#### 테스트 2: 문의 조회 (GET)
```bash
# 키크론 스토어의 pending 상태 문의 목록 조회
curl -X GET "http://localhost:8080/api/naver/keychron/inquiries?page=0&size=20&processingStatus=pending" \
  -H "Authorization: Bearer YOUR_SESSION_TOKEN"
```

**예상 응답**:
```json
{
  "inquiries": [
    {
      "inquiryNo": 12345,
      "brandChannel": "KEYCHRON",
      "title": "배송 문의",
      "inquiryContent": "언제 도착하나요?",
      ...
    }
  ],
  "totalCount": 45,
  "currentPage": 0,
  "pageSize": 20,
  "totalPages": 3,
  "hasNext": true,
  "hasPrevious": false
}
```

---

## 📊 로그 확인

실행 시 다음과 같은 로그를 확인할 수 있습니다:

```
[문의 동기화 시작] 스토어: keychron, 기간: 2024-10-01 ~ 2025-10-01, 페이지 크기: 10
[네이버 API 호출] URL: https://api.commerce.naver.com/external/v1/pay-user/inquiries?...
[네이버 API 성공] 10개의 문의를 조회했습니다.
[문의 삽입] inquiry_no: 12345
[문의 업데이트] inquiry_no: 12346
[문의 동기화 완료] 총: 10, 신규: 3, 업데이트: 2, 오류: 0
```

---

## 🔍 트러블슈팅

### 문제 1: "Mapper not found"
**원인**: MyBatis가 Mapper XML 파일을 찾지 못함  
**해결**:
1. `application.yml`에서 mapper 경로 확인
   ```yaml
   mybatis:
     mapper-locations: classpath:mapper/**/*.xml
   ```
2. CustomerInquiryMapper.xml 파일 위치 확인
   - 경로: `src/main/resources/mapper/naver/CustomerInquiryMapper.xml`

### 문제 2: "Invalid bearer token"
**원인**: 네이버 OAuth 토큰 발급 실패  
**해결**:
1. NaverCommerceApiService.getNaverOAuthBearToken() 로그 확인
2. application.yml의 client_id와 secret 확인
3. 네이버 커머스 API 인증 정보 재확인

### 문제 3: "JSON parse error"
**원인**: 네이버 API 응답 구조 변경 또는 DTO 매핑 오류  
**해결**:
1. 네이버 API 응답 로그 확인
2. CustomerInquiryDTO의 @JsonProperty 매핑 확인
3. 네이버 API 문서에서 응답 구조 재확인

---

## 📝 다음 단계

이제 기본적인 문의 수집 및 조회 API가 완성되었으므로, 다음 단계로 진행할 수 있습니다:

### Phase 1: 인프라 구축 (다음 작업)
1. Docker Compose로 개발 환경 구성
2. Weaviate, MongoDB, Redis 설정
3. GPU 환경 확인 및 Python 라이브러리 설치

### Phase 2: 데이터 준비
1. 제품 스펙 수집 (10개)
2. FAQ 데이터 작성 (50개)
3. MongoDB 스키마 설계 및 데이터 임포트

### Phase 3: AI 에이전트 코어 개발
1. 질문 분석 모듈 (Sentence-BERT + spaCy)
2. Weaviate 검색 서비스
3. 신뢰도 평가 시스템
4. Claude 통합 (MCP)

---

## ✨ 마무리

리팩토링이 성공적으로 완료되었습니다! 

**개선된 점**:
- ✅ 일관된 코드 스타일
- ✅ 명확한 에러 핸들링
- ✅ 상세한 로깅
- ✅ 완전한 JavaDoc 문서화
- ✅ 즉시 실행 가능한 코드

**테스트 권장사항**:
1. 소량의 데이터로 먼저 테스트 (size=10)
2. 로그를 확인하며 단계별 진행 상황 파악
3. DB에 데이터가 제대로 저장되는지 확인
4. 다양한 필터 조합으로 조회 테스트

문제가 발생하면 로그를 확인하고, 필요시 추가 지원 요청해주세요!

---

**작성자**: Claude  
**날짜**: 2025-10-01 22:40  
**버전**: 1.0
