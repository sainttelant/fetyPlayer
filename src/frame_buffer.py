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
        self._load_metadata()
        
    def _load_metadata(self):
        """Load metadata and frame size table from .ban file"""
        from .codec import deobfuscate_data, decrypt_aes, calculate_checksum, derive_key_from_content, ENCRYPTION_ENABLED, PinkConfig
        import struct
        
        with open(self.ban_path, 'rb') as f:
            # Read and verify magic number
            magic = deobfuscate_data(f.read(4))
            if magic != PinkConfig.BAN_MAGIC_NUMBER:
                raise Exception("Invalid .ban file format")
            
            # Read salt and IV
            salt = deobfuscate_data(f.read(32))
            iv = deobfuscate_data(f.read(16))
            self.salt = salt
            self.iv = iv
            
            # Read metadata
            header_data = f.read(16)
            fps, width, height, frame_count = struct.unpack('IIII', header_data)
            self.metadata = {
                'fps': fps,
                'width': width,
                'height': height,
                'frame_count': frame_count
            }
            
            # Derive key
            import hashlib
            seed = PinkConfig.BAN_MAGIC_NUMBER + salt + PinkConfig.APP_NAME.encode()
            self.master_key = hashlib.pbkdf2_hmac('sha256', seed, b'BananaKeyDerivation', 100000, 32)
            
            # Read frame size table
            sizes_len = struct.unpack('I', f.read(4))[0]
            encrypted_sizes = f.read(sizes_len)
            
            # Decrypt frame size table
            if ENCRYPTION_ENABLED:
                sizes_packet = decrypt_aes(encrypted_sizes, self.master_key, self.iv)
            else:
                sizes_packet = encrypted_sizes
            
            # Parse frame sizes
            sizes_data_bytes = sizes_packet[16:]
            self.frame_sizes = [int(s) for s in sizes_data_bytes[4:].decode('utf-8').split(',') if s]
            
            # Store offset for frame data
            self.frame_data_offset = f.tell()
    
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
        Decode specific frame from file
        Args:
            frame_idx: Frame index
        Returns:
            Decoded frame or None
        """
        from .codec import decrypt_aes, calculate_checksum, ENCRYPTION_ENABLED
        import struct
        
        try:
            with open(self.ban_path, 'rb') as f:
                # Calculate position of requested frame
                offset = self.frame_data_offset
                for i in range(frame_idx):
                    if i >= len(self.frame_sizes):
                        return None
                    offset += self.frame_sizes[i]
                
                # Seek to frame position
                f.seek(offset)
                
                # Read encrypted frame
                frame_size = self.frame_sizes[frame_idx] if frame_idx < len(self.frame_sizes) else 0
                if frame_size <= 0 or frame_size > 50 * 1024 * 1024:
                    return None
                
                encrypted_frame = f.read(frame_size)
                if len(encrypted_frame) < frame_size:
                    return None
                
                # Decrypt frame
                if ENCRYPTION_ENABLED:
                    frame_packet = decrypt_aes(encrypted_frame, self.master_key, self.iv)
                else:
                    frame_packet = encrypted_frame
                
                if not frame_packet:
                    return None
                
                # Verify checksum
                frame_checksum = frame_packet[4:20]
                frame_data = frame_packet[20:]
                if calculate_checksum(frame_data) != frame_checksum:
                    return None
                
                # Decode frame
                nparr = np.frombuffer(frame_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                return frame
        except Exception as e:
            print(f"Error decoding frame {frame_idx}: {e}")
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
