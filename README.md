# CS AI 에이전트 프로젝트

투비네트웍스 글로벌 FAQ 자동 응답 시스템

**최종 업데이트**: 2025-10-02 17:30, Claude 업데이트

---

## 📋 프로젝트 개요

현재 판매 채널(네이버 스마트스토어 등)의 FAQ를 CS 사원이 수동으로 응대하는 시스템을 AI 기반 자동 응답 시스템으로 전환하는 프로젝트입니다.

### 목표
- CS 사원의 반복 작업 80% 절감
- 평균 응답 시간 2시간 → 30분으로 단축
- 일일 처리 가능량 30건 → 300건으로 증가

### 현재 상태 (2025-10-02)
- ✅ Phase 0: 시스템 아키텍처 설계 (2025-09-30)
- ✅ Phase 1: 인프라 구축 (2025-10-01)
- ✅ Phase 2: 데이터 준비 (2025-10-02)
- ✅ **Phase 3: AI 코어 시스템 (2025-10-02)** 🎉
  - ✅ MongoDB/Weaviate Service 구현
  - ✅ QuestionAnalyzer 구현 (spaCy + Sentence-BERT)
  - ✅ 신뢰도 평가 시스템 구축
  - ✅ 18개 테스트 100% 통과
- 📅 Phase 4: Claude API 통합 (진행 예정)

**전체 진행률**: 44% (Phase 0~3 완료)

---

## 🚀 빠른 시작

### 필수 사항

