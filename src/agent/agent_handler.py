import re
from typing import Dict, Optional
from src.image.image_generator import ImageGenerator  # 假设你有图像生成器
import logging

logger = logging.getLogger(__name__)

class AgentHandler:
    """Agent处理类，用于判断和处理不同类型的请求"""
    
    def __init__(self):
        try:
            self.image_generator = ImageGenerator()
        except Exception as e:
            logger.error(f"Failed to initialize ImageGenerator: {str(e)}")
            self.image_generator = None
        
    def analyze_request(self, text: str) -> Dict:
        """分析用户请求类型"""
        
        # 画图相关的关键词
        draw_keywords = [
            r"画[一个]*",
            r"生成[一个]*图",
            r"绘制[一个]*",
            r"展示[一个]*",
            r"显示[一个]*图",
            r"create an image",
            r"draw",
            r"generate a picture",
            r"show me"
        ]
        
        # 组合关键词模式
        draw_pattern = "|".join(draw_keywords)
        
        if re.search(draw_pattern, text, re.IGNORECASE):
            # 提取画图描述
            description = re.sub(draw_pattern, "", text, flags=re.IGNORECASE).strip()
            return {
                "type": "image",
                "description": description
            }
        
        return {
            "type": "chat",
            "content": text
        }
    
    async def handle_request(self, text: str) -> Dict:
        """处理用户请求"""
        analysis = self.analyze_request(text)
        
        if analysis["type"] == "image":
            if not self.image_generator:
                return {
                    "type": "error",
                    "message": "Image generation not available"
                }
                
            try:
                image_data = await self.image_generator.generate(analysis["description"])
                return {
                    "type": "image",
                    "data": image_data,
                    "description": analysis["description"]
                }
            except Exception as e:
                return {
                    "type": "error",
                    "message": f"图像生成失败: {str(e)}"
                }
        
        return {
            "type": "chat",
            "content": text
        } 