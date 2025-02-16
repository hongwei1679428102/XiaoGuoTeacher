import os
import asyncio
import base64
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到 Python 路径
root_dir = Path(__file__).resolve().parent.parent.parent
import sys
sys.path.append(str(root_dir))

# 使用绝对导入
from src.image.image_generator import ImageGenerator

# 加载环境变量
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(env_path)

async def test_image_generation():
    """测试图像生成"""
    generator = ImageGenerator()
    
    try:
        # 测试用例列表
        test_cases = [
            {
                "name": "simple_landscape",
                "prompt": "一个美丽的山水风景画，有青山绿水"
            },
            {
                "name": "cartoon_character",
                "prompt": "一个可爱的卡通猫咪，大眼睛，微笑的表情"
            },
            {
                "name": "abstract_art",
                "prompt": "一幅抽象艺术画，充满活力的色彩"
            }
        ]
        
        # 创建输出目录
        output_dir = Path(__file__).parent / "test_outputs"
        output_dir.mkdir(exist_ok=True)
        
        # 运行测试
        for case in test_cases:
            print(f"\n测试: {case['name']}")
            print(f"提示词: {case['prompt']}")
            
            try:
                # 生成图像
                image_data = await generator.generate(case['prompt'])
                
                if image_data:
                    # 保存图像
                    image_path = output_dir / f"{case['name']}.png"
                    with open(image_path, 'wb') as f:
                        f.write(base64.b64decode(image_data))
                    print(f"✓ 成功生成图像: {image_path}")
                else:
                    print(f"✗ 生成失败: 未返回图像数据")
                    
            except Exception as e:
                print(f"✗ 生成失败: {str(e)}")
                
    finally:
        # 清理资源
        await generator.close()

def main():
    """主函数"""
    # 确保 OPENAI_API_KEY 存在
    if not os.getenv("OPENAI_API_KEY"):
        print("错误: 未设置 OPENAI_API_KEY 环境变量")
        return
        
    print("开始图像生成测试...")
    asyncio.run(test_image_generation())
    print("\n测试完成!")

if __name__ == "__main__":
    main() 