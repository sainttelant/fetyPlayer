"""
Configuration constants for Banana Player
"""
class Config:
   """Application configuration"""
   # Application Info
   APP_NAME = "Banana Player"
   APP_VERSION = "1.0.0"
   APP_AUTHOR = "Banana Player Team"
   # Window Settings
   WINDOW_WIDTH = 900
   WINDOW_HEIGHT = 650
   WINDOW_BG_COLOR = "#2b2b2b"
   # Video Canvas Settings
   CANVAS_BG_COLOR = "#000000"
   CANVAS_WIDTH = 800
   CANVAS_HEIGHT = 450
   # Control Panel Settings
   CONTROL_BG_COLOR = "#3b3b3b"
   BUTTON_BG_COLOR = "#4b4b4b"
   BUTTON_FG_COLOR = "white"
   # License Settings
   LICENSE_FILE = "banana_license.dat"
   TRIAL_DAYS = 30
   ENCRYPTION_KEY = b"BananaPlayerSecretKey2024"
   # Demo Golden Key (for testing)
   DEMO_GOLDEN_KEY_SEED = b"GOLDEN_BANANA_2024"
   # Video Format Settings
   BAN_MAGIC_NUMBER = b'BAN1'
   BAN_EXTENSION = ".ban"
   JPEG_QUALITY = 85
   # Supported Input Formats
   SUPPORTED_INPUT_FORMATS = [
       ("Video Files", "*.mp4 *.avi *.mov *.mkv *.flv *.wmv"),
       ("All Files", "*.*")
   ]
   # Colors
   COLOR_SUCCESS = "#00ff00"
   COLOR_ERROR = "#ff0000"
   COLOR_WARNING = "#ffd700"
   COLOR_INFO = "#aaaaaa"