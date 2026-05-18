@echo off
chcp 65001 >nul
title 视频转录系统 v2.3
echo ========================================
echo  视频转录系统 v2.3
echo  基于 Whisper + Ollama 的本地转录工具
echo ========================================
echo.
echo 正在启动...
python gui.py
if %errorlevel% neq 0 (
    echo.
    echo [错误] 启动失败，请确保已安装 Python 3.10+
    pause
)
