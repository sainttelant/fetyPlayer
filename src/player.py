"""
🎀 主播放器界面
粉红少女风格的视频播放器
"""
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2
from PIL import Image, ImageTk
import os
import threading
import time
from .config import PinkConfig
from .license_manager import LicenseManager
from .codec import BANCodec
from .ui_components import RoundedFrame, RoundButton, create_heart_decoration

class BananaPlayerPink:
   """粉红少女风格播放器主类"""
   def __init__(self, root):
       """初始化播放器
       Args:
           root: Tk根窗口
       """
       self.root = root
       self.root.title(PinkConfig.APP_NAME)
       self.root.geometry(f"{PinkConfig.WINDOW_WIDTH}x{PinkConfig.WINDOW_HEIGHT}")
       # 设置渐变背景
       self.setup_gradient_background()
       # 创建菜单栏
       self.create_menu_bar()
       # 初始化许可证管理器
       self.license_manager = LicenseManager()
       # 视频状态变量
       self.current_video = None
       self.frames = []
       self.metadata = None
       self.current_frame_idx = 0
       self.is_playing = False
       self.play_thread = None
       self.seeking = False  # 防止进度条递归更新
       # 创建UI
       self.setup_ui()
       # 检查许可证状态
       self.check_license_status()
       # 启动爱心动画
       self.animate_hearts()
   def setup_gradient_background(self):
       """设置渐变背景"""
       self.bg_canvas = tk.Canvas(self.root, highlightthickness=0)
       self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
       # 创建粉红渐变效果
       for i in range(100):
           ratio = i / 100
           # 从浅粉到深粉的渐变
           r1, g1, b1 = int(255), int(182 + (213-182)*ratio), int(217 + (228-217)*ratio)
           color = f'#{r1:02x}{g1:02x}{b1:02x}'
           self.bg_canvas.create_rectangle(0, i*10, 1000, (i+1)*10,
                                          fill=color, outline='')

   def create_menu_bar(self):
       """创建菜单栏"""
       menubar = tk.Menu(self.root)
       self.root.config(menu=menubar)

       # 文件菜单
       file_menu = tk.Menu(menubar, tearoff=0)
       menubar.add_cascade(label="文件 (File)", menu=file_menu)
       file_menu.add_command(label="📂 打开.ban视频...", command=self.open_video, accelerator="Ctrl+O")
       file_menu.add_command(label="🔄 转换视频到.ban...", command=self.convert_video, accelerator="Ctrl+T")
       file_menu.add_separator()
       file_menu.add_command(label="❌ 退出", command=self.root.quit, accelerator="Ctrl+Q")

       # 工具菜单
       tools_menu = tk.Menu(menubar, tearoff=0)
       menubar.add_cascade(label="工具 (Tools)", menu=tools_menu)
       tools_menu.add_command(label="📊 查看视频信息", command=self.show_video_info)
       tools_menu.add_separator()
       tools_menu.add_command(label="👑 激活黄金会员", command=self.activate_golden)
       tools_menu.add_command(label="🔑 查看许可证信息", command=self.show_license_info)

       # 播放菜单
       play_menu = tk.Menu(menubar, tearoff=0)
       menubar.add_cascade(label="播放 (Play)", menu=play_menu)
       play_menu.add_command(label="▶️ 播放/暂停", command=self.toggle_play, accelerator="Space")
       play_menu.add_command(label="⏹️ 停止", command=self.stop_video, accelerator="Ctrl+S")

       # 帮助菜单
       help_menu = tk.Menu(menubar, tearoff=0)
       menubar.add_cascade(label="帮助 (Help)", menu=help_menu)
       help_menu.add_command(label="📖 关于 Banana Player", command=self.show_about)
       help_menu.add_command(label="💡 使用说明", command=self.show_help)

       # 绑定快捷键
       self.root.bind('<Control-o>', lambda _: self.open_video())
       self.root.bind('<Control-t>', lambda _: self.convert_video())
       self.root.bind('<Control-q>', lambda _: self.root.quit())
       self.root.bind('<Control-s>', lambda _: self.stop_video())
       self.root.bind('<space>', lambda _: self.toggle_play())

   def setup_ui(self):
       """设置用户界面"""
       main_frame = tk.Frame(self.root, bg=PinkConfig.PINK_SOFT)
       main_frame.place(relx=0.5, rely=0.5, anchor='center', relwidth=0.95, relheight=0.95)
       # 创建各个UI组件
       self.create_header(main_frame)
       self.create_license_bar(main_frame)
       self.create_video_canvas(main_frame)
       self.create_controls(main_frame)
       self.create_info_bar(main_frame)
       # 添加爱心装饰
       self.add_heart_decorations()
   def create_header(self, parent):
       """创建顶部标题栏"""
       header_frame = RoundedFrame(
           parent,
           radius=PinkConfig.RADIUS_MEDIUM,
           bg_color=PinkConfig.PINK_SOFT,
           border_color=PinkConfig.PINK_PRIMARY,
           border_width=PinkConfig.BORDER_NORMAL,
           height=PinkConfig.HEADER_HEIGHT
       )
       header_frame.pack(fill=tk.X, padx=10, pady=10)
       # 标题
       title = tk.Label(
           header_frame,
           text=PinkConfig.APP_NAME,
           font=PinkConfig.FONT_TITLE,
           bg=PinkConfig.PINK_SOFT,
           fg=PinkConfig.PINK_DARK
       )
       header_frame.create_window(500, 40, window=title)
       # 菜单按钮
       btn_y = 40
       open_btn = RoundButton(header_frame, "📂 打开视频",
                             command=self.open_video, width=110, height=35)
       header_frame.create_window(100, btn_y, window=open_btn)
       convert_btn = RoundButton(header_frame, "🔄 转换视频",
                                command=self.convert_video, width=110, height=35)
       header_frame.create_window(230, btn_y, window=convert_btn)
       license_btn = RoundButton(header_frame, "👑 激活会员",
                                command=self.activate_golden, width=110, height=35)
       header_frame.create_window(850, btn_y, window=license_btn)
   def create_license_bar(self, parent):
       """创建许可证状态栏"""
       license_frame = RoundedFrame(
           parent,
           radius=PinkConfig.RADIUS_SMALL,
           bg_color=PinkConfig.PURPLE_SOFT,
           border_color=PinkConfig.PINK_PRIMARY,
           border_width=PinkConfig.BORDER_THIN,
           height=PinkConfig.LICENSE_BAR_HEIGHT
       )
       license_frame.pack(fill=tk.X, padx=10, pady=5)
       self.license_label = tk.Label(
           license_frame,
           text="",
           font=PinkConfig.FONT_HEADING,
           bg=PinkConfig.PURPLE_SOFT,
           fg=PinkConfig.PINK_DARK
       )
       license_frame.create_window(500, 25, window=self.license_label)
   def create_video_canvas(self, parent):
       """创建视频画布"""
       canvas_container = RoundedFrame(
           parent,
           radius=PinkConfig.RADIUS_MEDIUM,
           bg_color=PinkConfig.BLACK,
           border_color=PinkConfig.PINK_PRIMARY,
           border_width=PinkConfig.BORDER_THICK,
           height=PinkConfig.VIDEO_CANVAS_HEIGHT
       )
       canvas_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
       self.canvas = tk.Canvas(canvas_container, bg=PinkConfig.BLACK, highlightthickness=0)
       canvas_container.create_window(500, 225, window=self.canvas, width=950, height=420)
   def create_controls(self, parent):
       """创建控制面板"""
       control_frame = RoundedFrame(
           parent,
           radius=PinkConfig.RADIUS_SMALL,
           bg_color=PinkConfig.CREAM,
           border_color=PinkConfig.PINK_PRIMARY,
           border_width=PinkConfig.BORDER_NORMAL,
           height=PinkConfig.CONTROL_PANEL_HEIGHT
       )
       control_frame.pack(fill=tk.X, padx=10, pady=5)
       # 播放按钮
       self.play_btn = RoundButton(control_frame, "▶ 播放",
                                   command=self.toggle_play, width=100, height=35)
       control_frame.create_window(100, 40, window=self.play_btn)
       # 停止按钮
       stop_btn = RoundButton(control_frame, "■ 停止",
                             command=self.stop_video, width=100, height=35)
       control_frame.create_window(220, 40, window=stop_btn)
       # 进度条
       self.progress = ttk.Scale(control_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                                command=self.seek_video)
       control_frame.create_window(600, 40, window=self.progress, width=600, height=30)
       # 时间显示
       self.time_label = tk.Label(control_frame, text="00:00 / 00:00",
                                  font=('Arial', 11, 'bold'),
                                  bg=PinkConfig.CREAM, fg=PinkConfig.PINK_DARK)
       control_frame.create_window(900, 40, window=self.time_label)
       # 自定义进度条样式
       self._style_progress_bar()
   def _style_progress_bar(self):
       """自定义进度条样式"""
       style = ttk.Style()
       style.theme_use('clam')
       style.configure('TScale',
                      background=PinkConfig.PINK_PRIMARY,
                      troughcolor=PinkConfig.PINK_LIGHT,
                      borderwidth=0,
                      lightcolor=PinkConfig.PINK_PRIMARY,
                      darkcolor=PinkConfig.PINK_PRIMARY)
   def create_info_bar(self, parent):
       """创建信息栏"""
       info_frame = RoundedFrame(
           parent,
           radius=10,
           bg_color=PinkConfig.PINK_SOFT,
           border_color=PinkConfig.PINK_PRIMARY,
           border_width=PinkConfig.BORDER_THIN,
           height=PinkConfig.INFO_BAR_HEIGHT
       )
       info_frame.pack(fill=tk.X, padx=10, pady=5)
       self.info_label = tk.Label(
           info_frame,
           text="💕 欢迎使用 Banana Player～准备好享受视频时光了吗？",
           font=PinkConfig.FONT_SMALL,
           bg=PinkConfig.PINK_SOFT,
           fg=PinkConfig.PINK_DARK
       )
       info_frame.create_window(500, 20, window=self.info_label)
   def add_heart_decorations(self):
       """添加爱心装饰"""
       self.hearts = []
       for x, y in PinkConfig.HEART_POSITIONS:
           heart = create_heart_decoration(self.bg_canvas, x, y, size=PinkConfig.HEART_SIZE)
           self.hearts.append(heart)
   def animate_hearts(self):
       """爱心闪烁动画"""
       import random
       def pulse():
           for heart in self.hearts:
               # 随机改变颜色实现闪烁效果
               if random.random() > 0.5:
                   self.bg_canvas.itemconfig(heart, fill=PinkConfig.HEART_RED)
               else:
                   self.bg_canvas.itemconfig(heart, fill=PinkConfig.PINK_PRIMARY)
           self.root.after(500, pulse)
       pulse()
   def check_license_status(self):
       """检查许可证状态"""
       valid, message = self.license_manager.check_license()
       self.license_label.config(text=message)
       if not valid:
           messagebox.showwarning("许可证过期", "您的试用期已过期，请激活黄金会员继续使用！")
   def open_video(self):
       """打开视频文件"""
       valid, _ = self.license_manager.check_license()
       if not valid:
           messagebox.showerror("许可证错误", "您的许可证已过期，请激活黄金会员！")
           return
       file_path = filedialog.askopenfilename(
           title="选择.ban视频",
           filetypes=[("Banana视频", f"*{PinkConfig.BAN_EXTENSION}"), ("所有文件", "*.*")]
       )
       if file_path:
           try:
               self.info_label.config(text="💫 正在加载视频...")
               self.root.update()
               self.metadata, self.frames = BANCodec.decode_video(file_path)
               self.current_video = file_path
               self.current_frame_idx = 0
               self.progress.config(to=len(self.frames)-1)
               info_text = (f"✨ 已加载: {os.path.basename(file_path)} | "
                          f"{self.metadata['width']}x{self.metadata['height']} | "
                          f"{self.metadata['fps']} FPS")
               self.info_label.config(text=info_text)
               self.display_frame(0)
           except Exception as e:
               messagebox.showerror("错误", f"无法打开视频: {str(e)}")
   def convert_video(self):
       """转换视频到.ban格式"""
       input_path = filedialog.askopenfilename(
           title="选择要转换的视频",
           filetypes=PinkConfig.SUPPORTED_INPUT_FORMATS
       )
       if input_path:
           output_path = filedialog.asksaveasfilename(
               title="保存.ban视频",
               defaultextension=PinkConfig.BAN_EXTENSION,
               filetypes=[("Banana视频", f"*{PinkConfig.BAN_EXTENSION}")]
           )
           if output_path:
               try:
                   self.info_label.config(text="🎬 正在转换视频...请稍候")
                   self.root.update()
                   BANCodec.encode_video(input_path, output_path)
                   self.info_label.config(text="💖 转换完成！")
                   messagebox.showinfo("成功", f"视频已成功转换！\n保存位置: {output_path}")
               except Exception as e:
                   messagebox.showerror("错误", f"转换失败: {str(e)}")
   def display_frame(self, frame_idx):
       """显示指定帧"""
       if not self.frames or frame_idx >= len(self.frames) or frame_idx < 0:
           return

       frame = self.frames[frame_idx]
       frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
       # 调整大小以适应画布
       img = Image.fromarray(frame_rgb)
       img = img.resize((950, 420), Image.Resampling.LANCZOS)
       photo = ImageTk.PhotoImage(image=img)
       self.canvas.delete("all")
       self.canvas.create_image(475, 210, image=photo, anchor=tk.CENTER)
       self.canvas.image = photo

       # 更新进度条和时间（防止递归）
       if not self.seeking:
           self.seeking = True
           self.progress.set(frame_idx)
           self.seeking = False

       if self.metadata and self.metadata.get('fps', 0) > 0:
           current_time = frame_idx / self.metadata['fps']
           total_time = len(self.frames) / self.metadata['fps']
           self.time_label.config(
               text=f"{self._format_time(current_time)} / {self._format_time(total_time)}"
           )
   def _format_time(self, seconds):
       """格式化时间为MM:SS"""
       minutes = int(seconds // 60)
       secs = int(seconds % 60)
       return f"{minutes:02d}:{secs:02d}"
   def toggle_play(self):
       """播放/暂停切换"""
       if not self.frames:
           messagebox.showwarning("无视频", "请先打开一个.ban视频！")
           return

       self.is_playing = not self.is_playing
       if self.is_playing:
           self.play_btn.text = "⏸ 暂停"
           self.play_btn.draw_button()
           if self.play_thread is None or not self.play_thread.is_alive():
               self.play_thread = threading.Thread(target=self._play_video, daemon=True)
               self.play_thread.start()
       else:
           self.play_btn.text = "▶ 播放"
           self.play_btn.draw_button()
   def _play_video(self):
       """播放视频线程"""
       fps = self.metadata['fps']
       frame_delay = 1.0 / fps
       while self.is_playing and self.current_frame_idx < len(self.frames):
           start_time = time.time()
           self.root.after(0, self.display_frame, self.current_frame_idx)
           self.current_frame_idx += 1
           elapsed = time.time() - start_time
           sleep_time = frame_delay - elapsed
           if sleep_time > 0:
               time.sleep(sleep_time)

       # 播放结束处理
       if self.current_frame_idx >= len(self.frames):
           self.current_frame_idx = 0
           self.is_playing = False
           # 使用线程安全的方式更新UI
           def update_button():
               self.play_btn.text = "▶ 播放"
               self.play_btn.draw_button()
           self.root.after(0, update_button)
   def stop_video(self):
       """停止播放"""
       self.is_playing = False
       self.current_frame_idx = 0
       self.play_btn.text = "▶ 播放"
       self.play_btn.draw_button()
       if self.frames:
           self.display_frame(0)
   def seek_video(self, value):
       """跳转到指定位置"""
       if self.frames and not self.seeking:
           self.seeking = True
           self.current_frame_idx = int(float(value))
           self.display_frame(self.current_frame_idx)
           self.seeking = False
   def activate_golden(self):
       """激活黄金会员对话框"""
       dialog = tk.Toplevel(self.root)
       dialog.title("💎 激活黄金会员")
       dialog.geometry("450x250")
       dialog.configure(bg=PinkConfig.PINK_SOFT)
       # 让对话框居中并置顶
       dialog.transient(self.root)
       dialog.grab_set()
       tk.Label(
           dialog,
           text="✨ 输入黄金会员激活码 ✨",
           font=('Microsoft YaHei UI', 16, 'bold'),
           bg=PinkConfig.PINK_SOFT,
           fg=PinkConfig.PINK_DARK
       ).pack(pady=20)
       # 输入框容器
       entry_frame = tk.Frame(dialog, bg=PinkConfig.WHITE, bd=0)
       entry_frame.pack(pady=10, padx=40, fill=tk.X)
       key_entry = tk.Entry(
           entry_frame,
           font=('Arial', 14),
           justify='center',
           bg=PinkConfig.WHITE,
           fg=PinkConfig.PINK_DARK,
           relief=tk.FLAT,
           bd=2
       )
       key_entry.pack(ipady=8, padx=5, pady=5)
       # 提示
       hint = self.license_manager.get_golden_key_hint()
       tk.Label(
           dialog,
           text=f"💝 提示密钥: {hint}",
           font=('Arial', 10),
           bg=PinkConfig.PINK_SOFT,
           fg=PinkConfig.PURPLE_SOFT
       ).pack(pady=10)
       def activate():
           key = key_entry.get().strip()
           if self.license_manager.activate_golden_membership(key):
               messagebox.showinfo("成功", "🎉 黄金会员激活成功！\n现在您可以永久使用所有功能啦～")
               self.check_license_status()
               dialog.destroy()
           else:
               messagebox.showerror("错误", "❌ 激活码无效，请检查后重试")
       # 激活按钮
       activate_btn = RoundButton(dialog, "💖 立即激活", command=activate,
                                 width=150, height=40)
       activate_btn.pack(pady=20)

   def show_video_info(self):
       """显示当前视频信息"""
       if not self.metadata or not self.frames:
           messagebox.showinfo("提示", "请先打开一个.ban视频文件！")
           return

       info_text = f"""
📹 视频信息

文件名: {os.path.basename(self.current_video) if self.current_video else '未知'}

分辨率: {self.metadata['width']} x {self.metadata['height']}
帧率: {self.metadata['fps']} FPS
总帧数: {len(self.frames)}
时长: {len(self.frames) / self.metadata['fps']:.2f} 秒

当前帧: {self.current_frame_idx + 1} / {len(self.frames)}
       """
       messagebox.showinfo("视频信息", info_text.strip())

   def show_license_info(self):
       """显示许可证信息"""
       info = self.license_manager.get_license_info()
       license_type = "🌟 黄金会员" if info['type'] == 'golden' else "🎫 试用版"

       if info['type'] == 'golden':
           detail_text = f"""
许可证类型: {license_type}
状态: ✅ 已激活
激活日期: {info['data'].get('activation_date', '未知')[:10]}

您拥有所有功能的永久访问权限！
           """
       else:
           start_date = info['data'].get('start_date', '')[:10]
           expiry_date = info['data'].get('expiry_date', '')[:10]
           detail_text = f"""
许可证类型: {license_type}
状态: {'✅ 有效' if info['valid'] else '❌ 已过期'}
开始日期: {start_date}
到期日期: {expiry_date}

{info['message']}
           """

       messagebox.showinfo("许可证信息", detail_text.strip())

   def show_about(self):
       """显示关于对话框"""
       about_text = f"""
🎀 Banana Player 🎀
粉红少女风格视频播放器

版本: {PinkConfig.APP_VERSION}
作者: {PinkConfig.APP_AUTHOR}

✨ 特色功能 ✨
• 支持自定义.ban视频格式
• 粉红少女UI设计
• 流畅的视频播放体验
• 简单易用的格式转换

💖 感谢使用 Banana Player！
       """
       messagebox.showinfo("关于 Banana Player", about_text.strip())

   def show_help(self):
       """显示使用说明"""
       help_text = """
📖 Banana Player 使用说明

1️⃣ 转换视频
   文件 → 转换视频到.ban
   支持格式: MP4, AVI, MOV, MKV, FLV, WMV

2️⃣ 打开视频
   文件 → 打开.ban视频
   或点击工具栏的"打开视频"按钮

3️⃣ 播放控制
   • 播放/暂停: 点击播放按钮或按空格键
   • 停止: 点击停止按钮或按 Ctrl+S
   • 拖动进度条跳转到指定位置

4️⃣ 快捷键
   • Ctrl+O: 打开视频
   • Ctrl+T: 转换视频
   • Ctrl+S: 停止播放
   • Space: 播放/暂停
   • Ctrl+Q: 退出程序

5️⃣ 激活黄金会员
   工具 → 激活黄金会员
   输入激活码解锁永久使用权限

💡 提示: 首次使用有30天试用期
       """
       messagebox.showinfo("使用说明", help_text.strip())