1. **Python 3.11.9** ([다운로드](https://www.python.org/downloads/release/python-3119/))
2. **Docker Desktop** ([다운로드](https://www.docker.com/products/docker-desktop/))
3. **CUDA 12.6** (GPU 사용 시, RTX 3050 최적화)
4. **Claude API 키** ([Anthropic Console](https://console.anthropic.com/settings/keys))

### 설치 단계

```bash
# 1. 저장소 클론 (또는 폴더 생성)
cd C:\workspace\CSAI

# 2. 가상환경 생성 및 활성화
cd backend
python -m venv venv
venv\Scripts\activate

# 3. 패키지 설치
pip install -r requirements.txt
python -m spacy download ko_core_news_sm

# 4. 환경 변수 설정
cd ..
copy .env.example .env
# .env 파일에서 ANTHROPIC_API_KEY 설정

# 5. Docker 서비스 실행
docker-compose up -d

# 6. 서비스 상태 확인
docker-compose ps
```

### 데이터 임포트 (Phase 3 완료)

```bash
cd backend/scripts

# MongoDB 데이터 임포트
python import_data.py --type products --source ../../data/raw/products_keychron.csv --brand KEYCHRON
python import_data.py --type faqs --source ../../data/raw/faq_data_sample.csv

# Weaviate 벡터 임포트
python import_to_weaviate.py --type faqs --brand KEYCHRON
```

### 테스트 실행

```bash
cd backend/tests

# 전체 테스트
python test_services.py

# QuestionAnalyzer만 테스트
python test_services.py --analyzer-only
```

### 접속 주소

- **MongoDB**: mongodb://localhost:27017
- **Mongo Express**: http://localhost:8082 (admin/csai_2025)
- **Weaviate**: http://localhost:8081/v1/meta
- **Redis**: redis://localhost:6379

---

## 📊 기술 스택

### AI/ML
- **질문 분석**: Sentence-BERT (jhgan/ko-sroberta-multitask) + spaCy (ko_core_news_sm)
- **벡터 검색**: Weaviate 1.25 (하이브리드 검색, 768차원)
- **답변 생성**: Claude Sonnet 4 (예정)

### 데이터베이스
- **벡터 DB**: Weaviate 1.25
- **NoSQL**: MongoDB 7.0
- **캐시**: Redis 7.2

### 백엔드
- **Framework**: FastAPI 0.115 (예정)
- **Language**: Python 3.11.9
- **GPU**: CUDA 12.6 + PyTorch 2.7.1

---

## 📈 개발 일정

| Phase | 작업 내용 | 상태 | 완료일 |
|-------|-----------|------|--------|
| Phase 0 | 요구사항 & 설계 | ✅ | 2025-09-30 |
| Phase 1 | 인프라 구축 | ✅ | 2025-10-01 |
| Phase 2 | 데이터 준비 | ✅ | 2025-10-02 |
| **Phase 3** | **AI 코어 시스템** | **✅** | **2025-10-02** |
| Phase 4 | Claude API 통합 | 📅 | 예정 |
| Phase 5 | FastAPI 엔드포인트 | 📅 | 예정 |
| Phase 6 | CS UI 개발 | 📅 | 예정 |
| Phase 7 | 통합 테스트 | 📅 | 예정 |
| Phase 8 | 프로덕션 배포 | 📅 | 예정 |

**전체 진행률**: 44%

---

## 🎯 Phase 3 완료 내용 (2025-10-02)

### 구현된 기능

#### 1. MongoDB Service (`backend/app/services/mongodb_service.py`)
- FAQ CRUD 작업
- 통계 조회 (총 1,582개 FAQ)
- 비동기 처리 (Motor)

#### 2. Weaviate Service (`backend/app/services/weaviate_service.py`)
- FAQ 임베딩 생성 및 저장
- 유사 FAQ 검색 (벡터 검색)
- 하이브리드 검색 (벡터 + 키워드)
- Weaviate v4 API 완전 호환

#### 3. QuestionAnalyzer (`backend/app/services/question_analyzer.py`)
**7가지 핵심 기능**:
1. 키워드 추출 (spaCy) - 명사, 고유명사, 동사
2. 제품 코드 인식 (정규식) - K10, PRO MAX 등
3. 카테고리 분류 - 배송/반품/교환/상품/환불/기타
4. 복잡도 계산 - 0.0~1.0 점수
5. 임베딩 생성 (Sentence-BERT) - 768차원
6. 유사 FAQ 검색 - Weaviate 하이브리드
7. 신뢰도 평가 - 답변 가능 여부 판단

### 테스트 결과

```
✅ 전체 18개 테스트 통과 (100%)

MongoDB Service: 4/4
Weaviate Service: 5/5
QuestionAnalyzer: 4/4
통합 테스트: 5/5
```

**성능 지표**:
- 카테고리 분류 정확도: **100%** (4/4)
- 제품 코드 인식률: **75%** (3/4)
- 평균 신뢰도: **0.93** (0.82~0.97)
- 처리 속도: **~70ms** (QuestionAnalyzer 20ms + Weaviate 50ms)

### 데이터 현황

```
MongoDB (csai 데이터베이스):
  - products: 160개
  - faqs: 1,582개 (실제 운영 데이터)

Weaviate (FAQs 컬렉션):
  - 벡터: 100개 (테스트 데이터)
  - 차원: 768
  - 검색 타입: 하이브리드 (의미 + 키워드)
```

---

## 📚 문서

### 설계 문서
1. [프로젝트 개요](./docs/01_프로젝트_개요.md)
2. [시스템 아키텍처](./docs/02_시스템_아키텍처.md)
3. [질문 분석 기술](./docs/03_기술스택_질문분석.md)
4. [벡터 DB 기술](./docs/04_기술스택_벡터DB.md)
5. [NoSQL 기술](./docs/05_기술스택_NoSQL.md)
6. [개발 계획](./docs/09_개발_계획.md)

### 구현 문서
7. **[신뢰도 평가 시스템](./docs/08_신뢰도_평가_시스템.md)** ⭐ NEW
   - 복잡도 판단 알고리즘
   - 신뢰도 계산 로직
   - 답변 전가 조건
   - 성능 지표 및 개선 제안

### 진행 상황
- **[개발현황.md](./개발현황.md)** - 실시간 업데이트 (v4.0)
- [devlog/](./devlog/) - 일일 개발 로그

---

## 🧪 테스트

### 전체 테스트 실행
```bash
cd backend/tests
python test_services.py
```

### QuestionAnalyzer 단독 테스트
```bash
python test_services.py --analyzer-only
```

### 테스트 시나리오 (4가지)

| 시나리오 | 카테고리 | 복잡도 | 신뢰도 | 결과 |
|---------|---------|--------|--------|------|
| 배송 문의 | 배송 ✅ | 0.10 (LOW) | 0.97 | ✅ AI 답변 가능 |
| 반품 문의 | 반품 ✅ | 0.10 (LOW) | 0.97 | ✅ AI 답변 가능 |
| 블루투스 문제 | 상품 ✅ | 0.10 (LOW) | 0.97 | ✅ AI 답변 가능 |
| 펌웨어 업데이트 | 상품 ✅ | 0.60 (MED) | 0.82 | ✅ AI 답변 가능 |

---

## 💰 비용

| 항목 | 비용 |
|------|------|
| 개발 환경 (로컬 Docker) | $0/월 |
| MongoDB (셀프 호스팅) | $0/월 |
| Weaviate (셀프 호스팅) | $0/월 |
| Claude API (900건/월) | $45/월 |
| **총 운영 비용** | **$45/월** |

---

## 🔧 주요 명령어

### Docker
```bash
# 전체 서비스 시작
docker-compose up -d

# 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f weaviate
docker-compose logs -f mongodb

# 서비스 재시작
docker-compose restart

# 전체 종료
docker-compose down
```

### Python
```bash
# 가상환경 활성화
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# GPU 확인
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"

# spaCy 모델 확인
python -c "import spacy; spacy.load('ko_core_news_sm')"

# Sentence-BERT 모델 테스트
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('jhgan/ko-sroberta-multitask')"
```

### 데이터 관리
```bash
# MongoDB Express 접속
http://localhost:8082
# Username: admin
# Password: csai_2025

# Weaviate 메타 정보
curl http://localhost:8081/v1/meta

# Redis CLI
docker exec -it csai-redis redis-cli
```

---

## 🎯 다음 단계 (Phase 4)

### Claude API 통합

**목표**: Claude를 사용한 답변 생성 시스템 구축

**주요 작업**:
1. `ClaudeService` 클래스 구현
2. 프롬프트 템플릿 3종 작성
   - 단순 문의용
   - 기술 지원용
   - 반품/교환용
3. MCP 서버 설정 (선택)
4. 에러 핸들링 및 재시도 로직
5. 응답 캐싱 (Redis)
6. 비용 측정 및 최적화

**예상 기간**: 1주

---

## 🤝 기여

투비네트웍스 글로벌 개발팀

**문의**: support@keychron.kr

---

## 📄 라이선스

Copyright © 2025 투비네트웍스 글로벌  
All rights reserved.

---

**프로젝트 생성일**: 2025-09-23  
**최종 업데이트**: 2025-10-02 17:30  
**버전**: 0.4.0  
**상태**: Phase 3 완료 ✅
