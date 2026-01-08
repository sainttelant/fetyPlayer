#!/usr/bin/env python3
"""测试vis2.ban文件的调试脚本"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.codec import BANCodec

def test_ban_file_debug(ban_file):
    """详细测试.ban文件"""
    print("=" * 60)
    print(f"🔍 开始详细分析: {ban_file}")
    print("=" * 60)
    
    # 检查文件是否存在
    if not os.path.exists(ban_file):
        print(f"❌ 文件不存在: {ban_file}")
        return False
    
    # 显示文件大小
    file_size = os.path.getsize(ban_file)
    print(f"📁 文件大小: {file_size} 字节 ({file_size / 1024:.2f} KB)")
    
    # 先尝试读取头部信息
    print("\n📖 步骤1: 读取文件头部...")
    try:
        with open(ban_file, 'rb') as f:
            # 读取magic number
            magic = f.read(4)
            print(f"   Magic number: {magic}")
            print(f"   期望值: b'BAN1'")
            if magic == b'BAN1':
                print("   ✅ Magic number正确")
            else:
                print(f"   ❌ Magic number不匹配! 可能文件格式不同")
                # 尝试显示magic number的原始字节
                print(f"   原始字节: {magic.hex()}")
            
            # 尝试读取更多字节分析
            f.seek(0)
            header_bytes = f.read(24)
            print(f"\n   前24字节hex: {header_bytes.hex()}")
            
            # 回到开头，解析头部
            f.seek(0)
            magic = f.read(4)
            if magic == b'BAN1':
                header_data = f.read(16)
                import struct
                fps, width, height, frame_count = struct.unpack('IIII', header_data)
                print(f"\n   解析的头部信息:")
                print(f"   - FPS: {fps}")
                print(f"   - Width: {width}")
                print(f"   - Height: {height}")
                print(f"   - Frame count: {frame_count}")
                
                # 估算文件大小
                if frame_count > 0:
                    avg_frame_size = file_size / frame_count
                    print(f"   - 平均每帧大小: {avg_frame_size:.2f} 字节")
                
    except Exception as e:
        print(f"❌ 读取文件头部出错: {e}")
    
    # 使用BANCodec获取信息
    print("\n📊 步骤2: 使用BANCodec获取信息...")
    try:
        info = BANCodec.get_video_info(ban_file)
        print(f"✅ 视频信息获取成功:")
        print(f"   分辨率: {info['width']}x{info['height']}")
        print(f"   FPS: {info['fps']}")
        print(f"   帧数: {info['frame_count']}")
        print(f"   时长: {info['duration']:.2f}秒")
    except Exception as e:
        print(f"❌ 获取视频信息失败: {e}")
    
    # 完整解码测试
    print("\n🎬 步骤3: 完整解码测试...")
    try:
        metadata, frames = BANCodec.decode_video(ban_file)
        print(f"\n✅ 解码完成!")
        print(f"   元数据帧数: {metadata['frame_count']}")
        print(f"   实际解码帧数: {len(frames)}")
        
        if len(frames) > 0:
            print(f"\n   第一帧信息:")
            print(f"   - 形状: {frames[0].shape}")
            print(f"   - 数据类型: {frames[0].dtype}")
            print(f"   - 值范围: [{frames[0].min()}, {frames[0].max()}]")
            
            print(f"\n   最后帧信息:")
            print(f"   - 形状: {frames[-1].shape}")
            print("=" * 60)
            print("🎉 测试通过! 文件可以正常解码。")
            print("=" * 60)
            return True
        else:
            print("\n❌ 没有帧数据!")
            return False
            
    except Exception as e:
        print(f"\n❌ 解码失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
    else:
        test_file = "vis2.ban"
    
    print(f"测试文件: {test_file}")
    success = test_ban_file_debug(test_file)
    sys.exit(0 if success else 1)
