import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_dir))

import json
import requests
from typing import AsyncGenerator
import asyncio
from src.chat.base_chat import BaseChat, logger

class OllamaChat(BaseChat):
    """Ollama 聊天实现"""
    
    def __init__(self):
        api_key = os.getenv("OLLAMA_API_KEY", "")
        super().__init__(api_key)
        
        # 设置远程服务器地址
        self.base_url = "http://159.138.21.8:11434"
        self.model = "llama3.2-vision"  # 固定使用这个模型
        
        # 设置请求头和超时
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self.timeout = 30
        
        # 添加系统提示，限制只用英语回复
        self.system_prompt = {
            "role": "system",
            "content": "You are a helpful AI assistant. Always respond in English, regardless of the input language. Keep your responses clear and concise. 只能使用英文回答，禁止使用其它语言，回答问题时，所有输出只能是英文"
        }
        
        logger.info(f"初始化 OllamaChat，使用模型: {self.model}")
        logger.info(f"服务器地址: {self.base_url}")
        
        # 尝试连接服务器，但不阻止初始化
        self._try_server_connection()
    
    def _try_server_connection(self):
        """尝试连接服务器，但不抛出异常"""
        try:
            response = requests.get(
                f"{self.base_url}/api/version",
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            logger.info("Ollama 服务器连接成功")
            return True
        except requests.exceptions.RequestException as e:
            logger.warning(f"Ollama 服务器连接警告: {str(e)}")
            return False
    
    async def stream_chat(self, user_input: str) -> AsyncGenerator[str, None]:
        """流式对话实现"""
        print('--------------------------------')
        print(f"开始流式对话，用户输入: {user_input}")
        print(f"使用服务器: {self.base_url}")
        print('--------------------------------')
        
        # 在每次对话前检查连接
        if not self._try_server_connection():
            yield "Error: 无法连接到 Ollama 服务器，请检查网络连接"
            return
            
        try:
            # 准备消息，添加系统提示
            messages = [
                self.system_prompt,
                {"role": "user", "content": user_input}
            ]
            
            # 准备请求数据
            data = {
                "model": self.model,
                "messages": messages,
                "stream": True
            }
            
            url = f"{self.base_url}/api/chat"
            
            try:
                response = requests.post(
                    url,
                    json=data,
                    headers=self.headers,
                    stream=True,
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                full_response = ""
                for line in response.iter_lines():
                    if self._stop_streaming:
                        break
                        
                    if line:
                        try:
                            json_response = json.loads(line)
                            if "message" in json_response:
                                content = json_response["message"]["content"]
                                full_response += content
                                yield content
                                
                        except json.JSONDecodeError:
                            continue
                            
                # 保存到对话历史
                if full_response:
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": full_response
                    })
                    
            except requests.exceptions.RequestException as e:
                error_msg = f"API 请求错误: {str(e)}"
                logger.error(error_msg)
                yield f"Error: {error_msg}"
                
        except Exception as e:
            error_msg = f"Stream chat 出错: {str(e)}"
            logger.error(error_msg)
            yield f"Error: {error_msg}"
    
 
async def test():
    """测试函数"""
    chat = OllamaChat()
    
    
    # 测试聊天
    print("\n\n测试聊天:")
    user_input = "你好，我是中国人，请用中文回答我。你叫什么名字？"
    async for response in chat.stream_chat(user_input):
        if response.startswith("Error:"):
            print(f"\n错误: {response}")
            break
        print(response, end="", flush=True)
    print("\n")

if __name__ == "__main__":
    asyncio.run(test())