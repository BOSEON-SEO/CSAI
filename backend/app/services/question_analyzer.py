#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
질문 분석 서비스 (Question Analyzer)
투비네트웍스 글로벌 - CS AI 에이전트 프로젝트

2025-10-02 09:15, Claude 작성
2025-10-02 16:00, Claude 업데이트 (hybrid_search 파라미터 수정)

고객 문의를 분석하여:
1. 키워드 추출 (spaCy)
2. 카테고리 분류
3. 제품 코드 인식
4. 임베딩 생성 (Sentence-BERT)
5. 유사 FAQ 검색 (Weaviate)
6. 복잡도 판단
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

import spacy
from sentence_transformers import SentenceTransformer
import torch

from .weaviate_service import WeaviateService


# ==================== 로깅 설정 ====================

logger = logging.getLogger(__name__)


# ==================== 데이터 클래스 ====================

@dataclass
class AnalysisResult:
    """
    질문 분석 결과
    
    Attributes:
        keywords: 추출된 키워드 리스트
        product_codes: 인식된 제품 코드 리스트 (예: ['K10', 'PRO MAX'])
        category: 추정 카테고리 (배송/반품/상품/교환/환불/기타)
        complexity_score: 복잡도 점수 (0.0 ~ 1.0)
        embedding: 질문 임베딩 벡터 (768차원)
        similar_faqs: 유사 FAQ 리스트
        confidence: 답변 가능 신뢰도 (0.0 ~ 1.0)
        should_defer: 사람에게 전가 여부
        defer_reason: 전가 사유
    """
    keywords: List[str] = field(default_factory=list)
    product_codes: List[str] = field(default_factory=list)
    category: str = "기타"
    complexity_score: float = 0.0
    embedding: Optional[List[float]] = None
    similar_faqs: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    should_defer: bool = False
    defer_reason: Optional[str] = None


# ==================== 질문 분석기 ====================

