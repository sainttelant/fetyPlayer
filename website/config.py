"""
网站配置
"""
import os

# 基础配置
SECRET_KEY = 'banana-player-pink-secret-key-2024'
DEBUG = True

# 数据库配置
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(os.path.dirname(__file__), 'app.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False

# 上传配置
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'videos')
MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB
ALLOWED_EXTENSIONS = {'ban', 'mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv'}

# 视频配置
VIDEO_FOLDER = os.path.join(os.path.dirname(__file__), 'videos')

# 下载配置
DOWNLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'downloads')

# 分页配置
VIDEOS_PER_PAGE = 12

# 会员配置
PREMIUM_PRICES = {
    'monthly': {'price': 9.9, 'duration_days': 30, 'name': '月度会员'},
    'quarterly': {'price': 28.9, 'duration_days': 90, 'name': '季度会员'},
    'yearly': {'price': 98.9, 'duration_days': 365, 'name': '年度会员'}
}
