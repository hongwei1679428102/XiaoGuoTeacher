from fastapi import FastAPI, WebSocket, Request, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
import uvicorn
import json
import asyncio
import io
import os
from pathlib import Path
from dotenv import load_dotenv
import traceback
from src.agent.agent_handler import AgentHandler

# 获取项目根目录
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

# 加载环境变量
env_path = ROOT_DIR / '.env'
load_dotenv(env_path, override=True)  # 添加 override=True 强制重新加载

# 打印环境变量加载信息
print("\n=== 环境变量加载信息 ===")
print(f"环境变量文件路径: {env_path}")
print(f"文件是否存在: {env_path.exists()}")
print(f"CHAT_TYPE: {os.getenv('CHAT_TYPE')}")
print(f"OLLAMA_BASE_URL: {os.getenv('OLLAMA_BASE_URL')}")
print("=====================\n")

# 获取当前文件所在目录
BASE_DIR = Path(__file__).resolve().parent

# 修改导入路径
import sys
sys.path.append(str(ROOT_DIR))

# 修改导入语句
from src.audio.recorder import AudioRecorder
from src.transcription.senseVoiceSmall import SenseVoiceSmallProcessor
from src.chat.chat_factory import ChatFactory
from src.audio.text_to_speech import KokoroTTS

# 确保目录存在
static_dir = BASE_DIR / "static"
templates_dir = BASE_DIR / "templates"
static_dir.mkdir(parents=True, exist_ok=True)
templates_dir.mkdir(parents=True, exist_ok=True)

app = FastAPI()

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 设置模板
templates = Jinja2Templates(directory=str(templates_dir))

# 存储活动的 WebSocket 连接
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

manager = ConnectionManager()

@app.get("/")
async def get(request: Request):
    """返回主页"""
    try:
        # 确保模板目录存在
        if not templates_dir.exists():
            templates_dir.mkdir(parents=True, exist_ok=True)
            
        # 确保 index.html 存在
        index_path = templates_dir / "index.html"
        if not index_path.exists():
            # 如果不存在，运行设置脚本创建文件
            from .setup import setup_front_display
            setup_front_display()
            
        # 使用模板渲染
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "url_for": app.url_path_for  # 传递 url_for 函数给模板
            }
        )
    except Exception as e:
        print(f"Error serving index.html: {e}")
        traceback.print_exc()
        return HTMLResponse(
            content=f"Error loading template: {str(e)}",
            status_code=500
        )

@app.get("/static/{file_path:path}")
async def serve_static(file_path: str):
    """提供静态文件服务"""
    return FileResponse(static_dir / file_path)

@app.get("/debug")
async def debug():
    """返回调试信息"""
    try:
        static_files = list(static_dir.rglob("*"))
        template_files = list(templates_dir.rglob("*"))
        
        return {
            "base_dir": str(BASE_DIR),
            "static_dir": str(static_dir),
            "templates_dir": str(templates_dir),
            "static_exists": static_dir.exists(),
            "templates_exists": templates_dir.exists(),
            "static_files": [str(f.relative_to(static_dir)) for f in static_files if f.is_file()],
            "template_files": [str(f.relative_to(templates_dir)) for f in template_files if f.is_file()]
        }
    except Exception as e:
        traceback.print_exc()
        return {"error": str(e)}

