import os
from pathlib import Path
from openai import OpenAI
import requests
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv

# 加载环境变量
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(env_path)

class ImageGenerator:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.output_dir = Path(__file__).parent / "generated_images"
        self.output_dir.mkdir(exist_ok=True)

    def generate_image(self, prompt: str, size: str = "1024x1024") -> Path:
        """
        根据文本提示生成图片
        
        Args:
            prompt (str): 图片描述文本
            size (str): 图片尺寸，可选 "1024x1024", "512x512", "256x256"
            
        Returns:
            Path: 生成图片的保存路径
        """
        try:
            # 调用 DALL-E 生成图片
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                quality="standard",
                n=1,
            )

            # 获取图片 URL
            image_url = response.data[0].url

            # 下载图片
            image_response = requests.get(image_url)
            image = Image.open(BytesIO(image_response.content))

            # 保存图片
            output_path = self.output_dir / f"{hash(prompt)}.png"
            image.save(output_path)

            return output_path

        except Exception as e:
            print(f"生成图片时出错: {str(e)}")
            raise

    def generate_image_variation(self, image_path: str | Path) -> Path:
        """
        根据输入图片生成变体
        
        Args:
            image_path (str | Path): 输入图片路径
            
        Returns:
            Path: 生成的变体图片路径
        """
        try:
            # 打开并处理输入图片
            with open(image_path, "rb") as image_file:
                response = self.client.images.create_variation(
                    image=image_file,
                    n=1,
                    size="1024x1024"
                )

            # 获取变体图片 URL
            variation_url = response.data[0].url

            # 下载变体图片
            image_response = requests.get(variation_url)
            variation_image = Image.open(BytesIO(image_response.content))

            # 保存变体图片
            output_path = self.output_dir / f"variation_{Path(image_path).stem}.png"
            variation_image.save(output_path)

            return output_path

        except Exception as e:
            print(f"生成图片变体时出错: {str(e)}")
            raise 