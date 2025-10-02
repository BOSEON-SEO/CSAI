# Weaviate 설정 및 FAQ 임베딩 가이드

**작성일**: 2025-10-02 18:00, Claude 작성

이 가이드는 Weaviate Vector Database를 설정하고 FAQ 데이터를 임베딩하는 전체 과정을 설명합니다.

---

## 📋 전체 흐름

```
1. Weaviate 스키마 설정 (FAQ 클래스 생성)
         ↓
2. Sentence-BERT 모델 다운로드 (최초 1회)
         ↓
3. MongoDB에서 FAQ 읽기
         ↓
4. 각 FAQ를 768차원 벡터로 변환
         ↓
5. Weaviate에 벡터 + 메타데이터 저장
         ↓
6. 검색 테스트
```

---

## 🚀 Step 1: 필수 패키지 설치

```powershell
# 가상환경 활성화
cd C:\workspace\CSAI
.venv\Scripts\Activate.ps1

# 필요한 패키지 설치
pip install weaviate-client sentence-transformers torch
```

**GPU 가속 (RTX 3050 활용)**:
```powershell
# CUDA 버전 확인 (필수 아님, CPU로도 작동)
nvidia-smi

# PyTorch CUDA 버전 (선택사항)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

---

## 🔧 Step 2: Weaviate 스키마 설정

```powershell
cd C:\workspace\CSAI\backend\scripts

# Weaviate 스키마 생성
python setup_weaviate.py
```

**예상 출력**:
```
======================================================================
🚀 Weaviate 초기 설정 시작
======================================================================

[1/4] Weaviate 연결 중: http://localhost:8081
  ✅ Weaviate 연결 성공!

[2/4] FAQ 클래스 스키마 생성
📋 FAQ 클래스 스키마 생성 중...
  ✅ FAQ 클래스 생성 완료!

[3/4] Product 클래스 스키마 생성
📋 Product 클래스 스키마 생성 중...
  ✅ Product 클래스 생성 완료!

[4/4] 생성된 클래스 확인
  📋 총 2 개 클래스:
    - FAQ
    - Product

======================================================================
✅ Weaviate 초기 설정 완료!
======================================================================

다음 단계:
  1. Sentence-BERT 모델 설정
  2. MongoDB → Weaviate 데이터 임포트
  3. 검색 테스트
======================================================================
```

---

## 📦 Step 3: FAQ 임베딩 생성 및 업로드

### 기본 사용법

```powershell
# 모든 FAQ 임포트
python import_to_weaviate.py --type faqs
```

### 옵션

| 옵션 | 설명 | 기본값 | 예시 |
|------|------|--------|------|
| `--type` | 데이터 타입 | faqs | `--type faqs` |
| `--brand` | 브랜드 필터 | 없음 | `--brand KEYCHRON` |
| `--batch-size` | 배치 크기 | 100 | `--batch-size 50` |
| `--limit` | 최대 개수 (테스트용) | 없음 | `--limit 10` |

### 실행 예시

```powershell
# 1. 테스트: 10개만 임포트
python import_to_weaviate.py --type faqs --limit 10

# 2. KEYCHRON 브랜드만 임포트
python import_to_weaviate.py --type faqs --brand KEYCHRON

# 3. 전체 FAQ 임포트
python import_to_weaviate.py --type faqs

# 4. 메모리 부족 시 (배치 크기 감소)
python import_to_weaviate.py --type faqs --batch-size 50
```

---

## 📊 예상 출력 (전체 과정)

```
🤖 Sentence-BERT 모델 로딩: jhgan/ko-sroberta-multitask
  💻 디바이스: cuda
  🎮 GPU: NVIDIA GeForce RTX 3050
  ✅ 모델 로드 완료! (임베딩 차원: 768)

🔌 MongoDB 연결 중...
  ✅ MongoDB 연결 성공!

🔌 Weaviate 연결 중...
  ✅ Weaviate 연결 성공!

======================================================================
📦 FAQ → Weaviate 임포트 시작
======================================================================

[1/4] MongoDB에서 FAQ 읽기...
  ✅ 50개 FAQ 로드 완료

[2/4] FAQ 텍스트 준비 중...
  ✅ 50개 텍스트 준비 완료

[3/4] 임베딩 생성 중...
  🔄 50개 텍스트 임베딩 생성 중... (배치 크기: 100)
Batches: 100%|████████████████████| 1/1 [00:02<00:00,  2.34s/it]
  ✅ 50개 임베딩 생성 완료

[4/4] Weaviate에 저장 중...
  → 50/50 완료...

======================================================================
📊 임포트 결과
======================================================================
  ✅ 성공:    50개
  ❌ 실패:     0개
======================================================================

🔌 연결 종료

