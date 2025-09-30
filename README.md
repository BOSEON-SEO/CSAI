# CS AI 에이전트 프로젝트

투비네트웍스 글로벌 FAQ 자동 응답 시스템

## 📋 프로젝트 개요

현재 판매 채널(네이버 스마트스토어 등)의 FAQ를 CS 사원이 수동으로 응대하는 시스템을 AI 기반 자동 응답 시스템으로 전환하는 프로젝트입니다.

### 목표
- CS 사원의 반복 작업 80% 절감
- 평균 응답 시간 2시간 → 30분으로 단축
- 일일 처리 가능량 30건 → 300건으로 증가

### 현재 상태
- ✅ Phase 0: 시스템 아키텍처 설계 완료 (2025-09-30)
- ✅ **프로젝트 구조 초기화 완료 (2025-09-30)** ← NEW!
- 📅 Phase 1: 인프라 구축 준비 중 (2025-10-07 시작 예정)

---

## 📁 프로젝트 구조

```
C:\workspace\CSAI\
├─ backend/                    # 백엔드 Python 애플리케이션
│  ├─ main.py                  # ✅ FastAPI 진입점
│  ├─ config.py                # ✅ 설정 관리
│  ├─ requirements.txt         # ✅ Python 패키지 목록
│  │
│  ├─ app/                     # 메인 애플리케이션
│  │  ├─ api/                  # ✅ FastAPI 라우터
│  │  │  ├─ health.py          # 헬스체크 API
│  │  │  ├─ questions.py       # 질문 처리 API
│  │  │  ├─ reviews.py         # CS 검수 API
│  │  │  └─ stats.py           # 통계 API
│  │  │
│  │  ├─ core/                 # ✅ 핵심 비즈니스 로직
│  │  │  ├─ question_analyzer.py    # 질문 분석
│  │  │  ├─ confidence_scorer.py    # 신뢰도 평가
│  │  │  └─ answer_generator.py     # 답변 생성
│  │  │
│  │  ├─ services/             # ✅ 외부 서비스 연동
│  │  │  ├─ weaviate_service.py     # Weaviate 연동
│  │  │  ├─ mongodb_service.py      # MongoDB 연동
│  │  │  └─ claude_service.py       # Claude API 연동
│  │  │
│  │  ├─ models/               # ✅ 데이터 모델 (Pydantic)
│  │  ├─ schemas/              # ✅ API 스키마
│  │  └─ utils/                # ✅ 유틸리티
│  │     ├─ logger.py          # 로깅 설정
│  │     └─ exceptions.py      # 커스텀 예외
│  │
│  ├─ mcp/                     # ✅ MCP 서버 (Phase 3)
│  ├─ scripts/                 # ✅ 데이터 준비 스크립트
│  │  ├─ setup_weaviate.py    # Weaviate 초기화
│  │  ├─ import_products.py   # 제품 데이터 임포트
│  │  ├─ import_faqs.py       # FAQ 데이터 임포트
│  │  └─ create_embeddings.py # 임베딩 생성
│  │
│  └─ tests/                   # ✅ 테스트 코드
│     ├─ unit/                 # 단위 테스트
│     └─ integration/          # 통합 테스트
│
├─ frontend/                   # 프론트엔드 (Phase 4)
│
├─ data/                       # ✅ 데이터 파일
│  ├─ products/                # 제품 스펙 JSON (Phase 2)
│  ├─ faqs/                    # FAQ JSON (Phase 2)
│  └─ raw/                     # 원본 데이터
│
├─ docker/                     # ✅ Docker 설정
│  └─ docker-compose.yml       # 개발 환경 구성
│
├─ logs/                       # 로그 파일 (자동 생성)
│
├─ docs/                       # ✅ 문서
├─ presentation/               # ✅ 발표 자료
├─ .env.example                # ✅ 환경 변수 템플릿
├─ .gitignore                  # ✅ Git 제외 파일
├─ README.md                   # 이 파일
└─ 개발현황.md                  # 진행 상황 (Notion 연동)
```

**✅ = 초기화 완료** (2025-09-30 17:45)

---

## 🚀 빠른 시작

### 1. Python 설치 (필수)
**권장 버전**: **Python 3.11.9**

#### 추천 이유
- ✅ 안정성 (2024년 10월까지 버그 수정)
- ✅ 성능 (3.10 대비 10-60% 향상)
- ✅ 호환성 (모든 라이브러리 지원)
- ✅ 장기 지원 (2027년 10월까지 보안 업데이트)

