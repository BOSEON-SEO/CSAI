# Phase 2: Keychron 데이터 준비

**작성일**: 2025-10-01  
**작성자**: Claude  
**Phase**: Phase 2 - 데이터 준비 (2025-10-14 ~ 10-20 예정)  
**상태**: 진행 중

---

## 개요

이 문서는 CS AI 에이전트 프로젝트의 Phase 2에서 진행한 Keychron 제품 데이터 준비 과정을 기록합니다. 우리는 먼저 Keychron 브랜드부터 시작하기로 결정했습니다. Aiper와 GTGear에 비해 Keychron이 수집된 제품 데이터가 가장 많고, GTGear의 경우 추가 데이터 수집이 많이 필요하기 때문입니다.

---

## 목표

Phase 2의 핵심 목표는 다음과 같습니다.

제품 정보 데이터 구조를 설계하는 것이 첫 번째 목표입니다. MongoDB와 Weaviate에 저장할 제품 정보의 스키마를 설계해야 합니다. FAQ 데이터 구조도 함께 설계합니다. 고객 문의와 답변을 저장할 FAQ 스키마가 필요하기 때문입니다.

Keychron 제품 데이터를 변환하는 작업도 진행합니다. CSV 형태로 수집된 Keychron 제품 정보(160개 제품, 38개 컬럼)를 MongoDB에 적합한 JSON 형태로 변환해야 합니다. 마지막으로 Vector DB용 임베딩 파일을 생성합니다. 변환된 데이터를 Weaviate에 업로드할 수 있도록 준비하는 것입니다.

---

## 현재 데이터 현황

프로젝트 루트의 products_keychron.csv 파일에는 160개 제품의 정보가 38개 컬럼으로 구성되어 있습니다. 주요 속성으로는 제품명, 가격, 레이아웃, 스위치 옵션, 연결 방식, 배터리 용량, 크기, 무게 등이 포함되어 있습니다.

CSV 파일을 검토한 결과 몇 가지 특징을 확인할 수 있었습니다. 일부 필드는 비어있거나 정보 없음으로 표시되어 있습니다. 제품마다 다른 속성을 가지고 있다는 점도 중요합니다. 예를 들어 유선 키보드는 배터리 정보가 없고, 무선 키보드는 케이블 정보가 없습니다. 이러한 가변적인 속성 구조는 MongoDB의 유연한 스키마로 처리하기에 적합합니다.

---

## 데이터 구조 설계

### 제품 정보 구조 설계 원칙

우리는 MongoDB의 가장 큰 장점인 유연한 스키마를 활용하기로 결정했습니다. 각 제품 카테고리(키보드, 레이싱 휠, 수영장 로봇)별로 다른 속성을 자유롭게 담되, 공통 필드는 표준화하는 방식입니다.

설계 시 네 가지 원칙을 따랐습니다. 첫째, 공통 필드를 표준화합니다. 모든 제품이 공통으로 가지는 필드(제품 ID, 브랜드, 카테고리 등)는 일관된 구조를 유지합니다. 둘째, 가변 속성을 허용합니다. 제품 유형에 따라 다른 specs 구조를 허용하는 것입니다. 예를 들어 키보드에는 switch_options가 있지만, 레이싱 휠에는 force_feedback이 있습니다.

셋째, 검색 효율성을 고려합니다. product_id, brand, category 같은 공통 필드로 인덱싱하여 빠른 검색을 가능하게 합니다. 넷째, 확장 가능성을 염두에 둡니다. 나중에 이미지, 동영상 같은 미디어를 추가하거나 다국어 지원을 추가하기 쉽도록 설계하는 것입니다.

### MongoDB 제품 스키마의 구조

MongoDB 제품 문서는 여러 섹션으로 구성됩니다. 최상위에는 product_id, brand, category, model_name이 있습니다. basic_info 섹션에는 한글명, 영문명, 상태, 가격, 통화 정보가 들어갑니다.

specs 섹션이 가장 복잡합니다. 여기에는 레이아웃, 키보드 타입, 스위치 옵션, 연결 방식, 배터리, 핫스왑 지원 여부, RGB 백라이트, 멀티미디어 키 개수, 프레임 재질, 키캡 프로파일, n-key rollover, 폴링 레이트 등이 포함됩니다. 연결 방식은 다시 세부적으로 bluetooth, usb, wireless_2_4ghz로 나뉩니다.

