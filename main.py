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
import tkinter.font as tkfont


def get_system_font():
    """Get system available Chinese font (old version)"""
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
    available_fonts = set(tkfont.families())
    for f in fonts:
        if f in available_fonts:
            return f"{f} 12"  # include default size
    return 'Arial 12'  # Default fallback


def get_system_font_v2():
    """Alternative: explicit font with size fallback (for reliability)"""
    system = sys.platform
    size = 12
    if system.startswith('win'):
        fonts = ['Microsoft YaHei UI', 'SimHei', 'WenQuanYi Micro Hei', 'Noto Sans CJK SC', 'Arial']
    elif system.startswith('darwin'):
        fonts = ['PingFang SC', 'Heiti SC', 'WenQuanYi Micro Hei', 'Noto Sans CJK SC', 'Arial']
    else:
        fonts = ['WenQuanYi Micro Hei', 'Noto Sans CJK SC', 'Droid Sans Fallback', 'SimHei', 'AR PL UMing CN', 'Arial']
    available_fonts = set(tkfont.families())
    chosen = None
    for f in fonts:
        if f in available_fonts:
            chosen = f
            break
    if chosen:
        return f"{chosen} {size}"
    return f"Arial {size}"


def parse_font_desc(font_desc):
    """Parse a font description like 'Family 12' into (family, size)."""
    if not font_desc:
        return ("Arial", 12)
    parts = font_desc.split()
    if len(parts) >= 2:
        try:
            size = int(parts[-1])
            family = " ".join(parts[:-1])
            return (family, size)
        except Exception:
            return (font_desc, 12)
    return (font_desc, 12)


def set_default_font_from_desc(root, font_desc):
    """Create a Font object from description and apply as default font."""
    family, size = parse_font_desc(font_desc)
    try:
        AppFont = tkfont.Font(family=family, size=size)
        root.option_add('*Font', AppFont)
        return True
    except Exception:
        return False


from src.player import BananaPlayerPink


def main():
    """Main function"""
    root = tk.Tk()

    # Set default font robustly
    font_desc = get_system_font_v2()
    if not set_default_font_from_desc(root, font_desc):
        # Fallback to Arial if anything goes wrong
        try:
            AppFont = tkfont.Font(family='Arial', size=12)
            root.option_add('*Font', AppFont)
        except Exception:
            pass

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