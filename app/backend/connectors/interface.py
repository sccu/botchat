from abc import ABC, abstractmethod
from typing import Generator, Dict, Any

class ILLMConnector(ABC):
    """
    모든 LLM 엔진 연동을 위한 공통 인터페이스.
    macOS 파이프 기능을 통해 비동기 스트리밍 방식으로 데이터를 주고받습니다.
    """

    @abstractmethod
    def send_message(self, prompt: str, context: Dict[str, Any]) -> Generator[str, None, None]:
        """
        메시지를 LLM에 전송하고 스트리밍 방식으로 응답을 반환합니다.
        
        :param prompt: 사용자 입력 프롬프트
        :param context: 대화 컨텍스트 및 설정 (페르소나 등)
        :return: 스트리밍 텍스트 생성기
        """
        pass
