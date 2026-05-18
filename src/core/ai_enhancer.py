# -*- coding: utf-8 -*-
"""
AI 增强模块 - 四步精修推理链版本
支持本地 Ollama 和云端 API（OpenAI 兼容接口）

默认提供商：硅基流动 (SiliconFlow)
"""

import os
import re
import json
import requests
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field


# ============================================================
# 提供商配置
# ============================================================

PROVIDERS = {
    "ollama": {
        "name": "Ollama (本地)",
        "base_url": "http://localhost:11434",
        "models": ["gemma4:latest", "llama3:latest", "qwen2.5:latest", "phi4:latest"],
        "default_model": "gemma4:latest",
        "api_type": "ollama",
    },
    "siliconflow": {
        "name": "硅基流动 (SiliconFlow)",
        "base_url": "https://api.siliconflow.cn/v1",
        "models": ["Qwen/Qwen2.5-72B-Instruct", "THUDM/glm-4-9b-chat", "meta-llama/Llama-3.3-70B-Instruct", "01-ai/Yi-1.5-34B-Chat"],
        "default_model": "Qwen/Qwen2.5-72B-Instruct",
        "api_type": "openai",
    },
    "deepseek": {
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com",
        "models": ["deepseek-chat", "deepseek-reasoner"],
        "default_model": "deepseek-chat",
        "api_type": "openai",
    },
    "moonshot": {
        "name": "Moonshot (Kimi)",
        "base_url": "https://api.moonshot.cn/v1",
        "models": ["kimi-k2.5", "moonshot-v1-8k", "moonshot-v1-32k"],
        "default_model": "kimi-k2.5",
        "api_type": "openai",
    },
    "openai": {
        "name": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        "default_model": "gpt-4o-mini",
        "api_type": "openai",
    },
    "custom": {
        "name": "自定义 (兼容OpenAI)",
        "base_url": "",
        "models": [],
        "default_model": "",
        "api_type": "openai",
    },
}

DEFAULT_PROVIDER = "siliconflow"
DEFAULT_MODEL = "Qwen/Qwen2.5-72B-Instruct"


@dataclass
class ProviderConfig:
    """AI 提供商配置"""
    provider: str = DEFAULT_PROVIDER          # 提供商标识
    api_key: str = ""                          # API 密钥
    model: str = DEFAULT_MODEL                 # 模型名称
    base_url: str = ""                         # 自定义 API 地址
    timeout: int = 300                         # 超时时间


@dataclass
class EnhancementOptions:
    """增强选项 - 支持四步精修推理链"""
    # --- 基础修复选项 (步骤一) ---
    fix_punctuation: bool = True      # 修复标点
    add_paragraphs: bool = True       # 添加段落
    remove_filler: bool = True        # 去除语气词
    
    # --- 高级增强选项 ---
    logic_refine: bool = True         # 逻辑重构 (步骤二)
    style_polish: bool = True         # 风格润色 (步骤三)
    
    # --- 风格控制参数 ---
    target_audience: str = "普通大众"   # 目标听众
    tone: str = "专业、清晰"           # 目标语气
    
    # --- 附加功能选项 ---
    summarize: bool = False           # 生成摘要
    keywords: bool = False            # 提取关键词
    max_summary_length: int = 200     # 摘要最大长度
    keyword_count: int = 10           # 关键词数量


