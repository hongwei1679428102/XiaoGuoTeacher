# AI Voice Assistant Project

一个基于 Python 的智能语音助手项目，支持实时语音对话、图像生成和场景交互。

## 功能特点

- 🎙️ **实时语音对话**
  - 支持按住说话，松开自动识别
  - 流式语音识别，实时显示对话内容
  - 自然的语音合成回复
  - 使用 SenseVoice 进行语音识别
  - 使用 Kokoro 进行语音合成

- 🎨 **AI 图像生成**
  - 支持文本生成图像
  - 场景描述自动可视化
  - 图像变体生成

- 🤖 **智能对话**
  - 基于 DeepSeek 的对话模型
  - 上下文理解和连续对话
  - 自然流畅的对话体验

## 技术栈

- 前端：HTML5, JavaScript, WebSocket
- 后端：Python, FastAPI
- AI 模型：DeepSeek, SenseVoice
- 语音处理：KokoroTTS
- 图像生成：DALL-E 3

## 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/yourusername/ai-voice-assistant.git
cd ai-voice-assistant
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置环境变量**
创建 `.env` 文件并配置以下变量：
```bash
OPENAI_API_KEY=your_openai_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
SENSE_VOICE_KEY=your_sensevoice_key
```

## 运行项目

1. **命令行模式**
```bash
python run_symbol.py
```
- 按住 Option/Alt 键开始录音
- 松开键结束录音
- 等待 AI 回复

2. **Web 界面模式**
```bash
python run.py
```
- 打开浏览器访问：`http://localhost:8000`
- 点击并按住"按住开始对话"按钮进行对话
- 在场景设置区域可以生成 AI 图片

## 使用说明

1. **语音对话**
   - 点击并按住"按住开始对话"按钮
   - 对着麦克风说话
   - 松开按钮后等待 AI 回复
   - AI 会通过语音和文字同时回复

2. **场景生成**
   - 在左侧文本框中描述想要的场景
   - 点击"生成场景"按钮
   - 等待图片生成并显示

## 系统要求

- Python 3.8+
- 现代浏览器（支持 WebSocket）
- 麦克风设备
- 网络连接

## 常见问题

1. **麦克风权限**
   - 确保浏览器有麦克风访问权限
   - 检查系统麦克风设置

2. **音频问题**
   - 确保系统音量正常
   - 检查默认音频输入/输出设备

3. **连接问题**
   - 检查网络连接
   - 确保环境变量配置正确

## 项目结构

```
ai-voice-assistant/
├── src/
│   ├── audio/              # 音频处理模块
│   ├── chat/              # 对话模型接口
│   ├── front_display/     # Web 前端界面
│   ├── image_generation/  # 图像生成模块
│   └── transcription/     # 语音识别模块
├── run.py                 # Web 模式启动脚本
├── run_symbol.py          # 命令行模式启动脚本
└── requirements.txt       # 项目依赖
```

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交 Issue 或 Pull Request。

