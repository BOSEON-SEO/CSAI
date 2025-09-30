# 제품 데이터 디렉토리

이 디렉토리는 제품 스펙 JSON 파일을 저장합니다.

## 파일 형식

각 제품은 별도의 JSON 파일로 저장됩니다.

예시: `KB-TKL-001.json`

```json
{
  "product_code": "KB-TKL-001",
  "name": "텐키리스 기계식 키보드",
  "category": "keyboard",
  "specs": {
    "switch_type": "Cherry MX Blue",
    "connectivity": ["USB-C", "Bluetooth 5.0"],
    "battery": "2000mAh",
    "dimensions": "355 x 127 x 38mm",
    "weight": "750g"
  },
  "price": 89000,
  "stock": 50,
  "compatibility": ["Windows", "macOS", "Linux"],
  "firmware_version": "v1.2.3",
  "qc_sheet_url": "https://...",
  "manual_url": "https://..."
}
```

## Phase 2에서 작성 예정
- 최소 10개 제품 데이터 준비
