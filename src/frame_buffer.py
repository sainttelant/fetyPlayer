"""
🎀 Frame Buffer - Memory-efficient frame caching system
Implements LRU eviction and multi-threaded frame preloading
"""
import threading
import time
from collections import OrderedDict
from typing import Optional, List, Tuple
import cv2
import numpy as np
from .config import PinkConfig


class FrameBuffer:
    """
    Thread-safe frame buffer with LRU eviction
    Preloads frames ahead of current playback position
    """
    
    def __init__(self, max_frames: int = 60, max_memory_mb: int = 500):
        """
        Initialize frame buffer
        Args:
            max_frames: Maximum number of frames to cache
            max_memory_mb: Maximum memory usage in MB
        """
        self.max_frames = max_frames
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.cache = OrderedDict()
        self.current_memory = 0
        self.lock = threading.Lock()
        self.hits = 0
        self.misses = 0
        
    def put(self, frame_idx: int, frame: np.ndarray) -> bool:
        """
        Add frame to buffer (evicts oldest if necessary)
        Args:
            frame_idx: Frame index
            frame: Frame data (numpy array)
        Returns:
            bool: True if frame was added
        """
        frame_size = frame.nbytes
        
        with self.lock:
            # Calculate memory needed
            needed_memory = frame_size
            if frame_idx not in self.cache:
                needed_memory += frame_size
            
            # Evict frames until we have space
            while (len(self.cache) >= self.max_frames or 
                   self.current_memory + needed_memory > self.max_memory_bytes):
                if not self.cache:
                    break
                self._evict_oldest()
            
            # Add or update frame
            if frame_idx in self.cache:
                # Update existing frame (remove old memory first)
                old_frame = self.cache.pop(frame_idx)
                self.current_memory -= old_frame.nbytes
            
            # Add new frame to the end
            self.cache[frame_idx] = frame
            self.cache.move_to_end(frame_idx)
            self.current_memory += frame_size
            
            return True
    
    def get(self, frame_idx: int) -> Optional[np.ndarray]:
        """
        Get frame from buffer
        Args:
            frame_idx: Frame index
        Returns:
            Frame data or None if not cached
        """
        with self.lock:
            if frame_idx in self.cache:
                # Move to end (most recently used)
                self.hits += 1
                return self.cache[frame_idx]
            self.misses += 1
            return None
    
    def _evict_oldest(self):
        """Evict least recently used frame"""
        if self.cache:
            frame_idx, frame = self.cache.popitem(last=False)
            self.current_memory -= frame.nbytes
    
    def clear(self):
        """Clear all cached frames"""
        with self.lock:
            self.cache.clear()
            self.current_memory = 0
    
    def get_stats(self) -> dict:
        """Get buffer statistics"""
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
            return {
                'cached_frames': len(self.cache),
                'max_frames': self.max_frames,
                'memory_mb': self.current_memory / (1024 * 1024),
                'max_memory_mb': self.max_memory_bytes / (1024 * 1024),
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': hit_rate
            }
    
    def preload_range(self, start_idx: int, end_idx: int, frame_loader):
        """
        Preload a range of frames
        Args:
            start_idx: Start frame index
            end_idx: End frame index (exclusive)
            frame_loader: Function to load frame: (idx) -> frame
        """
        for idx in range(start_idx, min(end_idx, start_idx + self.max_frames // 2)):
            if idx not in self.cache:
                try:
                    frame = frame_loader(idx)
                    if frame is not None:
                        self.put(idx, frame)
                except Exception as e:
                    print(f"Error preloading frame {idx}: {e}")


class StreamingDecoder:
    """
    Streaming decoder for .ban files
    Decodes frames on-demand instead of loading all at once
    """
    
    def __init__(self, ban_path: str, buffer_size: int = 60, buffer_memory_mb: int = 500):
        """
        Initialize streaming decoder
        Args:
            ban_path: Path to .ban file
            buffer_size: Number of frames to cache
            buffer_memory_mb: Max buffer memory in MB
        """
        self.ban_path = ban_path
        self.frame_buffer = FrameBuffer(max_frames=buffer_size, max_memory_mb=buffer_memory_mb)
        self.metadata = None
        self.frame_sizes = []
        self.file_handle = None
        self.frame_data_offset = 0
        self.audio_data = None
        self._load_metadata()
        
    def _load_metadata(self):
        """Load metadata from .ban file (简化版)"""
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from src.simple_codec import SimpleBANCodec
        from .config import PinkConfig
        import struct

        try:
            with open(self.ban_path, 'rb') as f:
                # Read and verify magic number
                magic = f.read(4)
                if magic != b'BAN1':
                    raise Exception(f"无效的.ban文件格式: 魔数不匹配")

                # Read metadata
                header_data = f.read(16)
                if len(header_data) < 16:
                    raise Exception("文件头数据不完整")
                fps, width, height, frame_count = struct.unpack('IIII', header_data)
                self.metadata = {
                    'fps': fps,
                    'width': width,
                    'height': height,
                    'frame_count': frame_count
                }

                # Read audio data length and audio data
                audio_size_data = f.read(4)
                if len(audio_size_data) < 4:
                    raise Exception("音频数据长度不完整")
                audio_size = struct.unpack('I', audio_size_data)[0]
                
                if audio_size > 0:
                    self.audio_data = f.read(audio_size)
                    if len(self.audio_data) < audio_size:
                        print(f"警告: 音频数据不完整 (期望: {audio_size}, 实际: {len(self.audio_data)})")
                    else:
                        print(f"✅ 音频数据加载成功: {len(self.audio_data)} 字节")
                        self.metadata['has_audio'] = True
                else:
                    self.audio_data = None
                    self.metadata['has_audio'] = False
                    print("ℹ️  无音频数据")

                # 简化版格式：帧大小和帧数据交错存储，不需要单独的帧大小表
                # 我们在解码时动态读取帧大小
                self.frame_sizes = []  # 留空，按需读取

                # Store offset for frame data (after header and audio)
                self.frame_data_offset = f.tell()

                print(f"✅ 元数据加载成功: {frame_count} 帧, {width}x{height}, {fps} FPS")
        except Exception as e:
            print(f"❌ 加载元数据失败: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def get_frame(self, frame_idx: int) -> Optional[np.ndarray]:
        """
        Get frame at specified index (from cache or decode)
        Args:
            frame_idx: Frame index
        Returns:
            Frame data or None if invalid
        """
        if frame_idx < 0 or frame_idx >= self.metadata['frame_count']:
            return None
        
        # Check cache first
        cached_frame = self.frame_buffer.get(frame_idx)
        if cached_frame is not None:
            return cached_frame
        
        # Decode frame from file
        frame = self._decode_frame_at(frame_idx)
        if frame is not None:
            self.frame_buffer.put(frame_idx, frame)
        
        return frame
    
    def _decode_frame_at(self, frame_idx: int) -> Optional[np.ndarray]:
        """
        Decode specific frame from file (简化版)
        Args:
            frame_idx: Frame index
        Returns:
            Decoded frame or None
        """
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from src.simple_codec import simple_decrypt
        from .config import PinkConfig
        import hashlib
        import struct

        try:
            # 生成固定密钥（简化版）
            key = hashlib.sha256(b'BananaPlayerSimpleKey2024').digest()

            with open(self.ban_path, 'rb') as f:
                # Seek to frame data start
                f.seek(self.frame_data_offset)

                # Skip frames before the target frame
                for i in range(frame_idx):
                    # Read frame size
                    size_data = f.read(4)
                    if len(size_data) < 4:
                        print(f"错误: 在跳过帧 {i} 时遇到文件结束")
                        return None

                    frame_size = struct.unpack('I', size_data)[0]
                    if frame_size <= 0 or frame_size > 50 * 1024 * 1024:
                        print(f"错误: 帧 {i} 的大小无效: {frame_size}")
                        return None

                    # Skip frame data
                    f.seek(frame_size, 1)  # 相对当前位置跳过

                # Now at target frame position
                # Read frame size
                size_data = f.read(4)
                if len(size_data) < 4:
                    print(f"错误: 帧 {frame_idx} 大小数据不完整")
                    return None

                frame_size = struct.unpack('I', size_data)[0]
                if frame_size <= 0 or frame_size > 50 * 1024 * 1024:
                    print(f"错误: 帧 {frame_idx} 的大小无效: {frame_size}")
                    return None

                # Read encrypted frame
                encrypted_frame = f.read(frame_size)
                if len(encrypted_frame) < frame_size:
                    print(f"错误: 帧 {frame_idx} 数据不完整 (期望: {frame_size}, 实际: {len(encrypted_frame)})")
                    return None

                # Decrypt frame (简化版)
                frame_packet = simple_decrypt(encrypted_frame, key)
                if not frame_packet:
                    print(f"错误: 帧 {frame_idx} 解密失败")
                    return None

                # Parse frame index
                if len(frame_packet) < 4:
                    print(f"错误: 帧 {frame_idx} 数据包太短: {len(frame_packet)}")
                    return None

                frame_data = frame_packet[4:]

                # Decode frame
                nparr = np.frombuffer(frame_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                if frame is None:
                    print(f"错误: 帧 {frame_idx} JPEG解码失败")
                    return None

                return frame
        except Exception as e:
            print(f"错误: 解码帧 {frame_idx} 时发生异常: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def preload_frames(self, current_idx: int, preload_ahead: int = 30):
        """
        Preload frames ahead of current position
        Args:
            current_idx: Current frame index
            preload_ahead: Number of frames to preload ahead
        """
        start_idx = current_idx + 1
        end_idx = min(current_idx + preload_ahead + 1, self.metadata['frame_count'])
        self.frame_buffer.preload_range(start_idx, end_idx, self.get_frame)
    
    def clear_cache(self):
        """Clear frame cache"""
        self.frame_buffer.clear()
    
    def get_stats(self) -> dict:
        """Get decoder statistics"""
        buffer_stats = self.frame_buffer.get_stats()
        return {
            'metadata': self.metadata,
            'buffer_stats': buffer_stats
        }
    
    def get_audio_data(self) -> bytes:
        """Get audio data from .ban file
        
        Returns:
            bytes: Audio data in WAV format, or None if no audio
        """
        return self.audio_data


class FramePreloader:
    """
    Multi-threaded frame preloader
    Runs in background to keep buffer filled
    """
    
    def __init__(self, decoder: StreamingDecoder, preload_window: int = 30):
        """
        Initialize preloader
        Args:
            decoder: Streaming decoder instance
            preload_window: Number of frames to preload ahead
        """
        self.decoder = decoder
        self.preload_window = preload_window
        self.current_idx = 0
        self.running = False
        self.preload_thread = None
        self.lock = threading.Lock()
        
    def start(self):
        """Start preloader thread"""
        if not self.running:
            self.running = True
            self.preload_thread = threading.Thread(target=self._preload_loop, daemon=True)
            self.preload_thread.start()
    
    def stop(self):
        """Stop preloader thread"""
        self.running = False
        if self.preload_thread:
            self.preload_thread.join(timeout=1.0)
    
    def update_position(self, frame_idx: int):
        """
        Update current playback position
        Args:
            frame_idx: Current frame index
        """
        with self.lock:
            self.current_idx = frame_idx
    
    def _preload_loop(self):
        """Preload loop running in background thread"""
        last_idx = -1
        
        while self.running:
            with self.lock:
                current_idx = self.current_idx
            
            # Only preload if position changed
            if current_idx != last_idx:
                self.decoder.preload_frames(current_idx, self.preload_window)
                last_idx = current_idx
            
            # Sleep a bit to avoid CPU hogging
            time.sleep(0.01)
