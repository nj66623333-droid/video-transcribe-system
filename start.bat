@echo off
title 视频转录系统 v2.3
echo ========================================
echo  视频转录系统 v2.3
echo  基于 Whisper + Ollama 的本地转录工具
echo  [已内置 FFmpeg + 依赖包]
echo ========================================
echo.
echo 正在启动...
set PYTHONPATH=portable_lib;%PYTHONPATH%
python gui.py
if %errorlevel% neq 0 (
    echo.
    echo [错误] 请确保已安装 Python 3.10+
    pause
)
