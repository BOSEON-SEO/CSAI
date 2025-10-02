# CS AI 에이전트 프로젝트

투비네트웍스 글로벌 FAQ 자동 응답 시스템

**최종 업데이트**: 2025-10-02 15:30, Claude 업데이트

---

## 📋 프로젝트 개요

현재 판매 채널(네이버 스마트스토어 등)의 FAQ를 CS 사원이 수동으로 응대하는 시스템을 AI 기반 자동 응답 시스템으로 전환하는 프로젝트입니다.

### 목표
- CS 사원의 반복 작업 80% 절감
- 평균 응답 시간 2시간 → 30분으로 단축
- 일일 처리 가능량 30건 → 300건으로 증가

### 현재 상태
- ✅ Phase 0: 시스템 아키텍처 설계 완료 (2025-09-30)
- ✅ Phase 1: 인프라 구축 완료 (2025-10-01)
- ✅ Phase 2: 데이터 준비 완료 (2025-10-02)
- 🔄 **Phase 3: AI 코어 개발 진행 중** (2025-10-02 시작, 20% 완료)
  - ✅ MongoDB FAQ 1,581건 임포트 완료
  - ✅ Weaviate 벡터 DB 1,581개 임베딩 완룼
  - ✅ GPU 최적화 (RTX 3050, 10배 빠른 처리)
  - ⏳ QuestionAnalyzer 구현 예정

---

## 🚀 빠른 시작

### 필수 사항

1. **Python 3.11.9** 설치 ([다운로드](https://www.python.org/downloads/release/python-3119/))
2. **Docker Desktop** 설치 ([다운로드](https://www.docker.com/products/docker-desktop/))
3. **Claude API 키** 발급 ([Anthropic Console](https://console.anthropic.com/settings/keys))

### 설치 단계

```bash
# 1. 가상환경 생성 및 활성화
cd C:\workspace\CSAI\backend
python -m venv venv
venv\Scripts\activate

# 2. 패키지 설치
pip install -r requirements.txt
python -m spacy download ko_core_news_lg

# 3. 환경 변수 설정
cd ..
copy .env.example .env
# .env 파일에서 ANTHROPIC_API_KEY 설정

# 4. Docker 서비스 실행
cd docker
docker-compose up -d

# 5. 데이터 임포트
cd ../backend/scripts
python import_data.py --type products --source ../../data/raw/products_keychron.csv --brand KEYCHRON
python import_data.py --type faqs --source ../../data/raw/faq_data_sample.csv

# 6. FastAPI 서버 실행
cd ..
python main.py
```

### 접속 주소

- **API 문서**: http://localhost:8000/docs
- **Mongo Express**: http://localhost:8082
- **Weaviate**: http://localhost:8081/v1/meta

---

## 📊 기술 스택

### AI/ML
- **질문 분석**: Sentence-BERT + spaCy (GPU 가속)
- **벡터 검색**: Weaviate (하이브리드 검색)
- **답변 생성**: Claude Sonnet 4

### 데이터베이스
- **벡터 DB**: Weaviate 1.25
- **NoSQL**: MongoDB 7.0
- **캐시**: Redis 7.2

### 백엔드
- **Framework**: FastAPI 0.115
- **Language**: Python 3.11.9
- **MCP**: Claude MCP Protocol

---

## 📈 개발 일정

| Phase | 작업 내용 | 상태 | 완료일 |
|-------|-----------|------|--------|
| Phase 0 | 요구사항 & 설계 | ✅ | 2025-09-30 |
| Phase 1 | 인프라 구축 | ✅ | 2025-10-01 |
| Phase 2 | 데이터 준비 | ✅ | 2025-10-02 |
| **Phase 3** | **AI 코어 개발** | **🔄** | **진행 중** |
| Phase 4 | CS UI 개발 | 📅 | 예정 |
| Phase 5 | 통합 테스트 | 📅 | 예정 |
| Phase 6 | 프로덕션 배포 | 📅 | 예정 |

**전체 진행률**: 52% (Phase 3 진행 중 20%)

---

## 📚 문서

### 핵심 문서
1. [프로젝트 개요](./docs/01_프로젝트_개요.md)
2. [시스템 아키텍처](./docs/02_시스템_아키텍처.md)
3. [질문 분석](./docs/03_기술스택_질문분석.md)
4. [벡터 DB](./docs/04_기술스택_벡터DB.md) ⬅️ 업데이트됨
5. [NoSQL](./docs/05_기술스택_NoSQL.md) ⬅️ 업데이트됨
6. [개발 계획](./docs/09_개발_계획.md)

### 진행 상황
- [개발현황.md](./개발현황.md) - 실시간 업데이트

---

## 🎯 다음 작업 (Phase 3)

### 다음 작업
1. **벡터 검색 테스트** ⭐ 진행 예정
   ```bash
   # Weaviate 하이브리드 검색 테스트
   # 유사도 점수 threshold 설정
   ```

2. **QuestionAnalyzer 구현**
   - Sentence-BERT + spaCy 통합
   - 질문 분석 로직 작성
   - 복잡도 점수 계산

3. **WeaviateService 구현**
   - 하이브리드 검색 API
   - 필터링 (브랜드, 카테고리)

---

## 💰 비용

| 항목 | 비용 |
|------|------|
| 개발 환경 (로컬) | $0/월 |
| Claude API (900건/월) | $45/월 |
| **총 운영 비용** | **$45/월** |

---

## 🔧 주요 명령어

### Docker
```bash
# 서비스 시작
docker-compose up -d

# 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f
```

### Python
```bash
# 가상환경 활성화
venv\Scripts\activate

# 서버 실행
python main.py

# GPU 확인
python -c "import torch; print(torch.cuda.is_available())"
```

---

## 📞 문의

투비네트웍스 글로벌 개발팀

---

**프로젝트 생성일**: 2025-09-23  
**최종 업데이트**: 2025-10-02 15:30  
**버전**: 0.4.0  
**상태**: Phase 3 진행 중 20% (벡터 DB 구축 완료)
