# -*- coding: utf-8 -*-
"""
旧版本.ban格式解码器
用于兼容旧版本编码的.ban文件
"""
import cv2
import numpy as np
import struct
import os
from src.codec import deobfuscate_data, decrypt_aes, calculate_checksum, PinkConfig
import hashlib

def decode_legacy_ban(ban_path):
    """解码旧版本的.ban文件

    旧版本格式:
    [4字节] 魔数: "BAN1" (已混淆)
    [16字节] 头部: FPS, Width, Height, Frame Count
    [N字节] 帧数据 (每帧: 4字节大小 + JPEG数据)
    """
    print("=" * 70)
    print(f"🔍 尝试解码旧版本格式: {ban_path}")
    print("=" * 70)

    try:
        with open(ban_path, 'rb') as f:
            # 读取并验证magic number
            magic = f.read(4)
            print(f"\n📋 魔数 (原始): {magic.hex()}")

            # 尝试反混淆
            try:
                magic_deobf = deobfuscate_data(magic)
                print(f"📋 魔数 (反混淆): {magic_deobf}")
                if magic_deobf != b'BAN1':
                    print("❌ 不是旧版本格式")
                    return None, None
            except:
                # 如果反混淆失败，检查是否直接是BAN1
                if magic != b'BAN1':
                    print("❌ 不是旧版本格式")
                    return None, None
                print("✅ 直接匹配BAN1")

            # 读取元数据
            header_data = f.read(16)
            if len(header_data) < 16:
                print("❌ 文件头不完整")
                return None, None

            fps, width, height, frame_count = struct.unpack('IIII', header_data)
            metadata = {
                'fps': fps,
                'width': width,
                'height': height,
                'frame_count': frame_count
            }

            print(f"\n📊 视频元数据:")
            print(f"   FPS: {fps}")
            print(f"   分辨率: {width}x{height}")
            print(f"   帧数: {frame_count}")
            print(f"   时长: {frame_count / fps:.2f} 秒" if fps > 0 else "   时长: 未知")

            # 读取帧数据
            frames = []
            frame_sizes = []

            for i in range(frame_count):
                # 读取帧大小
                size_data = f.read(4)
                if len(size_data) < 4:
                    print(f"⚠️  文件在第{i}帧提前结束")
                    break

                frame_size = struct.unpack('I', size_data)[0]

                # 检查帧大小是否合理
                if frame_size <= 0 or frame_size > 50 * 1024 * 1024:
                    print(f"⚠️  第{i}帧大小异常: {frame_size}")
                    break

                frame_sizes.append(frame_size)

                # 读取帧数据
                frame_data = f.read(frame_size)
                if len(frame_data) < frame_size:
                    print(f"⚠️  第{i}帧数据不完整")
                    break

                # 解码帧
                nparr = np.frombuffer(frame_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                if frame is None:
                    print(f"⚠️  第{i}帧解码失败")
                    continue

                frames.append(frame)

                if (i + 1) % 100 == 0:
                    print(f"   已解码 {i + 1}/{frame_count} 帧...")

            print(f"\n✅ 解码完成: {len(frames)}/{frame_count} 帧")
            print(f"   最小帧大小: {min(frame_sizes) if frame_sizes else 0} 字节")
            print(f"   最大帧大小: {max(frame_sizes) if frame_sizes else 0} 字节")
            print(f"   平均帧大小: {sum(frame_sizes) / len(frame_sizes) if frame_sizes else 0:.0f} 字节")

            # 更新元数据为实际读取的帧数
            metadata['frame_count'] = len(frames)

            return metadata, frames

    except Exception as e:
        print(f"\n❌ 解码失败: {e}")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == "__main__":
    ban_file = 'jy.ban'
    metadata, frames = decode_legacy_ban(ban_file)

    if metadata and frames:
        print("\n" + "=" * 70)
        print("✅ 旧版本格式解码成功!")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("❌ 旧版本格式解码失败")
        print("=" * 70)
