# -*- coding: utf-8 -*-
"""
音频提取模块

从视频文件中提取音频，支持多种视频格式
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple


class AudioExtractor:
    """音频提取器"""
    
    SUPPORTED_VIDEO_FORMATS = ['.mp4', '.avi', '.mkv', '.mov', '.flv', '.wmv', '.webm']
    DEFAULT_SAMPLE_RATE = 16000  # Whisper 推荐 16kHz
    
    def __init__(self, ffmpeg_path: Optional[str] = None):
        """
        初始化音频提取器
        
        Args:
            ffmpeg_path: ffmpeg 可执行文件路径，None 则自动查找
        """
        self.ffmpeg_path = ffmpeg_path or self._find_ffmpeg()
        self._check_ffmpeg()
    
    def _find_ffmpeg(self) -> str:
        """查找 ffmpeg 可执行文件"""
        # 首先检查环境变量
        import shutil
        ffmpeg = shutil.which('ffmpeg')
        if ffmpeg:
            return ffmpeg
        
        # 检查常见安装路径
        common_paths = [
            r'C:\ffmpeg\bin\ffmpeg.exe',
            r'C:\Program Files\ffmpeg\bin\ffmpeg.exe',
            r'C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe',
            '/usr/bin/ffmpeg',
            '/usr/local/bin/ffmpeg',
            '/opt/homebrew/bin/ffmpeg',
        ]
        
        for path in common_paths:
            if os.path.isfile(path):
                return path
        
        raise RuntimeError(
            "未找到 ffmpeg，请安装 ffmpeg 并添加到系统 PATH\n"
            "下载地址: https://ffmpeg.org/download.html"
        )
    
    def _check_ffmpeg(self):
        """检查 ffmpeg 是否可用"""
        try:
            result = subprocess.run(
                [self.ffmpeg_path, '-version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                raise RuntimeError("ffmpeg 检查失败")
        except Exception as e:
            raise RuntimeError(f"ffmpeg 检查失败: {e}")
    
    def extract_audio(
        self,
        video_path: str,
        output_path: Optional[str] = None,
        sample_rate: int = DEFAULT_SAMPLE_RATE
    ) -> str:
        """
        从视频中提取音频
        
        Args:
            video_path: 视频文件路径
            output_path: 输出音频路径，None 则使用临时文件
            sample_rate: 采样率，默认 16kHz
            
        Returns:
            输出音频文件路径
        """
        video_path = Path(video_path)
        
        if not video_path.exists():
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        if video_path.suffix.lower() not in self.SUPPORTED_VIDEO_FORMATS:
            raise ValueError(f"不支持的格式: {video_path.suffix}")
        
        # 确定输出路径
        if output_path is None:
            temp_dir = tempfile.gettempdir()
            output_path = os.path.join(
                temp_dir,
                f"{video_path.stem}_{sample_rate}hz.wav"
            )
        
        # ffmpeg 命令
        cmd = [
            self.ffmpeg_path,
            '-i', str(video_path),           # 输入文件
            '-vn',                            # 不处理视频
            '-acodec', 'pcm_s16le',          # PCM 16位编码
            '-ac', '1',                       # 单声道
            '-ar', str(sample_rate),          # 采样率
            '-y',                             # 覆盖输出
            output_path
        ]
        
        # 执行提取
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"音频提取失败: {result.stderr}")
            
            return output_path
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("音频提取超时")
        except Exception as e:
            raise RuntimeError(f"音频提取失败: {e}")
    
    def get_video_info(self, video_path: str) -> dict:
        """
        获取视频信息
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            视频信息字典
        """
        cmd = [
            self.ffmpeg_path,
            '-i', video_path
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        # ffmpeg 将信息输出到 stderr
        info_text = result.stderr
        
        info = {
            'duration': None,
            'bitrate': None,
            'video_codec': None,
            'audio_codec': None,
            'resolution': None,
        }
        
        # 解析时长
        import re
        duration_match = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', info_text)
        if duration_match:
            h, m, s = duration_match.groups()
            info['duration'] = int(h) * 3600 + int(m) * 60 + float(s)
        
        # 解析分辨率
        resolution_match = re.search(r'(\d+)x(\d+)', info_text)
        if resolution_match:
            info['resolution'] = f"{resolution_match.group(1)}x{resolution_match.group(2)}"
        
        return info
    
    def cleanup(self, audio_path: str):
        """清理临时音频文件"""
        try:
            if os.path.exists(audio_path):
                os.remove(audio_path)
        except Exception:
            pass
