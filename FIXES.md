# Banana Player 修复总结

## 修复日期
2026-01-07 (第一轮修复)
2026-01-07 (第二轮修复 - 进度条递归问题)

## 最新修复 (2026-01-07 下午)

### 5. 进度条递归崩溃 🔴 严重
**问题描述**:
- 拖动进度条时程序崩溃
- 错误: `RecursionError: maximum recursion depth exceeded`
- 进度条的 `command` 回调和 `set()` 方法形成递归循环

**问题原因**:
```
用户拖动进度条 → seek_video() → display_frame()
→ progress.set() → 触发command → seek_video() → 无限循环
```

**修复位置**:
- `src/player.py:40` - 添加 `self.seeking` 标志位
- `src/player.py:319-323` - 修改 `display_frame()` 防止递归
- `src/player.py:382-388` - 修改 `seek_video()` 防止递归

**修复内容**:
```python
# 添加标志位
self.seeking = False

# display_frame 中
if not self.seeking:
    self.seeking = True
    self.progress.set(frame_idx)
    self.seeking = False

# seek_video 中
if self.frames and not self.seeking:
    self.seeking = True
    # 执行跳转
    self.seeking = False
```

**详细说明**: 请查看 [RECURSION_FIX.md](RECURSION_FIX.md)

---

## 第一轮修复 (2026-01-07 上午)

## 发现的问题

### 1. UI组件背景色错误
**问题描述**:
- `player.py` 中 `main_frame` 的背景色设置为空字符串 `bg=''`
- `ui_components.py` 中的 `RoundedFrame` 和 `RoundButton` 尝试读取父组件背景色时遇到空字符串
- 导致 Tkinter 报错: "unknown color name ''"

**修复位置**:
- `src/player.py:58` - 将 `bg=''` 改为 `bg=PinkConfig.PINK_SOFT`
- `src/ui_components.py:22-28` - 添加背景色错误处理
- `src/ui_components.py:92-99` - 为 RoundButton 添加背景色错误处理

**修复内容**:
```python
# 使用安全的背景色获取方式
parent_bg = parent['bg'] if parent['bg'] else 'systemTransparent'
try:
    self.config(bg=parent_bg)
except:
    self.config(bg=PinkConfig.PINK_SOFT)
```

---

### 2. MP4转.ban后播放超出长度问题
**问题描述**:
- 编码时OpenCV的 `CAP_PROP_FRAME_COUNT` 可能不准确
- 实际读取的帧数可能少于或多于元数据中记录的 `frame_count`
- 解码时按照元数据的帧数读取，导致超出文件末尾

**修复位置**:
- `src/codec.py:31-63` - 编码器修复
- `src/codec.py:90-129` - 解码器修复

**修复内容**:

#### 编码器修复:
1. 不再依赖 OpenCV 的 `frame_count`
2. 先写入临时帧数为0
3. 实际统计写入的帧数 `actual_frames`
4. 写入完成后回到文件头部更新实际帧数

```python
# 预留frame_count位置
header_pos = f.tell()
f.write(struct.pack('IIII', fps, width, height, 0))

# 统计实际写入的帧数
actual_frames = 0
while True:
    ret, frame = cap.read()
    if not ret:
        break
    # ... 写入帧数据
    actual_frames += 1

# 回到头部更新实际帧数
f.seek(header_pos)
f.write(struct.pack('IIII', fps, width, height, actual_frames))
```

#### 解码器修复:
1. 增加文件末尾检查，避免读取超出文件范围
2. 检查帧大小是否合理（< 10MB）
3. 验证读取的数据长度是否完整
4. 更新元数据为实际读取的帧数

```python
for i in range(frame_count):
    # 检查是否还有数据
    size_data = f.read(4)
    if len(size_data) < 4:
        print(f"警告: 文件在第{i}帧提前结束")
        break

    frame_size = struct.unpack('I', size_data)[0]

    # 检查帧大小是否合理
    if frame_size > 10 * 1024 * 1024:
        print(f"警告: 第{i}帧大小异常")
        break

    frame_data = f.read(frame_size)
    if len(frame_data) < frame_size:
        print(f"警告: 第{i}帧数据不完整")
        break

    # ... 解码帧

# 更新元数据为实际读取的帧数
metadata['frame_count'] = len(frames)
```

---

### 3. 线程安全问题
**问题描述**:
- 播放线程结束时直接修改UI组件
- 使用了不安全的 lambda 和 setattr 方式更新按钮

**修复位置**:
- `src/player.py:301-322` - 播放线程修复

**修复内容**:
```python
# 使用线程安全的方式更新UI
def update_button():
    self.play_btn.text = "▶ 播放"
    self.play_btn.draw_button()
self.root.after(0, update_button)
```

---

### 4. 边界检查增强
**问题描述**:
- `display_frame()` 缺少负数索引检查
- 元数据可能为None导致除零错误

**修复位置**:
- `src/player.py:260-282` - display_frame 方法

**修复内容**:
```python
# 增加更严格的边界检查
if not self.frames or frame_idx >= len(self.frames) or frame_idx < 0:
    return

# 增加元数据安全检查
if self.metadata and self.metadata.get('fps', 0) > 0:
    # ... 计算时间
```

---

## 测试结果

### 测试1: 模块导入测试
✅ 所有模块导入成功

### 测试2: 现有.ban文件解码测试
✅ vis.ban (146MB, 500帧) 解码成功
- 帧数: 500
- 分辨率: 2932x800
- FPS: 10

### 测试3: 完整转换流程测试
✅ MP4→BAN→解码 完整流程测试通过
- vis.mp4 (108.25 MB) → test_output.ban (145.50 MB)
- 500帧全部正确编码和解码
- 帧数完全匹配

---

## 文件修改清单

### 修改的文件:
1. **src/player.py** - 3处修改
   - 第58行: 修复main_frame背景色
   - 第260-282行: 增强display_frame边界检查
   - 第301-322行: 修复播放线程的UI更新

2. **src/codec.py** - 2处修改
   - 第31-63行: 修复编码器帧数统计
   - 第90-129行: 修复解码器文件读取安全性

3. **src/ui_components.py** - 2处修改
   - 第21-29行: RoundedFrame背景色错误处理
   - 第92-99行: RoundButton背景色错误处理

### 新增的测试文件:
1. **test_decode.py** - 解码测试脚本
2. **test_full.py** - 完整功能测试脚本
3. **test_gui.py** - GUI启动测试脚本

---

## 使用建议

### 运行播放器:
```bash
python3 main.py
```

### 运行测试:
```bash
# 测试解码
python3 test_decode.py vis.ban

# 测试完整流程
python3 test_full.py

# 测试GUI启动
python3 test_gui.py
```

---

## 注意事项

1. **对于已有的.ban文件**: 如果是用旧版本编码的，可能仍然存在帧数不匹配问题。建议重新转换。

2. **转换建议**: 使用修复后的版本重新转换MP4文件，确保元数据准确。

3. **内存使用**: 播放器会将所有帧加载到内存中，大视频文件可能占用较多内存。

4. **许可证系统**: 首次运行会创建30天试用许可，可以使用界面中的提示密钥激活黄金会员。

---

## 总结

所有问题已成功修复：
- ✅ UI组件背景色问题
- ✅ MP4转.ban后播放超出长度问题
- ✅ 线程安全问题
- ✅ 边界检查增强

测试通过率: 100%
