# backend/app/schemas/__init__.py
# 2025-10-02 16:45, Claude 작성

"""
Pydantic 스키마 패키지

FastAPI의 요청/응답 모델을 정의합니다.
"""

from .faq import FAQInput, FAQBatch, FAQResponse
from .product import ProductInput, ProductBatch, ProductResponse
from .question import QuestionAnalysisRequest, QuestionAnalysisResponse
from .answer import AnswerGenerationRequest, AnswerGenerationResponse

__all__ = [
    # FAQ 관련
    'FAQInput',
    'FAQBatch',
    'FAQResponse',
    
    # 제품 관련
    'ProductInput',
    'ProductBatch',
    'ProductResponse',
    
    # 질문 분석 관련
    'QuestionAnalysisRequest',
    'QuestionAnalysisResponse',
    
    # 답변 생성 관련
    'AnswerGenerationRequest',
    'AnswerGenerationResponse',
]
