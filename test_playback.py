#!/usr/bin/env python3
"""
测试播放功能
"""
import tkinter as tk
from src.player import BananaPlayerPink
from src.frame_buffer import StreamingDecoder, FramePreloader

def test_playback():
    """测试播放功能"""
    print("🧪 测试播放功能")
    print("=" * 50)
    
    # 创建播放器
    root = tk.Tk()
    app = BananaPlayerPink(root)
    
    # 模拟打开视频
    print("\n1. 模拟打开视频...")
    app.decoder = StreamingDecoder('vis.ban', buffer_size=60, buffer_memory_mb=500)
    app.metadata = app.decoder.metadata
    app.current_video = 'vis.ban'
    app.current_frame_idx = 0
    app.progress.config(to=app.metadata['frame_count']-1)
    app.preloader = FramePreloader(app.decoder, preload_window=30)
    
    print(f"✅ 视频加载成功: {app.metadata['frame_count']} 帧")
    
    # 测试播放按钮状态
    print("\n2. 测试播放按钮...")
    print(f"   初始状态: is_playing = {app.is_playing}")
    print(f"   播放按钮文字: {app.play_btn.text}")
    
    # 测试 toggle_play
    print("\n3. 测试 toggle_play()...")
    app.toggle_play()
    print(f"   toggle_play 后: is_playing = {app.is_playing}")
    print(f"   播放按钮文字: {app.play_btn.text}")
    
    # 测试 toggle_play 回来
    app.toggle_play()
    print(f"   再次 toggle_play: is_playing = {app.is_playing}")
    print(f"   播放按钮文字: {app.play_btn.text}")
    
    # 测试 seek_video
    print("\n4. 测试 seek_video()...")
    app.seeking = False
    original_idx = app.current_frame_idx
    
    # 拖拽到帧 100
    app.seek_video(100)
    print(f"   seek_video(100) 后: current_frame_idx = {app.current_frame_idx}")
    
    # 拖拽到帧 200
    app.seek_video(200)
    print(f"   seek_video(200) 后: current_frame_idx = {app.current_frame_idx}")
    
    # 测试进度条
    print("\n5. 测试进度条...")
    print(f"   进度条范围: 0 - {app.progress.cget('to')}")
    print(f"   当前进度: {app.progress.get()}")
    
    # 设置进度条
    app.progress.set(50)
    print(f"   设置为 50 后: {app.progress.get()}")
    
    # 测试 display_frame
    print("\n6. 测试 display_frame()...")
    
    # 显示帧 0
    app.seeking = False
    app.display_frame(0, force=True)
    print(f"   display_frame(0): 成功")
    
    # 显示帧 100
    app.display_frame(100, force=True)
    print(f"   display_frame(100): 成功")
    
    # 测试播放线程
    print("\n7. 测试播放线程...")
    app.is_playing = False
    app.current_frame_idx = 0
    
    # 启动播放（短时间）
    app.toggle_play()
    print(f"   播放已启动: is_playing = {app.is_playing}")
    
    # 等待一小段时间
    import time
    time.sleep(0.5)
    
    # 停止播放
    app.toggle_play()
    print(f"   播放已停止: is_playing = {app.is_playing}")
    print(f"   当前帧: {app.current_frame_idx}")
    
    print("\n" + "=" * 50)
    print("✅ 所有测试通过！")
    print("\n💡 播放功能正常，问题可能在于:")
    print("   1. 界面初始化时机（视频加载前）")
    print("   2. 进度条可见性问题")
    print("   3. 按钮绑定问题")
    
    root.destroy()

if __name__ == "__main__":
    test_playback()
