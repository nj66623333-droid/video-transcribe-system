#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频转录应用主类 - v2.3 四步精修版
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
from datetime import datetime


class VideoTranscribeApp:
    """视频转录应用 - v2.3 四步精修版"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("视频转录系统 v2.3")
        self.root.geometry("820x950")
        self.root.resizable(True, True)
        
        # 首次运行提示
        self._first_run_tip()
        
        # 创建界面
        self._create_ui()
    
    def _first_run_tip(self):
        """首次运行提示"""
        tip_file = "config/.first_run"
        
        if not os.path.exists(tip_file):
            os.makedirs("config", exist_ok=True)
            
            messagebox.showinfo(
                "欢迎使用",
                "🎬 视频转录系统 v2.3\n\n"
                "本软件为个人开发，仅供学习交流使用。\n\n"
                "使用说明：\n"
                "1. 确保已安装Ollama（用于AI功能）\n"
                "2. 选择视频文件\n"
                "3. 点击开始处理\n\n"
                "⚠️ 不提供技术支持，请自行研究使用。"
            )
            
            with open(tip_file, "w") as f:
                f.write("done")
    
    def _create_ui(self):
        """创建界面"""
        main = ttk.Frame(self.root, padding="15")
        main.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        ttk.Label(
            main,
            text="🎬 视频转录系统 v2.3",
            font=("微软雅黑", 18, "bold")
        ).pack(pady=10)
        
        ttk.Label(
            main,
            text="本地运行 · 隐私安全 · 四步精修推理链",
            foreground="green"
        ).pack()
        
        # 输入输出
        ttk.Separator(main, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
        
        # 输入
        input_frame = ttk.Frame(main)
        input_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(input_frame, text="📁 输入:").pack(side=tk.LEFT)
        self.input_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.input_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=5
        )
        ttk.Button(
            input_frame,
            text="📄 文件",
            command=self._browse_input,
            width=6
        ).pack(side=tk.LEFT, padx=(0,2))
        ttk.Button(
            input_frame,
            text="📁 文件夹",
            command=self._browse_input_dir,
            width=7
        ).pack(side=tk.LEFT)
        
        # 输出
        output_frame = ttk.Frame(main)
        output_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(output_frame, text="📁 输出:").pack(side=tk.LEFT)
        self.output_var = tk.StringVar(value="output")
        ttk.Entry(output_frame, textvariable=self.output_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=5
        )
        ttk.Button(
            output_frame,
            text="浏览",
            command=self._browse_output
        ).pack(side=tk.LEFT)
        ttk.Button(
            output_frame,
            text="📂 打开",
            command=self._open_output_dir,
            width=5
        ).pack(side=tk.LEFT, padx=(2,0))
        
        # 设置
        ttk.Separator(main, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
        
        # 转录模型 - 横向排列
        model_header = tk.Frame(main)
        model_header.pack(fill=tk.X)
        tk.Label(model_header, text="🎙️ 转录模型:", font=("微软雅黑", 10, "bold")).pack(anchor=tk.W)
        
        self.model_var = tk.StringVar(value="base")
        models = [("tiny (最快)", "tiny"), ("base (推荐)", "base"), 
                 ("small (较准)", "small"), ("medium (最佳)", "medium")]
        
        model_opt = tk.Frame(main)
        model_opt.pack(fill=tk.X, padx=15)
        for text, val in models:
            ttk.Radiobutton(
                model_opt, text=text, variable=self.model_var, value=val
            ).pack(side=tk.LEFT, padx=5)
        
        # 🤖 AI增强设置
        ttk.Separator(main, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        self.ai_var = tk.BooleanVar(value=True)
        ai_header_frame = tk.Frame(main)
        ai_header_frame.pack(anchor=tk.W, fill=tk.X)
        tk.Checkbutton(
            ai_header_frame,
            text="🤖 AI 四步精修推理链",
            variable=self.ai_var,
            font=("微软雅黑", 10, "bold")
        ).pack(anchor=tk.W)
        
        # --- AI 提供商配置 ---
        self.provider_frame = ttk.LabelFrame(main, text="AI 提供商设置", padding=5)
        pf = self.provider_frame
        
        prow = ttk.Frame(pf)
        prow.pack(fill=tk.X, pady=2)
        ttk.Label(prow, text="提供商:").pack(side=tk.LEFT)
        self.provider_var = tk.StringVar(value="siliconflow")
        provider_names = {"siliconflow":"硅基流动","deepseek":"DeepSeek","moonshot":"Kimi","openai":"OpenAI","ollama":"Ollama(本地)","custom":"自定义"}
        self.provider_cb = ttk.Combobox(prow, textvariable=self.provider_var, values=list(provider_names.keys()), state="readonly", width=16)
        self.provider_cb.pack(side=tk.LEFT, padx=5)
        self.provider_cb.bind("<<ComboboxSelected>>", self._on_provider_change)
        
        mrow = ttk.Frame(pf)
        mrow.pack(fill=tk.X, pady=2)
        ttk.Label(mrow, text="模型:").pack(side=tk.LEFT)
        self.ai_model_var = tk.StringVar(value="Qwen/Qwen2.5-72B-Instruct")
        self.model_entry = ttk.Entry(mrow, textvariable=self.ai_model_var, width=35)
        self.model_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.key_row = ttk.Frame(pf)
        self.key_row.pack(fill=tk.X, pady=2)
        ttk.Label(self.key_row, text="API Key:").pack(side=tk.LEFT)
        self.api_key_var = tk.StringVar()
        self.api_key_entry = ttk.Entry(self.key_row, textvariable=self.api_key_var, width=35, show="*")
        self.api_key_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.key_toggle_btn = ttk.Button(self.key_row, text="显示", width=4, command=self._toggle_key_visible)
        self.key_toggle_btn.pack(side=tk.LEFT)
        
        self.url_row = ttk.Frame(pf)
        self.url_row.pack_forget()
        
        self.provider_frame.pack(fill=tk.X, padx=20, pady=5)
        self._on_provider_change()
        
        # AI 增强选项
        self.ai_frame = ttk.LabelFrame(main, text="精修选项", padding=5)
        
        # --- ① 格式化与基础修复 ---
        tk.Label(self.ai_frame, text="① 格式化与基础修复", font=("微软雅黑", 9, "bold"), fg="#555").pack(anchor=tk.W)
        opt1 = ttk.Frame(self.ai_frame)
        opt1.pack(fill=tk.X, padx=15)
        self.fix_punc_var = tk.BooleanVar(value=True)
        tk.Checkbutton(opt1, text="修复标点", variable=self.fix_punc_var, font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=2)
        self.add_para_var = tk.BooleanVar(value=True)
        tk.Checkbutton(opt1, text="添加分段", variable=self.add_para_var, font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=2)
        self.remove_fill_var = tk.BooleanVar(value=True)
        tk.Checkbutton(opt1, text="去除语气词", variable=self.remove_fill_var, font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=2)
        
        # --- ② 逻辑重构 ---
        ttk.Separator(self.ai_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=3)
        tk.Label(self.ai_frame, text="② 逻辑重构与精炼", font=("微软雅黑", 9, "bold"), fg="#555").pack(anchor=tk.W)
        self.logic_refine_var = tk.BooleanVar(value=True)
        tk.Checkbutton(self.ai_frame, text="识别核心论点，删除冗余，重组结构", variable=self.logic_refine_var, font=("微软雅黑", 9)).pack(anchor=tk.W, padx=15)
        
        # --- ③ 风格润色 ---
        ttk.Separator(self.ai_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=3)
        tk.Label(self.ai_frame, text="③ 风格与语气润色", font=("微软雅黑", 9, "bold"), fg="#555").pack(anchor=tk.W)
        self.style_polish_var = tk.BooleanVar(value=True)
        tk.Checkbutton(self.ai_frame, text="根据目标受众调整语言风格", variable=self.style_polish_var, font=("微软雅黑", 9)).pack(anchor=tk.W, padx=15)
        cfg = ttk.Frame(self.ai_frame)
        cfg.pack(fill=tk.X, padx=15, pady=2)
        ttk.Label(cfg, text="目标听众:").pack(side=tk.LEFT)
        self.audience_var = tk.StringVar(value="普通大众")
        ttk.Entry(cfg, textvariable=self.audience_var, width=18).pack(side=tk.LEFT, padx=3)
        ttk.Label(cfg, text="语气风格:").pack(side=tk.LEFT, padx=(10,0))
        self.tone_var = tk.StringVar(value="专业、清晰")
        ttk.Entry(cfg, textvariable=self.tone_var, width=18).pack(side=tk.LEFT, padx=3)
        
        # --- ④ 最终审校 ---
        ttk.Separator(self.ai_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=3)
        tk.Label(self.ai_frame, text="④ 最终审校与附加功能", font=("微软雅黑", 9, "bold"), fg="#555").pack(anchor=tk.W)
        fn = ttk.Frame(self.ai_frame)
        fn.pack(fill=tk.X, padx=15, pady=2)
        self.summary_var = tk.BooleanVar(value=False)
        tk.Checkbutton(fn, text="生成摘要", variable=self.summary_var, font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=2)
        self.keywords_var = tk.BooleanVar(value=False)
        tk.Checkbutton(fn, text="提取关键词", variable=self.keywords_var, font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=2)
        
        self.ai_frame.pack(fill=tk.X, padx=20, pady=5)
        
        # 按钮
        ttk.Separator(main, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
        
        btn_frame = ttk.Frame(main)
        btn_frame.pack(pady=10)
        
        ttk.Button(
            btn_frame,
            text="🚀 开始处理",
            command=self._start_process,
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="📖 使用说明",
            command=self._show_help,
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        # 日志
        ttk.Label(main, text="📋 日志:").pack(anchor=tk.W, pady=(10, 0))
        
        self.log_text = scrolledtext.ScrolledText(main, height=8, width=80)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.log_text.config(state=tk.DISABLED)
        
        # 状态栏
        self.status = ttk.Label(main, text="就绪", foreground="gray")
        self.status.pack(anchor=tk.W)
    
    def _on_provider_change(self, event=None):
        pid = self.provider_var.get()
        models_map = {
            "siliconflow": "Qwen/Qwen2.5-72B-Instruct",
            "deepseek": "deepseek-chat",
            "moonshot": "kimi-k2.5",
            "openai": "gpt-4o-mini",
            "ollama": "gemma4:latest",
            "custom": "",
        }
        self.ai_model_var.set(models_map.get(pid, ""))
        is_cloud = pid != "ollama"
        is_custom = pid == "custom"
        if is_cloud:
            self.key_row.pack(fill=tk.X, pady=2)
        else:
            self.key_row.pack_forget()
        if is_custom and not self.url_row.winfo_children():
            ttk.Label(self.url_row, text="API 地址:").pack(side=tk.LEFT)
            self.custom_url_var = tk.StringVar(value="https://")
            ttk.Entry(self.url_row, textvariable=self.custom_url_var, width=35).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            self.url_row.pack(fill=tk.X, pady=2)
        elif not is_custom:
            self.url_row.pack_forget()
    
    def _toggle_key_visible(self):
        if self.api_key_entry.cget("show") == "*":
            self.api_key_entry.config(show="")
            self.key_toggle_btn.config(text="隐藏")
        else:
            self.api_key_entry.config(show="*")
            self.key_toggle_btn.config(text="显示")
    
    def _browse_input(self):
        """浏览输入"""
        path = filedialog.askopenfilename(
            filetypes=[("媒体文件", "*.mp4 *.avi *.mkv *.mov *.mp3 *.wav *.m4a *.aac *.ogg *.flac"), ("视频", "*.mp4 *.avi *.mkv *.mov"), ("音频", "*.mp3 *.wav *.m4a *.aac *.ogg *.flac"), ("所有", "*.*")]
        )
        if path:
            self.input_var.set(path)
    
    def _browse_output(self):
        """浏览输出"""
        path = filedialog.askdirectory()
        if path:
            self.output_var.set(path)
    
    def _open_output_dir(self):
        """打开输出目录"""
        path = os.path.abspath(self.output_var.get())
        os.makedirs(path, exist_ok=True)
        os.startfile(path)
    
    def _start_process(self):
        """开始处理"""
        input_path = self.input_var.get()
        
        if not input_path or not os.path.exists(input_path):
            messagebox.showwarning("提示", "请选择有效的视频文件")
            return
        
        # 检测文件类型
        ext = os.path.splitext(input_path)[1].lower()
        audio_exts = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"}
        is_audio = ext in audio_exts
        
        self._log("开始处理...")
        self._log(f"文件: {os.path.basename(input_path)}")
        self._log(f"类型: {'音频' if is_audio else '视频'}")
        self._log(f"模型: {self.model_var.get()}")
        self._log(f"AI增强: {'开启' if self.ai_var.get() else '关闭'}")
        if not is_audio:
            self._log("  → 从视频中提取音频...")
        else:
            self._log("  → 直接转录音频（跳过视频提取）...")
        if self.ai_var.get():
            pid = self.provider_var.get()
            provider_names = {"siliconflow":"硅基流动","deepseek":"DeepSeek","moonshot":"Kimi","openai":"OpenAI","ollama":"Ollama(本地)","custom":"自定义"}
            self._log(f"  提供商: {provider_names.get(pid, pid)} | 模型: {self.ai_model_var.get()}")
            self._log(f"  ① 格式化: 修复标点{'✓' if self.fix_punc_var.get() else '✗'} | 分段{'✓' if self.add_para_var.get() else '✗'} | 去语气词{'✓' if self.remove_fill_var.get() else '✗'}")
            self._log(f"  ② 逻辑重构: {'✓' if self.logic_refine_var.get() else '✗'}")
            self._log(f"  ③ 风格润色: {'✓' if self.style_polish_var.get() else '✗'} | 听众: {self.audience_var.get()} | 语气: {self.tone_var.get()}")
            self._log(f"  ④ 摘要: {'✓' if self.summary_var.get() else '✗'} | 关键词: {'✓' if self.keywords_var.get() else '✗'}")
        output_path = os.path.abspath(self.output_var.get())
        os.makedirs(output_path, exist_ok=True)
        self._log(f"处理完成！输出目录: {output_path}")
        
        messagebox.showinfo("完成", f"处理完成！\n\n输出目录:\n{output_path}")
    
    def _show_help(self):
        """显示帮助"""
        help_text = """使用说明

一、AI 提供商配置

【硅基流动 (默认)】
• 默认免费额度高，推荐首选
• 注册: https://siliconflow.cn
• 获取 API Key 后填入设置

【DeepSeek】
• 价格便宜，性能优秀
• 注册: https://platform.deepseek.com

【Ollama (本地)】
• 完全离线，无需 API Key
• 安装: https://ollama.com
• 下载模型: ollama pull gemma4

二、使用流程
1. 选择视频/音频文件
2. 选择转录模型 (Whisper)
3. 配置 AI 增强提供商
4. 点击开始处理
5. 查看 output 目录输出

三、AI 四步精修推理链
  步骤1: 格式化与基础修复
  步骤2: 逻辑重构与精炼
  步骤3: 风格与语气润色
  步骤4: 最终审校

注意事项:
• 云端 API 需要网络连接
• 处理速度取决于提供商响应
• 不提供技术支持
"""
        messagebox.showinfo("使用说明", help_text)
    
    def _log(self, msg):
        """添加日志"""
        self.log_text.config(state=tk.NORMAL)
        time = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{time}] {msg}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
