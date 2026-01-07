#!/usr/bin/env python3
"""测试解码.ban文件"""
from src.codec import BANCodec
import sys

def test_decode(ban_file):
    print(f"开始测试解码: {ban_file}")
    try:
        # 先获取视频信息
        info = BANCodec.get_video_info(ban_file)
        print(f"视频信息:")
        print(f"  分辨率: {info['width']}x{info['height']}")
        print(f"  FPS: {info['fps']}")
        print(f"  帧数: {info['frame_count']}")
        print(f"  时长: {info['duration']:.2f}秒")

        # 解码前5帧测试
        print("\n开始解码前5帧...")
        metadata, frames = BANCodec.decode_video(ban_file)

        print(f"\n解码结果:")
        print(f"  元数据帧数: {metadata['frame_count']}")
        print(f"  实际解码帧数: {len(frames)}")

        if len(frames) > 0:
            print(f"  第一帧形状: {frames[0].shape}")
            print("✅ 解码成功!")
        else:
            print("❌ 解码失败: 没有帧数据")

    except Exception as e:
        print(f"❌ 解码出错: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_decode(sys.argv[1])
    else:
        test_decode("vis.ban")
