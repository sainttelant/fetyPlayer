"""
Custom .ban video format encoder/decoder
"""
import cv2
import numpy as np
import struct
from .config import Config

class BANCodec:
   """Custom .ban video format encoder/decoder"""
   @staticmethod
   def encode_video(input_path, output_path, progress_callback=None):
       """Encode standard video to .ban format
       Args:
           input_path: Path to input video file
           output_path: Path to output .ban file
           progress_callback: Optional callback function(current, total)
       Returns:
           bool: True if successful, False otherwise
       """
       cap = cv2.VideoCapture(input_path)
       if not cap.isOpened():
           raise Exception("Could not open input video")
       # Get video properties
       fps = int(cap.get(cv2.CAP_PROP_FPS))
       width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
       height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
       frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
       try:
           with open(output_path, 'wb') as f:
               # Write header
               f.write(Config.BAN_MAGIC_NUMBER)
               f.write(struct.pack('IIII', fps, width, height, frame_count))
               # Write frames
               current_frame = 0
               while True:
                   ret, frame = cap.read()
                   if not ret:
                       break
                   # Compress frame (JPEG compression)
                   _, buffer = cv2.imencode('.jpg', frame,
                                           [cv2.IMWRITE_JPEG_QUALITY, Config.JPEG_QUALITY])
                   frame_data = buffer.tobytes()
                   # Write frame size and data
                   f.write(struct.pack('I', len(frame_data)))
                   f.write(frame_data)
                   current_frame += 1
                   # Progress callback
                   if progress_callback:
                       progress_callback(current_frame, frame_count)
           cap.release()
           return True
       except Exception as e:
           cap.release()
           raise Exception(f"Encoding failed: {str(e)}")
   @staticmethod
   def decode_video(ban_path, progress_callback=None):
       """Decode .ban format to frame list
       Args:
           ban_path: Path to .ban video file
           progress_callback: Optional callback function(current, total)
       Returns:
           tuple: (metadata: dict, frames: list)
       """
       try:
           with open(ban_path, 'rb') as f:
               # Read and verify header
               magic = f.read(4)
               if magic != Config.BAN_MAGIC_NUMBER:
                   raise Exception("Invalid .ban file format")
               # Read metadata
               fps, width, height, frame_count = struct.unpack('IIII', f.read(16))
               metadata = {
                   'fps': fps,
                   'width': width,
                   'height': height,
                   'frame_count': frame_count
               }
               # Read frames
               frames = []
               for i in range(frame_count):
                   try:
                       frame_size = struct.unpack('I', f.read(4))[0]
                       frame_data = f.read(frame_size)
                       # Decode frame
                       nparr = np.frombuffer(frame_data, np.uint8)
                       frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                       if frame is not None:
                           frames.append(frame)
                       # Progress callback
                       if progress_callback:
                           progress_callback(i + 1, frame_count)
                   except Exception as e:
                       print(f"Error decoding frame {i}: {e}")
                       break
               return metadata, frames
       except Exception as e:
           raise Exception(f"Decoding failed: {str(e)}")
   @staticmethod
   def get_video_info(ban_path):
       """Get video information without loading all frames
       Args:
           ban_path: Path to .ban video file
       Returns:
           dict: Video metadata
       """
       try:
           with open(ban_path, 'rb') as f:
               magic = f.read(4)
               if magic != Config.BAN_MAGIC_NUMBER:
                   raise Exception("Invalid .ban file format")
               fps, width, height, frame_count = struct.unpack('IIII', f.read(16))
               return {
                   'fps': fps,
                   'width': width,
                   'height': height,
                   'frame_count': frame_count,
                   'duration': frame_count / fps if fps > 0 else 0
               }
       except Exception as e:
           raise Exception(f"Could not read video info: {str(e)}")