**다운로드**: [Python 3.11.9](https://www.python.org/downloads/release/python-3119/)

설치 시 **"Add Python to PATH"** 체크 필수!

### 2. Python 가상환경 생성
```bash
# 프로젝트 루트로 이동
cd C:\workspace\CSAI\backend

# 가상환경 생성
python -m venv venv

# 가상환경 활성화 (Windows)
venv\Scripts\activate

# 성공 시 프롬프트에 (venv) 표시됨
```

### 3. 패키지 설치
```bash
# Python 패키지 설치
pip install -r requirements.txt

# spaCy 한국어 모델 다운로드 (약 500MB)
python -m spacy download ko_core_news_lg
```

### 4. 환경 변수 설정
```bash
# 프로젝트 루트로 이동
cd C:\workspace\CSAI

# .env.example을 .env로 복사
copy .env.example .env

# VSCode에서 .env 파일 편집
code .env
```

필수 설정 항목:
```env
# Claude API 키 (필수)
ANTHROPIC_API_KEY=your_api_key_here

# 나머지는 기본값 사용 가능
```

Claude API 키 발급: https://console.anthropic.com/settings/keys

### 5. Docker Desktop 설치 (Phase 1에서 사용)
**다운로드**: [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)

설치 후 Docker Desktop 실행 및 WSL 2 활성화

### 6. Docker 서비스 실행 (Phase 1)
```bash
cd C:\workspace\CSAI\docker

# 백그라운드 실행
docker-compose up -d

# 서비스 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f
```

실행되는 서비스:
- **Weaviate**: http://localhost:8080 (벡터 DB)
- **MongoDB**: http://localhost:27017 (NoSQL DB)
- **Redis**: http://localhost:6379 (캐시)
- **Mongo Express**: http://localhost:8081 (MongoDB GUI)

### 7. FastAPI 서버 실행
```bash
cd C:\workspace\CSAI\backend

# 가상환경 활성화 확인 (venv) 표시

# 서버 실행
python main.py

# 또는
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**접속**:
- API 문서 (Swagger): http://localhost:8000/docs
- API 대체 문서 (ReDoc): http://localhost:8000/redoc
- 기본 엔드포인트: http://localhost:8000/

### 8. GPU 확인 (선택)
```python
# Python 실행
python

# GPU 인식 확인
>>> import torch
>>> torch.cuda.is_available()
True  # GPU 사용 가능
>>> torch.cuda.get_device_name(0)
'NVIDIA GeForce RTX 3050'  # GPU 이름 확인
```

---

## 📚 문서

### 핵심 문서 (✅ 완료)
1. [프로젝트 개요](./docs/01_프로젝트_개요.md) - 현황, 문제점, 기대효과
2. [시스템 아키텍처](./docs/02_시스템_아키텍처.md) - 전체 구조 및 데이터 흐름
3. [기술 스택 - 질문 분석](./docs/03_기술스택_질문분석.md) - Sentence-BERT + spaCy
4. [기술 스택 - 벡터 DB](./docs/04_기술스택_벡터DB.md) - Weaviate
5. [기술 스택 - NoSQL](./docs/05_기술스택_NoSQL.md) - MongoDB
6. [개발 계획](./docs/09_개발_계획.md) - Phase별 일정

### 예정 문서 (Phase 1~)
- 기술 스택 - 답변 생성 (Phase 1)
- 데이터 모델 설계 (Phase 2)
- 신뢰도 평가 시스템 (Phase 3)
- 환경 설정 가이드 (Phase 1)
- 시연 시나리오 (Phase 5)

### 개발 진행 상황
- [개발현황.md](./개발현황.md) - 실시간 진행 상황 (Notion 연동)

---

## 📊 기술 스택

### AI/ML
- **질문 분석**: Sentence-BERT + spaCy (15-20ms, GPU 가속)
- **벡터 검색**: Weaviate (하이브리드 검색, 50ms)
- **답변 생성**: Claude Sonnet 4 (2500ms)

### 데이터베이스
- **벡터 DB**: Weaviate 1.25 (오픈소스, 셀프호스팅)
- **NoSQL**: MongoDB 7.0 (가변 스키마)
- **캐시**: Redis 7.2

### 백엔드
- **Framework**: FastAPI 0.115
- **Language**: Python 3.11.9
- **MCP**: Claude MCP Protocol
- **ASGI Server**: Uvicorn

### 프론트엔드 (Phase 4)
- **Framework**: Next.js 14
- **UI**: shadcn/ui + Tailwind CSS
- **Language**: TypeScript

---

## 📈 개발 일정 (총 9주)

| Phase | 작업 내용 | 기간 | 상태 |
|-------|-----------|------|------|
| Phase 0 | 요구사항 & 설계 | 2025-09-23 ~ 09-30 | ✅ 완료 |
| **현재** | **프로젝트 구조 초기화** | **2025-09-30** | **✅ 완료** |
| Phase 1 | 인프라 구축 | 2025-10-07 ~ 10-13 | 📅 예정 |
| Phase 2 | 데이터 준비 | 2025-10-14 ~ 10-20 | 📅 예정 |
| Phase 3 | AI 코어 개발 | 2025-10-21 ~ 11-03 | 📅 예정 |
| Phase 4 | CS UI 개발 | 2025-11-04 ~ 11-17 | 📅 예정 |
| Phase 5 | 통합 테스트 | 2025-11-18 ~ 11-24 | 📅 예정 |
| Phase 6 | 프로덕션 배포 | 2025-11-25 ~ 12-06 | 📅 예정 |

**목표 완료일**: 2025-12-06  
**전체 진행률**: 12.5% (Phase 0 + 구조 초기화 완료)

---

## 💰 비용 분석 (월 900건 기준)

| 항목 | 비용 | 비고 |
|------|------|------|
| Sentence-BERT + spaCy | $0 | 로컬 GPU (RTX 3050) |
| Weaviate (셀프호스팅) | $0 | Docker 로컬 실행 |
| MongoDB (셀프호스팅) | $0 | Docker 로컬 실행 |
| Redis (셀프호스팅) | $0 | Docker 로컬 실행 |
| Claude API | ~$45 | 월 900건 기준 |
| AWS EC2 (선택) | ~$30 | 프로덕션 배포 시 |
| **총 운영 비용** | **$45~75/월** | **개발 환경은 $0** |

---

## 🔧 개발 환경

### 개발 컴퓨터
- **OS**: Windows 11 Pro 64bit
- **CPU**: AMD Ryzen 5 9600 (6-Core, 3.80 GHz)
- **RAM**: 64GB
- **GPU**: Asus Geforce RTX 3050 (CUDA 지원)
- **IDE**: VSCode + Claude
- **Python**: 3.11.9

### 배포 환경 (Phase 6)
- Linux (CentOS / Ubuntu / macOS 선택)
- Docker + Docker Compose
- Nginx (리버스 프록시)
- SSL 인증서

---

## 📝 개발 규칙

### 코드 작성 규칙
1. **주석**: 모든 함수/클래스에 독스트링 작성
2. **타임스탬프**: 코드 수정 시 `# 2025-09-30 17:45, Claude 작성` 주석 추가
3. **타입 힌트**: Python 타입 힌트 필수 사용
4. **네이밍**: snake_case (변수/함수), PascalCase (클래스)

### 에러 처리
- 커스텀 예외 사용 (`app/utils/exceptions.py`)
- 모든 예외는 로깅 후 적절히 처리

### 로깅
- 중요 이벤트는 `logger` 사용
- 로그 레벨: DEBUG < INFO < WARNING < ERROR < CRITICAL

### Git 커밋
- 커밋 메시지: `[Phase X] 작업 내용`
- 예: `[Phase 1] Docker Compose 설정 완료`

---

## 🎯 다음 단계

### ✅ 완료된 작업 (2025-09-30)
- [x] 프로젝트 구조 설계
- [x] 폴더 구조 생성
- [x] 기본 Python 파일 작성 (스켈레톤)
- [x] requirements.txt 작성
- [x] Docker Compose 설정
- [x] .env.example 작성
- [x] README.md 업데이트

### 📅 즉시 진행 가능 (Phase 1 준비)
1. Python 3.11.9 설치
2. 가상환경 생성 및 패키지 설치
3. Docker Desktop 설치 및 실행
4. GPU 드라이버 최신화
5. Claude API 키 발급

### 📅 Phase 1 (2025-10-07 시작 예정)
1. Docker Compose로 Weaviate, MongoDB, Redis 실행
2. 각 서비스 연결 테스트
3. Health Check API 구현
4. 환경 설정 가이드 문서 작성
5. GPU 설정 확인 스크립트 작성

---

## 🐛 문제 해결

### Python 패키지 설치 오류
```bash
# pip 업그레이드
python -m pip install --upgrade pip

# 패키지 재설치
pip install -r requirements.txt --force-reinstall
```

### Docker 서비스 실행 오류
```bash
# Docker Desktop 실행 확인
# WSL 2 활성화 확인

# 컨테이너 재시작
docker-compose down
docker-compose up -d
```

### GPU 인식 안됨
```bash
# NVIDIA 드라이버 최신 버전 설치
# CUDA Toolkit 12.1 설치
# PyTorch 재설치 (CUDA 버전에 맞춰)
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

---

## 📞 문의

프로젝트 관련 문의: 투비네트웍스 글로벌 개발팀

---

**프로젝트 생성일**: 2025-09-23  
**최종 업데이트**: 2025-09-30 17:45  
**버전**: 0.1.0  
**상태**: Phase 0 완료 + 구조 초기화 완료
