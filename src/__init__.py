"""
Banana Player Package
"""
__version__ = "1.0.0"
__author__ = "Banana Player Team"
from .player import BananaPlayer
from .codec import BANCodec
from .license_manager import LicenseManager
from .config import Config
__all__ = ['BananaPlayer', 'BANCodec', 'LicenseManager', 'Config']