from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional
import logging

logger = logging.getLogger(__name__)

class BaseChat(ABC):
    """聊天基类，定义统一接口"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.conversation_history = []
        self._stop_streaming = False
        
    @abstractmethod
    async def stream_chat(self, user_input: str) -> AsyncGenerator[str, None]:
        """流式对话接口"""
        pass
        
    def stop_streaming(self):
        """停止流式输出"""
        self._stop_streaming = True
        
    def reset_conversation(self):
        """重置对话历史"""
        self.conversation_history = []
        self._stop_streaming = False
        
    def verify_api_key(self) -> bool:
        """验证 API 密钥"""
        if not self.api_key:
            logger.error("API 密钥未设置")
            return False
        
        if len(self.api_key) < 30:
            logger.error("API 密钥格式可能不正确")
            return False
        
        return True 