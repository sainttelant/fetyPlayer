#!/usr/bin/env python3
"""
测试界面组件显示
"""
import tkinter as tk
from src.player import BananaPlayerPink

def test_ui_visibility():
    """测试UI组件可见性"""
    print("🧪 测试UI组件可见性")
    print("=" * 50)
    
    # 创建播放器
    root = tk.Tk()
    app = BananaPlayerPink(root)
    
    # 测试控制面板
    print("\n1. 检查控制面板...")
    control_frame = app.control_frame
    print(f"   控制面板存在: {control_frame is not None}")
    print(f"   控制面板类型: {type(control_frame)}")
    
    # 测试进度条
    print("\n2. 检查进度条...")
    progress = app.progress
    print(f"   进度条存在: {progress is not None}")
    print(f"   进度条类型: {type(progress)}")
    
    if progress is not None:
        print(f"   进度条范围: {progress.cget('from')} - {progress.cget('to')}")
        print(f"   进度条当前值: {progress.get()}")
        
        # 检查进度条是否可见
        try:
            winfo = progress.winfo_width()
            print(f"   进度条宽度: {winfo} 像素")
            print(f"   进度条可见: {winfo > 0}")
        except:
            print(f"   进度条尚未显示")
    
    # 测试播放按钮
    print("\n3. 检查播放按钮...")
    play_btn = app.play_btn
    print(f"   播放按钮存在: {play_btn is not None}")
    print(f"   播放按钮类型: {type(play_btn)}")
    if play_btn is not None:
        print(f"   播放按钮文字: {play_btn.text}")
    
    # 测试时间标签
    print("\n4. 检查时间标签...")
    time_label = app.time_label
    print(f"   时间标签存在: {time_label is not None}")
    print(f"   时间标签类型: {type(time_label)}")
    if time_label is not None:
        print(f"   时间标签文字: {time_label.cget('text')}")
    
    # 检查布局
    print("\n5. 检查布局...")
    print(f"   主窗口尺寸: {root.winfo_width()}x{root.winfo_height()}")
    try:
        print(f"   控制面板尺寸: {control_frame.winfo_width()}x{control_frame.winfo_height()}")
    except:
        print(f"   控制面板尺寸: 尚未显示")
    
    print("\n" + "=" * 50)
    print("✅ UI组件检查完成")
    print("\n💡 现在启动完整GUI查看进度条是否显示...")
    print("   如果进度条仍然不可见，可能需要:")
    print("   1. 调整窗口大小")
    print("   2. 检查背景色和进度条颜色对比")
    print("   3. 查看窗口是否被其他元素遮挡")
    
    # 保持窗口打开一段时间
    root.after(5000, root.destroy)
    root.mainloop()

if __name__ == "__main__":
    test_ui_visibility()