compatibility 섹션에는 지원 OS 목록과 plug_and_play 여부가 있습니다. physical 섹션에는 크기, 무게, 높이 정보가 들어갑니다. colors 배열에는 사용 가능한 색상 목록이, package_contents 배열에는 패키지 구성품이 저장됩니다.

마지막으로 metadata 섹션에는 created_at, updated_at, data_source, tags 같은 메타 정보가 포함됩니다. tags는 검색을 위한 키워드 배열입니다.

이 구조의 장점은 여러 가지입니다. MongoDB의 유연성을 활용하여 각 카테고리는 완전히 다른 specs 구조를 가질 수 있습니다. 키보드에 force_feedback 필드가 없어도 괜찮고, 레이싱 기어에 battery 필드가 없어도 됩니다. product_id, brand, category 같은 공통 필드로 인덱싱하면 빠른 검색이 가능합니다. 또한 tags 배열로 다차원 필터링도 가능합니다. 나중에 이미지, 동영상 같은 미디어를 추가하거나 다국어 지원을 추가하기도 쉽습니다.

### FAQ 데이터 구조

FAQ는 특정 제품에 대한 것일 수도 있고, 여러 제품에 공통적인 내용일 수도 있습니다. 이 관계를 유연하게 표현하기 위해 다음과 같은 구조를 설계했습니다.

FAQ 문서는 faq_id, brand, category로 시작합니다. question 섹션에는 실제 질문 텍스트, 키워드 배열, 카테고리가 포함됩니다. answer 섹션에는 답변 텍스트와 함께 verified 여부, verified_by(검수자), verified_at(검수 시각) 정보가 들어갑니다.

related_products 배열로 하나의 FAQ가 여러 제품과 연결될 수 있습니다. 예를 들어 K8 시리즈 전체에 적용되는 배터리 정보 같은 내용을 중복 없이 관리할 수 있습니다. additional_info 섹션에는 적용 가능한 모델 목록, 관련 FAQ 링크, 외부 링크 등이 포함됩니다.

stats 섹션에는 조회수, 도움이 되었다는 평가 수, 도움이 되지 않았다는 평가 수가 저장됩니다. metadata 섹션에는 생성 시각, 수정 시각, 상태(active, outdated, deprecated) 정보가 들어갑니다.

---

## 데이터 변환 작업

### CSV 데이터 분석 스크립트

먼저 products_keychron.csv 파일을 읽고 구조를 파악하는 Python 스크립트를 작성했습니다. backend/scripts/analyze_csv.py 파일이 이 역할을 담당합니다.

이 스크립트는 CSV 파일을 pandas로 읽어서 기본 통계를 출력합니다. 총 제품 수, 컬럼 수를 확인하고, 각 컬럼별로 결측치 비율을 계산합니다. 샘플 데이터를 출력하여 실제 데이터 형태를 파악할 수 있게 하고, 각 컬럼의 고유값 개수도 함께 표시합니다. 이를 통해 어떤 필드가 범주형 데이터인지, 어떤 필드가 자유 텍스트인지 파악할 수 있습니다.

### MongoDB JSON 변환 스크립트

CSV 데이터를 MongoDB에 적합한 JSON 구조로 변환하는 스크립트를 backend/scripts/convert_keychron_to_json.py에 작성했습니다.

이 스크립트의 핵심은 clean_value 함수입니다. NaN, 빈 문자열, 정보 없음 등을 None으로 통일하여 데이터를 정제합니다. parse_switch_options 함수는 쉼표로 구분된 스위치 옵션 문자열을 리스트로 파싱합니다. parse_os_support 함수는 슬래시나 쉼표로 구분된 OS 문자열을 리스트로 변환합니다.

convert_row_to_document 함수가 가장 중요합니다. CSV의 한 행을 받아서 MongoDB 문서 구조로 변환하는 역할을 합니다. 제품 ID를 KB-0001 형식으로 생성하고, 각 필드를 적절한 섹션으로 분류합니다. 연결 방식 정보를 파싱하여 connectivity 객체를 구성하고, 배터리 정보가 있는 경우에만 battery 객체를 추가합니다.

변환된 문서들은 data/products_keychron.json 파일로 저장됩니다. 한글이 깨지지 않도록 ensure_ascii=False 옵션을 사용하고, 읽기 쉽게 indent=2로 포맷팅합니다.

### Vector DB용 임베딩 준비 스크립트

