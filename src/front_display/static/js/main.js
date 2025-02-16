// 全局状态管理
const state = {
    ws: null,
    stream: null,
    mediaRecorder: null,
    isRecording: false,
    audioChunks: [],
    currentChatStream: true,
    isStopped: false,
    currentResponse: '',
    audioQueue: [],
    isPlayingAudio: false
};

// 停止所有音频播放
function stopAllAudio() {
    if (state.currentSource) {
        try {
            state.currentSource.stop();
            state.currentSource.disconnect();
        } catch (e) {
            console.log('Audio source already stopped')
        }
    }
    
    if (state.currentAudioContext) {
        state.currentAudioContext.close().catch(console.error);
    }
    
    state.currentSource = null;
    state.currentAudioContext = null;
    state.isPlaying = false;
}

// 播放音频队列
async function playNextAudio() {
    if (state.audioQueue.length === 0 || state.isPlayingAudio) {
        return;
    }
    
    state.isPlayingAudio = true;
    const audioBlob = state.audioQueue.shift();
    const audioUrl = URL.createObjectURL(audioBlob);
    const audio = new Audio(audioUrl);
    
    audio.onended = () => {
        state.isPlayingAudio = false;
        URL.revokeObjectURL(audioUrl);
        playNextAudio();  // 播放下一个
    };
    
    try {
        await audio.play();
    } catch (error) {
        console.error('播放音频失败:', error);
        state.isPlayingAudio = false;
        playNextAudio();  // 尝试播放下一个
    }
}

// 添加消息到对话框
function addMessage(message, type) {
    const chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) {
        console.error('找不到聊天消息容器');
        return;
    }
    
    // 创建新消息元素
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type === 'user' ? 'user-message' : 'ai-message'}`;
    
    // 如果是AI消息，进行格式化处理
    if (type === 'chat') {
        // 分段处理
        const paragraphs = message.split(/(?=[#]{3}|[*]{2})/);
        
        paragraphs.forEach(paragraph => {
            // 创建段落元素
            const p = document.createElement('p');
            
            // 处理标题 (###)
            if (paragraph.startsWith('###')) {
                p.className = 'section-title';
                p.textContent = paragraph.replace(/^###\s*/, '');
            }
            // 处理小标题 (**)
            else if (paragraph.startsWith('**')) {
                p.className = 'sub-title';
                p.textContent = paragraph.replace(/^\*\*|\*\*$/g, '');
            }
            // 普通文本
            else {
                p.className = 'content';
                p.textContent = paragraph.trim();
            }
            
            messageDiv.appendChild(p);
        });
    } else {
        messageDiv.textContent = message;
    }
    
    // 添加到消息容器
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 初始化 WebSocket
function initWebSocket() {
    state.ws = new WebSocket(`ws://${window.location.host}/ws`);
    
    state.ws.onmessage = async function(event) {
        // 处理二进制数据（音频）
        if (event.data instanceof Blob) {
            state.audioQueue.push(event.data);
            playNextAudio();
            return;
        }

        // 处理文本数据（JSON）
        try {
            const data = JSON.parse(event.data);
            
            switch(data.type) {
                case 'image':
                    // 显示生成的图像
                    const imagePreview = document.getElementById('generated-image');
                    imagePreview.src = `data:image/png;base64,${data.data}`;
                    imagePreview.style.display = 'block';
                    break;
                    
                case 'transcription':
                    // 显示用户输入
                    addMessage(data.message, 'user');
                    break;
                    
                case 'chat':
                    // 显示AI响应
                    if (!document.querySelector('.ai-message:last-child')) {
                        addMessage(data.message, 'chat');
                    } else {
                        const lastMessage = document.querySelector('.ai-message:last-child');
                        lastMessage.textContent += data.message;
                    }
                    break;
                    
                case 'error':
                    console.error(data.message);
                    addMessage(`Error: ${data.message}`, 'error');
                    break;
            }
        } catch (e) {
            console.error('Error processing message:', e);
        }
    };
    
    state.ws.onerror = function(error) {
        console.error('WebSocket error:', error);
        addMessage('Connection error occurred', 'error');
    };
    
    state.ws.onclose = function() {
        console.log('WebSocket connection closed');
        setTimeout(initWebSocket, 1000);
    };
}

