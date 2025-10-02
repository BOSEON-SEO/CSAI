# 원본 데이터 디렉토리

이 디렉토리는 가공되지 않은 원본 데이터를 저장합니다.

## 용도
- Excel/CSV 파일
- PDF 문서
- 기타 원본 자료

## Phase 2에서 사용
원본 데이터를 정제하여 `products/` 및 `faqs/` 디렉토리로 변환

---

## 포함된 파일

### products_keychron.csv

**설명**: 키크론(Keychron) 브랜드 제품 정보

**파일 정보**:
- 인코딩: UTF-8
- 총 행 수: 160개
- 총 컬럼 수: 38개

**컬럼 구조**:

| # | 컬럼명 | 타입 | 설명 |
|---|--------|------|------|
| 1 | # | Integer | 순번 |
| 2 | id | Integer | 제품 고유 ID |
| 3 | product_name | String | 제품명 |
| 4 | product_name_synonyms | String | 제품명 동의어 |
| 5 | price | String | 가격 |
| 6 | discontinued | Boolean | 단종 여부 |
| 7 | release_date | String | 출시일 |
| 8 | key_binding | String | 키 바인딩 |
| 9 | tags | String | 태그 |
| 10 | features | String | 주요 기능 |
| 11 | keyboard_layout | String | 키보드 배열 |
| 12 | keyboard_type | String | 키보드 타입 |
| 13 | switch_options | String | 스위치 옵션 |
| 14 | multi_media_key_count | String | 멀티미디어 키 개수 |
| 15 | main_frame_material | String | 본체 재질 |
| 16 | key_cap_profile | String | 키캡 프로파일 |
| 17 | stabilizer | String | 스태빌라이저 |
| 18 | reinforcing_plate | String | 보강판 |
| 19 | n_key_rollover | String | N키 롤오버 |
| 20 | plug_and_play | String | 플러그 앤 플레이 |
| 21 | polling_rate | String | 폴링 레이트 |
| 22 | support_platforms | String | 지원 플랫폼 |
| 23 | battery_capacity | String | 배터리 용량 |
| 24 | bluetooth_runtime | String | 블루투스 사용시간 |
| 25 | backlight_pattern | String | 백라이트 패턴 |
| 26 | connection_method | String | 연결 방식 |
| 27 | supports_2_4ghz | String | 2.4GHz 지원 |
| 28 | dynamic_keystroke | String | 동적 키 입력 |
| 29 | hot_swap_socket | String | 핫스왑 소켓 |
| 30 | rapid_trigger | String | 래피드 트리거 |
| 31 | size | String | 크기 |
| 32 | height_including_key_cap | String | 키캡 포함 높이 |
| 33 | height_not_including_key_cap | String | 키캡 미포함 높이 |
| 34 | package_contents | String | 패키지 구성품 |
| 35 | warranty_period | String | 보증 기간 |
| 36 | weight | String | 무게 |
| 37 | color | String | 색상 |
| 38 | color_details | String | 색상 상세 |

**데이터 샘플**:
- 제품명 예시: "키크론 V10 PRO MAX 블루투스 인체공학 키보드"
- 가격 범위: 다양 (String 형태로 저장)
- 브랜드: Keychron (키크론)

**사용 목적**:
1. MongoDB `products` 컬렉션에 임포트
2. 제품 문의 응대 시 스펙 조회
3. 제품 코드 기반 검색 및 매칭

**처리 스크립트**: `backend/scripts/import_data.py`

**업데이트 이력**:
- 2025-10-02: 최초 작성, products_keychron.csv 정보 추가
