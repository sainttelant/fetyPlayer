"""
🎀 .ban格式视频编解码器
自定义视频格式的编码和解码
"""
import cv2
import numpy as np
import struct
import os
from .config import PinkConfig

class BANCodec:
   """BAN格式编解码器"""
   @staticmethod
   def encode_video(input_path, output_path, progress_callback=None):
       """将标准视频编码为.ban格式
       Args:
           input_path: 输入视频路径
           output_path: 输出.ban文件路径
           progress_callback: 进度回调函数(current, total)
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
       try:
           with open(output_path, 'wb') as f:
               # 写入头部 (预留frame_count位置)
               f.write(PinkConfig.BAN_MAGIC_NUMBER)
               header_pos = f.tell()
               # 先写入临时的帧数为0
               f.write(struct.pack('IIII', fps, width, height, 0))

               # 写入帧数据
               current_frame = 0
               actual_frames = 0  # 实际写入的帧数
               while True:
                   ret, frame = cap.read()
                   if not ret:
                       break
                   # 压缩帧（JPEG压缩）
                   _, buffer = cv2.imencode('.jpg', frame,
                                           [cv2.IMWRITE_JPEG_QUALITY, PinkConfig.JPEG_QUALITY])
                   frame_data = buffer.tobytes()
                   # 写入帧大小和数据
                   f.write(struct.pack('I', len(frame_data)))
                   f.write(frame_data)
                   current_frame += 1
                   actual_frames += 1
                   # 进度回调
                   if progress_callback:
                       progress_callback(current_frame, frame_count)

               # 回到头部更新实际的帧数
               f.seek(header_pos)
               f.write(struct.pack('IIII', fps, width, height, actual_frames))
           cap.release()
           return True
       except Exception as e:
           cap.release()
           raise Exception(f"编码失败: {str(e)}")
   @staticmethod
   def decode_video(ban_path, progress_callback=None):
       """解码.ban格式视频
       Args:
           ban_path: .ban视频文件路径
           progress_callback: 进度回调函数(current, total)
       Returns:
           tuple: (metadata: dict, frames: list)
       """
       try:
           with open(ban_path, 'rb') as f:
               # 读取并验证头部
               magic = f.read(4)
               if magic != PinkConfig.BAN_MAGIC_NUMBER:
                   raise Exception("无效的.ban文件格式")
               # 读取元数据
               fps, width, height, frame_count = struct.unpack('IIII', f.read(16))
               metadata = {
                   'fps': fps,
                   'width': width,
                   'height': height,
                   'frame_count': frame_count
               }
               # 读取帧
               frames = []
               for i in range(frame_count):
                   try:
                       # 检查是否还有足够的数据读取帧大小
                       size_data = f.read(4)
                       if len(size_data) < 4:
                           print(f"警告: 文件在第{i}帧提前结束，已读取{i}帧")
                           break

                       frame_size = struct.unpack('I', size_data)[0]

                       # 检查帧大小是否合理（避免损坏的文件）
                       if frame_size > 10 * 1024 * 1024:  # 10MB上限
                           print(f"警告: 第{i}帧大小异常({frame_size}字节)，停止解码")
                           break

                       frame_data = f.read(frame_size)
                       if len(frame_data) < frame_size:
                           print(f"警告: 第{i}帧数据不完整，已读取{i}帧")
                           break

                       # 解码帧
                       nparr = np.frombuffer(frame_data, np.uint8)
                       frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                       if frame is not None:
                           frames.append(frame)
                       else:
                           print(f"警告: 第{i}帧解码失败")

                       # 进度回调
                       if progress_callback:
                           progress_callback(i + 1, frame_count)
                   except Exception as e:
                       print(f"解码第{i}帧时出错: {e}")
                       break

               # 更新元数据为实际读取的帧数
               metadata['frame_count'] = len(frames)
               return metadata, frames
       except Exception as e:
           raise Exception(f"解码失败: {str(e)}")
   @staticmethod
   def get_video_info(ban_path):
       """获取视频信息（不加载所有帧）
       Args:
           ban_path: .ban视频文件路径
       Returns:
           dict: 视频元数据
       """
       try:
           with open(ban_path, 'rb') as f:
               magic = f.read(4)
               if magic != PinkConfig.BAN_MAGIC_NUMBER:
                   raise Exception("无效的.ban文件格式")
               fps, width, height, frame_count = struct.unpack('IIII', f.read(16))
               return {
                   'fps': fps,
                   'width': width,
                   'height': height,
                   'frame_count': frame_count,
                   'duration': frame_count / fps if fps > 0 else 0
               }
       except Exception as e:
           raise Exception(f"无法读取视频信息: {str(e)}")