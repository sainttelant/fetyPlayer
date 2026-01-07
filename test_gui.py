#!/usr/bin/env python3
"""测试GUI启动"""
import tkinter as tk
from src.player import BananaPlayerPink
import sys

def test_gui():
    """测试GUI能否正常启动"""
    print("启动GUI测试...")
    try:
        root = tk.Tk()
        print("✅ Tkinter根窗口创建成功")

        app = BananaPlayerPink(root)
        print("✅ 播放器初始化成功")
        print("✅ GUI启动成功！")
        print("\n注意: GUI窗口将在3秒后自动关闭...")

        # 3秒后自动关闭
        root.after(3000, root.destroy)
        root.mainloop()

        print("✅ GUI测试完成")
        return True

    except Exception as e:
        print(f"❌ GUI启动失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_gui()
