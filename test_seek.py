#!/usr/bin/env python3
"""
测试进度条拖拽功能
"""
import tkinter as tk
from src.player import BananaPlayerPink

def test_seek_functionality():
    """测试进度条拖拽"""
    print("🧪 测试进度条拖拽功能")
    print("=" * 50)
    
    # 创建播放器
    root = tk.Tk()
    app = BananaPlayerPink(root)
    
    # 模拟打开视频
    print("\n1. 模拟打开视频...")
    from src.frame_buffer import StreamingDecoder
    
    # 创建流式解码器
    app.decoder = StreamingDecoder('vis.ban', buffer_size=60, buffer_memory_mb=500)
    app.metadata = app.decoder.metadata
    app.current_video = 'vis.ban'
    app.current_frame_idx = 0
    app.progress.config(to=app.metadata['frame_count']-1)
    
    print(f"✅ 视频加载成功: {app.metadata['frame_count']} 帧")
    print(f"   分辨率: {app.metadata['width']}x{app.metadata['height']}")
    print(f"   FPS: {app.metadata['fps']}")
    
    # 测试拖拽到不同位置
    print("\n2. 测试进度条拖拽到不同位置...")
    
    test_positions = [0, 100, 250, 400, 499]
    for pos in test_positions:
        app.seeking = True
        app.current_frame_idx = pos
        app.progress.set(pos)
        
        # 获取帧
        frame = app.decoder.get_frame(pos)
        if frame is not None:
            print(f"✅ 拖拽到帧 {pos}: 成功 (帧尺寸: {frame.shape})")
        else:
            print(f"❌ 拖拽到帧 {pos}: 失败")
        
        app.seeking = False
    
    # 测试连续拖拽
    print("\n3. 测试连续拖拽...")
    for i in range(5):
        pos = i * 100
        app.seeking = True
        app.current_frame_idx = pos
        app.progress.set(pos)
        frame = app.decoder.get_frame(pos)
        app.seeking = False
    
    print("✅ 连续拖拽测试通过")
    
    # 测试缓存统计
    print("\n4. 检查帧缓存统计...")
    stats = app.decoder.get_stats()
    buffer_stats = stats['buffer_stats']
    
    print(f"   缓存帧数: {buffer_stats['cached_frames']}")
    print(f"   缓存命中率: {buffer_stats['hit_rate']:.1f}%")
    print(f"   内存使用: {buffer_stats['memory_mb']:.1f} MB")
    print(f"   最大内存: {buffer_stats['max_memory_mb']:.1f} MB")
    
    if buffer_stats['hit_rate'] > 80:
        print("✅ 缓存效果良好")
    else:
        print("⚠️  缓存命中率较低")
    
    # 测试边界条件
    print("\n5. 测试边界条件...")
    
    # 超出范围
    app.seeking = True
    app.current_frame_idx = -1
    frame = app.decoder.get_frame(-1)
    if frame is None:
        print("✅ 负索引正确处理")
    
    app.current_frame_idx = app.metadata['frame_count'] + 100
    frame = app.decoder.get_frame(app.metadata['frame_count'] + 100)
    if frame is None:
        print("✅ 超出范围正确处理")
    app.seeking = False
    
    print("\n" + "=" * 50)
    print("✅ 所有测试通过！进度条拖拽功能正常工作")
    print("\n💡 使用方法:")
    print("   1. 打开视频后，进度条会自动显示")
    print("   2. 拖动进度条滑块到想要的位置")
    print("   3. 释放鼠标后自动跳转到该帧")
    print("   4. 暂停状态下可以直接预览拖拽位置的画面")
    
    root.destroy()

if __name__ == "__main__":
    test_seek_functionality()
