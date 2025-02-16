import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_dir))

import httpx
import json
from typing import AsyncGenerator
import asyncio
from src.chat.base_chat import BaseChat, logger

class ErnieChat(BaseChat):
    """文心一言聊天实现"""
    
    def __init__(self):
        api_key = os.getenv("BAIDU_API_KEY")
        super().__init__(api_key)
        
        self.secret_key = os.getenv("BAIDU_SECRET_KEY")
        self.base_url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions"
        self.access_token = None
        self.client = httpx.AsyncClient()
        
    async def _get_access_token(self):
        """获取访问令牌"""
        url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={self.api_key}&client_secret={self.secret_key}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if response.status_code == 200:
                self.access_token = response.json()["access_token"]
            else:
                raise Exception("获取访问令牌失败")
                
    async def stream_chat(self, user_input: str) -> AsyncGenerator[str, None]:
        """流式对话实现"""
        print('--------------------------------')
        print(f"开始流式对话，用户输入: {user_input}")
        print('--------------------------------')
        try:
            if self._stop_streaming:
                return
                
            if not self.access_token:
                await self._get_access_token()
                
            self.conversation_history.append({"role": "user", "content": user_input})
            full_response = ""
            
            url = f"{self.base_url}?access_token={self.access_token}"
            data = {
                "messages": self.conversation_history,
                "stream": True,
                "temperature": 0.7
            }
            
            async with self.client.stream("POST", url, json=data) as response:
                if response.status_code != 200:
                    error_msg = f"API 调用失败: {await response.text()}"
                    logger.error(error_msg)
                    yield f"Error: {error_msg}"
                    return

                buffer = ""
                async for line in response.aiter_lines():
                    if self._stop_streaming:
                        break
                        
                    if not line.strip():
                        continue
                        
                    try:
                        # 处理可能的SSE格式
                        if line.startswith('data: '):
                            line = line[6:]
                        
                        # 累积buffer直到有完整的JSON
                        buffer += line
                        try:
                            chunk = json.loads(buffer)
                            buffer = ""  # 重置buffer
                            
                            if result := chunk.get("result", ""):
                                full_response += result
                                yield result
                                
                        except json.JSONDecodeError:
                            # 如果不是完整的JSON就继续累积
                            continue
                            
                    except Exception as e:
                        logger.error(f"处理响应chunk时出错: {str(e)}")
                        continue

            if not self._stop_streaming and full_response:
                self.conversation_history.append({
                    "role": "assistant",
                    "content": full_response
                })
                    
        except Exception as e:
            error_msg = f"Stream chat error: {str(e)}"
            logger.error(error_msg)
            yield f"Error: {error_msg}"
            
        finally:
            await self.client.aclose() 

async def test():
    # 确保环境变量已加载
    from dotenv import load_dotenv
    load_dotenv()
    
    chat = ErnieChat()
    user_input = "tell me something about honey."
    print(f"\n用户: {user_input}\n")
    print("助手: ", end='', flush=True)
    async for response in chat.stream_chat(user_input):
        print(response, end='', flush=True)
    print("\n")

if __name__ == "__main__":
    asyncio.run(test())