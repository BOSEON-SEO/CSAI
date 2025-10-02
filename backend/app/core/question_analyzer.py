# backend/app/core/question_analyzer.py
# 2025-10-02 16:30, Claude 작성

"""
고객 문의 질문 분석 모듈 (개선 버전)

이 모듈은 이미 구조화된 FAQ 데이터를 받아서:
1. 기존 카테고리 활용 (재분류 불필요)
2. 제품 정보 활용 (product_name에서 추출)
3. content에서 추가 정보만 추출 (키워드, 복잡도)

설계 원칙:
- 이미 있는 구조화된 데이터는 재분석하지 않음
- content 분석은 추가 정보 추출에만 집중
- 경량화된 분석으로 응답 속도 향상
"""

import re
import spacy
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class InquiryData:
    """
    Spring에서 받아온 구조화된 FAQ 데이터
    
    Spring이 이미 네이버 API에서 가져와서 정리한 데이터입니다.
    재분석이 필요 없는 필드들을 포함합니다.
    """
    # 필수 필드 (Spring에서 이미 제공)
    brand_channel: str              # "KEYCHRON", "GTGEAR" 등
    inquiry_category: str           # "반품", "배송", "교환", "상품" 등 (이미 분류됨!)
    title: str                      # 문의 제목
    inquiry_content: str            # 문의 내용 (실제 고객 질문)
    
    # 선택 필드
    product_name: Optional[str] = None      # "키크론 K10 PRO MAX..."
    product_order_option: Optional[str] = None  # "쉘화이트, 바나나축"
    customer_name: Optional[str] = None
    order_id: Optional[str] = None


@dataclass
class AnalysisResult:
    """
    질문 분석 결과
    
    기존 데이터를 활용하고, content에서 추가 정보만 추출합니다.
    """
    # Spring에서 받은 원본 정보 (재분류 안 함)
    category: str                   # inquiry_category 그대로 사용
    brand_channel: str              # brand_channel 그대로 사용
    
    # 제품 정보 (product_name에서 추출)
    product_codes: List[str] = field(default_factory=list)  # ["K10", "PRO MAX"]
    product_color: Optional[str] = None      # "쉘화이트"
    product_switch: Optional[str] = None     # "바나나축"
    
    # content에서 추출한 추가 정보
    keywords: List[str] = field(default_factory=list)  # 핵심 키워드
    tech_terms: List[str] = field(default_factory=list)  # 기술 용어
    complexity_score: float = 0.0   # 복잡도 (0-1)
    
    # 원본 데이터 참조
    title: str = ""
    inquiry_content: str = ""
    
    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            'category': self.category,
            'brand_channel': self.brand_channel,
            'product_codes': self.product_codes,
            'product_color': self.product_color,
            'product_switch': self.product_switch,
            'keywords': self.keywords,
            'tech_terms': self.tech_terms,
            'complexity_score': self.complexity_score,
        }


