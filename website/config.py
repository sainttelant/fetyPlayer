"""
网站配置
"""
import os

# 基础配置
SECRET_KEY = 'banana-player-pink-secret-key-2024'
DEBUG = True

# 上传配置
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'videos')
MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB
ALLOWED_EXTENSIONS = {'ban', 'mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv'}

# 视频配置
VIDEO_FOLDER = os.path.join(os.path.dirname(__file__), 'videos')

# 分页配置
VIDEOS_PER_PAGE = 12
