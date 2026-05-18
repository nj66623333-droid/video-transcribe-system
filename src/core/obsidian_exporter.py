# -*- coding: utf-8 -*-
"""
Obsidian 知识库导出模块

将视频转录结果导出为 Obsidian 兼容的 Markdown 格式
支持 YAML Frontmatter、标签、双向链接等 Obsidian 特性
"""

import os
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime


class ObsidianExporter:
    """Obsidian 知识库导出器"""
    
    def __init__(
        self,
        vault_path: Optional[str] = None,
        default_tags: Optional[List[str]] = None
    ):
        """
        初始化 Obsidian 导出器
        
        Args:
            vault_path: Obsidian 仓库路径
            default_tags: 默认标签列表
        """
        self.vault_path = vault_path
        self.default_tags = default_tags or ["视频转录", "笔记"]
    
    def export_note(
        self,
        title: str,
        content: str,
        output_dir: str,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        links: Optional[List[str]] = None,
        related_notes: Optional[List[str]] = None
    ) -> str:
        """
        导出为 Obsidian 笔记
        
        Args:
            title: 笔记标题
            content: 笔记内容
            output_dir: 输出目录
            metadata: YAML Frontmatter 元数据
            tags: 标签列表
            links: 外部链接
            related_notes: 相关笔记（双向链接）
            
        Returns:
            输出文件路径
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 清理文件名
        safe_title = self._sanitize_filename(title)
        file_path = output_path / f"{safe_title}.md"
        
        # 构建 YAML Frontmatter
        frontmatter = self._build_frontmatter(
            title=title,
            metadata=metadata,
            tags=tags
        )
        
        # 构建 Obsidian 格式的内容
        obsidian_content = self._build_obsidian_content(
            content=content,
            links=links,
            related_notes=related_notes
        )
        
        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter)
            f.write(obsidian_content)
        
        return str(file_path)
    
    def export_transcription(
        self,
        video_name: str,
        transcription_result: Dict[str, Any],
        output_dir: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        导出转录结果为 Obsidian 格式
        
        Args:
            video_name: 视频名称
            transcription_result: 转录结果字典
            output_dir: 输出目录
            options: 导出选项
            
        Returns:
            导出的文件路径字典
        """
        options = options or {}
        output_files = {}
        
        # 提取数据
        text = transcription_result.get('text', '')
        enhancement = transcription_result.get('enhancement', {})
        enhanced_text = enhancement.get('enhanced', text)
        summary = enhancement.get('summary', '')
        keywords = enhancement.get('keywords', [])
        
        # 1. 主笔记 - 完整转录内容
        main_note_content = self._format_main_note(enhanced_text, summary)
        main_tags = self.default_tags + ["转录原文"] + keywords[:5]
        
        main_path = self.export_note(
            title=f"{video_name}",
            content=main_note_content,
            output_dir=output_dir,
            metadata={
                "type": "video_transcription",
                "source": video_name,
                "created": datetime.now().isoformat(),
                "word_count": len(enhanced_text),
            },
            tags=main_tags,
            related_notes=[f"[[{video_name}_摘要]]"] if summary else []
        )
        output_files['main'] = main_path
        
        # 2. 摘要笔记（如果有摘要）
        if summary:
            summary_content = self._format_summary_note(summary, keywords)
            summary_tags = self.default_tags + ["摘要", "要点"] + keywords[:3]
            
            summary_path = self.export_note(
                title=f"{video_name}_摘要",
                content=summary_content,
                output_dir=output_dir,
                metadata={
                    "type": "summary",
                    "source": video_name,
                    "created": datetime.now().isoformat(),
                },
                tags=summary_tags,
                related_notes=[f"[[{video_name}]]"]
            )
            output_files['summary'] = summary_path
        
        # 3. 时间戳笔记（如果有片段）
        segments = transcription_result.get('segments', [])
        if segments and options.get('include_timestamps', True):
            timestamp_content = self._format_timestamp_note(segments)
            
            timestamp_path = self.export_note(
                title=f"{video_name}_时间戳",
                content=timestamp_content,
                output_dir=output_dir,
                metadata={
                    "type": "timestamps",
                    "source": video_name,
                    "created": datetime.now().isoformat(),
                },
                tags=self.default_tags + ["时间戳"],
                related_notes=[f"[[{video_name}]]"]
            )
            output_files['timestamps'] = timestamp_path
        
        # 4. MOC (Map of Content) 索引
        if options.get('create_moc', False):
            moc_content = self._format_moc(video_name, keywords, list(output_files.values()))
            
            moc_path = self.export_note(
                title=f"MOC_{video_name}",
                content=moc_content,
                output_dir=output_dir,
                metadata={
                    "type": "moc",
                    "source": video_name,
                    "created": datetime.now().isoformat(),
                },
                tags=self.default_tags + ["MOC", "索引"]
            )
            output_files['moc'] = moc_path
        
        return output_files
    
    def _build_frontmatter(
        self,
        title: str,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """构建 YAML Frontmatter"""
        lines = ["---"]
        lines.append(f'title: "{title}"')
        lines.append(f"created: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        if metadata:
            for key, value in metadata.items():
                if isinstance(value, str):
                    lines.append(f'{key}: "{value}"')
                else:
                    lines.append(f'{key}: {value}')
        
        if tags:
            lines.append(f"tags: {tags}")
        
        lines.append("---")
        lines.append("")
        
        return "\n".join(lines)
    
    def _build_obsidian_content(
        self,
        content: str,
        links: Optional[List[str]] = None,
        related_notes: Optional[List[str]] = None
    ) -> str:
        """构建 Obsidian 格式内容"""
        lines = [content]
        
        # 添加相关链接部分
        if related_notes:
            lines.append("")
            lines.append("## 相关笔记")
            lines.append("")
            for note in related_notes:
                lines.append(f"- {note}")
        
        # 添加外部链接
        if links:
            lines.append("")
            lines.append("## 参考链接")
            lines.append("")
            for link in links:
                lines.append(f"- {link}")
        
        return "\n".join(lines)
    
    def _format_main_note(self, text: str, summary: str = "") -> str:
        """格式化主笔记内容"""
        lines = []
        
        if summary:
            lines.append("## 摘要")
            lines.append("")
            lines.append(summary)
            lines.append("")
            lines.append("---")
            lines.append("")
        
        lines.append("## 转录内容")
        lines.append("")
        lines.append(text)
        
        return "\n".join(lines)
    
    def _format_summary_note(self, summary: str, keywords: List[str]) -> str:
        """格式化摘要笔记"""
        lines = []
        
        lines.append("## 核心要点")
        lines.append("")
        lines.append(summary)
        
        if keywords:
            lines.append("")
            lines.append("## 关键词")
            lines.append("")
            for kw in keywords:
                lines.append(f"- #[[{kw}]]")
        
        return "\n".join(lines)
    
    def _format_timestamp_note(self, segments: List[Dict]) -> str:
        """格式化时间戳笔记"""
        lines = ["## 带时间戳的内容", ""]
        
        for seg in segments:
            start = self._format_time(seg.get('start', 0))
            end = self._format_time(seg.get('end', 0))
            text = seg.get('text', '').strip()
            
            lines.append(f"**[{start} - {end}]** {text}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_moc(
        self,
        video_name: str,
        keywords: List[str],
        related_files: List[str]
    ) -> str:
        """格式化 MOC (Map of Content)"""
        lines = []
        lines.append(f"这是 [[{video_name}]] 的内容索引页。")
        lines.append("")
        lines.append("## 相关笔记")
        lines.append("")
        
        for file_path in related_files:
            file_name = Path(file_path).stem
            lines.append(f"- [[{file_name}]]")
        
        if keywords:
            lines.append("")
            lines.append("## 主题标签")
            lines.append("")
            for kw in keywords[:10]:
                lines.append(f"- #[[{kw}]]")
        
        return "\n".join(lines)
    
    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名，移除非法字符"""
        # 移除或替换非法字符
        illegal_chars = '<>:"/\\|?*'
        for char in illegal_chars:
            filename = filename.replace(char, '_')
        
        # 限制长度
        if len(filename) > 100:
            filename = filename[:100]
        
        return filename.strip()
    
    def _format_time(self, seconds: float) -> str:
        """格式化时间"""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"
    
    def create_daily_note(
        self,
        output_dir: str,
        transcriptions: List[Dict[str, Any]]
    ) -> str:
        """
        创建每日汇总笔记
        
        Args:
            output_dir: 输出目录
            transcriptions: 今日转录结果列表
            
        Returns:
            每日笔记路径
        """
        today = datetime.now().strftime('%Y-%m-%d')
        title = f"每日转录汇总_{today}"
        
        lines = ["## 今日转录视频", ""]
        
        for idx, trans in enumerate(transcriptions, 1):
            video_name = trans.get('video_name', f'视频{idx}')
            summary = trans.get('enhancement', {}).get('summary', '无摘要')
            
            lines.append(f"### {idx}. {video_name}")
            lines.append("")
            lines.append(f"[[{video_name}]]")
            lines.append("")
            lines.append(f"> {summary[:100]}..." if len(summary) > 100 else f"> {summary}")
            lines.append("")
        
        content = "\n".join(lines)
        
        return self.export_note(
            title=title,
            content=content,
            output_dir=output_dir,
            metadata={
                "type": "daily_note",
                "date": today,
            },
            tags=["每日汇总", "视频转录"]
        )
