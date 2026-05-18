# -*- coding: utf-8 -*-
"""
转录流水线模块

整合音频提取、语音识别、AI增强的完整处理流程
"""

import os
import json
from pathlib import Path
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, asdict

from .audio_extractor import AudioExtractor
from .transcriber import WhisperTranscriber
from .ai_enhancer import AIEnhancer, EnhancementOptions, ProviderConfig
from .obsidian_exporter import ObsidianExporter


@dataclass
class PipelineConfig:
    """流水线配置"""
    # 音频提取
    sample_rate: int = 16000
    
    # 语音识别
    whisper_model: str = 'base'
    language: str = 'zh'
    
    # AI 增强
    ai_enabled: bool = True
    ai_provider: str = 'siliconflow'
    ai_api_key: str = ''
    ai_model: str = 'Qwen/Qwen2.5-72B-Instruct'
    ai_base_url: str = ''
    fix_punctuation: bool = True
    add_paragraphs: bool = True
    remove_filler: bool = True
    logic_refine: bool = True
    style_polish: bool = True
    target_audience: str = "普通大众"
    tone: str = "专业、清晰"
    generate_summary: bool = False
    extract_keywords: bool = False
    
    # 输出
    output_formats: List[str] = None
    
    # Obsidian 导出
    obsidian_enabled: bool = True
    obsidian_vault_path: Optional[str] = None
    obsidian_create_moc: bool = True
    obsidian_include_timestamps: bool = True
    
    def __post_init__(self):
        if self.output_formats is None:
            self.output_formats = ['txt', 'srt', 'json', 'md']


