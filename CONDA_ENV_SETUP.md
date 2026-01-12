# 🚀 fetyPlayer 虚拟环境配置和启动指南

## ✅ Flask 已安装完成！

Flask 3.1.2 和依赖已成功安装在 fetyPlayer conda 环境中。

## 📋 快速开始

### 1️⃣ 激活虚拟环境并启动服务器

```bash
# 激活 fetyPlayer 环境
conda activate fetyPlayer

# 进入网站目录
cd website

# 启动 Flask 服务器
python3 app.py
```

### 2️⃣ 或使用启动脚本（推荐）

```bash
chmod +x start_server.sh
./start_server.sh
```

服务器将运行在 `http://localhost:5000`

## 📊 API 端点

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/video/<filename>/frame/<frame_idx>` | GET | 获取单帧数据 |
| `/api/video/<filename>/frames/<start>/<end>` | GET | 批量获取帧数据 |
| `/api/video/<filename>/info` | GET | 获取视频信息 |
| `/videos/<filename>` | GET | 下载视频文件 |
| `/` | GET | 首页（视频列表） |
| `/watch/<filename>` | GET | 播放页面 |

## 🧪 测试 API

### 测试视频信息

```bash
curl http://localhost:5000/api/video/vis.ban/info
```

### 测试单帧获取

```bash
curl http://localhost:5000/api/video/vis.ban/frame/0
```

### 测试批量帧获取（0-10帧）

```bash
curl http://localhost:5000/api/video/vis.ban/frames/0/10
```

## 📂 准备测试视频

当前 `website/videos/` 目录为空。需要复制 .ban 文件：

```bash
# 复制 vis.ban 到网站视频目录
cp vis.ban website/videos/

# 或复制所有 .ban 文件
cp *.ban website/videos/
```

## 🔧 常见问题

### Q: "no module named flask"
A: 确保已激活 fetyPlayer conda 环境：
```bash
conda activate fetyPlayer
pip install Flask
```

### Q: "ModuleNotFoundError: No module named 'src'"
A: 需要在 fetyPlayer 项目根目录运行，而不是 website 子目录。

### Q: 端口 5000 被占用
A: 在 `website/app.py` 中修改端口号：
```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
```

### Q: API 返回 404
A: 确保 .ban 文件已复制到 `website/videos/` 目录。

## 🎯 下一步

1. **复制测试视频**：将 .ban 文件复制到 `website/videos/`
2. **启动服务器**：运行 `python3 website/app.py`
3. **测试 API**：使用 curl 或浏览器访问 `http://localhost:5000`
4. **前端集成**：使用 P0 API 更新前端播放器
5. **运行测试套件**：执行 `python3 test_p0_api.py`

## 📚 相关文档

- `WEB_P0_IMPLEMENTION.md` - P0 阶段实现总结
- `WEB_PLAYER_ANALYSIS.md` - Web vs 桌面版对比分析
- `test_p0_api.py` - API 测试脚本
- `start_server.sh` - 快速启动脚本

---

**状态**: ✅ Flask 已安装，API 已实现，可以开始测试！
