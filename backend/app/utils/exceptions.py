# 2025-09-30 17:45, Claude 작성
"""
커스텀 예외 클래스
애플리케이션 전용 예외 정의
"""


class CSAIException(Exception):
    """
    CS AI Agent 기본 예외 클래스
    """
    def __init__(self, message: str, code: str = "UNKNOWN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class QuestionAnalysisError(CSAIException):
    """
    질문 분석 중 발생하는 예외
    """
    def __init__(self, message: str):
        super().__init__(message, code="QUESTION_ANALYSIS_ERROR")


class VectorSearchError(CSAIException):
    """
    벡터 검색 중 발생하는 예외
    """
    def __init__(self, message: str):
        super().__init__(message, code="VECTOR_SEARCH_ERROR")


class DatabaseError(CSAIException):
    """
    데이터베이스 작업 중 발생하는 예외
    """
    def __init__(self, message: str):
        super().__init__(message, code="DATABASE_ERROR")


class AnswerGenerationError(CSAIException):
    """
    답변 생성 중 발생하는 예외
    """
    def __init__(self, message: str):
        super().__init__(message, code="ANSWER_GENERATION_ERROR")


class LowConfidenceError(CSAIException):
    """
    신뢰도가 낮아 답변할 수 없는 경우
    """
    def __init__(self, confidence_score: float, threshold: float):
        message = f"신뢰도 점수({confidence_score:.2f})가 임계값({threshold:.2f})보다 낮습니다"
        super().__init__(message, code="LOW_CONFIDENCE")
        self.confidence_score = confidence_score
        self.threshold = threshold


class ServiceUnavailableError(CSAIException):
    """
    외부 서비스(Weaviate, MongoDB, Claude API) 이용 불가
    """
    def __init__(self, service_name: str):
        message = f"{service_name} 서비스를 사용할 수 없습니다"
        super().__init__(message, code="SERVICE_UNAVAILABLE")
        self.service_name = service_name
