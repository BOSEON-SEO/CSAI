# 2025-09-30 17:45, Claude 작성
"""
질문 분석 모듈
spaCy + Sentence-BERT를 이용한 질문 분석
"""

from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class QuestionAnalyzer:
    """
    질문 분석 클래스
    
    기능:
    - 키워드 추출 (spaCy)
    - 제품 코드 인식 (spaCy NER)
    - 질문 카테고리 분류 (Sentence-BERT)
    - 복잡도 판단
    """
    
    def __init__(self):
        """
        QuestionAnalyzer 초기화
        
        TODO: Phase 3에서 구현
        - spaCy 모델 로드
        - Sentence-BERT 모델 로드
        """
        logger.info("QuestionAnalyzer 초기화")
        # TODO: self.nlp = spacy.load("ko_core_news_lg")
        # TODO: self.sbert_model = SentenceTransformer("...")
        
    def analyze(self, question_text: str) -> Dict[str, any]:
        """
        질문 텍스트 분석
        
        Args:
            question_text: 고객 질문 텍스트
            
        Returns:
            Dict: 분석 결과
                - keywords: 추출된 키워드 리스트
                - product_codes: 인식된 제품 코드
                - category: 질문 카테고리
                - complexity: 복잡도 점수 (0-1)
                
        TODO: Phase 3에서 구현
        """
        logger.info(f"질문 분석 시작: {question_text[:50]}...")
        
        # TODO: spaCy로 키워드 추출
        keywords = []
        
        # TODO: 제품 코드 인식
        product_codes = []
        
        # TODO: Sentence-BERT로 카테고리 분류
        category = "unknown"
        
        # TODO: 복잡도 판단
        complexity = 0.5
        
        return {
            "keywords": keywords,
            "product_codes": product_codes,
            "category": category,
            "complexity": complexity
        }
    
    def extract_keywords(self, text: str) -> List[str]:
        """
        키워드 추출 (명사, 고유명사 중심)
        
        Args:
            text: 분석할 텍스트
            
        Returns:
            List[str]: 추출된 키워드 리스트
            
        TODO: Phase 3에서 구현
        """
        return []
    
    def detect_product_codes(self, text: str) -> List[str]:
        """
        제품 코드 인식 (정규식 + NER)
        
        Args:
            text: 분석할 텍스트
            
        Returns:
            List[str]: 인식된 제품 코드 리스트
            
        TODO: Phase 3에서 구현
        """
        return []
    
    def classify_category(self, text: str) -> str:
        """
        질문 카테고리 분류
        
        카테고리:
        - product_inquiry: 제품 문의
        - technical_support: 기술 지원
        - order_inquiry: 주문 문의
        - compatibility: 호환성 문의
        - etc: 기타
        
        Args:
            text: 분석할 텍스트
            
        Returns:
            str: 카테고리명
            
        TODO: Phase 3에서 구현
        """
        return "unknown"
    
    def calculate_complexity(self, text: str, keywords: List[str]) -> float:
        """
        질문 복잡도 계산
        
        고려 사항:
        - 문장 길이
        - 전문 용어 수
        - 질문 수 (?, ? 개수)
        - 복합 조건 여부
        
        Args:
            text: 질문 텍스트
            keywords: 추출된 키워드
            
        Returns:
            float: 복잡도 점수 (0-1, 높을수록 복잡)
            
        TODO: Phase 3에서 구현
        """
        return 0.5
