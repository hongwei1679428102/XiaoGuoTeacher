import os
from typing import Optional, Dict, List
from src.chat.base_chat import BaseChat, logger
from src.chat.deepseek_chat import DeepSeekChat
from src.chat.ernie_chat import ErnieChat
from src.chat.ollama_3 import OllamaChat
import asyncio
import time

os.environ["CHAT_TYPE"] = "ollama"

class ChatEvaluator:
    """聊天模型评估器"""
    
    @staticmethod
    async def evaluate_model(chat: BaseChat, test_cases: List[str]) -> Dict:
        """评估单个模型"""
        results = {
            "total_time": 0,
            "success_rate": 0,
            "avg_response_time": 0,
            "error_count": 0,
            "responses": []
        }
        
        start_time = time.time()
        success_count = 0
        
        for case in test_cases:
            case_start = time.time()
            response = ""
            try:
                async for chunk in chat.stream_chat(case):
                    if chunk.startswith("Error:"):
                        results["error_count"] += 1
                        response = chunk
                        break
                    response += chunk
                
                if not response.startswith("Error:"):
                    success_count += 1
                    
                results["responses"].append({
                    "input": case,
                    "output": response,
                    "time": time.time() - case_start
                })
                
            except Exception as e:
                results["error_count"] += 1
                results["responses"].append({
                    "input": case,
                    "error": str(e),
                    "time": time.time() - case_start
                })
                
        total_time = time.time() - start_time
        results["total_time"] = total_time
        results["success_rate"] = success_count / len(test_cases)
        results["avg_response_time"] = total_time / len(test_cases)
        
        return results

class ChatFactory:
    """聊天工厂类"""
    
    @staticmethod
    def create_chat(chat_type: Optional[str] = None) -> BaseChat:
        """
        创建聊天实例
        Args:
            chat_type: 聊天类型 ('deepseek', 'ernie' 或 'ollama')
        Returns:
            BaseChat: 聊天实例
        """
        if chat_type is None:
            chat_type = os.getenv('CHAT_TYPE', 'deepseek')
            
        chat_type = chat_type.lower()
        
        if chat_type == 'ernie':
            return ErnieChat()
        elif chat_type == 'deepseek':
            return DeepSeekChat()
        elif chat_type == 'ollama':
            return OllamaChat()
        else:
            raise ValueError(f"不支持的聊天类型: {chat_type}")
            
    @staticmethod
    async def evaluate_models(test_cases: List[str] = None) -> Dict:
        """评估所有支持的聊天模型"""
        if test_cases is None:
            test_cases = [
                "你好，请介绍一下你自己。",
                "What is the capital of France?",
                "解释一下量子计算的基本原理。",
                "Write a short poem about spring.",
                "计算 123 + 456 的结果。"
            ]
            
        results = {}
        
        # 评估 DeepSeek
        try:
            deepseek = DeepSeekChat()
            results["deepseek"] = await ChatEvaluator.evaluate_model(deepseek, test_cases)
            await deepseek.close()
        except Exception as e:
            logger.error(f"DeepSeek 评估失败: {str(e)}")
            results["deepseek"] = {"error": str(e)}
            
        # 评估文心一言
        try:
            ernie = ErnieChat()
            results["ernie"] = await ChatEvaluator.evaluate_model(ernie, test_cases)
            await ernie.close()
        except Exception as e:
            logger.error(f"文心一言评估失败: {str(e)}")
            results["ernie"] = {"error": str(e)}
            
        return results

# 测试代码
async def test_evaluation():
    """运行评估测试"""
    print("开始评估聊天模型...")
    
    test_cases = [
        "你好，请介绍一下你自己。",
        "What is the capital of France?",
        "解释一下量子计算的基本原理。",
        "Write a short poem about spring.",
        "计算 123 + 456 的结果。"
    ]
    
    results = await ChatFactory.evaluate_models(test_cases)
    
    print("\n评估结果:")
    for model, result in results.items():
        print(f"\n{model.upper()} 模型:")
        if "error" in result:
            print(f"评估失败: {result['error']}")
            continue
            
        print(f"总耗时: {result['total_time']:.2f} 秒")
        print(f"成功率: {result['success_rate']*100:.1f}%")
        print(f"平均响应时间: {result['avg_response_time']:.2f} 秒")
        print(f"错误次数: {result['error_count']}")
        
        print("\n详细响应:")
        for i, response in enumerate(result['responses']):
            print(f"\n测试用例 {i+1}:")
            print(f"输入: {response['input']}")
            if 'error' in response:
                print(f"错误: {response['error']}")
            else:
                print(f"输出: {response['output']}")
            print(f"耗时: {response['time']:.2f} 秒")

if __name__ == "__main__":
    asyncio.run(test_evaluation()) 