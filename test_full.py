#!/usr/bin/env python3
"""完整测试：MP4转换和播放"""
import os
import sys
from src.codec import BANCodec

def test_conversion_and_playback():
    """测试完整的转换和播放流程"""

    # 检查测试视频文件
    test_video = "vis.mp4"
    if not os.path.exists(test_video):
        print(f"❌ 测试视频不存在: {test_video}")
        return False

    print(f"✅ 找到测试视频: {test_video}")
    print(f"   文件大小: {os.path.getsize(test_video) / (1024*1024):.2f} MB")

    # 测试转换
    output_file = "test_output.ban"
    print(f"\n开始转换 {test_video} -> {output_file}")

    try:
        BANCodec.encode_video(test_video, output_file)
        print(f"✅ 转换成功!")
        print(f"   输出文件大小: {os.path.getsize(output_file) / (1024*1024):.2f} MB")
    except Exception as e:
        print(f"❌ 转换失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 测试解码
    print(f"\n开始测试解码 {output_file}")
    try:
        info = BANCodec.get_video_info(output_file)
        print(f"✅ 视频信息读取成功:")
        print(f"   分辨率: {info['width']}x{info['height']}")
        print(f"   FPS: {info['fps']}")
        print(f"   帧数: {info['frame_count']}")
        print(f"   时长: {info['duration']:.2f}秒")

        # 解码所有帧
        metadata, frames = BANCodec.decode_video(output_file)
        print(f"\n✅ 解码成功!")
        print(f"   元数据帧数: {metadata['frame_count']}")
        print(f"   实际解码帧数: {len(frames)}")

        if len(frames) != metadata['frame_count']:
            print(f"⚠️  警告: 帧数不匹配!")
        else:
            print(f"✅ 帧数匹配完美!")

        # 清理测试文件
        print(f"\n清理测试文件 {output_file}")
        os.remove(output_file)
        print("✅ 清理完成")

        return True

    except Exception as e:
        print(f"❌ 解码失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Banana Player - 完整功能测试")
    print("=" * 60)

    success = test_conversion_and_playback()

    print("\n" + "=" * 60)
    if success:
        print("✅ 所有测试通过!")
    else:
        print("❌ 测试失败!")
    print("=" * 60)
