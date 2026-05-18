# 视频转录系统

> 基于 Whisper + Ollama 的本地视频/音频转录与 AI 智能增强工具

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Whisper](https://img.shields.io/badge/Whisper-local-brightgreen)](https://github.com/openai/whisper)

## 📋 项目简介

视频转录系统是一款完全离线的本地视频/音频转文字工具，支持：

- 🎙️ **本地语音识别** - 基于 OpenAI Whisper，无需网络
- 🤖 **AI 智能增强** - 基于 Ollama 本地大模型，四步精修推理链
- 🔒 **完全离线** - 所有处理在本地完成，保护隐私安全
- 📝 **多格式输出** - 支持 TXT / SRT / JSON / Markdown / Obsidian

## ✨ 核心功能

### 语音识别

| 模型 | 速度 | 精度 | 推荐场景 |
|------|------|------|----------|
| tiny | ⚡ 最快 | 较低 | 实时测试 |
| base | 🚀 快 | 良好 | **日常推荐** |
| small | 🔄 适中 | 较好 | 质量要求较高 |
| medium | 🐢 较慢 | 最佳 | 专业场景 |

### AI 四步精修推理链

1. **格式化与基础修复** - 修正标点、分段、去除语气词
2. **逻辑重构与精炼** - 识别核心论点，重组逻辑结构
3. **风格与语气润色** - 根据目标听众调整语言风格
4. **最终审校** - 质量控制与完善

### 支持的文件格式

| 类型 | 格式 |
|------|------|
| 🎬 视频 | MP4 / AVI / MKV / MOV |
| 🎵 音频 | MP3 / WAV / M4A / AAC / OGG / FLAC |

> 音频文件无需视频提取步骤，直接转录，速度更快。

### 输出格式

- 📄 TXT 纯文本
- 🎬 SRT 字幕文件
- 📊 JSON 结构化数据
- 📝 Markdown 笔记
- 🗂️ Obsidian 知识库

## 🚀 快速开始

### 🧰 前置环境要求

#### 1️⃣ Python 3.10+

```bash
# 下载安装
https://www.python.org/downloads/windows/

# 安装时务必勾选 "Add Python to PATH"

# 验证安装
python --version
```

#### 2️⃣ FFmpeg（音视频处理核心，必须安装）

```bash
# 下载链接（选 Windows builds → ffmpeg-master-latest-win64-gpl.zip）
https://github.com/BtbN/FFmpeg-Builds/releases

# 安装步骤：
# 1. 解压到 C:\ffmpeg
# 2. 将 C:\ffmpeg\bin 添加到系统环境变量 PATH
# 3. 验证：打开 CMD 运行 `ffmpeg -version`
```

#### 3️⃣ Ollama（本地 AI 增强，可选）

```bash
# 下载安装
https://ollama.com/download

# 启动服务
ollama serve

# 下载推荐模型（约 2GB）
ollama pull gemma4

# 验证：ollama list 查看已下载模型
```

#### 4️⃣ 注册云端 API（可选，替代 Ollama）

| 提供商 | 注册链接 | 特点 | 推荐模型 |
|--------|---------|------|---------|
| **硅基流动** (推荐) | https://siliconflow.cn | 赠送 ￥14 额度，免费量大 | Qwen2.5-72B-Instruct |
| **DeepSeek** | https://platform.deepseek.com | 价格便宜 | deepseek-chat |
| **Moonshot (Kimi)** | https://platform.moonshot.cn | 中文优化 | kimi-k2.5 |

> 注册后获取 API Key，在 GUI 的 AI 提供商设置中填入即可。

### 📦 安装依赖

```bash
pip install -r requirements.txt
```

> ⚠️ 首次安装会下载 PyTorch + Whisper 模型（约 1-2GB），请耐心等待。
> 全程需要网络连接，后续离线可用。

### ▶️ 运行

```bash
# 方式一：双击 start.bat（Windows）
python src/gui/main.py
```

### ✅ 环境验证清单

```
□ Python 3.10+          → python --version
□ FFmpeg               → ffmpeg -version
□ pip 依赖              → pip list | findstr whisper
□ Ollama（可选）        → ollama --version
□ API Key（可选）       → 已在 GUI 中填入
```


## ⏱️ 处理速度参考

实际速度取决于硬件配置、模型大小和文本长度，以下为实际测试参考（约10-15分钟视频）：

| 场景 | 大概耗时 | 说明 |
|------|---------|------|
| 🌐 硅基流动（Qwen2.5） | ~9 分钟 | 含转录+四步精修+摘要，速度较快 |
| 💻 本地 Ollama（gemma4） | ~19 分钟 | 比云端慢约 10 分钟，适合离线场景 |
| 🎙️ 仅转录（关闭AI增强） | ~2 分钟 | 只跑 Whisper base 模型 |

> 可关闭不需要的 AI 步骤（摘要/关键词）来提速。


## 📖 使用教程

1. **选择文件** - 点击"📄 文件"选择视频（MP4/AVI/MKV/MOV）或音频（MP3/WAV/M4A/AAC/OGG/FLAC）；
   点击"📁 文件夹"批量处理整个目录
2. **选择转录模型** - 根据需要选择速度/精度
3. **配置 AI 增强** - 自定义逻辑重构和风格润色选项
4. **开始处理** - 点击"开始处理"等待完成
5. **查看结果** - 在 output 目录查看转录结果

## ⚙️ 配置说明

### AI 增强选项

| 选项 | 说明 | 默认 |
|------|------|------|
| 修复标点 | 自动修正中英文标点错误 | ✅ |
| 添加分段 | 根据语义自动分段 | ✅ |
| 去除语气词 | 删除"嗯""啊"等口语词 | ✅ |
| 逻辑重构 | 识别核心论点，重组结构 | ✅ |
| 风格润色 | 根据目标受众调整语言风格 | ✅ |
| 目标听众 | 指定听众群体 | 普通大众 |
| 语气风格 | 指定表达语气 | 专业、清晰 |
| 生成摘要 | 自动生成内容摘要 | ❌ |
| 提取关键词 | 自动提取核心关键词 | ❌ |

### 输出路径

默认输出到 `output/` 目录，可在界面中自定义。

## 🏗️ 项目结构

```
video-transcribe-project/
├── src/
│   ├── core/           # 核心模块
│   │   ├── ai_enhancer.py       # AI 增强（四步精修推理链）
│   │   ├── audio_extractor.py   # 音频提取
│   │   ├── transcriber.py       # Whisper 语音识别
│   │   ├── obsidian_exporter.py # Obsidian 导出
│   │   └── pipeline.py          # 完整处理流水线
│   └── gui/            # 图形界面
│       ├── app.py                # GUI 主类
│       └── main.py               # 入口
├── requirements.txt    # Python 依赖
└── README.md           # 本文件
```

## 🛠️ 技术栈

- **语音识别**: [OpenAI Whisper](https://github.com/openai/whisper)
- **AI 增强**: [Ollama](https://ollama.com/) + 本地大模型
- **GUI**: Python Tkinter
- **音视频**: FFmpeg

## 📄 许可证

本项目仅供个人学习交流使用。

## ⚠️ 免责声明

- 本软件为个人开发，仅供学习交流
- 不提供任何形式的技术支持
- 使用过程中产生的任何问题由使用者自行承担
