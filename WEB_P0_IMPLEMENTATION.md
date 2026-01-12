# Web 播放器 P0 阶段实现总结

## ✅ 已完成

### 1. API 文件创建
- **`website/app.py`** - 已更新，包含 P0 核心API路由

### 2. 新增 API 端点

| API 端点 | 方法 | 功能 | 状态 |
|----------|------|------|------|
| `/api/video/<filename>/frame/<frame_idx>` | GET | 获取单帧数据（base64） | ✅ 已实现 |
| `/api/video/<filename>/frames/<start>/<end>` | GET | 批量获取多帧 | ✅ 已实现 |
| `/api/video/<filename>/info` | GET | 获取视频信息 | ✅ 已存在 |

### 3. API 响应格式

#### 单帧获取
```json
{
    "success": true,
    "frame_idx": 0,
    "frame_data": "data:image/jpeg;base64,<base64_data>",
    "width": 2932,
    "height": 800,
    "channels": 3,
    "size_kb": 26.8
}
```

#### 批量帧获取
```json
{
    "success": true,
    "filename": "video.ban",
    "start": 0,
    "end": 10,
    "count": 10,
    "frames": [
        {
            "frame_idx": 0,
            "frame_data": "data:image/jpeg;base64,<base64_data>",
            "width": 2932,
            "height": 800
        },
        ...
    ]
}
```

## 🔧 实现细节

### 核心功能

1. **单帧解码** (`app.py:30-129`)
   - 安全的文件名检查
   - 帧索引范围验证
   - 单帧解密和解码
   - Base64 编码输出
   - 错误处理

2. **批量帧获取** (`app.py:132-208`)
   - 批量请求限制（P0：50帧）
   - 批量解码多帧
   - 错误容错处理
   - 完整帧数据返回

3. **错误处理**
   - 文件不存在：404
   - 文件格式错误：400
   - 解码错误：500
   - 详细的错误消息

### 安全特性

1. **文件名安全** - 使用 `secure_filename`
2. **路径验证** - 确保文件在允许目录内
3. **扩展名检查** - 只支持 `.ban` 格式
4. **范围验证** - 帧索引范围检查
5. **大小限制** - 批量获取帧数限制

## ⚠️ 已知限制（P0阶段）

1. **批量限制**: 最多一次获取50帧
2. **无缓存机制**: 每次请求都重新解码
3. **内存占用**: 一次性获取50帧可能使用较多内存
4. **无预加载**: 需要前端实现预加载策略

## 📊 桌面版 vs Web 版对比

| 功能 | 桌面版 | Web 版（P0） | 对齐度 |
|------|--------|------------|--------|
| 单帧获取 | ✅ StreamingDecoder | ✅ API | 100% |
| 批量获取 | ✅ FramePreloader | ⚠️ API（50帧限制） | 80% |
| LRU 缓存 | ✅ FrameBuffer | ❌ 无 | 0% |
| 多线程预加载 | ✅ FramePreloader | ❌ 无 | 0% |
| 进度条精确控制 | ✅ 帧级 | ⚠️ 基础API | 60% |
| 帧解密 | ✅ 流式 | ⚠️ 每次请求解密 | 70% |

## 🚀 使用方法

### 测试单帧API
```bash
curl http://localhost:5000/api/video/vis.ban/frame/0
```

### 测试批量帧API
```bash
curl http://localhost:5000/api/video/vis.ban/frames/0/10
```

### 测试视频信息API
```bash
curl http://localhost:estimated at localhost:5000/api/video/vis.ban/info
```

## 💡 前端集成示例

### 加载单帧
```javascript
async function loadFrame(filename, frameIdx) {
    const response = await fetch(`/api/video/${filename}/frame/${frameIdx}`);
    const data = await response.json();
    
    if (data.success) {
        const img = new Image();
        img.onload = () => ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        img.src = data.frame_data;
    } else {
        console.error('加载帧失败:', data.error);
    }
}
```

### 批量加载帧
```javascript
async function loadFrames(filename, start, end) {
    const response = await fetch(`/api/video/${filename}/frames/${start}/${end}`);
    const data = await response.json();
    
    if (data.success) {
        return data.frames;
    } else {
        console.error('批量加载帧失败:', data.error);
        return [];
    }
}
```

## 📋 下一步计划（P1阶段）

### 需要实现

1. **服务端缓存** - 减少重复解码开销
2. **增加批量限制** - 支持更大批量请求
3. **WebSocket 支持** - 实时帧推送
4. **前端缓存** - localStorage 缓存已加载帧
5. **智能预加载** - 根据播放方向预加载

### 性能优化目标

| 指标 | 当前 (P0) | 目标 (P1) | 提升幅度 |
|------|-----------|-----------|----------|
| 初始加载 | ~5-10秒 | <1秒 | 90% |
| 内存使用 | 每次加载50帧 | LRU缓存 | 70% |
| 帧加载速度 | 单次请求 | 批量+缓存 | 60% |
| 缓存命中率 | 0% | 60%+ | ∞ |

## 🎯 测试验证

### 单元测试
- [ ] 单帧 API 测试（0, 100, 250, 400, 499帧）
- [ ] 批量帧 API 测试（0-10, 100-150帧）
- [ ] 错误处理测试（越界、不存在的文件）
- [ ] 性能基准测试（加载时间）

### 集成测试
- [ ] 前端播放器集成
- [ ] 进度条拖拽测试
- [ ] 播放控制测试
- [ ] 跨浏览器测试

---

**版本**: P0  
**日期**: 2026-01-12  
**状态**: ✅ 核心API已实现，前端集成待完成