class QuestionAnalyzer:
    """
    경량화된 질문 분석기
    
    이미 구조화된 데이터를 받아서:
    - 카테고리: 재분류 ❌ (inquiry_category 사용)
    - 제품 정보: product_name에서 추출
    - 키워드/복잡도: inquiry_content에서 추출
    
    이점:
    1. ✅ 빠른 속도 (Sentence-BERT 불필요)
    2. ✅ 정확한 분류 (네이버의 분류 활용)
    3. ✅ 메모리 효율적
    
    Example:
        >>> analyzer = QuestionAnalyzer()
        >>> data = InquiryData(
        ...     brand_channel="KEYCHRON",
        ...     inquiry_category="상품",
        ...     title="키 안눌림",
        ...     inquiry_content="K10 키보드 ㅐ 키가 안 눌려요",
        ...     product_name="키크론 K10 PRO MAX"
        ... )
        >>> result = analyzer.analyze(data)
        >>> print(result.category)  # '상품' (재분류 안 함!)
        >>> print(result.product_codes)  # ['K10', 'PRO MAX']
    """
    
    # 키크론 제품 코드 패턴
    PRODUCT_CODE_PATTERNS = [
        r'K\d+',      # K10, K5 등
        r'V\d+',      # V1, V10 등
        r'B\d+',      # B6, B1 등
        r'Q\d+',      # Q11, Q6 등
        r'C\d+',      # C2 등
        r'M\d+',      # M6 등
    ]
    
    # 제품 시리즈/타입
    PRODUCT_SERIES = [
        r'PRO\s*MAX',
        r'PRO\s*SE2?',
        r'PRO',
        r'MAX',
        r'SE2?',
        r'ZMK',
    ]
    
    # 색상 키워드
    COLOR_KEYWORDS = [
        '쉘화이트', '쉘 화이트', 'shell white',
        '레트로', 'retro', '레트로 블루', '레트로 그린', '레트로 레드',
        '빈티지 우드', 'vintage wood',
        '바닐라 크림', 'vanilla cream',
        '스페이스 그레이', 'space gray',
        '화이트', 'white',
        '블랙', 'black',
        '그레이', 'gray',
        '블루', 'blue',
    ]
    
    # 스위치 타입
    SWITCH_TYPES = [
        '바나나축', '저소음 바나나축',
        '적축', '저소음 적축',
        '갈축', '저소음 갈축',
        '화이트축', '저소음 화이트축',
        '청축',
        '펜타그래프', '팬타그래프',
    ]
    
    # 기술 용어 (복잡도 계산용)
    TECH_TERMS = [
        'as', 'a/s', '에이에스',
        '불량', '펌웨어', '드라이버', '호환',
        '기판', '스위치', '블루투스',
        '리시버', '무선', '유선', '2.4ghz',
        '충전', '배터리', '연결', '페어링',
        '인식', '동작', '작동', '토글',
        '소리', '키감', '눌림', '스태빌라이저',
        '윈도우', '맥', 'mac', 'windows',
        '설정', '설치', '업데이트', '초기화',
        '핫스왑', '키캡', 'rgb', '백라이트',
    ]
    
    def __init__(self, spacy_model: str = 'ko_core_news_sm'):
        """
        QuestionAnalyzer 초기화 (경량화 버전)
        
        Sentence-BERT 제거 → 빠른 초기화!
        
        Args:
            spacy_model: spaCy 한국어 모델명
        """
        print("📚 QuestionAnalyzer 초기화 중 (경량 모드)...")
        
        # spaCy 한국어 모델만 로드
        print(f"  - spaCy 한국어 모델 로드: {spacy_model}")
        self.nlp = spacy.load(spacy_model)
        
        # 정규표현식 컴파일 (성능 최적화)
        self.product_code_regex = re.compile(
            '|'.join(self.PRODUCT_CODE_PATTERNS),
            re.IGNORECASE
        )
        
        self.product_series_regex = re.compile(
            '|'.join(self.PRODUCT_SERIES),
            re.IGNORECASE
        )
        
        print("✅ QuestionAnalyzer 초기화 완료! (Sentence-BERT 없이 경량 모드)\n")
    
    def analyze(self, data: InquiryData) -> AnalysisResult:
        """
        구조화된 데이터 분석 (경량 버전)
        
        Args:
            data: Spring에서 받은 InquiryData
            
        Returns:
            AnalysisResult 객체
            
        Example:
            >>> data = InquiryData(
            ...     brand_channel="KEYCHRON",
            ...     inquiry_category="상품",
            ...     title="키 안눌림",
            ...     inquiry_content="K10 키보드가 안 눌려요",
            ...     product_name="키크론 K10 PRO MAX 쉘화이트 바나나축"
            ... )
            >>> result = analyzer.analyze(data)
        """
        # 1. 카테고리: 재분류 안 함! (이미 분류된 데이터 사용)
        category = data.inquiry_category
        
        # 2. 제품 정보 추출 (product_name + content)
        product_codes, product_color, product_switch = self._extract_product_info(
            data.product_name or "",
            data.product_order_option or "",
            data.inquiry_content
        )
        
        # 3. 키워드 추출 (content에서만)
        keywords = self._extract_keywords(data.inquiry_content)
        
        # 4. 기술 용어 추출
        tech_terms = self._extract_tech_terms(data.inquiry_content)
        
        # 5. 복잡도 계산
        complexity = self._calculate_complexity(
            data.title,
            data.inquiry_content,
            tech_terms
        )
        
        return AnalysisResult(
            category=category,
            brand_channel=data.brand_channel,
            product_codes=product_codes,
            product_color=product_color,
            product_switch=product_switch,
            keywords=keywords,
            tech_terms=tech_terms,
            complexity_score=complexity,
            title=data.title,
            inquiry_content=data.inquiry_content
        )
    
    def _extract_product_info(
        self,
        product_name: str,
        product_option: str,
        content: str
    ) -> Tuple[List[str], Optional[str], Optional[str]]:
        """
        제품 정보 추출 (코드, 색상, 스위치)
        
        우선순위:
        1. product_name (가장 정확)
        2. product_option
        3. content (보조)
        
        Args:
            product_name: DB의 product_name
            product_option: DB의 product_order_option
            content: inquiry_content
            
        Returns:
            (제품코드 리스트, 색상, 스위치)
        """
        # 모든 텍스트 합치기
        full_text = f"{product_name} {product_option} {content}"
        
        # 1. 제품 코드 추출
        codes = []
        
        # 기본 코드 (K10, V1 등)
        base_codes = self.product_code_regex.findall(full_text)
        codes.extend([code.upper() for code in base_codes])
        
        # 시리즈 (PRO MAX, SE2 등)
        series = self.product_series_regex.findall(full_text)
        codes.extend([s.upper().replace(' ', ' ') for s in series])
        
        # 중복 제거
        codes = list(dict.fromkeys(codes))  # 순서 유지하며 중복 제거
        
        # 2. 색상 추출
        color = None
        for color_kw in self.COLOR_KEYWORDS:
            if color_kw.lower() in full_text.lower():
                color = color_kw
                break
        
        # 3. 스위치 타입 추출
        switch = None
        for switch_type in self.SWITCH_TYPES:
            if switch_type in full_text:
                switch = switch_type
                break
        
        return codes, color, switch
    
    def _extract_keywords(self, content: str) -> List[str]:
        """
        spaCy를 이용한 키워드 추출 (경량)
        
        명사만 추출하고, 불용어는 제거합니다.
        
        Args:
            content: inquiry_content
            
        Returns:
            키워드 리스트
        """
        doc = self.nlp(content)
        
        keywords = []
        
        # 명사와 고유명사 추출
        for token in doc:
            if token.pos_ in ['NOUN', 'PROPN']:
                # 2글자 이상만
                if len(token.text) > 1:
                    keywords.append(token.text)
        
        # 중복 제거
        keywords = list(set(keywords))
        
        return keywords[:10]  # 최대 10개로 제한
    
    def _extract_tech_terms(self, content: str) -> List[str]:
        """
        기술 용어 추출
        
        Args:
            content: inquiry_content
            
        Returns:
            기술 용어 리스트
        """
        content_lower = content.lower()
        
        found_terms = []
        for term in self.TECH_TERMS:
            if term in content_lower:
                found_terms.append(term)
        
        return found_terms
    
    def _calculate_complexity(
        self,
        title: str,
        content: str,
        tech_terms: List[str]
    ) -> float:
        """
        복잡도 계산 (간소화 버전)
        
        복잡도 요소:
        1. content 길이 (30%)
        2. 기술 용어 개수 (40%)
        3. 문장 개수 (30%)
        
        Args:
            title: 제목
            content: 내용
            tech_terms: 추출된 기술 용어
            
        Returns:
            복잡도 점수 (0-1)
        """
        score = 0.0
        
        # 1. 내용 길이 (200자 기준)
        length_score = min(len(content) / 200, 1.0) * 0.3
        score += length_score
        
        # 2. 기술 용어 (3개 기준)
        tech_score = min(len(tech_terms) / 3, 1.0) * 0.4
        score += tech_score
        
        # 3. 문장 개수 (5개 기준)
        sentence_count = (
            content.count('.') + 
            content.count('?') + 
            content.count('!')
        )
        sentence_score = min(sentence_count / 5, 1.0) * 0.3
        score += sentence_score
        
        return min(score, 1.0)
    
    def batch_analyze(
        self, 
        data_list: List[InquiryData]
    ) -> List[AnalysisResult]:
        """
        여러 질문을 배치로 분석
        
        Args:
            data_list: InquiryData 리스트
            
        Returns:
            AnalysisResult 리스트
        """
        return [self.analyze(data) for data in data_list]


