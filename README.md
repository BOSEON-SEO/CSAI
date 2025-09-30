# CS AI 에이전트 프로젝트

투비네트웍스 글로벌 FAQ 자동 응답 시스템 구축

## 📋 프로젝트 개요

현재 판매 채널(네이버 스마트스토어 등)의 FAQ를 CS 사원이 수동으로 응대하는 시스템을 AI 기반 자동 응답 시스템으로 전환하는 프로젝트입니다.

### 목표
- CS 사원의 반복 작업 80% 절감
- 평균 응답 시간 2시간 → 30분으로 단축
- 일일 처리 가능량 100건 → 500건으로 증가

### 현재 상태
- ✅ 시스템 아키텍처 설계 완료
- ✅ 질문 분석 모델 선정 완료 (Sentence-BERT + spaCy)
- ✅ 벡터 DB 선정 완료 (Weaviate)
- ✅ NoSQL DB 선정 완료 (MongoDB)
- 🔄 답변 생성 모델 검토 중 (Claude)
- 📅 개발 Phase 1 준비 중

---

## 📚 문서 구조

### 📘 핵심 문서
1. [프로젝트 개요](./docs/01_프로젝트_개요.md) - 현황, 문제점, 기대효과
2. [시스템 아키텍처](./docs/02_시스템_아키텍처.md) - 전체 구조 및 데이터 흐름
3. [기술 스택 - 질문 분석](./docs/03_기술스택_질문분석.md) - Sentence-BERT + spaCy
4. [기술 스택 - 벡터 DB](./docs/04_기술스택_벡터DB.md) - Weaviate 선정 근거
5. [기술 스택 - NoSQL](./docs/05_기술스택_NoSQL.md) - MongoDB 선정 근거
6. [기술 스택 - 답변 생성](./docs/06_기술스택_답변생성.md) - Claude (작성 예정)
7. [데이터 모델 설계](./docs/07_데이터_모델_설계.md) - 스키마 및 인덱스
8. [신뢰도 평가 시스템](./docs/08_신뢰도_평가_시스템.md) - 복잡도 판단 로직
9. [개발 계획](./docs/09_개발_계획.md) - Phase별 마일스톤
10. [환경 설정 가이드](./docs/10_환경_설정_가이드.md) - 개발 및 배포 환경

### 🎤 발표 자료
- [기술팀 공유용 (15분)](./presentation/기술팀_공유_15분.md)
- [시연 시나리오](./presentation/시연_시나리오.md)

---

## 🚀 빠른 시작

### 개발 환경 구성
```bash
# Python 가상환경
python -m venv venv
venv\Scripts\activate

# 필수 라이브러리
pip install -r requirements.txt

# spaCy 한국어 모델
python -m spacy download ko_core_news_lg
```

### 로컬 실행
```bash
# Docker Compose로 전체 스택 실행
docker-compose up -d

# FastAPI 서버 실행
cd backend
uvicorn main:app --reload
```

상세한 내용은 [환경 설정 가이드](./docs/10_환경_설정_가이드.md)를 참조하세요.

---

## 📊 기술 스택

### AI/ML
- **질문 분석**: Sentence-BERT (paraphrase-multilingual-MiniLM-L12-v2) + spaCy
- **벡터 검색**: Weaviate (하이브리드 검색)
- **답변 생성**: Claude Sonnet 4 (Anthropic)

### 데이터베이스
- **벡터 DB**: Weaviate (오픈소스, 셀프호스팅)
- **NoSQL**: MongoDB (가변 스키마)

### 백엔드
- **API 서버**: FastAPI (Python)
- **MCP 서버**: Claude MCP Protocol

### 프론트엔드
- **UI**: Next.js 15 + TypeScript
- **컴포넌트**: shadcn/ui
- **상태 관리**: Zustand

---

## 📈 개발 진행 상황

| Phase | 작업 내용 | 상태 | 예상 기간 |
|-------|-----------|------|-----------|
| Phase 0 | 요구사항 분석 & 아키텍처 설계 | ✅ 완료 | 1주 |
| Phase 1 | 인프라 구축 | 📅 예정 | 1주 |
| Phase 2 | 데이터 준비 | 📅 예정 | 1주 |
| Phase 3 | AI 에이전트 코어 개발 | 📅 예정 | 2주 |
| Phase 4 | CS 검수 UI 개발 | 📅 예정 | 2주 |
| Phase 5 | 통합 테스트 | 📅 예정 | 1주 |
| Phase 6 | 프로덕션 배포 | 📅 예정 | 1주 |

상세한 일정은 [개발 계획](./docs/09_개발_계획.md)을 참조하세요.

---

## 💰 비용 분석 (월 300~900건 기준)

| 항목 | 비용 |
|------|------|
| Sentence-BERT + spaCy | $0 (로컬 실행) |
| Weaviate (셀프호스팅) | $0 |
| MongoDB (셀프호스팅) | $0 |
| Claude API (900건) | ~$45 |
| **총 AI 비용** | **$45/월** |
| AWS EC2 t3.medium (선택) | ~$30/월 |
| **총 운영 비용** | **$75/월** |

---

## 📞 문의

프로젝트 관련 문의사항은 개발팀으로 연락주세요.

---

**Last Updated**: 2025-09-30  
**Version**: 0.1.0 (설계 단계)
