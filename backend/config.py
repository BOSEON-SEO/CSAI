# 2025-09-30 17:45, Claude 작성
"""
애플리케이션 설정 관리
환경 변수 및 전역 설정
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
    
    # Weaviate 설정
    WEAVIATE_URL: str = "http://localhost:8080"
    WEAVIATE_API_KEY: Optional[str] = None
    
    # MongoDB 설정
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "cs_ai_agent"
    
    # Redis 설정 (캐싱)
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_TTL: int = 3600  # 1시간
    
    # Claude API 설정
    ANTHROPIC_API_KEY: str = ""  # .env에서 로드 필수
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"
    CLAUDE_MAX_TOKENS: int = 4096
    
    # 신뢰도 평가 임계값
    CONFIDENCE_THRESHOLD: float = 0.7  # 70% 이상이면 자동 답변
    
    # 로깅 설정
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    class Config:
        """Pydantic 설정"""
        env_file = ".env"
        case_sensitive = True


# 전역 설정 인스턴스
settings = Settings()
