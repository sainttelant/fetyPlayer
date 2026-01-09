"""
🎀 .ban格式视频编解码器
自定义视频格式的编码和解码（强加密版）
"""
import cv2
import numpy as np
import struct
import os
import hashlib
import secrets
import json
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from .config import PinkConfig

# 加密配置
ENCRYPTION_ENABLED = True

def derive_key_from_salt(salt, password=None):
    """从盐值派生密钥（统一编解码的密钥派生方法）"""
    if password:
        # 如果提供了密码，使用PBKDF2派生强密钥
        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000, 32)
    else:
        # 否则使用固定的派生方法
        # 使用magic number + salt + app name作为种子
        seed = PinkConfig.BAN_MAGIC_NUMBER + salt + PinkConfig.APP_NAME.encode()
        return hashlib.pbkdf2_hmac('sha256', seed, b'BananaKeyDerivation', 100000, 32)

def derive_key_from_content(file_content, salt):
    """从文件内容派生密钥（使密钥依赖于文件数据）"""
    # 使用SHA256结合盐值和文件内容摘要
    content_hash = hashlib.sha256(file_content).digest()
    combined = salt + content_hash
    return hashlib.pbkdf2_hmac('sha256', combined, PinkConfig.APP_NAME.encode(), 100000, 32)

def encrypt_aes(data, key, iv):
    """AES-256-CBC加密"""
    # 添加PKCS7填充
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(data) + padder.finalize()
    
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    return encryptor.update(padded_data) + encryptor.finalize()

def decrypt_aes(data, key, iv):
    """AES-256-CBC解密"""
    try:
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(data) + decryptor.finalize()
        
        # 移除PKCS7填充
        unpadder = padding.PKCS7(128).unpadder()
        unpadded = unpadder.update(padded_data) + unpadder.finalize()
        return unpadded
    except Exception as e:
        print(f"解密错误: {e}")
        return None

def obfuscate_data(data):
    """数据混淆（增加逆向难度）"""
    # 字节置换表
    perm = list(range(256))
    # 使用固定但复杂的置换
    key = b'BananaPlayerPinkSecretKey2024'
    for i in range(256):
        j = (i * 7 + 3) % 256
        perm[i], perm[j] = perm[j], perm[i]
    
    return bytes(perm[b] for b in data)

def deobfuscate_data(data):
    """数据反混淆"""
    # 逆置换表
    perm = list(range(256))
    for i in range(256):
        j = (i * 7 + 3) % 256
        perm[i], perm[j] = perm[j], perm[i]
    
    inverse_perm = [0] * 256
    for i, p in enumerate(perm):
        inverse_perm[p] = i
    
    return bytes(inverse_perm[b] for b in data)

def calculate_checksum(data):
    """计算数据校验和"""
    return hashlib.sha256(data).digest()[:16]

