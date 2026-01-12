"""
Flask API - .ban格式视频帧级API
P0阶段：核心播放功能后端支持
"""
import os
import base64
import struct
import json
from flask import Flask, jsonify, send_file
import cv2
import numpy as np
import hashlib
from werkzeug.utils import secure_filename

from src.codec import BANCodec
from src.config import PinkConfig


class VideoAPI:
    """视频API处理类"""
    
    def __init__(self, app, video_folder):
        self.app = app
        self.video_folder = video_folder
        self.setup_routes()
    
    def setup_routes(self):
        """设置API路由"""
        
        # 单帧获取API
        @self.app.route('/api/video/<filename>/frame/<int:frame_idx>')
        def get_video_frame(filename, frame_idx):
            """获取单帧数据（base64编码）"""
            try:
                return self._get_single_frame(filename, frame_idx)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        # 批量帧获取API（用于预加载）
        @self.app.route('/api/video/<filename>/frames/<int:start>/<int:end>')
        def get_video_frames(filename, start, end):
            """批量获取帧数据"""
            try:
                return self._get_batch_frames(filename, start, end)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        # 视频元数据API（已存在，确保功能完整）
        @self.app.route('/api/video/<filename>/info')
        def get_video_info(filename):
            """获取视频元数据"""
            try:
                return self._get_video_info(filename)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        # 帧缓存统计API
        @self.app.route('/api/video/<filename>/cache/stats')
        def get_cache_stats(filename):
            """获取帧缓存统计"""
            try:
                return self._get_cache_stats(filename)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
    
    def _get_single_frame(self, filename, frame_idx):
        """获取单帧数据
        
        Args:
            filename: 视频文件名
            frame_idx: 帧索引
            
        Returns:
            JSON响应包含帧数据（base64编码）
        """
        # 安全检查文件名
        filename = secure_filename(filename)
        filepath = os.path.join(self.video_folder, filename)
        
        # 检查文件是否存在
        if not os.path.exists(filepath):
            return jsonify({'error': '视频不存在'}), 404
        
        # 检查文件扩展名
        ext = filename.lower().split('.')[-1]
        if ext != 'ban':
            return jsonify({'error': '只支持.ban格式'}), 400
        
        # 获取视频信息
        try:
            info = BANCodec.get_video_info(filepath)
        except Exception as e:
            return jsonify({'error': f'无法读取视频信息: {str(e)}'}), 500
        
        # 检查帧索引范围
        if frame_idx < 0 or frame_idx >= info['frame_count']:
            return jsonify({'error': f'帧索引超出范围: {frame_idx} >= {info["frame_count"]}'}), 400
        
        # 解码单帧
        try:
            frame = BANCodec.decode_single_frame(filepath, frame_idx)
            
            if frame is None:
                return jsonify({'error': '帧解码失败'}), 500
            
            # 转换为base64
            is_success, buffer = cv2.imencode('.jpg', frame, 
                                             [cv2.IMWRITE_JPEG_QUALITY, PinkConfig.JPEG_QUALITY])
            if not is_success:
                return jsonify({'error': '帧编码失败'}), 500
            
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            
            return jsonify({
                'success': True,
                'frame_idx': frame_idx,
                'frame_data': f'data:image/jpeg;base64,{frame_base64}',
                'width': frame.shape[1],
                'height': frame.shape[0],
                'channels': frame.shape[2] if len(frame.shape) > 2 else 1,
                'size_kb': len(buffer) / 1024
            })
            
        except Exception as e:
            return jsonify({'error': f'帧解码错误: {str(e)}'}), 500
    
    def _get_batch_frames(self, filename, start, end):
        """批量获取帧数据
        
        Args:
            filename: 视频文件名
            start: 起始帧索引
            end: 结束帧索引（不包含）
            
        Returns:
            JSON响应包含多帧数据
        """
        # 安全检查文件名
        filename = secure_filename(filename)
        filepath = os.path.join(self.video_folder, filename)
        
        # 检查文件是否存在
        if not os.path.exists(filepath):
            return jsonify({'error': '视频不存在'}), 404
        
        # 检查文件扩展名
        ext = filename.lower().split('.')[-1]
        if ext != 'ban':
            return jsonify({'error': '只支持.ban格式'}), 400
        
        # 获取视频信息
        try:
            info = BANCodec.get_video_info(filepath)
        except Exception as e:
            return jsonify({'error': f'无法读取视频信息: {str(e)}'}), 500
        
        # 检查帧索引范围
        if start < 0 or end > info['frame_count']:
            return jsonify({'error': f'帧索引超出范围: {start}-{end} > {info["frame_count"]}'}), 400
        
        if start >= end:
            return jsonify({'error': '起始帧索引必须小于结束帧索引'}), 400
        
        # 限制批量获取的帧数
        max_batch_size = 100  # 最多一次获取100帧
        if (end - start) > max_batch_size:
            return jsonify({'error': f'批量获取帧数超过限制: {max_batch_size} 帧'}), 400
        
        # 解码所有帧
        frames = []
        for frame_idx in range(start, end):
            try:
                frame = BANCodec.decode_single_frame(filepath, frame_idx)
                
                if frame is None:
                    frames.append({
                        'frame_idx': frame_idx,
                        'error': '帧解码失败'
                    })
                    continue
                
                # 转换为base64
                is_success, buffer = cv2.imencode('.jpg', frame,
                                                 [cv2.IMWRITE_JPEG_QUALITY, PinkConfig.JPEG_QUALITY])
                if not is_success:
                    frames.append({
                        'frame_idx': frame_idx,
                        'error': '帧编码失败'
                    })
                    continue
                
                frame_base64 = base64.b64encode(buffer).decode('utf-8')
                
                frames.append({
                    'frame_idx': frame_idx,
                    'frame_data': f'data:image/jpeg;base64,{frame_base64}',
                    'width': frame.shape[1],
                    'height': frame.shape[0]
                })
                
            except Exception as e:
                frames.append({
                    'frame_idx': frame_idx,
                    'error': f'解码错误: {str(e)}'
                })
        
        return jsonify({
            'success': True,
            'filename': filename,
            'start': start,
            'end': end,
            'count': len(frames),
            'frames': frames
        })
    
    def _get_video_info(self, filename):
        """获取视频元数据"""
        filepath = os.path.join(self.video_folder, filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': '视频不存在'}), 404
        
        ext = filename.lower().split('.')[-1]
        
        if ext == 'ban':
            try:
                info = BANCodec.get_video_info(filepath)
                return jsonify({
                    'success': True,
                    'info': info,
                    'is_ban_format': True
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        else:
            # 标准视频格式
            return jsonify({
                'success': True,
                'info': {
                    'is_standard': True,
                    'ext': ext
                },
                'is_ban_format': False
            })
    
    def _get_cache_stats(self, filename):
        """获取帧缓存统计
        
        注意：这是简化版本，实际的缓存统计需要在服务端实现
        """
        filepath = os.path.join(self.video_folder, filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': '视频不存在'}), 404
        
        try:
            info = BANCodec.get_video_info(filepath)
            file_size = os.path.getsize(filepath)
            
            return jsonify({
                'success': True,
                'filename': filename,
                'cache_stats': {
                    'total_frames': info['frame_count'],
                    'file_size_mb': file_size / (1024 * 1024),
                    'avg_frame_size_kb': (file_size / info['frame_count']) / 1024,
                    'estimated_cached_frames': 0,  # 需要服务端实现
                    'cache_hit_rate': 0.0,  # 需要服务端实现
                    'cache_memory_mb': 0.0  # 需要服务端实现
                }
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500


def init_api_routes(app, video_folder):
    """初始化API路由
    
    Args:
        app: Flask应用实例
        video_folder: 视频文件夹路径
    """
    api = VideoAPI(app, video_folder)
    return api
