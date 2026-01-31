# -*- coding: utf-8 -*-
"""
精确分析jy.ban文件结构
"""
import struct

def analyze_ban_structure(ban_file):
    """精确分析.ban文件结构"""
    print("=" * 70)
    print(f"🔍 精确分析文件: {ban_file}")
    print("=" * 70)

    with open(ban_file, 'rb') as f:
        # 读取前200字节
        data = f.read(200)
        print(f"\n📋 文件前200字节分析:")

        # 显示每个字段
        print(f"\n字段1: 魔数 (0-3字节)")
        magic = data[0:4]
        print(f"   原始: {magic.hex()}")
        print(f"   ASCII: {magic}")

        # 反混淆
        from src.codec import deobfuscate_data
        try:
            magic_deobf = deobfuscate_data(magic)
            print(f"   反混淆: {magic_deobf}")
            print(f"   是否BAN1: {'✅ 是' if magic_deobf == b'BAN1' else '❌ 否'}")
        except Exception as e:
            print(f"   反混淆失败: {e}")

        print(f"\n字段2: 盐值 (4-35字节)")
        salt = data[4:36]
        print(f"   长度: {len(salt)} 字节")
        print(f"   十六进制: {salt.hex()[:40]}...")

        print(f"\n字段3: IV (36-51字节)")
        iv = data[36:52]
        print(f"   长度: {len(iv)} 字节")
        print(f"   十六进制: {iv.hex()}")

        print(f"\n字段4: 元数据 (52-67字节)")
        metadata = data[52:68]
        print(f"   长度: {len(metadata)} 字节")
        print(f"   十六进制: {metadata.hex()}")

        if len(metadata) == 16:
            fps, width, height, frame_count = struct.unpack('IIII', metadata)
            print(f"\n   解析结果:")
            print(f"      FPS: {fps}")
            print(f"      宽度: {width}")
            print(f"      高度: {height}")
            print(f"      帧数: {frame_count}")

            # 检查值是否合理
            print(f"\n   合理性检查:")
            print(f"      FPS合理: {'✅ 是' if 1 <= fps <= 120 else '❌ 否'}")
            print(f"      分辨率合理: {'✅ 是' if 100 <= width <= 8000 and 100 <= height <= 8000 else '❌ 否'}")
            print(f"      帧数合理: {'✅ 是' if 1 <= frame_count <= 100000 else '❌ 否'}")

        print(f"\n字段5: 帧大小表长度 (68-71字节)")
        sizes_len_data = data[68:72]
        print(f"   长度: {len(sizes_len_data)} 字节")
        print(f"   十六进制: {sizes_len_data.hex()}")

        if len(sizes_len_data) == 4:
            sizes_len = struct.unpack('I', sizes_len_data)[0]
            print(f"   解析值: {sizes_len} 字节")

            # 检查是否合理
            file_size = len(open(ban_file, 'rb').read())
            print(f"   合理性检查:")
            print(f"      文件总大小: {file_size} 字节")
            print(f"      帧大小表位置: 72字节")
            print(f"      剩余空间: {file_size - 72} 字节")
            print(f"      帧大小表合理: {'✅ 是' if sizes_len < file_size - 72 else '❌ 否'}")

        print(f"\n字段6: 帧大小表数据 (72字节开始)")
        sizes_data = data[72:200]
        print(f"   长度: {len(sizes_data)} 字节")
        print(f"   十六进制 (前80字节): {sizes_data[:80].hex()}")

        # 尝试解析为文本
        try:
            text = sizes_data.decode('utf-8', errors='ignore')
            print(f"   尝试UTF-8解码: {text[:100]}")
        except:
            pass

        # 尝试解析为逗号分隔的数字
        try:
            text = sizes_data.decode('utf-8', errors='ignore')
            if ',' in text:
                parts = text.split(',')
                print(f"\n   尝试解析为逗号分隔的数字:")
                print(f"      前10个部分: {parts[:10]}")
                try:
                    numbers = [int(p) for p in parts[:10] if p.strip()]
                    print(f"      解析的数字: {numbers}")
                except:
                    pass
        except:
            pass

    print("\n" + "=" * 70)

if __name__ == "__main__":
    analyze_ban_structure('jy_new.ban')
