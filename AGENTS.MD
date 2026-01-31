# AGENTS.MD - Banana Player 代码仓库分析

## 📋 项目概述

**Banana Player** 是一个粉红少女风格的自定义格式视频播放器，支持 `.ban` 格式的编码和播放。项目包含桌面端播放器和Web端播放器两个主要部分。

### 基本信息
- **项目名称**: Banana Player (粉红少女版视频播放器)
- **版本**: 1.0.0
- **作者**: Banana Player Team
- **主要语言**: Python
- **UI框架**: Tkinter (桌面端), Flask (Web端)

---

## 🏗️ 项目架构

### 目录结构
```
fetyPlayer/
├── main.py                 # 桌面端程序入口
├── src/                    # 核心源代码目录
│   ├── __init__.py
│   ├── player.py          # 播放器主界面
│   ├── codec.py           # .ban编解码器
│   ├── config.py          # 配置文件
│   ├── license_manager.py # 许可证管理
│   ├── ui_components.py   # UI组件库
│   └── frame_buffer.py    # 帧缓冲系统
├── website/               # Web端应用
│   ├── app.py            # Flask主应用
│   ├── api.py            # API接口
│   ├── models.py          # 数据库模型
│   ├── config.py          # 网站配置
│   ├── templates/        # HTML模板
│   ├── static/           # 静态资源
│   └── videos/          # 视频存储目录
├── requirements.txt       # 桌面端依赖
└── README.md             # 项目说明文档
```

---

## 🎯 核心组件分析

### 1. 桌面端播放器 (src/player.py)

**类**: `BananaPlayerPink`

**主要功能**:
- 粉红少女风格UI界面
- 视频播放控制（播放/暂停/停止/进度条）
- 视频格式转换（MP4/AVI/MOV → .ban）
- 许可证管理（试用版/黄金会员）
- 完整菜单栏系统
- 快捷键支持

**关键方法**:
| 方法 | 功能 |
|------|------|
| `setup_gradient_background()` | 设置渐变背景 |
| `create_menu_bar()` | 创建菜单栏 |
| `setup_ui()` | 设置用户界面 |
| `open_video()` | 打开.ban视频 |
| `convert_video()` | 转换视频到.ban格式 |
| `display_frame()` | 显示指定帧 |
| `toggle_play()` | 播放/暂停切换 |
| `_play_video()` | 播放视频线程 |
| `activate_golden()` | 激活黄金会员 |

**UI组件**:
- Header: 标题栏，包含标题和操作按钮
- License Bar: 许可证状态显示
- Video Canvas: 视频播放区域
- Control Panel: 播放控制面板
- Info Bar: 信息提示栏

---

### 2. 编解码器 (src/codec.py)

**类**: `BANCodec`

**主要功能**:
- 将标准视频编码为 `.ban` 格式
- 解码 `.ban` 格式视频
- 单帧解码（用于Web播放器）
- 视频信息获取

**.ban文件格式**:
```
[4字节] 魔数: "BAN1" (已混淆)
[32字节] 盐值 (已混淆)
[16字节] IV (已混淆)
[16字节] 头部: FPS, Width, Height, Frame Count
[N字节] 加密帧数据
[4字节] 帧大小表长度
[N字节] 加密帧大小表
[32字节] 文件校验和 (SHA256)
```

**加密特性**:
- AES-256-CBC 加密
- PBKDF2 密钥派生 (100,000轮)
- 数据混淆 (字节置换)
- 帧级校验和验证
- 文件完整性校验

**关键方法**:
| 方法 | 功能 |
|------|------|
| `encode_video()` | 编码视频为.ban格式 |
| `decode_video()` | 解码.ban视频 |
| `decode_single_frame()` | 解码单帧 |
| `get_video_info()` | 获取视频信息 |

---

### 3. 帧缓冲系统 (src/frame_buffer.py)

**类**:
- `FrameBuffer`: 线程安全的帧缓冲，LRU淘汰策略
- `StreamingDecoder`: 流式解码器，按需解码帧
- `FramePreloader`: 多线程帧预加载器

**主要功能**:
- 内存高效的帧缓存
- LRU (Least Recently Used) 淘汰策略
- 按需解码，避免一次性加载所有帧
- 多线程预加载，提升播放流畅度

