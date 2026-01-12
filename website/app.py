"""
Flask 主应用 - Banana Player 网站
"""
import os
import sys
import base64
import struct
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from src.codec import BANCodec
import cv2
import numpy as np

app = Flask(__name__)
app.config.from_pyfile('config.py')

# 确保视频目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# ==================== P0阶段 - 核心API ====================

@app.route('/api/video/<filename>/frame/<int:frame_idx>')
def get_video_frame(filename, frame_idx):
    """获取单帧数据（P0阶段）
    
    Args:
        filename: 视频文件名
        frame_idx: 帧索引
    """
    # 安全检查文件名
    if not filename:
        return jsonify({'error': '缺少文件名'}), 400
    
    filepath = os.path.join(app.config['VIDEO_FOLDER'], filename)
    
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
        from src.config import PinkConfig
        from src.codec import calculate_checksum
        from src.license_manager import decrypt_aes, ENCRYPTION_ENABLED
        
        # 读取并解码单帧
        with open(filepath, 'rb') as f:
            # 跳过文件头（magic, salt, iv）
            magic = f.read(4)
            salt = f.read(32)
            iv = f.read(16)
            
            # 跳过视频信息头
            f.read(16)
            
            # 读取帧大小表
            sizes_len = struct.unpack('I', f.read(4))[0]
            encrypted_sizes = f.read(sizes_len)
            
            # 解密帧大小表
            if ENCRYPTION_ENABLED:
                sizes_packet = decrypt_aes(encrypted_sizes, BANCodec._derive_key(salt), iv)
            else:
                sizes_packet = encrypted_sizes
            
            # 解析帧大小
            sizes_data_bytes = sizes_packet[16:]
            frame_sizes = [int(s) for s in sizes_data_bytes[4:].decode('utf-8').split(',') if s]
            
            # 计算帧数据起始位置
            frame_data_offset = f.tell()
            
            # 计算目标帧位置
            offset = frame_data_offset
            for i in range(frame_idx):
                if i >= len(frame_sizes):
                    raise IndexError(f"帧索引超出范围: {frame_idx} >= {len(frame_sizes)}")
                offset += frame_sizes[i]
            
            # 读取并解密目标帧
            f.seek(offset)
            frame_size = frame_sizes[frame_idx]
            if frame_size <= 0 or frame_size > 50 * 1024 * 1024:
                raise Exception(f"无效的帧大小: {frame_size}")
            
            encrypted_frame = f.read(frame_size)
            if len(encrypted_frame) < frame_size:
                raise Exception("帧数据不完整")
            
            # 解密帧
            if ENCRYPTION_ENABLED:
                frame_packet = decrypt_aes(encrypted_frame, BANCodec._derive_key(salt), iv)
            else:
                frame_packet = encrypted_frame
            
            if not frame_packet:
                return jsonify({'error': '帧解密失败'}), 500
            
            # 验证校验和
            frame_checksum = frame_packet[4:20]
            frame_data = frame_packet[20:]
            if calculate_checksum(frame_data) != frame_checksum:
                return jsonify({'error': '帧数据校验失败'}), 500
            
            # 解码帧
            nparr = np.frombuffer(frame_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
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


@app.route('/api/video/<filename>/frames/<int:start>/<int:end>')
def get_video_frames(filename, start, end):
    """批量获取帧数据（P0阶段）
    
    Args:
        filename: 视频文件名
        start: 起始帧索引
        end: 结束帧索引（不包含）
    """
    # 安全检查文件名
    if not filename:
        return jsonify({'error': '缺少文件名'}), 400
    
    filepath = os.path.join(app.config['VIDEO_FOLDER'], filename)
    
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
    max_batch_size = 50  # P0阶段：最多一次获取50帧
    if (end - start) > max_batch_size:
        return jsonify({'error': f'批量获取帧数超过限制: {max_batch_size} 帧'}), 400
    
    # 解码所有帧
    frames = []
    for frame_idx in range(start, end):
        try:
            # 获取单帧数据
            frame_response_data = get_video_frame.__wrapped__(filename, frame_idx)
            
            if 'success' not in frame_response_data[0]:
                frames.append({
                    'frame_idx': frame_idx,
                    'error': frame_response_data[0].get('error', '未知错误')
                })
                continue
            
            frame_data = frame_response_data[0]
            frames.append({
                'frame_idx': frame_idx,
                'frame_data': frame_data['frame_data'],
                'width': frame_data['width'],
                'height': frame_data['height']
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


# ==================== 原有功能 ====================

def get_videos_list():
    """获取视频列表"""
    videos = []
    video_folder = app.config['VIDEO_FOLDER']
    
    if os.path.exists(video_folder):
        for filename in os.listdir(video_folder):
            filepath = os.path.join(video_folder, filename)
            if os.path.isfile(filepath):
                ext = filename.lower().split('.')[-1]
                if ext == 'ban':
                    try:
                        info = BANCodec.get_video_info(filepath)
                        videos.append({
                            'filename': filename,
                            'name': os.path.splitext(filename)[0],
                            'fps': info['fps'],
                            'width': info['width'],
                            'height': info['height'],
                            'frame_count': info['frame_count'],
                            'duration': info['duration'],
                            'size': os.path.getsize(filepath),
                            'ext': ext
                        })
                    except Exception as e:
                        print(f"无法读取视频信息 {filename}: {e}")
                elif ext in ['mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv']:
                    videos.append({
                        'filename': filename,
                        'name': os.path.splitext(filename)[0],
                        'ext': ext,
                        'size': os.path.getsize(filepath)
                    })
    
    return sorted(videos, key=lambda x: x['name'])


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

    
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """视频上传页面"""
    if request.method == 'POST':
        if 'video' not in request.files:
            flash('没有文件', 'error')
            return redirect(request.url)
        
        file = request.files['video']
        if file.filename == '':
            flash('没有选择文件', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # 如果是普通视频，转换为 .ban 格式
            if filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv')):
                try:
                    ban_path = os.path.splitext(filepath)[0] + '.ban'
                    BANCodec.encode_video(filepath, ban_path)
                    os.remove(filepath)  # 删除原始文件
                    flash(f'视频已转换为 .ban 格式', 'success')
                except Exception as e:
                    flash(f'视频转换失败: {e}', 'error')
            else:
                flash('视频上传成功', 'success')
            
            return redirect(url_for('index'))
        else:
            flash('不支持的文件格式', 'error')
            return redirect(request.url)
    
    return render_template('upload.html')


@app.route('/search')
def search():
    """搜索视频"""
    query = request.args.get('q', '').lower()
    videos = get_videos_list()
    
    if query:
        videos = [v for v in videos if query in v['name'].lower()]
    
    return render_template('index.html', 
                          videos=videos,
                          page=1,
                          total_pages=1,
                          search_query=query)


@app.route('/api/videos')
def api_videos():
    """API - 获取视频列表"""
    videos = get_videos_list()
    return jsonify({'videos': videos, 'total': len(videos)})


@app.route('/api/video/<filename>/info')
def api_video_info(filename):
    """API - 获取视频信息"""
    filepath = os.path.join(app.config['VIDEO_FOLDER'], filename)
    
    if not os.path.exists(filepath):
        return jsonify({'error': '视频不存在'}), 404
    
    ext = filename.lower().split('.')[-1]
    
    if ext == 'ban':
        try:
            info = BANCodec.get_video_info(filepath)
            return jsonify({'info': info, 'filename': filename})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'info': {'is_standard': True}, 'filename': filename})


@app.route('/videos/<filename>')
def serve_video(filename):
    """提供视频文件访问"""
    return send_from_directory(app.config['VIDEO_FOLDER'], filename)


@app.route('/api/delete/<filename>', methods=['DELETE'])
def delete_video(filename):
    """API - 删除视频"""
    filepath = os.path.join(app.config['VIDEO_FOLDER'], filename)
    
    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({'success': True})
    else:
        return jsonify({'error': '视频不存在'}), 404


# ==================== 核心路由 ====================

@app.route('/')
def index():
    """首页 - 视频列表"""
    videos = get_videos_list()
    page = request.args.get('page', 1, type=int)
    per_page = app.config['VIDEOS_PER_PAGE']
    start = (page - 1) * per_page
    end = start + per_page
    paginated_videos = videos[start:end]
    
    return render_template('index.html', 
                          videos=paginated_videos,
                          page=page,
                          total_pages=((len(videos) + per_page - 1) // per_page) if videos else 1)


@app.route('/watch/<filename>')
def watch(filename):
    """视频播放页面"""
    filepath = os.path.join(app.config['VIDEO_FOLDER'], filename)
    
    if not os.path.exists(filepath):
        flash('视频不存在', 'error')
        return redirect(url_for('index'))
    
    ext = filename.lower().split('.')[-1]
    
    if ext == 'ban':
        try:
            info = BANCodec.get_video_info(filepath)
            return render_template('watch.html',
                                  filename=filename,
                                  video_info=info)
        except Exception as e:
            flash(f'无法读取视频信息: {e}', 'error')
            return redirect(url_for('index'))
    else:
        return render_template('watch.html',
                              filename=filename,
                              video_info={'is_standard': True})


# ==================== 下载功能 ====================

@app.route('/downloads', endpoint='downloads')
def downloads_page():
    """下载页面"""
    # 获取可下载的 exe 文件
    downloads = []
    download_folder = app.config.get('DOWNLOAD_FOLDER', os.path.join(os.path.dirname(__file__), 'downloads'))
    os.makedirs(download_folder, exist_ok=True)
    
    if os.path.exists(download_folder):
        for filename in os.listdir(download_folder):
            if filename.endswith('.exe'):
                filepath = os.path.join(download_folder, filename)
                size = os.path.getsize(filepath)
                size_mb = size / (1024 * 1024)
                downloads.append({
                    'filename': filename,
                    'name': os.path.splitext(filename)[0],
                    'version': '1.0.0',
                    'size_mb': round(size_mb, 2),
                    'download_count': 0  # 可以添加统计功能
                })
    
    return render_template('downloads.html', downloads=downloads)


@app.route('/api/downloads', endpoint='api_downloads')
def api_downloads():
    """API - 获取可下载列表"""
    downloads = []
    download_folder = app.config.get('DOWNLOAD_FOLDER', os.path.join(os.path.dirname(__file__), 'downloads'))
    os.makedirs(download_folder, exist_ok=True)
    
    if os.path.exists(download_folder):
        for filename in os.listdir(download_folder):
            if filename.endswith('.exe'):
                filepath = os.path.join(download_folder, filename)
                size = os.path.getsize(filepath)
                downloads.append({
                    'filename': filename,
                    'name': os.path.splitext(filename)[0],
                    'version': '1.0.0',
                    'size_mb': round(size / (1024 * 1024), 2)
                })
    
    return jsonify({'downloads': downloads, 'total': len(downloads)})


@app.route('/download/<filename>', endpoint='download_file')
def download_file(filename):
    """下载文件"""
    from flask import send_from_directory
    
    download_folder = app.config.get('DOWNLOAD_FOLDER', os.path.join(os.path.dirname(__file__), 'downloads'))
    os.makedirs(download_folder, exist_ok=True)
    
    # 安全检查文件名
    if not filename:
        return '缺少文件名', 400
    
    filepath = os.path.join(download_folder, filename)
    
    # 确保文件存在且是 exe 文件
    if not os.path.exists(filepath):
        flash('文件不存在', 'error')
        return redirect(url_for('downloads'))
    
    if not filename.lower().endswith('.exe'):
        flash('不支持的文件格式', 'error')
        return redirect(url_for('downloads'))
    
    return send_from_directory(download_folder, filename, as_attachment=True, download_name=filename)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