class AIEnhancer:
    """AI 文本增强器 - 四步精修版（支持本地/云端）"""
    
    def __init__(
        self,
        provider_config: Optional[ProviderConfig] = None,
    ):
        """
        初始化 AI 增强器
        
        Args:
            provider_config: 提供商配置，None 则使用默认（硅基流动）
        """
        self.config = provider_config or ProviderConfig()
        
        # 获取提供商信息
        provider_id = self.config.provider
        provider_info = PROVIDERS.get(provider_id, PROVIDERS[DEFAULT_PROVIDER])
        self.provider_info = provider_info
        
        # 确定 API 地址
        if provider_id == "custom" and self.config.base_url:
            self.api_base = self.config.base_url.rstrip('/')
        else:
            self.api_base = provider_info["base_url"].rstrip('/')
        
        # 确定模型
        if not self.config.model:
            self.model = provider_info["default_model"]
        else:
            self.model = self.config.model
        
        self.api_type = provider_info["api_type"]
        self.api_key = self.config.api_key
        self.timeout = self.config.timeout
        
        # 非 OLLAMA 模式下需要 API Key
        if self.api_type != "ollama" and not self.api_key:
            provider_name = provider_info["name"]
            print(f"⚠️ 警告: {provider_name} 需要 API Key，请在设置中填写")
    
    def enhance(
        self,
        text: str,
        options: Optional[EnhancementOptions] = None
    ) -> Dict[str, Any]:
        """
        使用"多步长推理链"增强转录文本
        
        Args:
            text: 原始转录文本
            options: 增强选项
            
        Returns:
            增强结果字典
        """
        if options is None:
            options = EnhancementOptions()
        
        current_text = text
        process_log = []
        provider_name = PROVIDERS.get(self.config.provider, {}).get("name", self.config.provider)
        print(f"  [提供商] {provider_name} | 模型: {self.model}")
        
        # 步骤一：【格式化与基础修复】
        if options.fix_punctuation or options.add_paragraphs or options.remove_filler:
            print("  → [步骤 1/4] 正在进行格式化与基础修复...")
            try:
                current_text = self._step1_format_and_fix(
                    current_text, 
                    options.fix_punctuation, 
                    options.add_paragraphs, 
                    options.remove_filler
                )
                process_log.append("步骤一完成：标点、分段和口语化修复")
            except Exception as e:
                print(f"  ✗ 步骤一失败: {e}")
                process_log.append(f"步骤一失败: {e}")

        # 步骤二：【逻辑重构与精炼】
        if options.logic_refine:
            print("  → [步骤 2/4] 正在进行逻辑重构与精炼...")
            try:
                current_text = self._step2_logic_refine(current_text)
                process_log.append("步骤二完成：逻辑重构与内容精炼")
            except Exception as e:
                print(f"  ✗ 步骤二失败: {e}")
                process_log.append(f"步骤二失败: {e}")

        # 步骤三：【语气与风格润色】
        if options.style_polish:
            print("  → [步骤 3/4] 正在进行风格润色...")
            try:
                current_text = self._step3_style_polish(
                    current_text,
                    target_audience=options.target_audience,
                    tone=options.tone
                )
                process_log.append("步骤三完成：风格与语气润色")
            except Exception as e:
                print(f"  ✗ 步骤三失败: {e}")
                process_log.append(f"步骤三失败: {e}")

        # 步骤四：【最终审校与摘要】
        print("  → [步骤 4/4] 正在进行最终审校...")
        
        # 生成摘要
        summary = ""
        if options.summarize:
            print("  → 生成摘要中...")
            summary = self._generate_summary(current_text, options.max_summary_length)
            process_log.append("摘要生成完成")

        # 提取关键词
        keywords = []
        if options.keywords:
            print("  → 提取关键词中...")
            keywords = self._extract_keywords(current_text, options.keyword_count)
            process_log.append("关键词提取完成")
        
        result = {
            'original': text,
            'enhanced': current_text.strip(),
            'summary': summary,
            'keywords': keywords,
            'process_log': process_log,
            'provider': provider_name,
            'model': self.model,
        }
        
        print("  ✓ 四步精修处理完成!")
        return result
    
    def _step1_format_and_fix(self, text: str, fix_punc: bool, add_para: bool, remove_fill: bool) -> str:
        """步骤一：修复标点、分段、去除填充词"""
        tasks = []
        if fix_punc:
            tasks.append("修正所有标点错误，特别是句号、逗号的使用")
        if add_para:
            tasks.append("根据语义的停顿，将文本切分为逻辑清晰的段落")
        if remove_fill:
            tasks.append("删除所有无意义的口语词，如\"嗯\"、\"啊\"、\"那个\"、\"就是说\"等")
        
        prompt = f"""你是一个专业的文字校对员。请对以下转录稿进行基础格式化修复。

任务要求：
{chr(10).join(f"{i+1}. {task}" for i, task in enumerate(tasks))}

处理规则：
- 保持原文的核心意思和信息不变
- 直接输出修复后的文本，不要添加任何解释或前言
- 确保修改后的文本读起来自然流畅

原文：
{text}"""
        
        return self._generate("", prompt).strip()
    
    def _step2_logic_refine(self, text: str) -> str:
        """步骤二：逻辑重构与精炼"""
        prompt = f"""你是一位资深的内容架构师。请分析以下文本，并对其进行逻辑重构与精炼。

核心任务：
1. 识别出文章的核心论点和支持论据
2. 删除所有重复、冗余或偏离主题的论述
3. 将内容按照"提出观点 → 分析论证 → 得出结论"的结构进行重新组织
4. 保持所有关键信息和数据，确保内容完整性

处理原则：
- 保持专业性和准确性
- 确保逻辑链条清晰、环环相扣
- 文章应该更具可读性和说服力

原文：
{text}

请输出重构后的、逻辑更清晰的版本。"""
        
        return self._generate("", prompt).strip()
    
    def _step3_style_polish(self, text: str, target_audience: str, tone: str) -> str:
        """步骤三：语气与风格润色"""
        prompt = f"""你是一位顶级的文案作家和演讲稿专家。请将以下文本进行风格化润色。

风格设定：
- 目标听众：{target_audience}
- 期望语气：{tone}

润色要求：
1. 调整语言风格，使其完全符合目标听众的阅读习惯和认知水平
2. 精炼过渡句，让段落衔接更自然流畅
3. 创造或强化一两个令人印象深刻的金句或核心观点
4. 确保内容的专业性、感染力和吸引力
5. 保持原文的核心信息和数据准确无误

原文：
{text}

请输出最终润色完成的、可以直接使用的版本。"""
        
        return self._generate("", prompt).strip()
    
    def _generate(self, system_prompt: str, user_prompt: str) -> str:
        """根据配置的提供商类型调用 LLM"""
        if self.api_type == "ollama":
            return self._generate_ollama(system_prompt, user_prompt)
        else:
            return self._generate_openai(system_prompt, user_prompt)
    
    def _generate_ollama(self, system_prompt: str, user_prompt: str) -> str:
        """调用本地 Ollama 生成文本"""
        full_prompt = f"{system_prompt}\n\n{user_prompt}".strip()
        
        payload = {
            'model': self.model,
            'prompt': full_prompt,
            'stream': False,
            'options': {
                'temperature': 0.3,
                'num_predict': 4096,
            }
        }
        
        response = requests.post(
            f"{self.api_base}/api/generate",
            json=payload,
            timeout=self.timeout
        )
        
        if response.status_code != 200:
            raise RuntimeError(f"Ollama API 错误: {response.status_code}")
        
        result = response.json()
        return result.get('response', '')
    
    def _generate_openai(self, system_prompt: str, user_prompt: str) -> str:
        """调用 OpenAI 兼容 API 生成文本"""
        if not self.api_key:
            raise RuntimeError(f"未配置 API Key，请先填写提供商 {self.config.provider} 的 API Key")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 4096,
            "stream": False
        }
        
        response = requests.post(
            f"{self.api_base}/chat/completions",
            json=payload,
            headers=headers,
            timeout=self.timeout
        )
        
        if response.status_code == 401:
            raise RuntimeError("API Key 无效或已过期，请检查设置")
        elif response.status_code == 429:
            raise RuntimeError("API 请求频率超限，请稍后重试")
        elif response.status_code != 200:
            raise RuntimeError(f"API 错误 ({response.status_code}): {response.text[:200]}")
        
        result = response.json()
        
        try:
            return result["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"API 响应解析失败: {e}")
    
    def _generate_summary(self, text: str, max_length: int = 200) -> str:
        """生成摘要"""
        prompt = f"""请为以下文本生成一段简短的摘要（不超过{max_length}字）：

{text}

摘要："""
        
        try:
            return self._generate("", prompt).strip()
        except Exception as e:
            print(f"摘要生成失败: {e}")
            return ""
    
    def _extract_keywords(self, text: str, count: int = 10) -> List[str]:
        """提取关键词"""
        prompt = f"""请从以下文本中提取{count}个核心关键词，用逗号分隔：

{text}

关键词："""
        
        try:
            result_text = self._generate("", prompt).strip()
            keywords = [k.strip() for k in re.split(r'[,，、]', result_text) if k.strip()]
            return keywords[:count]
        except Exception as e:
            print(f"关键词提取失败: {e}")
            return []
    
    def format_as_article(
        self,
        text: str,
        title: Optional[str] = None
    ) -> str:
        """
        将转录文本格式化为文章 (保留原有功能)
        
        Args:
            text: 转录文本
            title: 文章标题
            
        Returns:
            格式化后的文章
        """
        prompt = """请将以下转录内容整理成一篇结构清晰的文章：

要求：
1. 添加合适的标题（如果没有提供）
2. 分段清晰，每段有明确的主题
3. 修正口语化表达，使其更适合阅读
4. 保持内容的完整性和准确性
5. 可以适当添加小标题

原文：
"""
        
        if title:
            prompt = f"标题：{title}\n\n" + prompt
        
        try:
            return self._generate(prompt, text)
        except Exception as e:
            print(f"文章格式化失败: {e}")
            return text


def get_default_config() -> ProviderConfig:
    """获取默认提供商配置（硅基流动）"""
    return ProviderConfig(
        provider="siliconflow",
        model="Qwen/Qwen2.5-72B-Instruct",
    )
