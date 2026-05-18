#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频转录系统 v2.3 - 图形界面主程序
基于 Whisper + Ollama 的本地视频转录与 AI 智能增强工具
"""

import sys
import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from datetime import datetime

# 尝试导入流水线模块（本地 core/ 目录）
try:
    from core.pipeline import TranscribePipeline, PipelineConfig
    PIPELINE_AVAILABLE = True
except ImportError:
    PIPELINE_AVAILABLE = False

import requests


# AI 提供商配置
PROVIDERS = {
    "siliconflow": {"name": "硅基流动 (SiliconFlow)", "base_url": "https://api.siliconflow.cn/v1", "models": ["Qwen/Qwen2.5-72B-Instruct", "THUDM/glm-4-9b-chat", "meta-llama/Llama-3.3-70B-Instruct", "01-ai/Yi-1.5-34B-Chat"], "default_model": "Qwen/Qwen2.5-72B-Instruct"},
    "deepseek": {"name": "DeepSeek", "base_url": "https://api.deepseek.com", "models": ["deepseek-chat", "deepseek-reasoner"], "default_model": "deepseek-chat"},
    "moonshot": {"name": "Moonshot (Kimi)", "base_url": "https://api.moonshot.cn/v1", "models": ["kimi-k2.5", "moonshot-v1-8k"], "default_model": "kimi-k2.5"},
    "openai": {"name": "OpenAI", "base_url": "https://api.openai.com/v1", "models": ["gpt-4o", "gpt-4o-mini"], "default_model": "gpt-4o-mini"},
    "ollama": {"name": "Ollama (本地)", "base_url": "http://localhost:11434", "models": ["gemma4:latest", "llama3:latest", "qwen2.5:latest", "phi4:latest"], "default_model": "gemma4:latest"},
    "custom": {"name": "自定义 (OpenAI兼容)", "base_url": "", "models": [""], "default_model": ""},
}

DEFAULT_PROVIDER = "siliconflow"


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
        # 整体容器
        outer = ttk.Frame(self.root, padding="15")
        outer.pack(fill=tk.BOTH, expand=True)
        
        # 上半部分：滚动区域（设置区）
        canvas_frame = ttk.Frame(outer)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 内部容器
        main = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=main, anchor="nw", width=self.canvas.winfo_reqwidth())
        
        # 绑定画布尺寸变化
        def _configure_canvas(event):
            self.canvas.itemconfig(self.canvas_window, width=event.width)
        self.canvas.bind("<Configure>", _configure_canvas)
        
        # 绑定内部框架尺寸变化
        def _configure_inner(event):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        main.bind("<Configure>", _configure_inner)
        
        # 鼠标滚轮滚动
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
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
        
        # 转录模型
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
        
        # 提供商选择
        prow = ttk.Frame(pf)
        prow.pack(fill=tk.X, pady=2)
        ttk.Label(prow, text="提供商:").pack(side=tk.LEFT)
        self.provider_var = tk.StringVar(value=DEFAULT_PROVIDER)
        provider_names = [(k, v["name"]) for k, v in PROVIDERS.items()]
        self.provider_cb = ttk.Combobox(prow, textvariable=self.provider_var, values=[v[0] for v in provider_names], state="readonly", width=20)
        self.provider_cb.pack(side=tk.LEFT, padx=5)
        self.provider_cb.bind("<<ComboboxSelected>>", self._on_provider_change)
        
        # 模型选择
        mrow = ttk.Frame(pf)
        mrow.pack(fill=tk.X, pady=2)
        ttk.Label(mrow, text="模型:").pack(side=tk.LEFT)
        self.ai_model_var = tk.StringVar(value=PROVIDERS[DEFAULT_PROVIDER]["default_model"])
        self.model_entry = ttk.Entry(mrow, textvariable=self.ai_model_var, width=35)
        self.model_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # API Key（云端需要）
        self.key_row = ttk.Frame(pf)
        self.key_row.pack(fill=tk.X, pady=2)
        ttk.Label(self.key_row, text="API Key:").pack(side=tk.LEFT)
        self.api_key_var = tk.StringVar()
        self.api_key_entry = ttk.Entry(self.key_row, textvariable=self.api_key_var, width=35, show="*")
        self.api_key_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.key_toggle_btn = ttk.Button(self.key_row, text="显示", width=4, command=self._toggle_key_visible)
        self.key_toggle_btn.pack(side=tk.LEFT)
        
        # 自定义 API 地址（仅自定义时显示）
        self.url_row = ttk.Frame(pf)
        self.url_row.pack_forget()
        
        self.provider_frame.pack(fill=tk.X, padx=20, pady=5)
        
        # 初始化提供商状态
        self._on_provider_change()
        
        # AI 增强选项
        self.ai_frame = ttk.LabelFrame(main, text="精修选项", padding=5)
        
        # --- 步骤一：格式化与基础修复 ---
        step1_frame = ttk.Frame(self.ai_frame)
        step1_frame.pack(fill=tk.X, pady=2)
        tk.Label(step1_frame, text="① 格式化与基础修复", font=("微软雅黑", 9, "bold"), fg="#555").pack(anchor=tk.W)
        
        opt_frame1 = ttk.Frame(self.ai_frame)
        opt_frame1.pack(fill=tk.X, padx=15)
        
        self.fix_punc_var = tk.BooleanVar(value=True)
        tk.Checkbutton(opt_frame1, text="修复标点", variable=self.fix_punc_var, font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=2)
        
        self.add_para_var = tk.BooleanVar(value=True)
        tk.Checkbutton(opt_frame1, text="添加分段", variable=self.add_para_var, font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=2)
        
        self.remove_fill_var = tk.BooleanVar(value=True)
        tk.Checkbutton(opt_frame1, text="去除语气词", variable=self.remove_fill_var, font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=2)
        
        # --- 步骤二：逻辑重构 ---
        ttk.Separator(self.ai_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=3)
        tk.Label(self.ai_frame, text="② 逻辑重构与精炼", font=("微软雅黑", 9, "bold"), fg="#555").pack(anchor=tk.W)
        self.logic_refine_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            self.ai_frame,
            text="识别核心论点，删除冗余，重组为'观点→论证→结论'结构",
            variable=self.logic_refine_var,
            font=("微软雅黑", 9)
        ).pack(anchor=tk.W, padx=15)
        
        # --- 步骤三：风格润色 ---
        ttk.Separator(self.ai_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=3)
        tk.Label(self.ai_frame, text="③ 风格与语气润色", font=("微软雅黑", 9, "bold"), fg="#555").pack(anchor=tk.W)
        
        self.style_polish_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            self.ai_frame,
            text="根据目标受众调整语言风格",
            variable=self.style_polish_var,
            font=("微软雅黑", 9)
        ).pack(anchor=tk.W, padx=15)
        
        # 目标听众 + 语气风格
        cfg_frame = ttk.Frame(self.ai_frame)
        cfg_frame.pack(fill=tk.X, padx=15, pady=2)
        ttk.Label(cfg_frame, text="目标听众:").pack(side=tk.LEFT)
        self.audience_var = tk.StringVar(value="普通大众")
        ttk.Entry(cfg_frame, textvariable=self.audience_var, width=18).pack(side=tk.LEFT, padx=3)
        ttk.Label(cfg_frame, text="语气风格:").pack(side=tk.LEFT, padx=(10,0))
        self.tone_var = tk.StringVar(value="专业、清晰")
        ttk.Entry(cfg_frame, textvariable=self.tone_var, width=18).pack(side=tk.LEFT, padx=3)
        
        # --- 步骤四：最终审校 ---
        ttk.Separator(self.ai_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=3)
        tk.Label(self.ai_frame, text="④ 最终审校与附加功能", font=("微软雅黑", 9, "bold"), fg="#555").pack(anchor=tk.W)
        
        final_frame = ttk.Frame(self.ai_frame)
        final_frame.pack(fill=tk.X, padx=15, pady=2)
        
        self.summary_var = tk.BooleanVar(value=False)
        tk.Checkbutton(final_frame, text="生成摘要", variable=self.summary_var, font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=2)
        
        self.keywords_var = tk.BooleanVar(value=False)
        tk.Checkbutton(final_frame, text="提取关键词", variable=self.keywords_var, font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=2)
        
        # 显示AI框架
        self.ai_frame.pack(fill=tk.X, padx=20, pady=5)
        
        # 按钮
        ttk.Separator(main, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
        
        self.btn_frame = ttk.Frame(main)
        self.btn_frame.pack(pady=10)
        
        ttk.Button(
            self.btn_frame,
            text="🚀 开始处理",
            command=self._start_process,
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            self.btn_frame,
            text="📖 使用说明",
            command=self._show_help,
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        # 日志（在外层，不参与滚动）
        ttk.Label(outer, text="📋 日志:").pack(anchor=tk.W, pady=(10, 0))
        
        self.log_text = scrolledtext.ScrolledText(outer, height=6, width=80)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.log_text.config(state=tk.DISABLED)
        
        # 状态栏
        self.status = ttk.Label(outer, text="就绪", foreground="gray")
        self.status.pack(anchor=tk.W)
    
    def _on_provider_change(self, event=None):
        """切换提供商时更新界面"""
        pid = self.provider_var.get()
        info = PROVIDERS.get(pid, PROVIDERS["siliconflow"])
        
        # 更新模型列表
        if info["models"] and info["models"][0]:
            self.ai_model_var.set(info["default_model"])
        
        is_cloud = pid != "ollama"
        is_custom = pid == "custom"
        
        # API Key 行：云端显示，本地隐藏
        if is_cloud:
            self.key_row.pack(fill=tk.X, pady=2, before=self.key_row)
        else:
            self.key_row.pack_forget()
        
        # 自定义 API 地址：仅 customs 显示
        if is_custom:
            ttk.Label(self.url_row, text="API 地址:").pack(side=tk.LEFT)
            self.custom_url_var = tk.StringVar(value="https://")
            ttk.Entry(self.url_row, textvariable=self.custom_url_var, width=35).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            self.url_row.pack(fill=tk.X, pady=2)
        else:
            self.url_row.pack_forget()
    
    def _toggle_key_visible(self):
        """切换 API Key 显示/隐藏"""
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
    
    def _browse_input_dir(self):
        """打开文件夹 - 批量处理"""
        path = filedialog.askdirectory(title="选择媒体文件文件夹")
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
        """开始处理（异步运行流水线）"""
        input_path = self.input_var.get()
        
        if not input_path or not os.path.exists(input_path):
            messagebox.showwarning("提示", "请选择有效的视频/音频文件或文件夹")
            return
        
        output_dir = self.output_var.get()
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.abspath(output_dir)
        
        is_dir = os.path.isdir(input_path)
        audio_exts = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"}
        video_exts = {".mp4", ".avi", ".mkv", ".mov"}
        media_exts = audio_exts | video_exts
        
        if is_dir:
            files = [os.path.join(input_path, f) for f in os.listdir(input_path) if os.path.splitext(f)[1].lower() in media_exts]
            self._log(f"批量处理: {len(files)} 个媒体文件")
            self._log(f"文件夹: {input_path}")
        else:
            ext = os.path.splitext(input_path)[1].lower()
            is_audio = ext in audio_exts
            files = [input_path]
            self._log(f"文件: {os.path.basename(input_path)}")
            self._log(f"类型: {'音频' if is_audio else '视频'}")
        self._log(f"输出: {output_path}")
        self._log(f"输出: {output_path}")
        self._log(f"Whisper模型: {self.model_var.get()}")
        self._log(f"AI增强: {'开启' if self.ai_var.get() else '关闭'}")
        
        if not PIPELINE_AVAILABLE:
            self._log("⚠️ 流水线模块未加载（缺少依赖或路径），使用模拟模式")
            if not is_audio:
                self._log("  → 模拟: 从视频中提取音频...")
            self._log("处理完成！")
            messagebox.showinfo("完成", f"模拟模式完成\n\n输出目录:\n{output_path}")
            return
        
        self._set_buttons_state(tk.DISABLED)
        self.status.config(text="处理中...")
        
        def run_pipeline():
            try:
                config = PipelineConfig(
                    whisper_model=self.model_var.get(),
                    ai_enabled=self.ai_var.get(),
                    ai_provider=self.provider_var.get(),
                    ai_api_key=self.api_key_var.get(),
                    ai_model=self.ai_model_var.get(),
                    ai_base_url=getattr(self, 'custom_url_var', tk.StringVar(value="")).get() if self.provider_var.get() == "custom" else "",
                    fix_punctuation=self.fix_punc_var.get(),
                    add_paragraphs=self.add_para_var.get(),
                    remove_filler=self.remove_fill_var.get(),
                    logic_refine=self.logic_refine_var.get(),
                    style_polish=self.style_polish_var.get(),
                    target_audience=self.audience_var.get(),
                    tone=self.tone_var.get(),
                    generate_summary=self.summary_var.get(),
                    extract_keywords=self.keywords_var.get(),
                )
                pipeline = TranscribePipeline(config=config)
                result = pipeline.process(input_path, output_dir)
                self.root.after(0, lambda: self._on_pipeline_done(result, output_path))
            except Exception as e:
                self.root.after(0, lambda: self._log(f"  ✗ 处理失败: {e}"))
                root.after(0, lambda: messagebox.showerror("错误", f"处理失败:\n{str(e)}"))
            finally:
                self.root.after(0, lambda: self._set_buttons_state(tk.NORMAL))
                self.root.after(0, lambda: self.status.config(text="就绪"))
        
        t = threading.Thread(target=run_pipeline, daemon=True)
        t.start()
    
    def _on_pipeline_done(self, result, output_path):
        """流水线完成回调"""
        if result.get("success"):
            files = result.get("output_files", [])
            for f in files[:5]:
                self._log(f"  ✓ {os.path.basename(f)}")
            if len(files) > 5:
                self._log(f"  ...和其他 {len(files)-5} 个文件")
            self._log("全部完成！")
            messagebox.showinfo("完成", f"处理完成！\n\n输出目录:\n{output_path}")
        else:
            error = result.get("error", "未知错误")
            self._log(f"  ✗ 失败: {error}")
            messagebox.showerror("错误", f"处理失败:\n{error}")
    
    def _set_buttons_state(self, state):
        for child in self.btn_frame.winfo_children():
            if isinstance(child, ttk.Button):
                child.config(state=state)
    
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


五、处理速度参考（约10-15分钟视频）
   云端 API（硅基流动）:  ~13 分钟（转录+四步精修+摘要）
   本地 Ollama（CPU）:   ~20-30 分钟（取决于CPU性能）
   仅转录（关AI增强）:    ~2 分钟

可关闭摘要/关键词来提速。

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


def main():
    """主函数"""
    root = tk.Tk()
    app = VideoTranscribeApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
