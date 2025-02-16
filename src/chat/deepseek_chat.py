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

class DeepSeekChat(BaseChat):
    """DeepSeek 聊天实现"""
    
    def __init__(self):
        api_key = os.getenv("DEEPSEEK_API_KEY")
        super().__init__(api_key)
        
        self.base_url = "https://api.deepseek.com/v1"
        self.model = "deepseek-chat"
        
        # 验证 API 密钥
        if not self.verify_api_key():
            raise ValueError("DeepSeek API 密钥无效")
            
        logger.info(f"初始化 DeepSeekChat，使用模型: {self.model}")
        
        # 初始化 HTTP 客户端
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )

    def set_stop_streaming(self, stop: bool):
        self._stop_streaming = stop
        
    async def stream_chat(self, user_input: str) -> AsyncGenerator[str, None]:
        """流式对话实现"""
        print("开始流式对话")
        print("self._stop_streaming: ", self._stop_streaming)
        self.set_stop_streaming(False)
        try:
            print("开始处理用户输入: ", user_input)
            logger.info(f"开始处理用户输入: {user_input}")
            
            # 添加系统提示，限制只用英语回复
            system_prompt = {
                "role": "system",
                "content": "You are a helpful AI assistant. Always respond in English, regardless of the input language. Keep your responses clear and concise."
            }
            
            # 添加用户输入到对话历史
            messages = [system_prompt]  # 添加系统提示作为第一条消息
            messages.extend(self.conversation_history[-4:])  # 保留最近4轮对话
            messages.append({"role": "user", "content": user_input})
            
            # 准备请求数据
            data = {
                "model": self.model,
                "messages": messages,
                "stream": True,
                "temperature": 0.7,
                "max_tokens": 2000
            }
            print("发送请求到 DeepSeek API")
            logger.info("发送请求到 DeepSeek API")
            
            try:
                async with self.client.stream(
                    "POST", 
                    "/chat/completions", 
                    json=data
                ) as response:
                    if response.status_code != 200:
                        error_text = await response.text()
                        logger.error(f"API 调用失败: {error_text}")
                        yield f"Error: API 调用失败 ({response.status_code}): {error_text}"
                        return

                    logger.info("开始接收流式响应")
                    full_response = ""
                    
                    async for line in response.aiter_lines():
                        if self._stop_streaming:
                            logger.info("流式输出被中断")
                            self.set_stop_streaming(False)
                            break
                            
                        if line.strip():
                            if line.startswith("data: "):
                                try:
                                    line = line.removeprefix("data: ")
                                    if line.strip() == "[DONE]":
                                        logger.info("收到结束标记")
                                        continue
                                        
                                    chunk = json.loads(line)
                                    if content := chunk["choices"][0]["delta"].get("content"):
                                        full_response += content
                                        logger.debug(f"收到响应片段: {content}")
                                        yield content
                                        
                                except json.JSONDecodeError:
                                    logger.warning(f"JSON 解析错误，跳过: {line}")
                                    continue
                                except Exception as e:
                                    logger.error(f"处理响应chunk时出错: {str(e)}")
                                    continue

                    # 如果成功完成对话，保存到历史记录
                    if full_response:
                        logger.info("对话完成，保存到历史记录")
                        self.conversation_history.append({
                            "role": "assistant",
                            "content": full_response
                        })
                        
            except httpx.TimeoutError:
                error_msg = "API 请求超时"
                logger.error(error_msg)
                yield f"Error: {error_msg}"
            except Exception as e:
                error_msg = f"API 请求出错: {str(e)}"
                logger.error(error_msg)
                yield f"Error: {error_msg}"
                
        except Exception as e:
            error_msg = f"Stream chat 出错: {str(e)}"
            logger.error(error_msg)
            yield f"Error: {error_msg}"
            
    async def close(self):
        """关闭客户端"""
        if self.client:
            await self.client.aclose()
            self.client = None
            
    def __del__(self):
        """析构函数"""
        if self.client:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.client.aclose())
            except:
                pass 


async def test():
    # 确保环境变量已加载
    from dotenv import load_dotenv
    load_dotenv()
    
    chat = DeepSeekChat()
    user_input = "tell me something about honey."
    print(f"\n用户: {user_input}\n")
    print("助手: ", end='', flush=True)
    
    try:
        async for response in chat.stream_chat(user_input):
            if response.startswith("Error:"):
                print(f"\n错误: {response}")
                break
            print(response, end='', flush=True)
        print("\n")
    finally:
        await chat.close()

if __name__ == "__main__":
    asyncio.run(test())