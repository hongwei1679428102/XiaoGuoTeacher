import os
import httpx
import json
from typing import AsyncGenerator, Optional
import logging
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from src.utils.logger import logger

# 配置日志
logger.setLevel(logging.INFO)

# 创建控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# 设置日志格式
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# 添加处理器到日志记录器
logger.addHandler(console_handler)

class StreamChat:
    def __init__(self):
        # 从环境变量获取 API 密钥
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("未设置 DEEPSEEK_API_KEY 环境变量")
            
        self.base_url = "https://api.deepseek.com/v1"
        self.model = "deepseek-chat"
        self.conversation_history = []
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
        self._stop_streaming = False  # 添加停止标志
        
    def stop_streaming(self):
        """停止当前的流式输出"""
        self._stop_streaming = True
        
    def reset(self):
        """重置所有状态"""
        self.conversation_history = []
        self._stop_streaming = False
        
    async def stream_chat(self, user_input: str) -> AsyncGenerator[str, None]:
        """流式处理用户输入并返回回应"""
        try:
            if self._stop_streaming:
                return
                
            # 记录用户输入
            self.conversation_history.append({"role": "user", "content": user_input})
            full_response = ""
            
            # 准备请求数据
            data = {
                "model": self.model,
                "messages": self.conversation_history,
                "stream": True,
                "temperature": 0.7
            }
            
            # 发送请求
            async with self.client.stream("POST", "/chat/completions", json=data) as response:
                if response.status_code != 200:
                    error_msg = f"API 调用失败: {await response.text()}"
                    logger.error(error_msg)
                    yield f"Error: {error_msg}"
                    return

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            line = line.removeprefix("data: ")
                            if line.strip() == "[DONE]":
                                continue
                                
                            chunk = json.loads(line)
                            if content := chunk["choices"][0]["delta"].get("content"):
                                full_response += content
                                yield content
                                
                        except json.JSONDecodeError as e:
                            logger.error(f"JSON 解析错误: {str(e)}")
                            continue
                        except Exception as e:
                            logger.error(f"处理响应chunk时出错: {str(e)}")
                            continue

            # 如果没有被中断，记录完整的对话历史
            if not self._stop_streaming and full_response:
                self.conversation_history.append({
                    "role": "assistant",
                    "content": full_response
                })
                    
        except Exception as e:
            error_msg = f"Error in stream chat: {str(e)}"
            logger.error(error_msg)
            yield error_msg
            
        finally:
            await self.client.aclose()
    
    def reset_conversation(self):
        """重置对话历史"""
        self.conversation_history = []

    def verify_api_key(self):
        """验证 API 密钥是否有效"""
        if not self.api_key:
            logger.error("API 密钥未设置")
            return False
        
        if len(self.api_key) < 30:  # 一般的 API 密钥长度检查
            logger.error("API 密钥格式可能不正确")
            return False
        
        return True

async def test():
    chat = StreamChat()
    
    # 测试流式对话
    user_input = "tell me something about honey."
    print(f"\n用户: {user_input}\n")
    print("助手: ", end='', flush=True)
    
    try:
        async for response in chat.stream_chat(user_input):
            print(response, end='', flush=True)
        print("\n")
    except KeyboardInterrupt:
        print("\n对话被用户中断")
    finally:
        await chat.client.aclose()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test()) 