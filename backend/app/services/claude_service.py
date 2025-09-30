# 2025-09-30 17:45, Claude 작성
"""
Claude API 서비스
답변 생성 및 MCP 연동
"""

from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class ClaudeService:
    """
    Claude API 서비스 클래스
    
    기능:
    - 답변 생성
    - 프롬프트 템플릿 관리
    - MCP 도구 활용
    """
    
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        """
        ClaudeService 초기화
        
        Args:
            api_key: Anthropic API 키
            model: 사용할 Claude 모델
            
        TODO: Phase 3에서 구현
        """
        self.api_key = api_key
        self.model = model
        logger.info(f"ClaudeService 초기화: {model}")
        
        # TODO: Anthropic 클라이언트 초기화
        # from anthropic import Anthropic
        # self.client = Anthropic(api_key=api_key)
    
    def generate_answer(
        self,
        question: str,
        context: Dict[str, any]
    ) -> Dict[str, any]:
        """
        질문에 대한 답변 생성
        
        Args:
            question: 고객 질문
            context: 컨텍스트 정보
                - similar_faqs: 유사 FAQ 리스트
                - product_info: 제품 정보
                - customer_info: 고객 정보 (선택)
                
        Returns:
            Dict: 답변 결과
                - answer: 생성된 답변
                - reasoning: 답변 근거
                
        TODO: Phase 3에서 구현
        """
        logger.info(f"답변 생성 요청: {question[:50]}...")
        
        # TODO: 프롬프트 구성
        prompt = self._build_prompt(question, context)
        
        # TODO: Claude API 호출
        # response = self.client.messages.create(
        #     model=self.model,
        #     max_tokens=4096,
        #     messages=[{"role": "user", "content": prompt}]
        # )
        
        return {
            "answer": "Not implemented",
            "reasoning": "Not implemented"
        }
    
    def _build_prompt(self, question: str, context: Dict) -> str:
        """
        프롬프트 템플릿 구성
        
        Args:
            question: 질문
            context: 컨텍스트
            
        Returns:
            str: 완성된 프롬프트
            
        TODO: Phase 3에서 구현
        """
        prompt = f"""
당신은 투비네트웍스 글로벌의 고객 지원 AI입니다.
아래 정보를 바탕으로 고객의 질문에 답변해주세요.

## 고객 질문
{question}

## 참고 정보
### 유사 FAQ
TODO: FAQ 정보 추가

### 제품 정보
TODO: 제품 정보 추가

## 답변 지침
1. 정확하고 친절하게 답변하세요
2. 제품 코드나 스펙은 정확히 명시하세요
3. 불확실한 경우 "확인이 필요합니다"라고 명시하세요
4. 한국어로 답변하세요

답변:
"""
        return prompt
    
    def health_check(self) -> bool:
        """
        Claude API 연결 상태 확인
        
        Returns:
            bool: API 키 유효성 여부
            
        TODO: Phase 3에서 구현
        """
        # TODO: 간단한 API 호출로 확인
        return False
