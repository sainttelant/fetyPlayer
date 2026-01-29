"""

🎀 粉红少女风格配置文件

包含所有颜色、常量配置

"""


class PinkConfig:

    """粉红少女风格配置类"""

    # ==================== 粉红色系配色方案 ====================

    PINK_PRIMARY = "#FF69B4"      # 热粉红 - 主色调

    PINK_LIGHT = "#FFB6D9"        # 浅粉红 - 浅色背景

    PINK_DARK = "#FF1493"         # 深粉红 - 强调色

    PINK_SOFT = "#FFC0CB"         # 柔粉红 - 柔和背景

    PINK_GRADIENT_1 = "#FF85C1"   # 渐变粉1

    PINK_GRADIENT_2 = "#FFD4E5"   # 渐变粉2

    PURPLE_SOFT = "#E6B3F0"       # 柔紫色 - 辅助色

    WHITE = "#FFFFFF"             # 纯白色

    CREAM = "#FFF5F7"             # 奶油白 - 温馨背景

    HEART_RED = "#FF1493"         # 爱心红

    BLACK = "#000000"             # 黑色 - 视频背景

    # ==================== 应用程序信息 ====================

    APP_NAME = "🎀 Banana Player 🎀"

    APP_VERSION = "1.0.0"

    APP_AUTHOR = "Banana Player Team"

    # ==================== 窗口设置 ====================

    WINDOW_WIDTH = 1000

    WINDOW_HEIGHT = 750

    # ==================== 许可证设置 ====================

    LICENSE_FILE = "banana_license.dat"

    TRIAL_DAYS = 30

    ENCRYPTION_KEY = b"BananaPlayerPinkKey2024"

    DEMO_GOLDEN_KEY_SEED = b"GOLDEN_BANANA_2024"

    # ==================== .ban格式设置 ====================

    BAN_MAGIC_NUMBER = b'BAN2'  # 更新版本号以支持音频

    BAN_EXTENSION = ".ban"

    JPEG_QUALITY = 85

    # ==================== 音频设置 ====================

    AUDIO_ENABLED = True

    AUDIO_SAMPLE_RATE = 44100

    AUDIO_CHANNELS = 2

    AUDIO_CHUNK_SIZE = 1024

    AUDIO_FORMAT = 'pcm_s16le'

    # ==================== 支持的输入格式 ====================

    SUPPORTED_INPUT_FORMATS = [

        ("视频文件", "*.mp4 *.avi *.mov *.mkv *.flv *.wmv"),

        ("所有文件", "*.*")

    ]

    # ==================== UI组件尺寸 ====================

    HEADER_HEIGHT = 80

    LICENSE_BAR_HEIGHT = 50

    VIDEO_CANVAS_HEIGHT = 450

    CONTROL_PANEL_HEIGHT = 80

    INFO_BAR_HEIGHT = 40

    # 圆角半径

    RADIUS_LARGE = 25      # 大组件圆角

    RADIUS_MEDIUM = 20     # 中等组件圆角

    RADIUS_SMALL = 15      # 小组件圆角

    RADIUS_BUTTON = 25     # 按钮圆角

    # 边框宽度

    BORDER_THICK = 4       # 粗边框

    BORDER_NORMAL = 3      # 普通边框

    BORDER_THIN = 2        # 细边框

    # ==================== 字体设置 ====================
    # 使用系统可用的中文字体，优先选择顺序
    FONT_FAMILY = ('WenQuanYi Micro Hei', 'Noto Sans CJK SC', 'Droid Sans Fallback', 'SimHei', 'Microsoft YaHei UI', 'Arial', 'sans-serif')

    FONT_TITLE = (FONT_FAMILY, 24, 'bold')

    FONT_HEADING = (FONT_FAMILY, 16, 'bold')

    FONT_NORMAL = (FONT_FAMILY, 12)

    FONT_BUTTON = (FONT_FAMILY, 12, 'bold')

    FONT_SMALL = (FONT_FAMILY, 10)

    # ==================== 爱心装饰位置 ====================

    HEART_POSITIONS = [

        (50, 50), (950, 50), (50, 700), (950, 700),

        (150, 100), (850, 100), (150, 650), (850, 650)

    ]

    HEART_SIZE = 0.8
 