# Web 版本播放器 vs 桌面版播放器功能对比

## 📊 功能对比表

| 功能 | 桌面版 (main.py) | Web 版本 (website/) | 状态 |
|------|-------------------|------------------|------|
| 基础播放 | ✅ tkinter Canvas | ✅ HTML5 Canvas | ⚠️ 需完善 |
| 流式解码 | ✅ StreamingDecoder | ❌ 无实现 | 🔴 需实现 |
| 帧缓存 | ✅ LRU (60帧, 500MB) | ❌ 无缓存 | 🔴 需实现 |
| 多线程预加载 | ✅ FramePreloader | ❌ 无预加载 | 🔴 需实现 |
| 进度条拖拽 | ✅ 完全支持 | ⚠️ 基础实现 | ⚠️ 需增强 |
| 播放/暂停 | ✅ 完全支持 | ✅ 基础实现 | ✅ 可用 |
| 帧跳转 | ✅ 支持 | ⚠️ 基础支持 | ⚠️ 需增强 |
| 时间显示 | ✅ MM:SS 格式 | ✅ MM:SS 格式 | ✅ 完全一致 |
| 音量控制 | ❌ 无 | ⚠️ UI 存在, 无功能 | 🔴 需实现 |
| 全屏 | ❌ 无 | ✅ 基础支持 | ✅ 可用 |

## 🔴 Web 版本缺失的关键功能

### 1. 流式解码器
**桌面版** (`src/frame_buffer.py`):
- `StreamingDecoder` - 按需加载帧
- `FrameBuffer` - LRU 缓存
- `FramePreloader` - 后台预加载

**Web 版本** (`website/static/js/player.js:83-32`):
```javascript
async decodeBanVideo(filename) {
    // ❌ 当前只是占位符
    this.frames = [];
    this.showLoading();
    this.showMessage('正在准备播放 .ban 格式视频...');
}
```

### 2. 后端 API 缺失
**需要添加的后端 API**:
```
GET  /api/video/<filename>/frame/<frame_idx>     # 获取单帧
POST /api/video/<filename>/frames/<start>/<end>     # 批量获取帧
GET  /api/video/<filename>/info                # 视频元数据
```

### 3. 前端播放器功能不完整
**桌面版功能**:
- ✅ 实时帧解码
- ✅ 智能缓存管理
- ✅ 流式播放
- ✅ 内存优化

**Web 版本当前状态**:
- ⚠️ 播放器只有基础框架
- ❌ 没有实际解码逻辑
- ⚠️ 进度条功能有限
- ❌ 无缓存机制

## 💡 实现方案

### 方案一：添加完整后端帧级 API (推荐)

#### 新增后端 API (`website/api.py`)

```python
from flask import send_file, jsonify
from src.codec import BANCodec, obfuscate_data, decrypt_aes, calculate_checksum
import struct
import cv2
import numpy as np
import hashlib
from .config import app

# 获取单帧
@app.route('/api/video/<filename>/frame/<int:frame_idx>')
def get_frame(filename, frame_idx):
    filepath = os.path.join(app.config['VIDEO_FOLDER'], filename)
    
    if not os.path.exists(filepath):
        return jsonify({'error': '视频不存在'}), 404
    
    # 获取视频信息
    info = BANCodec.get_video_info(filepath)
    if frame_idx < 0 or frame_idx >= info['frame_count']:
        return jsonify({'error': '帧索引超出范围'}), 400
    
    try:
        # 解码单帧
        frame = BANCodec.decode_single_frame(filepath, frame_idx)
        
        # 转换为 base64
        is_success, buffer = cv2.imencode('.jpg', frame)
        if not is_success:
            return jsonify({'error': '帧编码失败'}), 500
        
        import base64
        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return jsonify({
            'frame_idx': frame_idx,
            'frame_data': f'data:image/jpeg;base64,{frame_base64}',
            'width': frame.shape[1],
            'height': frame.shape[0]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 批量获取帧 (用于预加载)
@app.route('/api/video/<filename>/frames/<int:start>/<int:end>')
def get_frames(filename, start, end):
    # 实现类似逻辑，返回多帧数据
    pass

# 获取视频元数据 (已存在，可能需要增强)
@app.route('/api/video/<filename>/info')
def get_video_info_api(filename):
    # 已实现，可能需要添加更多元数据
    pass
```

#### BANCodec 扩展 (`src/codec.py`)

