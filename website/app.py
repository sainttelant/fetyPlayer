"""
Flask 主应用 - Banana Player 网站
"""
import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from src.codec import BANCodec

app = Flask(__name__)
app.config.from_pyfile('config.py')

# 确保视频目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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
        # 对于普通视频，直接返回
        return render_template('watch.html',
                             filename=filename,
                             video_info={'is_standard': True})

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