// 初始化音频设备
async function initAudioDevice() {
    try {
        state.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        console.log("音频设备初始化成功");
        return state.stream;
    } catch (error) {
        console.error('音频设备初始化失败:', error);
        alert('无法访问麦克风，请检查权限设置');
        return null;
    }
}

// 终止当前对话
async function terminateCurrentChat() {
    if (state.ws && state.ws.readyState === WebSocket.OPEN) {
        state.ws.send(JSON.stringify({ type: 'stop' }));
    }
    state.isStopped = true;
    state.currentChatStream = false;
}

// 开始新录音
async function startRecording() {
    console.log("开始新录音");
    
    // 1. 终止当前对话
    await terminateCurrentChat();
    
    // 2. 重置状态
    state.isStopped = false;
    state.currentChatStream = true;
    state.audioChunks = [];
    
    try {
        // 3. 初始化音频设备（如果还没有初始化）
        if (!state.stream) {
            const stream = await initAudioDevice();
            if (!stream) return;
        }
        
        // 4. 创建新的 MediaRecorder
        state.mediaRecorder = new MediaRecorder(state.stream);
        
        // 5. 设置数据处理
        state.mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                state.audioChunks.push(event.data);
            }
        };
        
        // 6. 设置停止处理
        state.mediaRecorder.onstop = () => {
            if (!state.isStopped && state.audioChunks.length > 0) {
                const audioBlob = new Blob(state.audioChunks, { type: 'audio/wav' });
                if (state.ws && state.ws.readyState === WebSocket.OPEN) {
                    state.ws.send(audioBlob);
                }
            }
            state.audioChunks = [];
        };
        
        // 7. 开始录音
        state.mediaRecorder.start();
        state.isRecording = true;
        console.log("录音已开始");
        
    } catch (error) {
        console.error('开始录音时出错:', error);
        alert('无法启动录音，请检查麦克风权限');
    }
}

// 停止录音
function stopRecording() {
    console.log("停止录音");
    if (!state.isRecording) return;
    
    state.isRecording = false;
    if (state.mediaRecorder && state.mediaRecorder.state === 'recording') {
        state.mediaRecorder.stop();
    }
}

// 发送音频数据
async function sendAudioData(audioData) {
    if (state.ws && state.ws.readyState === WebSocket.OPEN) {
        try {
            // 确保发送的是 Blob 数据
            if (!(audioData instanceof Blob)) {
                audioData = new Blob([audioData], { type: 'audio/wav' });
            }
            state.ws.send(audioData);
        } catch (error) {
            console.error('Error sending audio data:', error);
        }
    }
}

// 添加图像生成函数
function generateScene() {
    const sceneInput = document.getElementById('scene-input');
    const description = sceneInput.value.trim();
    
    if (description && state.ws && state.ws.readyState === WebSocket.OPEN) {
        state.ws.send(JSON.stringify({
            type: 'text',
            text: description
        }));
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', async function() {
    console.log("页面加载完成，初始化功能");
    
    initWebSocket();
    await initAudioDevice();
    addMessage('您好，我是您的AI助手，请按住按钮开始对话。', 'ai-message');
    
    const voiceButton = document.getElementById('voice-button');
    
    // 按下按钮开始录音
    voiceButton.addEventListener('mousedown', async function(e) {
        e.preventDefault();
        console.log("按下语音按钮");
        await startRecording();
        this.textContent = '松开结束对话';
        this.classList.add('recording');
    });
    
    // 松开按钮结束录音
    voiceButton.addEventListener('mouseup', function(e) {
        e.preventDefault();
        console.log("松开语音按钮");
        stopRecording();
        this.textContent = '按住开始对话';
        this.classList.remove('recording');
    });
    
    // 鼠标移出按钮时也要结束录音
    voiceButton.addEventListener('mouseleave', function(e) {
        if (state.isRecording) {
            console.log("鼠标移出按钮，结束录音");
            stopRecording();
            this.textContent = '按住开始对话';
            this.classList.remove('recording');
        }
    });
});