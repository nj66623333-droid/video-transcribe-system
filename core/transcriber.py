# -*- coding: utf-8 -*-
"""
语音识别模块

使用 Whisper 模型进行语音转文字
"""

import os
import warnings
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
import json

# 忽略 torch 的 FutureWarning
warnings.filterwarnings('ignore', category=FutureWarning)


class WhisperTranscriber:
    """Whisper 语音识别器"""
    
    AVAILABLE_MODELS = {
        'tiny': {'size': '39 MB', 'speed': '~10x', 'accuracy': '一般'},
        'base': {'size': '74 MB', 'speed': '~7x', 'accuracy': '良好'},
        'small': {'size': '244 MB', 'speed': '~4x', 'accuracy': '较好'},
        'medium': {'size': '769 MB', 'speed': '~2x', 'accuracy': '优秀'},
        'large': {'size': '1550 MB', 'speed': '1x', 'accuracy': '最佳'},
    }
    
    def __init__(
        self,
        model_name: str = 'base',
        device: Optional[str] = None,
        download_root: Optional[str] = None
    ):
        """
        初始化 Whisper 转录器
        
        Args:
            model_name: 模型名称 (tiny/base/small/medium/large)
            device: 计算设备 (cuda/cpu)，None 则自动选择
            download_root: 模型下载目录
        """
        self.model_name = model_name
        self.device = device or self._auto_select_device()
        self.download_root = download_root
        self.model = None
        self._load_model()
    
    def _auto_select_device(self) -> str:
        """自动选择计算设备"""
        try:
            import torch
            if torch.cuda.is_available():
                return 'cuda'
        except ImportError:
            pass
        return 'cpu'
    
    def _load_model(self):
        """加载 Whisper 模型"""
        try:
            import whisper
            
            print(f"正在加载 Whisper 模型: {self.model_name} (设备: {self.device})")
            
            self.model = whisper.load_model(
                self.model_name,
                device=self.device,
                download_root=self.download_root
            )
            
            print(f"模型加载完成")
            
        except ImportError:
            raise RuntimeError(
                "未安装 whisper 库，请运行: pip install openai-whisper"
            )
        except Exception as e:
            raise RuntimeError(f"模型加载失败: {e}")
    
    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = 'zh',
        task: str = 'transcribe',
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> Dict[str, Any]:
        """
        转录音频文件
        
        Args:
            audio_path: 音频文件路径
            language: 语言代码 (zh/en/ja/ko 等)，None 则自动检测
            task: 任务类型 (transcribe/translate)
            progress_callback: 进度回调函数，接收 0-1 的进度值
            
        Returns:
            转录结果字典
        """
        if self.model is None:
            raise RuntimeError("模型未加载")
        
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")
        
        # 转录选项
        options = {
            'task': task,
            'verbose': False,
            'fp16': self.device == 'cuda',
        }
        
        if language:
            options['language'] = language
        
        # 执行转录
        try:
            result = self.model.transcribe(
                str(audio_path),
                **options
            )
            
            # 格式化结果
            formatted_result = {
                'text': result['text'].strip(),
                'language': result.get('language', 'unknown'),
                'segments': [],
                'duration': 0,
            }
            
            # 处理片段
            for seg in result.get('segments', []):
                formatted_result['segments'].append({
                    'id': seg.get('id', 0),
                    'start': seg.get('start', 0),
                    'end': seg.get('end', 0),
                    'text': seg.get('text', '').strip(),
                    'confidence': seg.get('avg_logprob', 0),
                })
            
            # 计算总时长
            if formatted_result['segments']:
                formatted_result['duration'] = formatted_result['segments'][-1]['end']
            
            return formatted_result
            
        except Exception as e:
            raise RuntimeError(f"转录失败: {e}")
    
    def transcribe_with_timestamps(
        self,
        audio_path: str,
        language: Optional[str] = 'zh'
    ) -> List[Dict[str, Any]]:
        """
        转录并返回带时间戳的片段
        
        Args:
            audio_path: 音频文件路径
            language: 语言代码
            
        Returns:
            带时间戳的文本片段列表
        """
        result = self.transcribe(audio_path, language=language)
        return result.get('segments', [])
    
    def save_result(
        self,
        result: Dict[str, Any],
        output_path: str,
        format: str = 'txt'
    ):
        """
        保存转录结果
        
        Args:
            result: 转录结果字典
            output_path: 输出文件路径
            format: 输出格式 (txt/json/srt/vtt)
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == 'txt':
            # 纯文本格式
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result['text'])
                
        elif format == 'json':
            # JSON 格式
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
                
        elif format == 'srt':
            # SRT 字幕格式
            with open(output_path, 'w', encoding='utf-8') as f:
                for seg in result['segments']:
                    f.write(f"{seg['id'] + 1}\n")
                    f.write(f"{self._format_time(seg['start'])} --> {self._format_time(seg['end'])}\n")
                    f.write(f"{seg['text']}\n\n")
                    
        elif format == 'vtt':
            # WebVTT 格式
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("WEBVTT\n\n")
                for seg in result['segments']:
                    f.write(f"{self._format_time(seg['start'], vtt=True)} --> {self._format_time(seg['end'], vtt=True)}\n")
                    f.write(f"{seg['text']}\n\n")
    
    def _format_time(self, seconds: float, vtt: bool = False) -> str:
        """格式化时间"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        
        if vtt:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
        else:
            return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    @classmethod
    def list_models(cls) -> Dict[str, Dict[str, str]]:
        """列出可用模型"""
        return cls.AVAILABLE_MODELS.copy()
    
    def unload(self):
        """卸载模型释放内存"""
        if self.model is not None:
            import torch
            del self.model
            self.model = None
            torch.cuda.empty_cache() if self.device == 'cuda' else None