```python
@staticmethod
def decode_single_frame(filepath, frame_idx):
    """解码单帧（用于流式播放）"""
    import hashlib
    
    with open(filepath, 'rb') as f:
        # 读取头文件
        magic = deobfuscate_data(f.read(4))
        if magic != PinkConfig.BAN_MAGIC_NUMBER:
            raise Exception("无效的 .ban 文件格式")
        
        salt = deobfuscate_data(f.read(32))
        iv = deobfuscate_data(f.read(16))
        
        # 读取视频信息
        header = f.read(16)
        fps, width, height, frame_count = struct.unpack('IIII', header)
        
        # 生成密钥
        seed = PinkConfig.BAN_MAGIC_NUMBER + salt + PinkConfig.APP_NAME.encode()
        from .license_manager import hashlib_pbkdf2_hmac
        master_key = hashlib_pbkdf2_hmac('sha256', seed, b'BananaKeyDerivation', 100000, 32)
        
        # 读取帧大小表
        sizes_len = struct.unpack('I', f.read(4))[0]
        encrypted_sizes = f.read(sizes_len)
        
        # 解密帧大小表
        if ENCRYPTION_ENABLED:
            from .license_manager import decrypt_aes
            sizes_packet = decrypt_aes(encrypted_sizes, master_key, iv)
        else:
            sizes_packet = encrypted_sizes
        
        # 解析帧大小
        sizes_data_bytes = sizes_packet[16:]
        frame_sizes = [int(s) for s in sizes_data_bytes[4:].decode('utf-8').split(',') if s]
        
        # 计算帧数据位置
        frame_data_offset = f.tell()
        
        # 计算目标帧位置
        offset = frame_data_offset
        for i in range(frame_idx):
            if i >= len(frame_sizes):
                raise IndexError(f"帧索引超出范围: {frame_idx} >= len(frame_sizes)}")
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
            from .license_manager import decrypt_aes
            frame_packet = decrypt_aes(encrypted_frame, master_key, iv)
        else:
            frame_packet = encrypted_frame
        
        if not frame_packet:
            return None
        
        # 验证校验和
        frame_checksum = frame_packet[4:20]
        frame_data = frame_packet[20:]
        if calculate_checksum(frame_data) != frame_checksum:
            return None
        
        # 解码帧
        nparr = np.frombuffer(frame_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        return frame
```

#### 前端播放器增强 (`website/static/js/player.js`)

```javascript
async loadBanVideo(filename) {
    this.isBanFormat = true;
    this.showLoading();
    
    try {
        // 获取视频信息
        const infoResponse = await fetch(`/api/video/${filename}/info`);
        const infoData = await infoResponse.json();
        
        if (infoData.error) {
            throw new Error(infoData.error);
        }
        
        this.fps = infoData.info.fps || 30;
        this.totalFrames = infoData.info.frame_count || 0;
        this.frameInterval = 1000 / this.fps;
        
        // 初始化播放器
        this.hideLoading();
        this.renderFrame();
        this.updateTimeDisplay();
        
    } catch (error) {
        console.error('加载视频失败:', error);
        this.showError(error.message);
    }
}

async renderFrame() {
    if (this.isBanFormat && this.currentFrame < this.totalFrames) {
        // 从后端获取帧
        try {
            const response = await fetch(`/api/video/${window.videoConfig.filename}/frame/${this.currentFrame}`);
            const frameData = await response.json();
            
            if (frameData.error) {
                throw new Error(frameData.error);
            }
            
            // 显示帧
            const img = new Image();
            img.onload = () => {
                this.ctx.drawImage(img, 0, 0, this.canvas.width, this.canvas.height);
            };
            img.src = `data:${frameData.frame_data}`;
            
        } catch (error) {
            console.error('获取帧失败:', error);
            this.showError('无法加载帧');
        }
    }
}
```

### 方案二：使用 WebAssembly (高级)

将 Python 解码器编译为 WebAssembly，在浏览器中直接运行。

### 方案三：前端分片加载 (简化版)

在服务器端提供按需分片传输，前端渐进式加载。

## 📋 实现优先级

### P0 - 核心功能（立即实现）
1. ✅ 后端单帧 API (`get_single_frame`)
2. ✅ BANCodec 单帧解码 (`decode_single_frame`)
3. ✅ 前端帧加载 (`loadFrameFromAPI`)
4. ✅ 进度条增强（精确跳转）

### P1 - 性能优化（2周内）
1. ✅ 批量帧 API (预加载)
2. ✅ 前端帧缓存 (LRU 缓存)
3. ✅ 智能预加载策略
4. ✅ 内存管理

### P2 - 高级功能（1个月内）
1. ⚠️ WebAssembly 编译
2. ⚠️ 后台线程池
3. ⚠️ 实时转码接口

## 🔧 代码修改清单

### 需要创建的文件
- [ ] `website/api.py` - 后端 API 路由
- [ ] `src/codec.py` - 添加 `decode_single_frame` 方法

### 需要修改的文件
- [ ] `website/static/js/player.js` - 增强播放器逻辑
- [ ] `website/config.py` - 添加视频配置选项
- [ ] `requirements.txt` - 确保所有依赖已安装

### 测试验证
- [ ] 单帧获取 API 测试
- [ ] 流式播放测试
- [ ] 缓存命中率测试
- [ ] 性能基准测试

## 🎯 目标功能对比

| 功能 | 当前 Web | 目标桌面版 | 优先级 |
|------|----------|------------|--------|
| 单帧获取 | ❌ 无 | ✅ StreamingDecoder | P0 |
| 批量帧获取 | ❌ 无 | ✅ 批量解码 | P1 |
| LRU 缓存 | ❌ 无 | ✅ FrameBuffer | P1 |
| 多线程预加载 | ❌ 无 | ✅ FramePreloader | P1 |
| 进度条精确 | ⚠️ 百分比 | ✅ 帧级 | P0 |
| 播放控制 | ⚠️ 基础 | ✅ 完整 | P1 |
| 时间显示 | ✅ MM:SS | ✅ MM:SS | ✅ 已实现 |

---

**版本**: 2.0  
**日期**: 2026-01-12  
**状态**: 需要实现 P0 功能以匹配桌面版播放器能力
