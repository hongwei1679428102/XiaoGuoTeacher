import time
from src.audio.recorder import AudioRecorder
from src.transcription.senseVoiceSmall import SenseVoiceSmallProcessor
from src.chat.deepseek import DeepSeekChat
from src.audio.text_to_speech import KokoroTTS
import sounddevice as sd
import numpy as np
from pynput import keyboard
from src.chat.stream_chat import StreamChat
from src.chat.chat_factory import ChatFactory
import os
# from src.audio.text_to_speech import KokoroTTS
# from src.llm.symbol import test

# from src.llm.translate import test
# from src.chat.deepseek import test
# from src.transcription.senseVoiceSmall import test
# from src.audio.recorder import test

class VoiceAssistant:
    def __init__(self):
        self.recorder = AudioRecorder()
        self.senseVoiceSmall = SenseVoiceSmallProcessor()
        
        # 使用工厂类创建聊天实例
        chat_type = os.getenv('CHAT_TYPE', 'deepseek')
        self.chat = ChatFactory.create_chat(chat_type)
        
        self.tts = KokoroTTS()
        self.is_recording = False
        self.stream_chat = StreamChat()
        
    def on_press(self, key):
        """按键按下时的回调"""
        try:
            if key == keyboard.Key.alt and not self.is_recording:
                print("\n开始录音...")
                self.is_recording = True
                self.start_time = time.time()
                self.recorder.start_recording()
        except AttributeError:
            pass

    async def on_release(self, key):
        """按键释放时的回调"""
        try:
            if key == keyboard.Key.esc:
                # Stop listener
                return False
            
            if key == keyboard.Key.enter:
                result = self.recognizer.recognize()
                print("语音识别结果:", result)
                
                # 修改这里的流式处理
                async for response in self.stream_chat.stream_chat(result):
                    print("AI回复:", response)
                    
        except Exception as e:
            print(f"Error: {str(e)}")

    def run(self):
        """运行语音助手"""
        print("语音助手已启动，按住 Option/Alt 键开始录音，松开键结束录音...")
        
        # 监听键盘事件
        with keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release) as listener:
            listener.join()

if __name__ == "__main__":
    assistant = VoiceAssistant()
    assistant.run()
