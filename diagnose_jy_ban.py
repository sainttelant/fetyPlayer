# -*- coding: utf-8 -*-
"""
jy.ban 文件详细诊断脚本
"""
import sys
import os

# 设置编码环境
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['LANG'] = 'zh_CN.UTF-8'
os.environ['LC_ALL'] = 'zh_CN.UTF-8'

def diagnose_ban_file(ban_file):
    """诊断.ban文件"""
    print("=" * 70)
    print(f"🔍 诊断文件: {ban_file}")
    print("=" * 70)

    # 检查文件是否存在
    if not os.path.exists(ban_file):
        print(f"❌ 错误: 文件 {ban_file} 不存在!")
        return False

    # 获取文件大小
    file_size = os.path.getsize(ban_file)
    print(f"📁 文件大小: {file_size / (1024*1024):.2f} MB ({file_size} 字节)")

    # 读取文件头
    try:
        with open(ban_file, 'rb') as f:
            # 读取前100字节
            header = f.read(100)
            print(f"\n📋 文件头 (前100字节):")
            print(f"   十六进制: {header[:50].hex()}")
            print(f"   ASCII: {header[:50]}")

            # 检查魔数
            magic = header[:4]
            print(f"\n🔑 魔数: {magic}")
            print(f"   期望: BAN1")
            print(f"   匹配: {'✅ 是' if magic == b'BAN1' else '❌ 否'}")

            # 读取盐值和IV
            salt = header[4:36]
            iv = header[36:52]
            print(f"\n🔐 加密信息:")
            print(f"   盐值 (32字节): {salt.hex()[:40]}...")
            print(f"   IV (16字节): {iv.hex()}")

            # 读取元数据
            metadata = header[52:68]
            import struct
            fps, width, height, frame_count = struct.unpack('IIII', metadata)
            print(f"\n📊 视频元数据:")
            print(f"   FPS: {fps}")
            print(f"   分辨率: {width}x{height}")
            print(f"   帧数: {frame_count}")
            print(f"   时长: {frame_count / fps:.2f} 秒" if fps > 0 else "   时长: 未知")

            # 检查帧大小表
            f.seek(68)
            sizes_len_data = f.read(4)
            if len(sizes_len_data) == 4:
                sizes_len = struct.unpack('I', sizes_len_data)[0]
                print(f"\n📏 帧大小表:")
                print(f"   长度: {sizes_len} 字节")

                if sizes_len > 0 and sizes_len < file_size:
                    encrypted_sizes = f.read(sizes_len)
                    print(f"   实际读取: {len(encrypted_sizes)} 字节")

                    # 尝试解密
                    try:
                        from src.codec import deobfuscate_data, decrypt_aes, calculate_checksum, PinkConfig
                        import hashlib

                        # 派生密钥
                        seed = PinkConfig.BAN_MAGIC_NUMBER + salt + PinkConfig.APP_NAME.encode()
                        master_key = hashlib.pbkdf2_hmac('sha256', seed, b'BananaKeyDerivation', 100000, 32)
                        print(f"\n🔑 密钥派生:")
                        print(f"   密钥长度: {len(master_key)} 字节")
                        print(f"   密钥 (前16字节): {master_key[:16].hex()}")

                        # 解密帧大小表
                        sizes_packet = decrypt_aes(encrypted_sizes, master_key, iv)
                        if sizes_packet:
                            print(f"\n✅ 帧大小表解密成功!")
                            print(f"   数据包长度: {len(sizes_packet)} 字节")

                            # 验证校验和
                            expected_sum = sizes_packet[:16]
                            actual_sum = calculate_checksum(sizes_packet[16:])
                            print(f"\n🔍 校验和验证:")
                            print(f"   期望: {expected_sum.hex()}")
                            print(f"   实际: {actual_sum.hex()}")
                            print(f"   匹配: {'✅ 是' if expected_sum == actual_sum else '❌ 否'}")

                            # 解析帧大小
                            sizes_data_bytes = sizes_packet[16:]
                            stored_frame_count = struct.unpack('I', sizes_data_bytes[:4])[0]
                            sizes_str = sizes_data_bytes[4:].decode('utf-8')
                            frame_sizes = [int(s) for s in sizes_str.split(',') if s]

                            print(f"\n📊 帧大小统计:")
                            print(f"   存储的帧数: {stored_frame_count}")
                            print(f"   解析的帧数: {len(frame_sizes)}")
                            if frame_sizes:
                                print(f"   最小帧大小: {min(frame_sizes)} 字节")
                                print(f"   最大帧大小: {max(frame_sizes)} 字节")
                                print(f"   平均帧大小: {sum(frame_sizes) / len(frame_sizes):.0f} 字节")
                                print(f"   总帧数据大小: {sum(frame_sizes) / (1024*1024):.2f} MB")
                        else:
                            print(f"\n❌ 帧大小表解密失败!")
                    except Exception as e:
                        print(f"\n❌ 解密过程出错: {e}")
                        import traceback
                        traceback.print_exc()
                else:
                    print(f"\n❌ 帧大小表长度无效: {sizes_len}")
            else:
                print(f"\n❌ 无法读取帧大小表长度")

    except Exception as e:
        print(f"\n❌ 诊断过程出错: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 70)
    print("✅ 诊断完成")
    print("=" * 70)
    return True

if __name__ == "__main__":
    ban_file = 'jy.ban'
    diagnose_ban_file(ban_file)
