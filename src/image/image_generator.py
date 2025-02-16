import os
from typing import Optional
import base64
import httpx
from openai import AsyncOpenAI

class ImageGenerator:
    """图像生成器 - 使用 OpenAI DALL-E"""
    
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
    
    async def generate(self, prompt: str) -> Optional[str]:
        """生成图像"""
        try:
            response = await self.client.images.generate(
                model="dall-e-3",  # 或 "dall-e-2"
                prompt=prompt,
                n=1,
                size="1024x1024",  # 可选 "256x256", "512x512", "1024x1024"
                response_format="b64_json"
            )
            
            # 返回 base64 编码的图像数据
            return response.data[0].b64_json
            
        except Exception as e:
            raise Exception(f"图像生成失败: {str(e)}")
            
    async def close(self):
        """关闭客户端"""
        if self.client:
            await self.client.close() 
        


