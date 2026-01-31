# -*- coding: utf-8 -*-
"""
检查jy.ban文件的实际格式
"""
import struct

def check_ban_format(ban_file):
    """检查.ban文件格式"""
    print("=" * 70)
    print(f"🔍 检查文件: {ban_file}")
    print("=" * 70)

    with open(ban_file, 'rb') as f:
        # 读取前4字节
        magic = f.read(4)
        print(f"\n📋 前4字节 (原始):")
        print(f"   十六进制: {magic.hex()}")
        print(f"   ASCII: {magic}")

        # 尝试反混淆
        from src.codec import deobfuscate_data
        try:
            deobfuscated = deobfuscate_data(magic)
            print(f"\n📋 前4字节 (反混淆后):")
            print(f"   十六进制: {deobfuscated.hex()}")
            print(f"   ASCII: {deobfuscated}")
            print(f"   是否为BAN1: {'✅ 是' if deobfuscated == b'BAN1' else '❌ 否'}")
        except Exception as e:
            print(f"\n❌ 反混淆失败: {e}")

        # 读取完整的文件头结构
        f.seek(0)
        header = f.read(100)
        print(f"\n📋 完整文件头 (前100字节):")
        for i in range(0, min(100, len(header)), 16):
            chunk = header[i:i+16]
            hex_str = ' '.join(f'{b:02x}' for b in chunk)
            ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
            print(f"   {i:04x}: {hex_str:<48} {ascii_str}")

        # 尝试不同的格式解析
        print(f"\n🔍 尝试不同的格式解析:")

        # 格式1: 当前格式 (混淆魔数 + 盐值 + IV + 元数据)
        f.seek(0)
        magic1 = f.read(4)
        salt1 = f.read(32)
        iv1 = f.read(16)
        meta1 = f.read(16)
        if len(meta1) == 16:
            fps, width, height, frame_count = struct.unpack('IIII', meta1)
            print(f"\n   格式1 (当前格式):")
            print(f"      魔数: {magic1.hex()}")
            print(f"      FPS: {fps}, 分辨率: {width}x{height}, 帧数: {frame_count}")

        # 格式2: 旧格式 (未混淆魔数 + 元数据)
        f.seek(0)
        magic2 = f.read(4)
        meta2 = f.read(16)
        if len(meta2) == 16:
            fps, width, height, frame_count = struct.unpack('IIII', meta2)
            print(f"\n   格式2 (旧格式 - 未混淆):")
            print(f"      魔数: {magic2}")
            print(f"      FPS: {fps}, 分辨率: {width}x{height}, 帧数: {frame_count}")

        # 格式3: 简化格式 (魔数 + 元数据)
        f.seek(0)
        magic3 = f.read(4)
        if magic3 == b'BAN1':
            meta3 = f.read(16)
            if len(meta3) == 16:
                fps, width, height, frame_count = struct.unpack('IIII', meta3)
                print(f"\n   格式3 (简化格式):")
                print(f"      魔数: BAN1")
                print(f"      FPS: {fps}, 分辨率: {width}x{height}, 帧数: {frame_count}")

        # 检查帧大小表位置
        print(f"\n📏 检查帧大小表位置:")

        # 位置1: 当前格式 (魔数4 + 盐值32 + IV16 + 元数据16 = 68字节)
        f.seek(68)
        sizes_len_data1 = f.read(4)
        if len(sizes_len_data1) == 4:
            sizes_len1 = struct.unpack('I', sizes_len_data1)[0]
            print(f"   位置1 (68字节偏移): {sizes_len1} 字节")

        # 位置2: 旧格式 (魔数4 + 元数据16 = 20字节)
        f.seek(20)
        sizes_len_data2 = f.read(4)
        if len(sizes_len_data2) == 4:
            sizes_len2 = struct.unpack('I', sizes_len_data2)[0]
            print(f"   位置2 (20字节偏移): {sizes_len2} 字节")

        # 位置3: 直接在元数据后
        f.seek(4 + 16)
        sizes_len_data3 = f.read(4)
        if len(sizes_len_data3) == 4:
            sizes_len3 = struct.unpack('I', sizes_len_data3)[0]
            print(f"   位置3 (20字节偏移): {sizes_len3} 字节")

    print("\n" + "=" * 70)

if __name__ == "__main__":
    check_ban_format('jy.ban')