✅ 모든 작업 완료!
```

---

## 🔍 데이터 확인

### 방법 1: Python으로 확인

```python
import weaviate

# Weaviate 연결
client = weaviate.connect_to_local(
    host="localhost",
    port=8081,
    grpc_port=50051
)

# FAQ 개수 확인
collection = client.collections.get("FAQ")
result = collection.aggregate.over_all(total_count=True)
print(f"총 FAQ: {result.total_count}개")

# 샘플 FAQ 조회
faqs = collection.query.fetch_objects(limit=5)
for faq in faqs.objects:
    print(f"- [{faq.properties['inquiry_no']}] {faq.properties['faq_id']}")

client.close()
```

### 방법 2: 검색 테스트

```python
import weaviate

client = weaviate.connect_to_local(
    host="localhost",
    port=8081,
    grpc_port=50051
)

# 의미 검색 테스트
collection = client.collections.get("FAQ")

response = collection.query.near_text(
    query="블루투스 연결이 안돼요",
    limit=3
)

print("\n검색 결과:")
for obj in response.objects:
    props = obj.properties
    print(f"\n[{props['inquiry_no']}] {props['category']}")
    print(f"유사도: {obj.metadata.distance:.4f}")
    print(f"텍스트: {props['combined_text'][:100]}...")

client.close()
```

---

## 💡 Sentence-BERT 모델 정보

### 사용 모델
**이름**: `jhgan/ko-sroberta-multitask`

**특징**:
- ✅ 한국어 + 영어 멀티링구얼 지원
- ✅ 768차원 벡터 생성
- ✅ 코사인 유사도 최적화
- ✅ 여러 NLP 태스크로 학습 (multitask)

**크기**: 약 500MB (최초 1회 다운로드)

**성능** (RTX 3050 기준):
- 임베딩 생성: 약 100개/초
- 메모리 사용: 약 2GB (GPU)

---

## 🎯 벡터 저장 구조

### Weaviate에 저장되는 데이터

```json
{
  "faq_id": "FAQ-302260746",
  "inquiry_no": 302260746,
  "mongodb_id": "67036a1f3c4b2e8f9a123456",
  "brand_channel": "KEYCHRON",
  "category": "반품",
  "combined_text": "반품주소 여기로 보내면되나요 경기도 용인시...",
  "answered": true,
  "created_at": "2025-10-02T09:00:00Z",
  "vector": [0.234, -0.567, 0.891, ...]  // 768차원
}
```

### MongoDB와의 연결

```python
# 1. Weaviate에서 유사 FAQ ID 검색
weaviate_results = weaviate.search("블루투스 문제")
# → [{"faq_id": "FAQ-001", "mongodb_id": "abc123"}]

# 2. MongoDB에서 상세 정보 조회
faq = mongodb.faqs.find_one({"_id": ObjectId("abc123")})
# → 전체 FAQ 내용 (질문, 답변, 고객 정보 등)
```

---

## ❗ 문제 해결

### 문제 1: Weaviate 연결 실패

**증상**:
```
❌ Weaviate 연결 실패: ConnectionRefusedError
```

**해결**:
```powershell
# Docker 컨테이너 확인
docker-compose ps

# Weaviate 재시작
docker-compose restart weaviate

# 로그 확인
docker-compose logs weaviate
```

### 문제 2: GPU 메모리 부족

**증상**:
```
RuntimeError: CUDA out of memory
```

**해결**:
```powershell
# 배치 크기 감소
python import_to_weaviate.py --type faqs --batch-size 50

# 또는 CPU 사용
$env:CUDA_VISIBLE_DEVICES = "-1"
python import_to_weaviate.py --type faqs
```

### 문제 3: 모델 다운로드 느림

**증상**: Sentence-BERT 모델 다운로드가 매우 느림

**해결**:
```python
# 다운로드 위치 확인
import os
print(os.path.expanduser("~/.cache/huggingface"))

# 미러 사이트 사용 (선택)
export HF_ENDPOINT=https://hf-mirror.com
```

---

## 🔄 데이터 업데이트

### FAQ 수정 후 재임베딩

```powershell
# 특정 FAQ만 업데이트 (현재 버전에서는 전체 재임포트)
python import_to_weaviate.py --type faqs

# Weaviate는 UUID 기반 upsert를 지원하므로
# 동일한 faq_id는 자동으로 업데이트됩니다
```

---

## 📈 다음 단계

FAQ 임베딩이 완료되었습니다! 이제:

1. ✅ **검색 테스트**: 의미 검색이 잘 작동하는지 확인
2. ⏭️ **AI 에이전트 개발**: FastAPI + Claude API 통합
3. ⏭️ **검색 최적화**: 하이브리드 검색 (벡터 + 키워드)

---

**작성**: 2025-10-02 18:00, Claude  
**업데이트**: 2025-10-02 18:00