@app.get("/favicon.ico")
async def favicon():
    return FileResponse(str(static_dir / "favicon.ico"))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """处理 WebSocket 连接"""
    chat = None
    agent = AgentHandler()
    current_task = None
    is_connected = True
    
    try:
        # 初始化组件
        sense_voice = SenseVoiceSmallProcessor()
        tts = KokoroTTS()
        
        # 重新加载环境变量
        load_dotenv(env_path, override=True)
        
        # 从环境变量获取聊天类型
        chat_type = os.getenv("CHAT_TYPE", "deepseek").lower().strip()
        chat_type = chat_type.split('#')[0].strip()  # 移除可能的注释
        
        print("\n=== 创建聊天模型 ===")
        print(f"当前工作目录: {os.getcwd()}")
        print(f"环境变量 CHAT_TYPE: {os.getenv('CHAT_TYPE')}")
        print(f"使用的聊天类型: {chat_type}")
        
        try:
            chat = ChatFactory.create_chat(chat_type)
            print(f"成功创建聊天模型: {chat.__class__.__name__}")
        except Exception as e:
            print(f"创建聊天模型失败: {str(e)}")
            traceback.print_exc()
            print("使用默认的 DeepSeek 模型")
            chat = ChatFactory.create_chat("deepseek")
        
        print("环境变量内容:")
        print(f"CHAT_TYPE: {os.getenv('CHAT_TYPE')}")
        print(f"OLLAMA_BASE_URL: {os.getenv('OLLAMA_BASE_URL')}")
        
        await manager.connect(websocket)
        print("WebSocket connected")
        
        while True:
            try:
                message = await websocket.receive()
                
                # 处理音频数据
                if "bytes" in message:
                    print("Processing audio data...")
                    received_audio_data = message["bytes"]
                    
                    # 取消之前的任务
                    if current_task and not current_task.done():
                        current_task.cancel()
                        try:
                            await current_task
                        except asyncio.CancelledError:
                            pass
                    
                    # 确保聊天客户端就绪
                    if hasattr(chat, '_ensure_client'):
                        await chat._ensure_client()
                    
                    async def process_audio_task(audio_data):
                        try:
                            audio_buffer = io.BytesIO(audio_data)
                            result, error = sense_voice.process_audio(audio_buffer)
                            
                            if error:
                                print(f"Audio processing error: {error}")
                                await websocket.send_json({
                                    "type": "error",
                                    "message": str(error)
                                })
                                return
                            
                            if result:
                                print(f"Transcription result: {result}")
                                await websocket.send_json({
                                    "type": "transcription",
                                    "message": result
                                })
                                
                                print("Starting chat response...")
                                current_response = ""
                                sentence_buffer = ""
                                
                                try:
                                    print("Sending request to chat API...")
                                    async for response in chat.stream_chat(result):
                                        print(f"Got response chunk: {response}")
                                        
                                        if not is_connected:
                                            print("WebSocket disconnected during chat")
                                            break
                                            
                                        if response:
                                            if response.startswith("Error:"):
                                                print(f"Chat error: {response}")
                                                await websocket.send_json({
                                                    "type": "error",
                                                    "message": response
                                                })
                                                break
                                                
                                            print(f"Processing response chunk: {response}")
                                            current_response += response
                                            sentence_buffer += response
                                            
                                            if any(char in response for char in '.!?。！？'):
                                                print(f"Sending complete sentence: {sentence_buffer}")
                                                try:
                                                    await websocket.send_json({
                                                        "type": "chat",
                                                        "message": sentence_buffer
                                                    })
                                                except Exception as e:
                                                    print(f"Error sending chat message: {e}")
                                                    break
                                                    
                                                try:
                                                    tts_audio = tts.speak(sentence_buffer)
                                                    if tts_audio and is_connected:
                                                        print("Sending audio response")
                                                        await websocket.send_bytes(tts_audio[0])
                                                except Exception as e:
                                                    print(f"TTS error: {e}")
                                                    
                                                sentence_buffer = ""
                                                
                                except Exception as e:
                                    print(f"Chat error: {e}")
                                    traceback.print_exc()
                                    try:
                                        await websocket.send_json({
                                            "type": "error",
                                            "message": f"Chat error: {str(e)}"
                                        })
                                    except Exception as send_error:
                                        print(f"Error sending error message: {send_error}")
                            else:
                                print("No transcription result")
                                
                        except Exception as e:
                            print(f"Error in process_audio_task: {e}")
                            traceback.print_exc()
                    
                    current_task = asyncio.create_task(process_audio_task(received_audio_data))
                    try:
                        await current_task
                    except asyncio.CancelledError:
                        print("Audio processing task cancelled")
                
                # 处理文本消息
                elif "text" in message:
                    try:
                        # 只处理有效的 JSON 消息
                        data = json.loads(message["text"])
                        if not isinstance(data, dict):  # 确保是 JSON 对象
                            continue
                            
                        # 处理停止命令
                        if data.get("type") == "stop":
                            if chat:
                                chat.stop_streaming()
                            if current_task and not current_task.done():
                                current_task.cancel()
                            continue
                            
                        # 处理其他文本消息
                        result = await agent.handle_request(data.get("text", ""))
                        
                        if result["type"] == "image":
                            await websocket.send_json({
                                "type": "image",
                                "data": result["data"],
                                "description": result["description"]
                            })
                        else:
                            # 继续现有的聊天处理
                            async for response in chat.stream_chat(result["content"]):
                                await websocket.send_json({
                                    "type": "chat",
                                    "message": response
                                })
                    except json.JSONDecodeError:
                        # 忽略无效的 JSON 消息
                        continue
                
            except WebSocketDisconnect:
                print("WebSocket disconnected")
                is_connected = False
                break
            except Exception as e:
                print(f"Error in websocket loop: {e}")
                traceback.print_exc()
                if "Cannot call \"receive\" once a disconnect" in str(e):
                    is_connected = False
                    break
                
    finally:
        print("Cleaning up resources...")
        if current_task and not current_task.done():
            current_task.cancel()
            try:
                await current_task
            except asyncio.CancelledError:
                pass
        
        if chat:
            await chat.close()
            
        manager.disconnect(websocket)
        try:
            await websocket.close()
        except Exception as e:
            print(f"Error closing websocket: {e}")
            
        print("WebSocket connection cleaned up")

if __name__ == "__main__":
    # 打印调试信息
    print(f"Base directory: {BASE_DIR}")
    print(f"Static directory: {static_dir}")
    print(f"Templates directory: {templates_dir}")
    
    # 启动服务器，使用 websockets 后端
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        ws='websockets'
    ) 