class TranscribePipeline:
    """转录流水线"""
    
    def __init__(
        self,
        config: Optional[PipelineConfig] = None,
        ffmpeg_path: Optional[str] = None
    ):
        """
        初始化转录流水线
        
        Args:
            config: 流水线配置
            ffmpeg_path: ffmpeg 路径
        """
        self.config = config or PipelineConfig()
        self.ffmpeg_path = ffmpeg_path
        
        # 初始化组件
        self.audio_extractor: Optional[AudioExtractor] = None
        self.transcriber: Optional[WhisperTranscriber] = None
        self.ai_enhancer: Optional[AIEnhancer] = None
        self.obsidian_exporter: Optional[ObsidianExporter] = None
        
        self._progress_callback: Optional[Callable[[str, float], None]] = None
    
    def set_progress_callback(self, callback: Callable[[str, float], None]):
        """
        设置进度回调函数
        
        Args:
            callback: 回调函数，接收 (阶段, 进度) 参数
                     阶段: 'extract', 'transcribe', 'enhance', 'save'
                     进度: 0-1 之间的浮点数
        """
        self._progress_callback = callback
    
    def _update_progress(self, stage: str, progress: float):
        """更新进度"""
        if self._progress_callback:
            self._progress_callback(stage, progress)
    
    def process(
        self,
        video_path: str,
        output_dir: str,
        video_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        处理视频文件
        
        Args:
            video_path: 视频文件路径
            output_dir: 输出目录
            video_name: 视频名称（用于输出文件名）
            
        Returns:
            处理结果字典
        """
        video_path = Path(video_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if not video_name:
            video_name = video_path.stem
        
        result = {
            'success': False,
            'video_path': str(video_path),
            'output_dir': str(output_dir),
            'video_name': video_name,
            'audio_path': None,
            'transcription': None,
            'enhancement': None,
            'output_files': [],
            'error': None,
            'start_time': datetime.now().isoformat(),
            'end_time': None,
        }
        
        audio_path = None
        
        try:
            # 步骤 1: 提取音频
            self._update_progress('extract', 0.0)
            audio_path = self._extract_audio(video_path)
            result['audio_path'] = audio_path
            self._update_progress('extract', 1.0)
            
            # 步骤 2: 语音识别
            self._update_progress('transcribe', 0.0)
            transcription = self._transcribe_audio(audio_path)
            result['transcription'] = transcription
            self._update_progress('transcribe', 1.0)
            
            # 步骤 3: AI 增强
            if self.config.ai_enabled:
                self._update_progress('enhance', 0.0)
                enhancement = self._enhance_text(transcription['text'])
                result['enhancement'] = enhancement
                self._update_progress('enhance', 1.0)
            
            # 步骤 4: 保存结果
            self._update_progress('save', 0.0)
            output_files = self._save_results(result, output_dir, video_name)
            result['output_files'] = output_files
            self._update_progress('save', 1.0)
            
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
            raise
        
        finally:
            # 清理临时文件
            if audio_path and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except Exception:
                    pass
            
            # 卸载模型释放资源
            if self.transcriber:
                self.transcriber.unload()
            
            result['end_time'] = datetime.now().isoformat()
        
        return result
    
    def _extract_audio(self, video_path: Path) -> str:
        """提取音频"""
        if self.audio_extractor is None:
            self.audio_extractor = AudioExtractor(self.ffmpeg_path)
        
        return self.audio_extractor.extract_audio(
            str(video_path),
            sample_rate=self.config.sample_rate
        )
    
    def _transcribe_audio(self, audio_path: str) -> Dict[str, Any]:
        """转录音频"""
        if self.transcriber is None:
            self.transcriber = WhisperTranscriber(
                model_name=self.config.whisper_model
            )
        
        return self.transcriber.transcribe(
            audio_path,
            language=self.config.language
        )
    
    def _enhance_text(self, text: str) -> Dict[str, Any]:
        """增强文本"""
        if self.ai_enhancer is None:
            self.ai_enhancer = AIEnhancer(provider_config=ProviderConfig(provider=self.config.ai_provider, api_key=self.config.ai_api_key, model=self.config.ai_model, base_url=self.config.ai_base_url,))
        
        options = EnhancementOptions(
            fix_punctuation=self.config.fix_punctuation,
            add_paragraphs=self.config.add_paragraphs,
            remove_filler=self.config.remove_filler,
            logic_refine=self.config.logic_refine,
            style_polish=self.config.style_polish,
            target_audience=self.config.target_audience,
            tone=self.config.tone,
            summarize=self.config.generate_summary,
            keywords=self.config.extract_keywords,
        )
        
        return self.ai_enhancer.enhance(text, options)
    
    def _save_results(
        self,
        result: Dict[str, Any],
        output_dir: Path,
        video_name: str
    ) -> List[str]:
        """保存处理结果"""
        output_files = []
        
        # 确定要保存的文本
        if result.get('enhancement'):
            text_to_save = result['enhancement']['enhanced']
            summary = result['enhancement'].get('summary')
            keywords = result['enhancement'].get('keywords')
        else:
            text_to_save = result['transcription']['text']
            summary = None
            keywords = None
        
        # 保存各种格式
        for fmt in self.config.output_formats:
            if fmt == 'txt':
                # 纯文本
                output_path = output_dir / f"{video_name}.txt"
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(f"标题: {video_name}\n")
                    f.write(f"处理时间: {result['start_time']}\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(text_to_save)
                    
                    if summary:
                        f.write("\n\n" + "=" * 50 + "\n")
                        f.write("【摘要】\n")
                        f.write(summary)
                    
                    if keywords:
                        f.write("\n\n【关键词】\n")
                        f.write(", ".join(keywords))
                
                output_files.append(str(output_path))
                
            elif fmt == 'srt':
                # SRT 字幕
                if self.transcriber and result.get('transcription'):
                    output_path = output_dir / f"{video_name}.srt"
                    self.transcriber.save_result(
                        result['transcription'],
                        str(output_path),
                        'srt'
                    )
                    output_files.append(str(output_path))
                    
            elif fmt == 'json':
                # JSON 完整数据
                output_path = output_dir / f"{video_name}.json"
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                output_files.append(str(output_path))
                
            elif fmt == 'md':
                # Markdown 格式
                output_path = output_dir / f"{video_name}.md"
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(f"# {video_name}\n\n")
                    f.write(f"> 处理时间: {result['start_time']}\n\n")
                    
                    if summary:
                        f.write("## 摘要\n\n")
                        f.write(summary + "\n\n")
                    
                    f.write("## 正文\n\n")
                    f.write(text_to_save)
                    f.write("\n")
                    
                    if keywords:
                        f.write("\n## 关键词\n\n")
                        for kw in keywords:
                            f.write(f"- {kw}\n")
                
                output_files.append(str(output_path))
        
        # Obsidian 导出
        if self.config.obsidian_enabled:
            self._update_progress('save', 0.9)
            obsidian_files = self._export_to_obsidian(
                result, output_dir, video_name
            )
            output_files.extend(obsidian_files.values())
        
        return output_files
    
    def _export_to_obsidian(
        self,
        result: Dict[str, Any],
        output_dir: Path,
        video_name: str
    ) -> Dict[str, str]:
        """导出为 Obsidian 格式"""
        if self.obsidian_exporter is None:
            self.obsidian_exporter = ObsidianExporter(
                vault_path=self.config.obsidian_vault_path
            )
        
        # 准备转录结果数据
        transcription_data = {
            'text': result.get('transcription', {}).get('text', ''),
            'segments': result.get('transcription', {}).get('segments', []),
            'enhancement': result.get('enhancement', {}),
        }
        
        # 导出为 Obsidian 格式
        obsidian_options = {
            'create_moc': self.config.obsidian_create_moc,
            'include_timestamps': self.config.obsidian_include_timestamps,
        }
        
        obsidian_dir = output_dir / 'obsidian'
        obsidian_dir.mkdir(exist_ok=True)
        
        return self.obsidian_exporter.export_transcription(
            video_name=video_name,
            transcription_result=transcription_data,
            output_dir=str(obsidian_dir),
            options=obsidian_options
        )
    
    def batch_process(
        self,
        video_paths: List[str],
        output_dir: str,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        批量处理视频
        
        Args:
            video_paths: 视频文件路径列表
            output_dir: 输出目录
            progress_callback: 进度回调，接收 (当前索引, 总数, 当前文件) 参数
            
        Returns:
            处理结果列表
        """
        results = []
        total = len(video_paths)
        
        for i, video_path in enumerate(video_paths, 1):
            if progress_callback:
                progress_callback(i, total, Path(video_path).name)
            
            try:
                result = self.process(video_path, output_dir)
                results.append(result)
            except Exception as e:
                results.append({
                    'success': False,
                    'video_path': video_path,
                    'error': str(e),
                })
        
        return results
