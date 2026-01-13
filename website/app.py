"""
Flask 主应用 - Banana Player 网站
"""
import os
import sys
import base64
import struct
import json
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from src.codec import BANCodec
import cv2
import numpy as np

app = Flask(__name__)
app.config.from_pyfile('config.py')

from models import db, User, Subscription, PaymentRecord

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '请先登录'


@login_manager.user_loader
def load_user(user_id):
    """加载用户"""
    return User.query.get(int(user_id))

# 确保视频目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# ==================== 用户权限和播放限制 ====================

class UserSession:
    """用户会话管理"""
    def __init__(self):
        self.is_premium = False
        self.watch_time_limit = 15  # 非会员15秒限制
        self.session_start = None
        
    def check_watch_limit(self, current_time):
        """检查观看时间限制"""
        if self.is_premium:
            return True, None  # 会员无限制
        
        if self.session_start is None:
            self.session_start = current_time
            return True, None
        
        elapsed = current_time - self.session_start
        if elapsed >= self.watch_time_limit:
            return False, f"非会员用户只能观看{self.watch_time_limit}秒，请升级会员解锁完整功能"
        
        return True, None

def get_user_session(request):
    """获取用户会话"""
    user_session = UserSession()
    
    if current_user.is_authenticated:
        user_session.is_premium = current_user.is_premium_active()
    
    return user_session

# ==================== P0阶段 - 核心API ====================

