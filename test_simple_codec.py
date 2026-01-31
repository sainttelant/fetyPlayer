# -*- coding: utf-8 -*-
"""
测试简化版编解码器
"""
import sys
import os

# 添加src目录到路径
#sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from .src.simple_codec import SimpleBANCodec

def test_simple_codec():
    """测试简化版编解码器"""
    if len(sys.argv) < 2:
        print("用法: python test_simple_codec.py <input_video.mp4>")
        return
    
    input_file = sys.argv[1]
    output_file = input_file.rsplit('.', 1)[0] + '_simple.ban'
    
    print("=" * 70)
    print("简化版编解码器测试")
    print("=" * 70)
    
    try:
        # 测试编码
        print(f"\n📹 编码视频: {input_file}")
        SimpleBANCodec.encode_video(input_file, output_file)
        
        # 测试解码
        print(f"\n🎬 解码视频: {output_file}")
        metadata, frames = SimpleBANCodec.decode_video(output_file)
        
        print(f"\n✅ 测试成功!")
        print(f"   解码帧数: {len(frames)}")
        print(f"   元数据帧数: {metadata['frame_count']}")
        print(f"   FPS: {metadata['fps']}")
        print(f"   分辨率: {metadata['width']}x{metadata['height']}")
        
        # 测试单帧解码
        print(f"\n🔍 测试单帧解码...")
        frame = SimpleBANCodec.decode_single_frame(output_file, 0)
        if frame is not None:
            print(f"   ✅ 第0帧解码成功: {frame.shape}")
        else:
            print(f"   ❌ 第0帧解码失败")
        
        print("\n" + "=" * 70)
        print("✅ 所有测试通过!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_codec()