# 테스트 함수
def test_analyzer():
    """QuestionAnalyzer 테스트 (개선 버전)"""
    print("🧪 QuestionAnalyzer 테스트 시작 (경량 모드)\n")
    
    analyzer = QuestionAnalyzer()
    
    # 테스트 데이터 (실제 Spring에서 받을 형식)
    test_data = [
        InquiryData(
            brand_channel="KEYCHRON",
            inquiry_category="배송",
            title="배송 문의",
            inquiry_content="배송 언제 오나요?"
        ),
        InquiryData(
            brand_channel="KEYCHRON",
            inquiry_category="반품",
            title="반품 가능 여부",
            inquiry_content="K10 PRO MAX 반품 가능한가요?",
            product_name="키크론 K10 PRO MAX 무선 기계식 키보드",
            product_order_option="쉘화이트, 저소음 바나나축"
        ),
        InquiryData(
            brand_channel="KEYCHRON",
            inquiry_category="상품",
            title="블루투스 연결 불가",
            inquiry_content="V1 PRO 키보드 블루투스 연결이 안되는데 AS 가능한가요? 펌웨어 업데이트도 해봤어요.",
            product_name="키크론 V1 PRO MAX"
        ),
        InquiryData(
            brand_channel="KEYCHRON",
            inquiry_category="교환",
            title="색상 교환",
            inquiry_content="쉘화이트 대신 레트로 블루로 교환하고 싶습니다",
            product_name="키크론 K5 SE"
        ),
        InquiryData(
            brand_channel="KEYCHRON",
            inquiry_category="상품",
            title="키 안눌림",
            inquiry_content="키보드 'ㅐ' 키가 안 눌려요. 스위치 문제인가요?",
            product_name="키크론 K10 PRO SE2",
            product_order_option="레트로, 저소음 적축"
        ),
    ]
    
    for i, data in enumerate(test_data, 1):
        print(f"{'='*70}")
        print(f"테스트 {i}")
        print(f"{'='*70}")
        print(f"브랜드: {data.brand_channel}")
        print(f"카테고리: {data.inquiry_category}")
        print(f"제목: {data.title}")
        print(f"내용: {data.inquiry_content}")
        if data.product_name:
            print(f"제품명: {data.product_name}")
        if data.product_order_option:
            print(f"옵션: {data.product_order_option}")
        print()
        
        result = analyzer.analyze(data)
        
        print(f"📊 분석 결과:")
        print(f"  - 카테고리: {result.category}")
        print(f"  - 제품 코드: {result.product_codes}")
        print(f"  - 색상: {result.product_color}")
        print(f"  - 스위치: {result.product_switch}")
        print(f"  - 키워드: {result.keywords}")
        print(f"  - 기술 용어: {result.tech_terms}")
        print(f"  - 복잡도: {result.complexity_score:.2f}")
        print()


if __name__ == '__main__':
    test_analyzer()
