# -*- coding: utf-8 -*-
"""
测试 jy.ban 文件解码
"""
import sys
import os

# 设置编码环境
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['LANG'] = 'zh_CN.UTF-8'
os.environ['LC_ALL'] = 'zh_CN.UTF-8'

from src.codec import BANCodec
from src.config import PinkConfig

def test_jy_ban():
    """测试jy.ban文件"""
    ban_file = 'jy.ban'

    print("=" * 60)
    print(f"测试文件: {ban_file}")
    print("=" * 60)

    # 检查文件是否存在
    if not os.path.exists(ban_file):
        print(f"❌ 错误: 文件 {ban_file} 不存在!")
        return False

    # 获取文件大小
    file_size = os.path.getsize(ban_file)
    print(f"📁 文件大小: {file_size / (1024*1024):.2f} MB")

    try:
        # 测试获取视频信息
        print("\n📊 尝试获取视频信息...")
        info = BANCodec.get_video_info(ban_file)
        print(f"✅ 视频信息获取成功:")
        print(f"   - FPS: {info['fps']}")
        print(f"   - 分辨率: {info['width']}x{info['height']}")
        print(f"   - 帧数: {info['frame_count']}")
        print(f"   - 时长: {info['duration']:.2f} 秒")

        # 测试解码第一帧
        print("\n🎬 尝试解码第一帧...")
        frame = BANCodec.decode_single_frame(ban_file, 0)
        if frame is not None:
            print(f"✅ 第一帧解码成功:")
            print(f"   - 帧尺寸: {frame.shape}")
            print(f"   - 数据类型: {frame.dtype}")
        else:
            print("❌ 第一帧解码失败!")
            return False

        # 测试解码中间帧
        if info['frame_count'] > 1:
            mid_frame_idx = info['frame_count'] // 2
            print(f"\n🎬 尝试解码中间帧 (索引: {mid_frame_idx})...")
            frame = BANCodec.decode_single_frame(ban_file, mid_frame_idx)
            if frame is not None:
                print(f"✅ 中间帧解码成功:")
                print(f"   - 帧尺寸: {frame.shape}")
            else:
                print("❌ 中间帧解码失败!")
                return False

        print("\n" + "=" * 60)
        print("✅ 所有测试通过! jy.ban 文件格式正确")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        print("\n详细错误信息:")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_jy_ban()
    sys.exit(0 if success else 1)