**关键参数**:
- `max_frames`: 最大缓存帧数 (默认60)
- `max_memory_mb`: 最大内存使用 (默认500MB)
- `preload_window`: 预加载窗口 (默认30帧)

---

### 4. 许可证管理 (src/license_manager.py)

**类**: `LicenseManager`

**主要功能**:
- 试用期管理 (30天)
- 黄金会员激活
- 许可证加密存储
- 许可证状态检查

**许可证类型**:
- **试用版**: 30天免费试用
- **黄金会员**: 永久使用权限

**加密方式**: XOR加密 (生产环境建议使用更强的加密)

---

### 5. UI组件库 (src/ui_components.py)

**类**:
- `RoundedFrame`: 圆角边框框架
- `RoundButton`: 圆形渐变按钮
- `create_heart_decoration()`: 爱心装饰函数

**主要功能**:
- 提供粉红少女风格的UI组件
- 圆角设计
- 渐变效果
- 爱心装饰

---

### 6. 配置管理 (src/config.py)

**类**: `PinkConfig`

**主要配置**:

**配色方案**:
```python
PINK_PRIMARY = "#FF69B4"      # 热粉红 - 主色调
PINK_LIGHT = "#FFB6D9"        # 浅粉红 - 浅色背景
PINK_DARK = "#FF1493"         # 深粉红 - 强调色
PINK_SOFT = "#FFC0CB"         # 柔粉红 - 柔和背景
PURPLE_SOFT = "#E6B3F0"       # 柔紫色 - 辅助色
CREAM = "#FFF5F7"             # 奶油白 - 温馨背景
HEART_RED = "#FF1493"         # 爱心红
```

**应用配置**:
- 窗口尺寸: 1000x750
- 最小窗口: 800x600
- 试用天数: 30天
- JPEG质量: 85

---

## 🌐 Web端应用 (website/)

### 1. Flask主应用 (website/app.py)

**主要功能**:
- 视频上传和转换
- 视频播放页面
- 用户认证系统
- 会员订阅系统
- 支付系统（支付宝/比特币）
- 下载页面

**核心API**:
| 路由 | 功能 |
|------|------|
| `/api/video/<filename>/frame/<int:frame_idx>` | 获取单帧数据 |
| `/api/video/<filename>/frames/<int:start>/<int:end>` | 批量获取帧 |
| `/api/video/<filename>/info` | 获取视频信息 |
| `/api/videos` | 获取视频列表 |
| `/api/delete/<filename>` | 删除视频 |

**用户权限**:
- 非会员: 15秒观看限制
- 会员: 无限制观看

---

### 2. API接口 (website/api.py)

**类**: `VideoAPI`

**主要功能**:
- 单帧获取API
- 批量帧获取API
- 视频元数据API
- 帧缓存统计API

**响应格式**:
```json
{
  "success": true,
  "frame_idx": 0,
  "frame_data": "data:image/jpeg;base64,...",
  "width": 1920,
  "height": 1080,
  "channels": 3,
  "size_kb": 45.2
}
```

---

### 3. 数据库模型 (website/models.py)

**模型**:
- `User`: 用户模型
- `Subscription`: 订阅模型
- `PaymentRecord`: 支付记录模型

**用户字段**:
- id, username, email, password_hash
- is_premium, created_at, last_login

**订阅字段**:
- id, user_id, plan_type
- start_date, end_date, status, price

**支付记录字段**:
- id, user_id, amount, currency
- payment_method, status, transaction_id

---

### 4. 网站配置 (website/config.py)

**主要配置**:
- 数据库: SQLite
- 上传限制: 500MB
- 支持格式: ban, mp4, avi, mov, mkv, flv, wmv
- 分页: 每页12个视频

**会员套餐**:
```python
PREMIUM_PRICES = {
    'monthly': {'price': 9.9, 'duration_days': 30},
    'quarterly': {'price': 28.9, 'duration_days': 90},
    'yearly': {'price': 98.9, 'duration_days': 365}
}
```

---

## 🔧 技术栈

### 桌面端
- **UI框架**: Tkinter
- **视频处理**: OpenCV (cv2)
- **图像处理**: Pillow (PIL)
- **加密**: cryptography
- **数值计算**: NumPy

### Web端
- **Web框架**: Flask
- **数据库**: SQLite (Flask-SQLAlchemy)
- **用户认证**: Flask-Login
- **视频处理**: OpenCV
- **加密**: cryptography

---

## 🎨 设计特点