변환된 제품 데이터를 Weaviate에 업로드할 수 있도록 텍스트 표현을 생성하는 스크립트를 backend/scripts/prepare_embeddings.py에 작성했습니다.

generate_product_text 함수가 핵심입니다. 제품 정보를 하나의 텍스트 문자열로 변환하는 역할을 합니다. 이 텍스트는 나중에 Sentence-BERT로 임베딩되어 Weaviate에 저장될 것입니다.

함수는 제품의 모든 중요 정보를 파이프(|) 문자로 구분된 하나의 긴 문자열로 결합합니다. 제품명, 모델명, 브랜드, 카테고리로 시작하여 상태, 가격, 레이아웃, 키보드 타입, 스위치 옵션, 연결 방식, 배터리 정보, 핫스왑 여부, RGB 지원 여부, 물리적 크기, 호환 OS, 태그까지 포함합니다.

prepare_weaviate_data 함수는 MongoDB JSON 데이터를 읽어서 각 제품에 대해 Weaviate 객체를 생성합니다. 각 객체에는 product_id, brand, category, model_name과 함께 generate_product_text로 생성된 텍스트가 포함됩니다. 결과는 data/products_keychron_weaviate.json 파일로 저장됩니다.

---

## 생성된 파일 구조

위 스크립트들을 실행하면 다음과 같은 파일들이 생성됩니다.

프로젝트 루트에 data 폴더가 새로 생성됩니다. 이 폴더 안에 products_keychron.json과 products_keychron_weaviate.json 파일이 들어갑니다. 전자는 MongoDB용 제품 데이터이고, 후자는 Weaviate용 제품 데이터입니다.

backend/scripts 폴더에는 세 개의 스크립트가 있습니다. analyze_csv.py는 CSV 분석 스크립트이고, convert_keychron_to_json.py는 JSON 변환 스크립트이며, prepare_embeddings.py는 임베딩 준비 스크립트입니다.

원본 CSV 데이터인 products_keychron.csv 파일은 프로젝트 루트에 그대로 유지됩니다.

---

## 다음 단계

Phase 2를 완료하기 위해 아직 필요한 작업들이 있습니다.

첫째, FAQ 데이터를 수집해야 합니다. 실제 고객 문의 내역에서 FAQ 50개를 추출하여 JSON 형태로 정리하는 작업입니다. 둘째, MongoDB 임포트 스크립트를 작성해야 합니다. 변환된 제품 데이터를 MongoDB에 실제로 임포트하는 스크립트가 필요합니다.

셋째, Weaviate 업로드 스크립트를 작성합니다. Sentence-BERT로 임베딩을 생성하고 Weaviate에 업로드하는 작업입니다. 넷째, GTGear와 Aiper 브랜드의 데이터도 준비해야 합니다. Keychron 작업이 완료되면 나머지 브랜드의 데이터도 수집하고 변환하는 것입니다.

---

## MongoDB와 Weaviate의 역할

이 프로젝트에서 MongoDB와 Weaviate는 서로 보완적인 역할을 합니다.

Weaviate는 Vector DB로서 의미적 유사도 검색(Semantic Search)을 담당합니다. 제품과 FAQ의 임베딩 벡터를 저장하고, 검색 시에는 유사도 점수와 문서 ID를 반환합니다.

MongoDB는 NoSQL 데이터베이스로서 실제 데이터 저장 및 구조화된 쿼리를 담당합니다. 제품 스펙, 고객 정보, FAQ 원본, 메타데이터를 저장하고, 검색 시에는 실제 데이터를 반환합니다.

전체 작동 흐름은 다음과 같습니다. 먼저 Weaviate에서 유사한 제품 ID를 검색합니다. 예를 들어 [KB-0001, KB-0045, KB-0123] 같은 ID 목록을 받습니다. 그 다음 MongoDB에서 해당 제품의 실제 데이터를 가져옵니다. 고객 정보 및 주문 정보도 MongoDB에서 조회합니다. 마지막으로 모든 정보를 Claude에게 전달하여 답변을 생성합니다.

비유하자면 Weaviate는 도서관의 사서와 같습니다. 어떤 책이 필요한지 찾아주는 역할입니다. MongoDB는 책장과 같습니다. 실제 내용을 담고 있는 곳입니다. 두 시스템이 함께 작동해야 효율적인 검색과 정확한 답변이 가능합니다.

---

**문서 버전**: 1.0  
**최종 업데이트**: 2025-10-01  
**다음 업데이트 예정**: FAQ 데이터 수집 완료 시
