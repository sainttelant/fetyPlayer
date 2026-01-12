#!/usr/bin/env python3
import sys
sys.path.insert(0, '..')
from src.codec import BANCodec
import cv2
import base64
import os

# 测试解码单帧
def test_frame_decoding():
    print("=== 测试单帧解码 ===")
    filepath = './videos/vis.ban'
    
    if not os.path.exists(filepath):
        print(f"错误：文件不存在 {filepath}")
        return
    
    try:
        # 测试多帧解码
        print("测试多帧解码...")
        metadata, frames = BANCodec.decode_video(filepath)
        print(f"成功解码 {len(frames)} 帧")
        print(f"元数据: {metadata}")
        
        # 保存第一帧为图像文件
        if frames:
            first_frame = frames[0]
            print(f"第一帧尺寸: {first_frame.shape}")
            
            # 保存为图像文件
            output_path = './test_frame.jpg'
            cv2.imwrite(output_path, first_frame)
            print(f"第一帧已保存到: {output_path}")
            
            # 转换为base64
            is_success, buffer = cv2.imencode('.jpg', first_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if is_success:
                frame_base64 = base64.b64encode(buffer).decode('utf-8')
                print(f"Base64数据长度: {len(frame_base64)}")
                print(f"Base64前100字符: {frame_base64[:100]}")
            
            return True
        else:
            print("没有成功解码任何帧")
            return False
            
    except Exception as e:
        print(f"解码失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_frame_decoding()
    if success:
        print("\n✓ 测试通过")
    else:
        print("\n✗ 测试失败")