def decode_frame_from_file(filepath, frame_idx):
    """从文件中解码单帧的辅助函数"""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from src.config import PinkConfig
    from src.codec import decrypt_aes, calculate_checksum, ENCRYPTION_ENABLED, derive_key_from_salt, deobfuscate_data
    import hashlib
    
    # 读取并解码单帧
    with open(filepath, 'rb') as f:
        # 跳过文件头（magic, salt, iv）
        magic = deobfuscate_data(f.read(4))
        salt = deobfuscate_data(f.read(32))
        iv = deobfuscate_data(f.read(16))
        
        # 派生加密密钥
        master_key = derive_key_from_salt(salt)
        
        # 跳过视频信息头
        f.read(16)
        
        # 读取帧大小表
        sizes_len = struct.unpack('I', f.read(4))[0]
        encrypted_sizes = f.read(sizes_len)
        
        # 解密帧大小表
        if ENCRYPTION_ENABLED:
            sizes_packet = decrypt_aes(encrypted_sizes, master_key, iv)
            if sizes_packet is None:
                raise Exception(f'帧大小表解密失败，密钥长度={len(master_key)}, IV长度={len(iv)}, 数据长度={len(encrypted_sizes)}')
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
            frame_packet = decrypt_aes(encrypted_frame, master_key, iv)
        else:
            frame_packet = encrypted_frame
        
        if not frame_packet:
            raise Exception('帧解密失败')
        
        # 验证校验和
        frame_checksum = frame_packet[4:20]
        frame_data = frame_packet[20:]
        if calculate_checksum(frame_data) != frame_checksum:
            raise Exception('帧数据校验失败')
        
        # 解码帧
        nparr = np.frombuffer(frame_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            raise Exception('帧解码失败')
        
        # 转换为base64
        is_success, buffer = cv2.imencode('.jpg', frame, 
                                         [cv2.IMWRITE_JPEG_QUALITY, PinkConfig.JPEG_QUALITY])
        if not is_success:
            raise Exception('帧编码失败')
        
        frame_base64 = base64.b64encode(buffer.tobytes()).decode('utf-8')
        
        return {
            'success': True,
            'frame_idx': frame_idx,
            'frame_data': f'data:image/jpeg;base64,{frame_base64}',
            'width': frame.shape[1],
            'height': frame.shape[0],
            'channels': frame.shape[2] if len(frame.shape) > 2 else 1,
            'size_kb': len(buffer) / 1024
        }


@app.route('/api/video/<filename>/frame/<int:frame_idx>')
def get_video_frame(filename, frame_idx):
    """获取单帧数据（P0阶段）- 带15秒限制
    
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
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'无法读取视频信息: {str(e)}'}), 500
    
    # 检查帧索引范围
    if frame_idx < 0 or frame_idx >= info['frame_count']:
        return jsonify({'error': f'帧索引超出范围: {frame_idx} >= {info["frame_count"]}'}), 400
    
    # 检查观看时间限制
    user_session = get_user_session(request)
    current_time = frame_idx / info['fps']  # 当前帧对应的时间
    can_watch, limit_msg = user_session.check_watch_limit(current_time)
    if not can_watch:
        return jsonify({'error': limit_msg, 'limit_reached': True}), 403
    
    # 解码单帧
    try:
        result = decode_frame_from_file(filepath, frame_idx)
        result['watch_limit'] = {
            'can_watch': True,
            'remaining_time': max(0, user_session.watch_time_limit - current_time)
        }
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'帧解码错误: {str(e)}'}), 500


@app.route('/api/video/<filename>/frames/<int:start>/<int:end>')
def get_video_frames(filename, start, end):
    """批量获取帧数据（P0阶段）- 带15秒限制
    
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
    
    # 检查观看时间限制（检查结束帧的时间）
    user_session = get_user_session(request)
    end_time = end / info['fps']
    can_watch, limit_msg = user_session.check_watch_limit(end_time)
    if not can_watch:
        return jsonify({'error': limit_msg, 'limit_reached': True}), 403
    
    # 解码所有帧
    frames = []
    for frame_idx in range(start, end):
        try:
            # 获取单帧数据
            frame_data = decode_frame_from_file(filepath, frame_idx)
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
        'frames': frames,
        'watch_limit': {
            'can_watch': True,
            'remaining_time': max(0, user_session.watch_time_limit - end_time)
        }
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


@app.route('/test')
def test_player():
    """测试播放器页面"""
    return render_template('test_player.html')

@app.route('/debug')
def debug_player():
    """调试播放器页面"""
    return render_template('debug_player.html')

@app.route('/minimal')
def minimal_test():
    """最小Canvas测试页面"""
    return render_template('minimal_test.html')
    """测试播放器页面"""
    return render_template('test_player.html')

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


# ==================== 用户认证 ====================

@app.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not username or not email or not password:
            flash('请填写所有字段', 'error')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('两次输入的密码不一致', 'error')
            return redirect(url_for('register'))
        
        if len(password) < 6:
            flash('密码长度至少为6位', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('邮箱已被注册', 'error')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email)
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('注册成功，请登录', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'注册失败: {str(e)}', 'error')
            return redirect(url_for('register'))
    
    return render_template('auth/register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('请填写用户名和密码', 'error')
            return redirect(url_for('login'))
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            user.last_login = datetime.utcnow()
            db.session.commit()
            login_user(user)
            flash('登录成功', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('用户名或密码错误', 'error')
            return redirect(url_for('login'))
    
    return render_template('auth/login.html')


@app.route('/logout')
@login_required
def logout():
    """用户登出"""
    logout_user()
    flash('已登出', 'success')
    return redirect(url_for('index'))


# ==================== 会员和支付 ====================

@app.route('/premium')
def premium():
    """会员套餐页面"""
    return render_template('premium.html')


@app.route('/api/premium/plans')
def api_premium_plans():
    """获取会员套餐信息"""
    from config import PREMIUM_PRICES
    return jsonify({'plans': PREMIUM_PRICES})


@app.route('/payment/<plan_type>', methods=['GET', 'POST'])
@login_required
def payment(plan_type):
    """支付页面"""
    from config import PREMIUM_PRICES
    
    if plan_type not in PREMIUM_PRICES:
        flash('无效的套餐', 'error')
        return redirect(url_for('premium'))
    
    plan = PREMIUM_PRICES[plan_type]
    
    if request.method == 'POST':
        payment_method = request.form.get('payment_method')
        
        if payment_method not in ['alipay', 'bitcoin']:
            flash('请选择支付方式', 'error')
            return redirect(url_for('payment', plan_type=plan_type))
        
        payment_record = PaymentRecord(
            user_id=current_user.id,
            amount=plan['price'],
            currency='USD' if payment_method == 'bitcoin' else 'CNY',
            payment_method=payment_method,
            status='pending'
        )
        
        db.session.add(payment_record)
        db.session.commit()
        
        if payment_method == 'bitcoin':
            return redirect(url_for('bitcoin_payment', payment_id=payment_record.id, plan_type=plan_type))
        elif payment_method == 'alipay':
            return redirect(url_for('alipay_payment', payment_id=payment_record.id, plan_type=plan_type))
    
    return render_template('payment.html', plan_type=plan_type, plan=plan)


@app.route('/payment/bitcoin/<int:payment_id>/<plan_type>')
@login_required
def bitcoin_payment(payment_id, plan_type):
    """比特币支付页面"""
    from config import PREMIUM_PRICES
    
    payment_record = PaymentRecord.query.get_or_404(payment_id)
    
    if payment_record.user_id != current_user.id:
        flash('无权访问此支付记录', 'error')
        return redirect(url_for('premium'))
    
    plan = PREMIUM_PRICES.get(plan_type, {})
    
    bitcoin_address = "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"
    
    amount_btc = payment_record.amount * 0.000015
    
    return render_template('payment_bitcoin.html', 
                         payment=payment_record, 
                         plan=plan,
                         bitcoin_address=bitcoin_address,
                         amount_btc=amount_btc)


@app.route('/payment/alipay/<int:payment_id>/<plan_type>')
@login_required
def alipay_payment(payment_id, plan_type):
    """支付宝支付页面"""
    from config import PREMIUM_PRICES
    
    payment_record = PaymentRecord.query.get_or_404(payment_id)
    
    if payment_record.user_id != current_user.id:
        flash('无权访问此支付记录', 'error')
        return redirect(url_for('premium'))
    
    plan = PREMIUM_PRICES.get(plan_type, {})
    
    return render_template('payment_alipay.html', 
                         payment=payment_record, 
                         plan=plan)


@app.route('/api/payment/confirm/<int:payment_id>', methods=['POST'])
@login_required
def confirm_payment(payment_id):
    """确认支付（模拟）"""
    payment_record = PaymentRecord.query.get_or_404(payment_id)
    
    if payment_record.user_id != current_user.id:
        return jsonify({'error': '无权操作'}), 403
    
    if payment_record.status != 'pending':
        return jsonify({'error': '支付记录状态无效'}), 400
    
    plan_type = request.json.get('plan_type')
    from config import PREMIUM_PRICES
    
    if plan_type not in PREMIUM_PRICES:
        return jsonify({'error': '无效的套餐'}), 400
    
    plan = PREMIUM_PRICES[plan_type]
    
    payment_record.status = 'completed'
    payment_record.completed_at = datetime.utcnow()
    payment_record.transaction_id = f"TXN{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{payment_record.id}"
    
    current_user.is_premium = True
    
    subscription = Subscription(
        user_id=current_user.id,
        plan_type=plan_type,
        end_date=datetime.utcnow() + timedelta(days=plan['duration_days']),
        status='active',
        price=plan['price'],
        payment_id=payment_record.id
    )
    
    db.session.add(subscription)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': '支付成功，会员已激活',
        'subscription': {
            'plan_type': plan_type,
            'end_date': subscription.end_date.isoformat()
        }
    })


@app.route('/api/payment/status/<int:payment_id>')
@login_required
def payment_status(payment_id):
    """查询支付状态"""
    payment_record = PaymentRecord.query.get_or_404(payment_id)
    
    if payment_record.user_id != current_user.id:
        return jsonify({'error': '无权访问'}), 403
    
    return jsonify({
        'status': payment_record.status,
        'amount': payment_record.amount,
        'currency': payment_record.currency,
        'payment_method': payment_record.payment_method,
        'transaction_id': payment_record.transaction_id
    })


@app.route('/api/user/subscription')
@login_required
def api_user_subscription():
    """获取用户订阅信息"""
    active_subscription = current_user.subscriptions.filter(
        Subscription.end_date >= datetime.utcnow(),
        Subscription.status == 'active'
    ).first()
    
    if active_subscription:
        return jsonify({
            'is_premium': True,
            'plan_type': active_subscription.plan_type,
            'end_date': active_subscription.end_date.isoformat(),
            'days_remaining': (active_subscription.end_date - datetime.utcnow()).days
        })
    else:
        return jsonify({
            'is_premium': False,
            'plan_type': None,
            'end_date': None,
            'days_remaining': 0
        })


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
