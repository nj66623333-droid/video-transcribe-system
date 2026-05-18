#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频转录系统 - 主入口
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.app import VideoTranscribeApp
import tkinter as tk


def main():
    """主函数"""
    root = tk.Tk()
    app = VideoTranscribeApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
