import pytest
from pathlib import Path
from image_generator import ImageGenerator

def test_image_generation():
    # 初始化图片生成器
    generator = ImageGenerator()
    
    # 测试文本到图片生成
    prompt = "一只可爱的小熊猫在竹林中玩耍"
    try:
        image_path = generator.generate_image(prompt)
        assert image_path.exists(), "生成的图片文件应该存在"
        print(f"图片已生成并保存到: {image_path}")
    except Exception as e:
        print(f"生成图片失败: {str(e)}")
        raise

def test_image_variation():
    # 初始化图片生成器
    generator = ImageGenerator()
    
    # 首先生成一张原始图片
    original_prompt = "一只金色的小猪猪在花园里"
    try:
        original_image_path = generator.generate_image(original_prompt)
        
        # 测试图片变体生成
        variation_path = generator.generate_image_variation(original_image_path)
        assert variation_path.exists(), "变体图片文件应该存在"
        print(f"变体图片已生成并保存到: {variation_path}")
    except Exception as e:
        print(f"生成图片变体失败: {str(e)}")
        raise

if __name__ == "__main__":
    # 运行测试
    print("开始测试图片生成...")
    test_image_generation()
    print("\n开始测试图片变体生成...")
    test_image_variation()
    print("\n所有测试完成！") 