class QuestionAnalyzer:
    """
    질문 분석 서비스
    
    spaCy + Sentence-BERT + Weaviate를 활용하여
    고객 문의를 종합적으로 분석합니다.
    """
    
    # 카테고리별 키워드 (확장 가능)
    CATEGORY_KEYWORDS = {
        '배송': ['배송', '도착', '발송', '택배', '송장', '수령', '받', '언제'],
        '반품': ['반품', '환불', '취소', '반송', '수거'],
        '교환': ['교환', '변경', '바꾸', '다른'],
        '상품': ['불량', '고장', '작동', '인식', '연결', '안됨', '안돼', '문제'],
        '환불': ['환불', '돈', '결제', '취소'],
        '기타': ['문의', '질문', '궁금']
    }
    
    # 제품 코드 패턴 (정규식)
    PRODUCT_CODE_PATTERNS = [
        r'K\d{1,2}',  # K10, K8, K5 등
        r'Q\d{1,2}',  # Q10, Q13 등
        r'V\d{1,2}',  # V10, V6 등
        r'B\d{1,2}',  # B6, B1 등
        r'C\d{1,2}',  # C2 등
        r'M\d{1,2}',  # M6 (마우스)
        r'PRO\s*MAX',
        r'PRO\s*SE\d?',
        r'ZMK',
    ]
    
    # 복잡도 판단 키워드
    HIGH_COMPLEXITY_KEYWORDS = [
        '펌웨어', 'firmware', '드라이버', 'driver',
        '호환', '지원', 'bios', '바이오스',
        '업데이트', 'update', '버전', 'version',
        '블루투스', 'bluetooth', '연결', '끊김',
        '인식', '페어링', 'pairing', '무선'
    ]
    
    def __init__(
        self,
        spacy_model: str = "ko_core_news_sm",
        sbert_model: str = "jhgan/ko-sroberta-multitask",
        weaviate_service: Optional[WeaviateService] = None
    ):
        """
        초기화
        
        Args:
            spacy_model: spaCy 한국어 모델 이름
            sbert_model: Sentence-BERT 모델 이름
            weaviate_service: WeaviateService 인스턴스
        """
        logger.info("🤖 QuestionAnalyzer 초기화 중...")
        
        # spaCy 모델 로드
        logger.info(f"  📚 spaCy 모델 로딩: {spacy_model}")
        try:
            self.nlp = spacy.load(spacy_model)
        except OSError:
            logger.error(f"  ❌ spaCy 모델이 설치되지 않았습니다: {spacy_model}")
            logger.info(f"  💡 설치 명령: python -m spacy download {spacy_model}")
            raise
        
        # Sentence-BERT 모델 로드
        logger.info(f"  🧠 Sentence-BERT 모델 로딩: {sbert_model}")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"     디바이스: {device}")
        self.sbert = SentenceTransformer(sbert_model, device=device)
        
        # Weaviate 서비스
        self.weaviate = weaviate_service
        
        logger.info("  ✅ QuestionAnalyzer 초기화 완료!")
    
    def extract_keywords(self, text: str, top_k: int = 10) -> List[str]:
        """
        텍스트에서 키워드 추출 (spaCy)
        
        명사, 고유명사, 동사를 추출하고 빈도순으로 정렬합니다.
        
        Args:
            text: 분석할 텍스트
            top_k: 상위 몇 개 키워드를 반환할지
        
        Returns:
            키워드 리스트
        """
        doc = self.nlp(text)
        
        # 품사 필터링: 명사(NOUN), 고유명사(PROPN), 동사(VERB)
        keywords = []
        for token in doc:
            if token.pos_ in ['NOUN', 'PROPN', 'VERB'] and len(token.text) > 1:
                keywords.append(token.text)
        
        # 중복 제거 및 빈도 계산
        keyword_freq = {}
        for keyword in keywords:
            keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
        
        # 빈도순 정렬
        sorted_keywords = sorted(
            keyword_freq.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # 상위 K개 반환
        return [keyword for keyword, _ in sorted_keywords[:top_k]]
    
    def extract_product_codes(self, text: str) -> List[str]:
        """
        제품 코드 추출 (정규식)
        
        Args:
            text: 분석할 텍스트
        
        Returns:
            제품 코드 리스트
        """
        codes = []
        
        for pattern in self.PRODUCT_CODE_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            codes.extend([m.upper().strip() for m in matches])
        
        # 중복 제거
        return list(set(codes))
    
    def classify_category(self, text: str, keywords: List[str]) -> str:
        """
        카테고리 분류
        
        텍스트와 키워드를 기반으로 문의 카테고리를 추정합니다.
        
        Args:
            text: 분석할 텍스트
            keywords: 추출된 키워드
        
        Returns:
            카테고리 (배송/반품/교환/상품/환불/기타)
        """
        text_lower = text.lower()
        keywords_lower = [k.lower() for k in keywords]
        
        # 각 카테고리별 점수 계산
        scores = {}
        for category, category_keywords in self.CATEGORY_KEYWORDS.items():
            score = 0
            for keyword in category_keywords:
                # 텍스트에서 직접 발견
                if keyword in text_lower:
                    score += 2
                
                # 추출된 키워드에 포함
                if keyword in keywords_lower:
                    score += 1
            
            scores[category] = score
        
        # 가장 높은 점수의 카테고리 반환
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        else:
            return "기타"
    
    def calculate_complexity(self, text: str, keywords: List[str]) -> float:
        """
        복잡도 점수 계산
        
        다음 요소를 고려합니다:
        - 고복잡도 키워드 포함 여부
        - 텍스트 길이
        - 질문 문장 수
        
        Args:
            text: 분석할 텍스트
            keywords: 추출된 키워드
        
        Returns:
            복잡도 점수 (0.0 ~ 1.0)
        """
        score = 0.0
        
        text_lower = text.lower()
        
        # 1. 고복잡도 키워드 체크 (가중치: 0.5)
        complexity_keyword_count = 0
        for keyword in self.HIGH_COMPLEXITY_KEYWORDS:
            if keyword in text_lower:
                complexity_keyword_count += 1
        
        if complexity_keyword_count > 0:
            score += 0.5
        
        # 2. 텍스트 길이 (가중치: 0.3)
        if len(text) > 200:
            score += 0.3
        elif len(text) > 100:
            score += 0.15
        
        # 3. 질문 문장 수 (가중치: 0.2)
        question_marks = text.count('?') + text.count('?')
        if question_marks >= 3:
            score += 0.2
        elif question_marks >= 2:
            score += 0.1
        
        return min(score, 1.0)  # 최대 1.0
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        텍스트 임베딩 생성 (Sentence-BERT)
        
        Args:
            text: 분석할 텍스트
        
        Returns:
            768차원 임베딩 벡터
        """
        embedding = self.sbert.encode(
            text,
            convert_to_tensor=False,
            normalize_embeddings=True
        )
        return embedding.tolist()
    
    def calculate_confidence(
        self,
        similar_faqs: List[Dict[str, Any]],
        complexity_score: float
    ) -> Tuple[float, bool, Optional[str]]:
        """
        답변 가능 신뢰도 계산
        
        Args:
            similar_faqs: 유사 FAQ 리스트
            complexity_score: 복잡도 점수
        
        Returns:
            (신뢰도, 전가 여부, 전가 사유)
        """
        # 기본 신뢰도: 유사 FAQ의 평균 점수/유사도
        if not similar_faqs:
            return 0.0, True, "유사한 FAQ를 찾을 수 없습니다"
        
        # 'score' (하이브리드) 또는 'similarity' (벡터만) 사용
        avg_similarity = sum(
            faq.get('score', faq.get('similarity', 0)) 
            for faq in similar_faqs
        ) / len(similar_faqs)
        
        # 복잡도 패널티
        confidence = avg_similarity * (1 - complexity_score * 0.3)
        
        # 전가 판단
        should_defer = False
        defer_reason = None
        
        # 복잡도가 높으면 전가
        if complexity_score > 0.7:
            should_defer = True
            defer_reason = "전문 지식이 필요한 문의입니다 (펌웨어/드라이버/호환성 등)"
        
        # 유사도가 낮으면 전가
        elif avg_similarity < 0.6:
            should_defer = True
            defer_reason = "유사한 이전 사례가 부족합니다"
        
        # 신뢰도가 낮으면 전가
        elif confidence < 0.5:
            should_defer = True
            defer_reason = "답변 신뢰도가 낮습니다"
        
        return confidence, should_defer, defer_reason
    
    async def analyze(
        self,
        inquiry_content: str,
        brand_channel: str,
        title: Optional[str] = None,
        category: Optional[str] = None,
        product_name: Optional[str] = None
    ) -> AnalysisResult:
        """
        질문 종합 분석
        
        전체 분석 파이프라인:
        1. 키워드 추출
        2. 제품 코드 인식
        3. 카테고리 분류
        4. 복잡도 계산
        5. 임베딩 생성
        6. 유사 FAQ 검색
        7. 신뢰도 평가
        
        Args:
            inquiry_content: 문의 내용
            brand_channel: 브랜드 채널
            title: 문의 제목 (선택)
            category: 문의 카테고리 (선택, 없으면 자동 분류)
            product_name: 제품명 (선택)
        
        Returns:
            AnalysisResult 객체
        """
        logger.info(f"📝 질문 분석 시작: '{inquiry_content[:50]}...'")
        
        result = AnalysisResult()
        
        # 전체 텍스트 (제목 + 내용)
        full_text = f"{title or ''} {inquiry_content} {product_name or ''}".strip()
        
        # 1. 키워드 추출
        logger.info("  🔍 키워드 추출 중...")
        result.keywords = self.extract_keywords(full_text)
        logger.info(f"     키워드: {result.keywords[:5]}")
        
        # 2. 제품 코드 인식
        logger.info("  🏷️  제품 코드 인식 중...")
        result.product_codes = self.extract_product_codes(full_text)
        if result.product_codes:
            logger.info(f"     제품 코드: {result.product_codes}")
        
        # 3. 카테고리 분류
        if category:
            result.category = category
        else:
            logger.info("  📂 카테고리 분류 중...")
            result.category = self.classify_category(full_text, result.keywords)
            logger.info(f"     카테고리: {result.category}")
        
        # 4. 복잡도 계산
        logger.info("  🧮 복잡도 계산 중...")
        result.complexity_score = self.calculate_complexity(full_text, result.keywords)
        logger.info(f"     복잡도: {result.complexity_score:.2f}")
        
        # 5. 임베딩 생성
        logger.info("  🧠 임베딩 생성 중...")
        result.embedding = self.generate_embedding(inquiry_content)
        logger.info(f"     임베딩: 768차원 벡터")
        
        # 6. 유사 FAQ 검색 (Weaviate)
        if self.weaviate:
            logger.info("  🔎 유사 FAQ 검색 중...")
            
            # 하이브리드 검색 (벡터 + 키워드)
            result.similar_faqs = await self.weaviate.hybrid_search(
                query_text=inquiry_content,
                keywords=result.keywords[:5],  # 상위 5개 키워드
                brand_channel=brand_channel,
                category=result.category if result.category != "기타" else None,
                limit=5
            )
            
            # 최소 점수 필터링 (0.5 이상만)
            result.similar_faqs = [
                faq for faq in result.similar_faqs 
                if faq.get('score', 0) >= 0.5
            ]
            
            logger.info(f"     유사 FAQ: {len(result.similar_faqs)}개 발견")
            
            if result.similar_faqs:
                top_score = result.similar_faqs[0].get('score', 0)
                logger.info(f"     최고 점수: {top_score:.2f}")
        
        # 7. 신뢰도 평가
        logger.info("  📊 신뢰도 평가 중...")
        result.confidence, result.should_defer, result.defer_reason = \
            self.calculate_confidence(result.similar_faqs, result.complexity_score)
        
        logger.info(f"     신뢰도: {result.confidence:.2f}")
        logger.info(f"     전가 여부: {result.should_defer}")
        if result.defer_reason:
            logger.info(f"     전가 사유: {result.defer_reason}")
        
        logger.info("  ✅ 분석 완료!\n")
        
        return result


# ==================== 유틸리티 함수 ====================

def format_analysis_result(result: AnalysisResult) -> str:
    """
    분석 결과를 보기 좋게 포맷팅
    
    Args:
        result: AnalysisResult 객체
    
    Returns:
        포맷팅된 문자열
    """
    lines = [
        "=" * 70,
        "📊 질문 분석 결과",
        "=" * 70,
        "",
        f"🔑 키워드: {', '.join(result.keywords[:10])}",
        f"🏷️  제품 코드: {', '.join(result.product_codes) if result.product_codes else 'N/A'}",
        f"📂 카테고리: {result.category}",
        f"🧮 복잡도: {result.complexity_score:.2f}",
        "",
        f"🔎 유사 FAQ: {len(result.similar_faqs)}개 발견",
    ]
    
    # 유사 FAQ 상위 3개
    if result.similar_faqs:
        lines.append("")
        for i, faq in enumerate(result.similar_faqs[:3], 1):
            score = faq.get('score', faq.get('similarity', 0))
            lines.append(f"  [{i}] 점수 {score:.2f}: {faq.get('title', 'N/A')}")
    
    lines.extend([
        "",
        f"📊 신뢰도: {result.confidence:.2f}",
        f"⚠️  전가 여부: {'예' if result.should_defer else '아니오'}",
    ])
    
    if result.defer_reason:
        lines.append(f"   사유: {result.defer_reason}")
    
    lines.append("=" * 70)
    
    return '\n'.join(lines)
