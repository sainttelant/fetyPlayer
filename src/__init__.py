"""
🎀 Banana Player 粉红版包初始化
"""
__version__ = "1.0.0"
__author__ = "Banana Player Team"
__description__ = "粉红少女风格视频播放器"
from .player import BananaPlayerPink
from .config import PinkConfig
from .license_manager import LicenseManager
from .codec import BANCodec
from .ui_components import RoundedFrame, RoundButton, create_heart_decoration
__all__ = [
   'BananaPlayerPink',
   'PinkConfig',
   'LicenseManager',
   'BANCodec',
   'RoundedFrame',
   'RoundButton',
   'create_heart_decoration'
]