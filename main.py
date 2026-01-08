# -*- coding: utf-8 -*-
"""
Banana Player - Main entry point
Pink-themed video player
"""
import sys
import os

# Set encoding environment (fix Chinese garbled text)
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['LANG'] = 'zh_CN.UTF-8'
os.environ['LC_ALL'] = 'zh_CN.UTF-8'

# Set Windows console encoding
if sys.platform.startswith('win'):
    import ctypes
    ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    ctypes.windll.kernel32.SetConsoleCP(65001)

import tkinter as tk
from tkinter import font

def get_system_font():
    """Get system available Chinese font"""
    system = sys.platform
    
    if system.startswith('win'):
        # Windows system
        fonts = ['Microsoft YaHei UI', 'SimHei', 'WenQuanYi Micro Hei', 'Noto Sans CJK SC', 'Arial']
    elif system.startswith('darwin'):
        # macOS system
        fonts = ['PingFang SC', 'Heiti SC', 'WenQuanYi Micro Hei', 'Noto Sans CJK SC', 'Arial']
    else:
        # Linux system
        fonts = ['WenQuanYi Micro Hei', 'Noto Sans CJK SC', 'Droid Sans Fallback', 'SimHei', 'AR PL UMing CN', 'Arial']
    
    # Check available fonts
    available_fonts = set(font.families())
    for f in fonts:
        if f in available_fonts:
            return f
    
    return 'Arial'  # Default fallback

from src.player import BananaPlayerPink

def main():
    """Main function"""
    root = tk.Tk()
    
    # Set Tkinter font encoding (key step for Chinese display)
    root.option_add('*Font', get_system_font())
    
    # Try to set window icon
    try:
        root.iconbitmap('icon.ico')
    except:
        pass
    
    # Create player instance
    app = BananaPlayerPink(root)
    
    # Start main loop
    root.mainloop()

if __name__ == "__main__":
    main()