class BANCodec:
    """BAN格式编解码器"""
    @staticmethod
    def encode_video(input_path, output_path, progress_callback=None, password=None):
        """将标准视频编码为.ban格式（强加密）
        Args:
            input_path: 输入视频路径
            output_path: 输出.ban文件路径
            progress_callback: 进度回调函数(current, total)
            password: 可选密码（增强加密）
        Returns:
            bool: 是否成功
        """
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise Exception("无法打开输入视频文件")
        
        # 获取视频属性
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # 生成随机盐值和IV
        salt = secrets.token_bytes(32)
        iv = secrets.token_bytes(16)
        
        # 生成主密钥（使用统一的密钥派生方法）
        if password:
            # 如果提供了密码，使用PBKDF2派生强密钥
            master_key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000, 32)
        else:
            # 使用固定的派生方法
            seed = PinkConfig.BAN_MAGIC_NUMBER + salt + PinkConfig.APP_NAME.encode()
            master_key = hashlib.pbkdf2_hmac('sha256', seed, b'BananaKeyDerivation', 100000, 32)
        
        try:
            with open(output_path, 'wb') as f:
                # 写入混淆的magic number
                magic = obfuscate_data(PinkConfig.BAN_MAGIC_NUMBER)
                f.write(magic)
                
                # 写入盐值（已混淆）
                f.write(obfuscate_data(salt))
                
                # 写入IV（已混淆）
                f.write(obfuscate_data(iv))
                
                # 预留头部空间（16字节：4字节fps, 4字节width, 4字节height, 4字节frames）
                header_pos = f.tell()
                f.write(struct.pack('IIII', fps, width, height, 0))
                
                # 加密帧数据
                encrypted_frames = []
                frame_sizes = []
                current_frame = 0
                actual_frames = 0
                
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    # 压缩帧（JPEG压缩）
                    _, buffer = cv2.imencode('.jpg', frame,
                                            [cv2.IMWRITE_JPEG_QUALITY, PinkConfig.JPEG_QUALITY])
                    frame_data = buffer.tobytes()
                    
                    # 添加帧序号和校验和
                    frame_header = struct.pack('I', current_frame) + calculate_checksum(frame_data)
                    frame_packet = frame_header + frame_data
                    
                    # AES加密
                    if ENCRYPTION_ENABLED:
                        encrypted = encrypt_aes(frame_packet, master_key, iv)
                        encrypted_frames.append(encrypted)
                    else:
                        encrypted_frames.append(frame_packet)
                    
                    frame_sizes.append(len(encrypted_frames[-1]))
                    current_frame += 1
                    actual_frames += 1
                    
                    # 进度回调
                    if progress_callback:
                        progress_callback(current_frame, frame_count)
                
                # 写入帧大小表（加密）
                sizes_data = struct.pack('I', len(frame_sizes)) + b','.join([str(s).encode() for s in frame_sizes])
                sizes_packet = calculate_checksum(sizes_data) + sizes_data
                encrypted_sizes = encrypt_aes(sizes_packet, master_key, iv) if ENCRYPTION_ENABLED else sizes_packet
                f.write(struct.pack('I', len(encrypted_sizes)))
                f.write(encrypted_sizes)
                
                # 写入加密的帧数据
                for enc_frame in encrypted_frames:
                    f.write(enc_frame)
                
                # 回到头部更新实际的帧数
                f.seek(header_pos)
                f.write(struct.pack('IIII', fps, width, height, actual_frames))
                
                # 写入文件校验和（在更新帧数后）
                f.seek(0, 2)  # 移到文件末尾
                file_content = open(output_path, 'rb').read()[:-32]  # 不包括校验和本身
                file_checksum = hashlib.sha256(file_content).digest()
                f.write(file_checksum)
                
            cap.release()
            return True
        except Exception as e:
            cap.release()
            raise Exception(f"编码失败: {str(e)}")

    @staticmethod
    def decode_video(ban_path, progress_callback=None, password=None):
        """解密并解码.ban格式视频（强加密）
        Args:
            ban_path: .ban视频文件路径
            progress_callback: 进度回调函数(current, total)
            password: 可选密码
        Returns:
            tuple: (metadata: dict, frames: list)
        """
        try:
            with open(ban_path, 'rb') as f:
                file_size = os.fstat(f.fileno()).st_size
                
                # 读取并验证magic number
                magic = f.read(4)
                magic = deobfuscate_data(magic)
                if magic != PinkConfig.BAN_MAGIC_NUMBER:
                    raise Exception(f"无效的.ban文件格式：magic number不匹配")
                
                # 读取盐值和IV
                salt = deobfuscate_data(f.read(32))
                iv = deobfuscate_data(f.read(16))
                
                # 读取元数据
                header_data = f.read(16)
                fps, width, height, frame_count = struct.unpack('IIII', header_data)
                metadata = {
                    'fps': fps,
                    'width': width,
                    'height': height,
                    'frame_count': frame_count
                }
                
                # 重建主密钥
                if password:
                    master_key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000, 32)
                else:
                    # 使用固定的派生方法（与编码时一致）
                    seed = PinkConfig.BAN_MAGIC_NUMBER + salt + PinkConfig.APP_NAME.encode()
                    master_key = hashlib.pbkdf2_hmac('sha256', seed, b'BananaKeyDerivation', 100000, 32)
                
                # 读取帧大小表
                sizes_len_data = f.read(4)
                if len(sizes_len_data) < 4:
                    raise Exception("文件格式错误：无法读取帧大小表长度")
                
                sizes_len = struct.unpack('I', sizes_len_data)[0]
                encrypted_sizes = f.read(sizes_len)
                
                # 解密帧大小表
                sizes_packet = decrypt_aes(encrypted_sizes, master_key, iv)
                if not sizes_packet:
                    raise Exception("解密失败：密钥错误或文件已损坏")
                
                # 验证校验和
                expected_sum = sizes_packet[:16]
                actual_sum = calculate_checksum(sizes_packet[16:])
                if expected_sum != actual_sum:
                    raise Exception("文件完整性验证失败：帧大小表校验和不匹配")
                
                # 解析帧大小
                # 格式：4字节帧数量 + 帧大小列表（逗号分隔）
                sizes_data_bytes = sizes_packet[16:]
                stored_frame_count = struct.unpack('I', sizes_data_bytes[:4])[0]
                sizes_str = sizes_data_bytes[4:].decode('utf-8')
                frame_sizes = [int(s) for s in sizes_str.split(',') if s]
                
                # 读取帧
                frames = []
                for i in range(frame_count):
                    try:
                        frame_size = frame_sizes[i] if i < len(frame_sizes) else 0
                        if frame_size <= 0 or frame_size > 50 * 1024 * 1024:
                            break
                        
                        encrypted_frame = f.read(frame_size)
                        if len(encrypted_frame) < frame_size:
                            break
                        
                        # 解密帧
                        if ENCRYPTION_ENABLED:
                            frame_packet = decrypt_aes(encrypted_frame, master_key, iv)
                            if not frame_packet:
                                continue
                        else:
                            frame_packet = encrypted_frame
                        
                        # 验证帧校验和
                        # 帧格式：4字节序号 + 16字节校验和 + JPEG数据
                        frame_checksum = frame_packet[4:20]
                        frame_data = frame_packet[20:]
                        if calculate_checksum(frame_data) != frame_checksum:
                            continue
                        
                        # 解析帧序号
                        frame_idx = struct.unpack('I', frame_packet[:4])[0]
                        
                        # 解码帧
                        nparr = np.frombuffer(frame_data, np.uint8)
                        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                        if frame is not None:
                            frames.append(frame)
                            
                        if progress_callback:
                            progress_callback(len(frames), frame_count)
                    except Exception as e:
                        print(f"帧解密错误: {e}")
                        continue
                
                # 验证文件校验和
                f.seek(0, 2)
                stored_checksum = f.read(32)
                f.seek(0)
                content_for_check = f.read(file_size - 32)
                if hashlib.sha256(content_for_check).digest() != stored_checksum:
                    print("警告：文件完整性验证失败")
                
                # 更新元数据为实际读取的帧数
                metadata['frame_count'] = len(frames)
                return metadata, frames
        except Exception as e:
            raise Exception(f"解码失败: {str(e)}")

    @staticmethod
    def get_video_info(ban_path):
        """获取视频信息（需要解密）
        Args:
            ban_path: .ban视频文件路径
        Returns:
            dict: 视频元数据
        """
        try:
            with open(ban_path, 'rb') as f:
                # 读取magic number（已混淆）
                magic = f.read(4)
                magic = deobfuscate_data(magic)
                if magic != PinkConfig.BAN_MAGIC_NUMBER:
                    raise Exception(f"无效的.ban文件格式")
                
                # 跳过盐值和IV（已混淆）
                f.read(32)  # salt
                f.read(16)  # iv
                
                # 读取元数据（未混淆）
                header_data = f.read(16)
                fps, width, height, frame_count = struct.unpack('IIII', header_data)
                return {
                    'fps': fps,
                    'width': width,
                    'height': height,
                    'frame_count': frame_count,
                    'duration': frame_count / fps if fps > 0 else 0
                }
        except Exception as e:
            raise Exception(f"无法读取视频信息: {str(e)}")
