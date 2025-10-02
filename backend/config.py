# backend/config.py
# 2025-10-02 18:20, Claude 작성

"""
애플리케이션 설정 관리

루트 docker-compose.yml의 설정에 맞춰 업데이트:
- Weaviate: localhost:8081 (Spring의 8080 충돌 방지)
- MongoDB: localhost:27017 (인증 포함)
- Redis: localhost:6379
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    애플리케이션 설정 클래스
    .env 파일에서 환경 변수를 자동으로 로드
    """
    
    # 애플리케이션 기본 설정
    APP_NAME: str = "CS AI Agent"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # API 서버 설정
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Weaviate 설정 (루트 docker-compose.yml 기준)
    WEAVIATE_URL: str = "http://localhost:8081"  # Spring 8080 충돌 방지
    WEAVIATE_API_KEY: Optional[str] = None
    
    # MongoDB 설정 (루트 docker-compose.yml 기준)
    MONGODB_URL: str = "mongodb://admin:csai_admin_2025@localhost:27017"
    MONGODB_DB_NAME: str = "csai"
    
    # Redis 설정 (캐싱)
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_TTL: int = 3600  # 1시간
    
    # Sentence-BERT 모델
    SENTENCE_BERT_MODEL: str = "jhgan/ko-sroberta-multitask"
    
    # Claude API 설정
    ANTHROPIC_API_KEY: str = ""  # .env에서 로드 필수
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"
    CLAUDE_MAX_TOKENS: int = 4096
    
    # 신뢰도 평가 임계값
    CONFIDENCE_THRESHOLD: float = 0.7  # 70% 이상이면 자동 답변
    COMPLEXITY_THRESHOLD: float = 0.6  # 60% 이상이면 복잡한 질문
    
    # 검색 설정
    SIMILAR_FAQ_LIMIT: int = 5  # 유사 FAQ 최대 개수
    MIN_SIMILARITY: float = 0.6  # 최소 유사도
    
    # 로깅 설정
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    class Config:
        """Pydantic 설정"""
        env_file = ".env"
        case_sensitive = True


# 전역 설정 인스턴스
settings = Settings()
