# FAQ 데이터 디렉토리

이 디렉토리는 FAQ JSON 파일을 저장합니다.

## 파일 형식

각 FAQ는 카테고리별로 분류됩니다.

예시: `product_inquiry_001.json`

```json
{
  "faq_id": "FAQ-PROD-001",
  "category": "product_inquiry",
  "question": "KB-TKL-001 키보드의 배터리 수명은 얼마나 되나요?",
  "answer": "KB-TKL-001의 배터리 용량은 2000mAh이며, 블루투스 모드에서 약 30일 사용 가능합니다. USB-C 케이블로 충전하며, 완충 시간은 약 2시간입니다.",
  "keywords": ["배터리", "수명", "충전", "KB-TKL-001"],
  "related_products": ["KB-TKL-001"],
  "complexity": 0.3,
  "created_at": "2025-09-01",
  "updated_at": "2025-09-01"
}
```

## 카테고리
- `product_inquiry`: 제품 문의
- `technical_support`: 기술 지원
- `order_inquiry`: 주문 문의
- `compatibility`: 호환성 문의
- `etc`: 기타

## Phase 2에서 작성 예정
- 최소 50개 FAQ 데이터 준비 (카테고리별 10개씩)
