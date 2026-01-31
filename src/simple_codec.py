# -*- coding: utf-8 -*-
"""
简化版.ban格式编解码器
使用简单的加密方式，避免复杂逻辑导致的问题
"""
import cv2
import numpy as np
import struct
import os
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from .config import PinkConfig

# 简化版加密配置
SIMPLE_ENCRYPTION = True

def simple_encrypt(data, key):
    """简单的AES-256-CBC加密"""
    # 生成随机IV
    iv = os.urandom(16)
    
    # 添加PKCS7填充
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(data) + padder.finalize()
    
    # 加密
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted = encryptor.update(padded_data) + encryptor.finalize()
    
    # 返回 IV + 加密数据
    return iv + encrypted

def simple_decrypt(data, key):
    """简单的AES-256-CBC解密"""
    if len(data) < 16:
        return None
    
    # 提取IV和加密数据
    iv = data[:16]
    encrypted_data = data[16:]
    
    # 解密
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(encrypted_data) + decryptor.finalize()
    
    # 移除PKCS7填充
    unpadder = padding.PKCS7(128).unpadder()
    try:
        return unpadder.update(padded_data) + unpadder.finalize()
    except:
        return None

class SimpleBANCodec:
    """简化版BAN格式编解码器"""
    
    @staticmethod
    def encode_video(input_path, output_path, progress_callback=None):
        """将标准视频编码为.ban格式（简化版）
        
        简化版文件格式:
        [4字节] 魔数: "BAN1" (不混淆)
        [16字节] 头部: FPS, Width, Height, Frame Count
        [4字节] 音频数据长度 (0表示无音频)
        [N字节] 音频数据 (WAV格式，不加密)
        [N字节] 帧数据 (每帧: 4字节大小 + JPEG数据)
        [32字节] 文件校验和 (SHA256)
        """
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise Exception("无法打开输入视频文件")
        
        # 获取视频属性
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # 生成固定密钥（简化版）
        key = hashlib.sha256(b'BananaPlayerSimpleKey2024').digest()
        
        print(f"编码视频: {input_path}")
        print(f"  FPS: {fps}, 分辨率: {width}x{height}, 帧数: {frame_count}")
        
        # 提取音频
        audio_data = None
        try:
            from pydub import AudioSegment
            import tempfile
            import os
            
            # 使用pydub提取音频
            audio = AudioSegment.from_file(input_path)
            
            # 转换为WAV格式（使用更兼容的参数）
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
                temp_audio_path = temp_audio.name
                # 使用标准PCM格式，16位，44100Hz，单声道（更兼容）
                audio.export(temp_audio_path, format='wav',
                          codec='pcm_s16le',
                          parameters=['-ar', '44100', '-ac', '1'])
            
            # 读取WAV数据
            with open(temp_audio_path, 'rb') as f:
                audio_data = f.read()
            
            # 删除临时文件
            os.unlink(temp_audio_path)
            
            print(f"  音频提取成功: {len(audio_data)} 字节")
        except Exception as e:
            print(f"  音频提取失败: {e} (将创建无音频视频)")
            audio_data = None
        
        try:
            with open(output_path, 'wb') as f:
                # 写入magic number (不混淆)
                f.write(b'BAN1')
                
                # 预留头部空间
                header_pos = f.tell()
                f.write(struct.pack('IIII', fps, width, height, 0))
                
                # 写入音频数据长度和音频数据（不加密）
                if audio_data:
                    f.write(struct.pack('I', len(audio_data)))
                    f.write(audio_data)
                else:
                    f.write(struct.pack('I', 0))
                
                # 读取并编码所有帧
                actual_frames = 0
                
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    # 压缩帧（JPEG压缩）
                    _, buffer = cv2.imencode('.jpg', frame,
                                            [cv2.IMWRITE_JPEG_QUALITY, PinkConfig.JPEG_QUALITY])
                    frame_data = buffer.tobytes()
                    
                    # 添加帧序号
                    frame_header = struct.pack('I', actual_frames)
                    frame_packet = frame_header + frame_data
                    
                    # 加密（简化版）
                    if SIMPLE_ENCRYPTION:
                        encrypted = simple_encrypt(frame_packet, key)
                    else:
                        encrypted = frame_packet
                    
                    # 写入帧大小和加密数据
                    f.write(struct.pack('I', len(encrypted)))
                    f.write(encrypted)
                    
                    actual_frames += 1
                    
                    # 进度回调
                    if progress_callback and actual_frames % 10 == 0:
                        progress_callback(actual_frames, frame_count)
                
                # 回到头部更新实际的帧数
                f.seek(header_pos)
                f.write(struct.pack('IIII', fps, width, height, actual_frames))
                
                # 写入文件校验和
                f.seek(0, 2)  # 移到文件末尾
                file_content = open(output_path, 'rb').read()
                file_checksum = hashlib.sha256(file_content).digest()
                f.write(file_checksum)
                
            cap.release()
            
            print(f"编码完成: {actual_frames} 帧")
            print(f"输出文件: {output_path}")
            print(f"文件大小: {os.path.getsize(output_path) / (1024*1024):.2f} MB")
            
            return True
        except Exception as e:
            cap.release()
            raise Exception(f"编码失败: {str(e)}")
    
    @staticmethod
    def decode_video(ban_path, progress_callback=None):
        """解密并解码.ban格式视频（简化版）
        
        Returns:
            tuple: (metadata: dict, frames: list, audio_data: bytes or None)
        """
        try:
            with open(ban_path, 'rb') as f:
                file_size = os.fstat(f.fileno()).st_size
                
                # 读取并验证magic number
                magic = f.read(4)
                if magic != b'BAN1':
                    raise Exception(f"无效的.ban文件格式：magic number不匹配")
                
                # 读取元数据
                header_data = f.read(16)
                fps, width, height, frame_count = struct.unpack('IIII', header_data)
                metadata = {
                    'fps': fps,
                    'width': width,
                    'height': height,
                    'frame_count': frame_count
                }
                
                print(f"解码视频: {ban_path}")
                print(f"  FPS: {fps}, 分辨率: {width}x{height}, 帧数: {frame_count}")
                
                # 读取音频数据长度和音频数据
                audio_size_data = f.read(4)
                if len(audio_size_data) < 4:
                    raise Exception("音频数据长度不完整")
                audio_size = struct.unpack('I', audio_size_data)[0]
                
                audio_data = None
                if audio_size > 0:
                    audio_data = f.read(audio_size)
                    if len(audio_data) < audio_size:
                        print(f"警告: 音频数据不完整 (期望: {audio_size}, 实际: {len(audio_data)})")
                    else:
                        print(f"  音频数据: {len(audio_data)} 字节")
                
                # 生成固定密钥（简化版）
                key = hashlib.sha256(b'BananaPlayerSimpleKey2024').digest()
                
                # 读取帧
                frames = []
                for i in range(frame_count):
                    # 读取帧大小
                    size_data = f.read(4)
                    if len(size_data) < 4:
                        print(f"警告: 文件在第{i}帧提前结束")
                        break
                    
                    frame_size = struct.unpack('I', size_data)[0]
                    
                    # 检查帧大小是否合理
                    if frame_size <= 0 or frame_size > 50 * 1024 * 1024:
                        print(f"警告: 第{i}帧大小异常: {frame_size}")
                        break
                    
                    # 读取加密帧
                    encrypted_frame = f.read(frame_size)
                    if len(encrypted_frame) < frame_size:
                        print(f"警告: 第{i}帧数据不完整")
                        break
                    
                    # 解密（简化版）
                    if SIMPLE_ENCRYPTION:
                        frame_packet = simple_decrypt(encrypted_frame, key)
                    else:
                        frame_packet = encrypted_frame
                    
                    if not frame_packet:
                        print(f"警告: 第{i}帧解密失败")
                        continue
                    
                    # 解析帧序号
                    frame_idx = struct.unpack('I', frame_packet[:4])[0]
                    
                    # 解码帧
                    frame_data = frame_packet[4:]
                    nparr = np.frombuffer(frame_data, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    
                    if frame is not None:
                        frames.append(frame)
                    
                    # 进度回调
                    if progress_callback and (i + 1) % 100 == 0:
                        progress_callback(len(frames), frame_count)
                
                # 验证文件校验和
                f.seek(0)
                stored_checksum = f.read()[-32:]
                f.seek(0)
                content_for_check = f.read()[:-32]
                if hashlib.sha256(content_for_check).digest() != stored_checksum:
                    print("警告：文件完整性验证失败")
                
                # 更新元数据为实际读取的帧数
                metadata['frame_count'] = len(frames)
                
                print(f"解码完成: {len(frames)} 帧")
                
                return metadata, frames, audio_data
        except Exception as e:
            raise Exception(f"解码失败: {str(e)}")
    
    @staticmethod
    def decode_single_frame(ban_path, frame_idx):
        """解码单帧（用于Web播放器）
        
        Returns:
            numpy.ndarray: 帧数据，失败返回None
        """
        try:
            with open(ban_path, 'rb') as f:
                # 读取并验证magic number
                magic = f.read(4)
                if magic != b'BAN1':
                    raise Exception(f"无效的.ban文件格式")
                
                # 读取元数据
                header_data = f.read(16)
                fps, width, height, frame_count = struct.unpack('IIII', header_data)
                
                # 检查帧索引范围
                if frame_idx < 0 or frame_idx >= frame_count:
                    raise Exception(f"帧索引超出范围: {frame_idx} >= {frame_count}")
                
                # 生成固定密钥（简化版）
                key = hashlib.sha256(b'BananaPlayerSimpleKey2024').digest()
                
                # 计算目标帧位置
                offset = 4 + 16  # magic + header
                for i in range(frame_idx):
                    size_data = f.read(4)
                    if len(size_data) < 4:
                        raise IndexError(f"帧索引超出范围")
                    frame_size = struct.unpack('I', size_data)[0]
                    offset += 4 + frame_size
                
                # 读取并解密目标帧
                f.seek(offset)
                size_data = f.read(4)
                if len(size_data) < 4:
                    raise Exception("帧大小数据不完整")
                frame_size = struct.unpack('I', size_data)[0]
                
                if frame_size <= 0 or frame_size > 50 * 1024 * 1024:
                    raise Exception(f"无效的帧大小: {frame_size}")
                
                encrypted_frame = f.read(frame_size)
                if len(encrypted_frame) < frame_size:
                    raise Exception("帧数据不完整")
                
                # 解密（简化版）
                if SIMPLE_ENCRYPTION:
                    frame_packet = simple_decrypt(encrypted_frame, key)
                else:
                    frame_packet = encrypted_frame
                
                if not frame_packet:
                    raise Exception('帧解密失败')
                
                # 解码帧
                frame_data = frame_packet[4:]
                nparr = np.frombuffer(frame_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if frame is None:
                    raise Exception('帧解码失败')
                
                return frame
        except Exception as e:
            print(f"解码单帧失败: {e}")
            return None
    
    @staticmethod
    def get_video_info(ban_path):
        """获取视频信息
        
        Returns:
            dict: 视频元数据
        """
        try:
            with open(ban_path, 'rb') as f:
                # 读取magic number
                magic = f.read(4)
                if magic != b'BAN1':
                    raise Exception(f"无效的.ban文件格式")
                
                # 读取元数据
                header_data = f.read(16)
                fps, width, height, frame_count = struct.unpack('IIII', header_data)
                
                # 读取音频数据长度
                audio_size_data = f.read(4)
                if len(audio_size_data) < 4:
                    raise Exception("音频数据长度不完整")
                audio_size = struct.unpack('I', audio_size_data)[0]
                
                return {
                    'fps': fps,
                    'width': width,
                    'height': height,
                    'frame_count': frame_count,
                    'duration': frame_count / fps if fps > 0 else 0,
                    'has_audio': audio_size > 0,
                    'audio_size': audio_size
                }
        except Exception as e:
            raise Exception(f"无法读取视频信息: {str(e)}")

if __name__ == "__main__":
    # 测试编码
    import sys
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_file = input_file.rsplit('.', 1)[0] + '_simple.ban'
        
        print("=" * 70)
        print("简化版编码器测试")
        print("=" * 70)
        
        SimpleBANCodec.encode_video(input_file, output_file)
        
        print("\n" + "=" * 70)
        print("测试解码...")
        print("=" * 70)
        
        metadata, frames = SimpleBANCodec.decode_video(output_file)
        
        print(f"\n✅ 测试成功!")
        print(f"   解码帧数: {len(frames)}")
        print(f"   元数据帧数: {metadata['frame_count']}")