### 1. 粉红少女风格
- 渐变粉色背景
- 圆角设计
- 爱心装饰
- 柔和配色方案

### 2. 自定义视频格式
- `.ban` 专用格式
- AES-256-CBC 加密
- 帧级校验和
- 文件完整性验证

### 3. 内存优化
- 流式解码
- LRU缓存策略
- 按需加载
- 多线程预加载

### 4. 用户体验
- 完整菜单栏
- 快捷键支持
- 进度条显示
- 实时时间显示

---

## 🔐 安全特性

### 1. 加密
- AES-256-CBC 视频加密
- PBKDF2 密钥派生 (100,000轮)
- 数据混淆
- 许可证加密存储

### 2. 校验
- 帧级校验和验证
- 文件完整性校验 (SHA256)
- 魔数验证

### 3. 访问控制
- 用户认证
- 会员权限控制
- 观看时间限制

---

## 📊 数据流

### 视频编码流程
```
输入视频 (MP4/AVI/MOV)
    ↓
OpenCV 读取帧
    ↓
JPEG 压缩 (质量85)
    ↓
添加帧序号和校验和
    ↓
AES-256-CBC 加密
    ↓
写入 .ban 文件
    ↓
添加文件校验和
```

### 视频解码流程
```
.ban 文件
    ↓
读取并验证魔数
    ↓
读取盐值和IV
    ↓
派生解密密钥
    ↓
读取帧大小表
    ↓
解密帧数据
    ↓
验证校验和
    ↓
JPEG 解码
    ↓
输出帧数据
```

### Web播放流程
```
用户请求帧
    ↓
检查用户权限
    ↓
检查观看限制
    ↓
解码单帧
    ↓
转换为Base64
    ↓
返回JSON响应
    ↓
前端显示
```

---

## 🚀 快速开始

### 桌面端
```bash
# 安装依赖
pip install -r requirements.txt

# 运行程序
python main.py
```

### Web端
```bash
# 进入网站目录
cd website

# 安装依赖
pip install -r requirements.txt

# 运行服务器
python app.py
```

---

## 📝 依赖项

### 桌面端 (requirements.txt)
```
opencv-python>=4.8.0
numpy>=1.24.0
pillow>=10.0.0
cryptography>=41.0.0
```

### Web端 (website/requirements.txt)
```
Flask==2.3.3
Werkzeug==2.3.7
opencv-python==4.8.0.74
numpy==1.24.3
cryptography==41.0.3
Flask-Login==0.6.3
Flask-SQLAlchemy==3.0.5
```

---

## 🎯 核心功能

### 桌面端功能
1. ✅ 视频播放控制
2. ✅ 视频格式转换
3. ✅ 许可证管理
4. ✅ 完整菜单栏
5. ✅ 快捷键支持
6. ✅ 视频信息查看
7. ✅ 黄金会员激活

### Web端功能
1. ✅ 视频上传
2. ✅ 视频播放
3. ✅ 用户注册/登录
4. ✅ 会员订阅
5. ✅ 支付系统
6. ✅ 下载页面
7. ✅ 视频搜索

---

## 🔍 代码质量

### 优点
- 模块化设计良好
- 代码注释清晰
- 错误处理完善
- 类型提示部分使用

### 改进建议
- 添加更多类型提示
- 增加单元测试
- 优化加密性能
- 添加日志系统
- 改进错误处理

---

## 📚 相关文档

- [README.md](README.md) - 项目说明
- [USER_GUIDE.md](USER_GUIDE.md) - 用户指南
- [FIXES.md](FIXES.md) - 修复说明
- [SECURITY_ANALYSIS.md](SECURITY_ANALYSIS.md) - 安全分析
- [WEB_P0_IMPLEMENTATION.md](WEB_P0_IMPLEMENTATION.md) - Web实现文档

---

## 🎉 总结

Banana Player 是一个功能完整的自定义格式视频播放器，具有以下特点：

1. **双端支持**: 桌面端和Web端
2. **自定义格式**: .ban加密格式
3. **粉红风格**: 少女心UI设计
4. **会员系统**: 试用版和黄金会员
5. **内存优化**: 流式解码和LRU缓存
6. **安全加密**: AES-256-CBC加密

项目架构清晰，模块化设计良好，适合学习和扩展。

---

**文档生成时间**: 2026-01-31
**分析工具**: Kilo Code Agent
