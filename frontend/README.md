# Frontend - CS 검수 UI

Next.js + shadcn/ui 기반 프론트엔드

## Phase 4에서 작업 예정

### 기술 스택
- **Framework**: Next.js 14 (App Router)
- **UI Library**: shadcn/ui + Tailwind CSS
- **State Management**: Zustand
- **API Client**: Axios
- **실시간 통신**: Server-Sent Events (SSE)

### 주요 화면
1. 대기열 목록 (ReviewQueue)
2. 답변 상세/검수 (ReviewDetail)
3. 통계 대시보드 (Dashboard)

### 프로젝트 초기화 (Phase 4)
```bash
cd frontend
npx create-next-app@latest . --typescript --tailwind --app
npx shadcn@latest init
```
