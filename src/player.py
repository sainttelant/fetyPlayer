"""
Banana Player Main Interface
Pink-themed video player
"""
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2
from PIL import Image, ImageTk
import os
import threading
import time
import pygame
import tempfile
from .config import PinkConfig
from .license_manager import LicenseManager
from .simple_codec import SimpleBANCodec
from .ui_components import RoundedFrame, RoundButton, create_heart_decoration
from .frame_buffer import StreamingDecoder, FramePreloader

class BananaPlayerPink:
    """Banana Player Main Class"""
    def __init__(self, root):
        """Initialize player
        Args:
            root: Tk root window
        """
        self.root = root
        self.root.title(PinkConfig.APP_NAME)
        self.root.geometry(f"{PinkConfig.WINDOW_WIDTH}x{PinkConfig.WINDOW_HEIGHT}")
        self.root.minsize(800, 600)  # 设置最小尺寸
        
        # Initialize pygame mixer for audio
        try:
            pygame.mixer.init()
            self.audio_enabled = True
        except Exception as e:
            print(f"音频初始化失败: {e}")
            self.audio_enabled = False
        
        # Set gradient background
        self.setup_gradient_background()
        # Create menu bar
        self.create_menu_bar()
        # Initialize license manager
        self.license_manager = LicenseManager()
        # Initialize video state variables (streaming mode)
        self.current_video = None
        self.decoder = None  # Streaming decoder instead of frames list
        self.preloader = None  # Frame preloader
        self.metadata = None
        self.current_frame_idx = 0
        self.is_playing = False
        self.play_thread = None
        self.seeking = False  # Prevent progress bar recursive update
        self.original_video_size = None  # Store original video resolution
        self.control_frame = None  # Control panel frame
        self.inner_frame = None  # Inner frame for controls
        
        # Audio state variables
        self.audio_file = None  # Temporary audio file path
        self.audio_sound = None  # Pygame Sound object
        self.audio_volume = 0.7  # Default volume (0.0 to 1.0)
        self.audio_muted = False
        
        # Create UI
        self.setup_ui()
        # Check license status
        self.check_license_status()
        # Start heart animation (after setup_ui so self.hearts is initialized)
        self.init_hearts_and_animate()
        # Bind window resize event for video auto-resize
        
    def setup_gradient_background(self):
        """Set gradient background"""
        self.bg_canvas = tk.Canvas(self.root, highlightthickness=0)
        self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        # Create pink gradient effect
        for i in range(100):
            ratio = i / 100
            # From light pink to dark pink
            r1, g1, b1 = int(255), int(182 + (213-182)*ratio), int(217 + (228-217)*ratio)
            color = f'#{r1:02x}{g1:02x}{b1:02x}'
            self.bg_canvas.create_rectangle(0, i*10, 1000, (i+1)*10,
                                           fill=color, outline='')

    def create_menu_bar(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open .ban video...", command=self.open_video, accelerator="Ctrl+O")
        file_menu.add_command(label="Convert video to .ban...", command=self.convert_video, accelerator="Ctrl+T")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit, accelerator="Ctrl+Q")

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Video Info", command=self.show_video_info)
        tools_menu.add_separator()
        tools_menu.add_command(label="Activate Gold Member", command=self.activate_golden)
        tools_menu.add_command(label="License Info", command=self.show_license_info)

        # Play menu
        play_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Play", menu=play_menu)
        play_menu.add_command(label="Play/Pause", command=self.toggle_play, accelerator="Space")
        play_menu.add_command(label="Stop", command=self.stop_video, accelerator="Ctrl+S")

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About Banana Player", command=self.show_about)
        help_menu.add_command(label="Usage Guide", command=self.show_help)

        # Bind shortcuts
        self.root.bind('<Control-o>', lambda _: self.open_video())
        self.root.bind('<Control-t>', lambda _: self.convert_video())
        self.root.bind('<Control-q>', lambda _: self.root.quit())
        self.root.bind('<Control-s>', lambda _: self.stop_video())
        self.root.bind('<space>', lambda _: self.toggle_play())

    def setup_ui(self):
        """Set up user interface"""
        main_frame = tk.Frame(self.root, bg=PinkConfig.PINK_SOFT)
        main_frame.place(relx=0.5, rely=0.5, anchor='center', relwidth=0.95, relheight=0.95)
        # Create UI components
        self.create_header(main_frame)
        self.create_license_bar(main_frame)
        self.create_video_canvas(main_frame)
        self.create_controls(main_frame)
        self.create_info_bar(main_frame)
        # Add heart decorations
        self.add_heart_decorations()
        
        # 绑定窗口大小变化事件，用于自适应视频大小
        self.root.bind('<Configure>', self._on_window_resize)
        
    def create_header(self, parent):
        """Create header title bar"""
        header_frame = RoundedFrame(
            parent,
            radius=PinkConfig.RADIUS_MEDIUM,
            bg_color=PinkConfig.PINK_SOFT,
            border_color=PinkConfig.PINK_PRIMARY,
            border_width=PinkConfig.BORDER_NORMAL,
            height=PinkConfig.HEADER_HEIGHT
        )
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        # Title
        title = tk.Label(
            header_frame,
            text=PinkConfig.APP_NAME,
            font=PinkConfig.FONT_TITLE,
            bg=PinkConfig.PINK_SOFT,
            fg=PinkConfig.PINK_DARK
        )
        header_frame.create_window(500, 40, window=title)
        # Menu buttons - Use simplified English for reliability
        btn_y = 40
        open_btn = RoundButton(header_frame, "[ Open ]",
                              command=self.open_video, width=110, height=35)
        header_frame.create_window(100, btn_y, window=open_btn)
        convert_btn = RoundButton(header_frame, "[ Convert ]",
                                 command=self.convert_video, width=110, height=35)
        header_frame.create_window(230, btn_y, window=convert_btn)
        license_btn = RoundButton(header_frame, "[ VIP ]",
                                 command=self.activate_golden, width=110, height=35)
        header_frame.create_window(850, btn_y, window=license_btn)
        
    def create_license_bar(self, parent):
        """Create license status bar"""
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
        """Create video canvas"""
        # 使用普通的Frame而不是RoundedFrame，因为RoundedFrame的delete('all')会删除子组件
        canvas_container = tk.Frame(
            parent,
            bg=PinkConfig.BLACK,
            bd=0,
            highlightthickness=0
        )
        canvas_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建视频画布 - 直接在container上创建
        self.canvas = tk.Canvas(canvas_container, bg=PinkConfig.BLACK, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
    def _load_audio(self):
        """加载音频数据"""
        if not self.audio_enabled or not self.decoder:
            return
        
        try:
            audio_data = self.decoder.get_audio_data()
            if audio_data:
                # 创建临时音频文件
                if self.audio_file and os.path.exists(self.audio_file):
                    try:
                        os.unlink(self.audio_file)
                    except:
                        pass
                
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
                    self.audio_file = temp_audio.name
                    temp_audio.write(audio_data)
                
                # 尝试加载音频到 pygame mixer
                try:
                    pygame.mixer.music.load(self.audio_file)
                    pygame.mixer.music.set_volume(self.audio_volume)
                    print(f"✅ 音频加载成功: {self.audio_file}")
                except Exception as e:
                    print(f"❌ pygame mixer 加载失败: {e}")
                    # 尝试使用 sound 对象代替
                    try:
                        self.audio_sound = pygame.mixer.Sound(self.audio_file)
                        print(f"✅ 音频加载成功 (使用 Sound): {self.audio_file}")
                    except Exception as e2:
                        print(f"❌ Sound 加载也失败: {e2}")
                        self.audio_file = None
            else:
                print("ℹ️  无音频数据")
        except Exception as e:
            print(f"❌ 音频加载失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _play_audio(self):
        """播放音频"""
        if not self.audio_enabled:
            return
        
        try:
            # 优先使用 music
            if self.audio_file:
                if not pygame.mixer.music.get_busy():
                    pygame.mixer.music.play()
            # 如果有 sound 对象，使用 sound
            elif hasattr(self, 'audio_sound') and self.audio_sound:
                self.audio_sound.play(loops=-1)  # 循环播放
        except Exception as e:
            print(f"❌ 音频播放失败: {e}")
    
    def _pause_audio(self):
        """暂停音频"""
        if not self.audio_enabled:
            return
        
        try:
            if self.audio_file:
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.pause()
            elif hasattr(self, 'audio_sound') and self.audio_sound:
                self.audio_sound.stop()
        except Exception as e:
            print(f"❌ 音频暂停失败: {e}")
    
    def _resume_audio(self):
        """恢复音频播放"""
        if not self.audio_enabled:
            return
        
        try:
            if self.audio_file:
                pygame.mixer.music.unpause()
            elif hasattr(self, 'audio_sound') and self.audio_sound:
                self.audio_sound.play(loops=-1)
        except Exception as e:
            print(f"❌ 音频恢复失败: {e}")
    
    def _stop_audio(self):
        """停止音频"""
        if not self.audio_enabled:
            return
        
        try:
            if self.audio_file:
                pygame.mixer.music.stop()
            elif hasattr(self, 'audio_sound') and self.audio_sound:
                self.audio_sound.stop()
        except Exception as e:
            print(f"❌ 音频停止失败: {e}")
    
    def _set_volume(self, volume):
        """设置音量
        Args:
            volume: 音量值 (0.0 到 1.0)
        """
        if not self.audio_enabled:
            return
        
        self.audio_volume = max(0.0, min(1.0, volume))
        
        # 设置 music 音量
        if self.audio_file:
            pygame.mixer.music.set_volume(self.audio_volume)
        # 设置 sound 音量
        elif hasattr(self, 'audio_sound') and self.audio_sound:
            self.audio_sound.set_volume(self.audio_volume)
    
    def _toggle_mute(self):
        """切换静音状态"""
        if not self.audio_enabled:
            return
        
        self.audio_muted = not self.audio_muted
        
        if self.audio_muted:
            if self.audio_file:
                pygame.mixer.music.set_volume(0.0)
            elif hasattr(self, 'audio_sound') and self.audio_sound:
                self.audio_sound.set_volume(0.0)
        else:
            if self.audio_file:
                pygame.mixer.music.set_volume(self.audio_volume)
            elif hasattr(self, 'audio_sound') and self.audio_sound:
                self.audio_sound.set_volume(self.audio_volume)
        
        return self.audio_muted
    
    def create_controls(self, parent):
        """Create control panel"""
        # 创建圆角外框（用于装饰）
        control_frame_container = tk.Frame(parent, bg=PinkConfig.PINK_SOFT)
        control_frame_container.pack(fill=tk.X, padx=10, pady=5)
        
        # 圆角边框
        control_frame = RoundedFrame(
            control_frame_container,
            radius=PinkConfig.RADIUS_SMALL,
            bg_color=PinkConfig.CREAM,
            border_color=PinkConfig.PINK_PRIMARY,
            border_width=PinkConfig.BORDER_NORMAL,
            height=PinkConfig.CONTROL_PANEL_HEIGHT
        )
        control_frame.pack(fill=tk.BOTH, expand=True)
        
        # 内部容器用于放置控件（不会被 delete 清除）
        inner_frame = tk.Frame(control_frame, bg=PinkConfig.CREAM)
        inner_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER, 
                        relwidth=0.95, relheight=0.8)
        
        # Play button
        self.play_btn = RoundButton(inner_frame, "[ Play ]",
                                     command=self.toggle_play, width=100, height=35)
        self.play_btn.grid(row=0, column=0, padx=10, pady=10)
        
        # Stop button
        stop_btn = RoundButton(inner_frame, "[ Stop ]",
                              command=self.stop_video, width=100, height=35)
        stop_btn.grid(row=0, column=1, padx=10, pady=10)
        
        # Progress bar frame
        progress_frame = tk.Frame(inner_frame, bg=PinkConfig.CREAM)
        progress_frame.grid(row=0, column=2, padx=20, pady=10, sticky="ew")
        
        self.progress = ttk.Scale(progress_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                                 command=self.seek_video)
        self.progress.pack(fill=tk.X, expand=True)
        
        # Time display
        self.time_label = tk.Label(inner_frame, text="00:00 / 00:00",
                                   font=PinkConfig.FONT_NORMAL,
                                   bg=PinkConfig.CREAM, fg=PinkConfig.PINK_DARK)
        self.time_label.grid(row=0, column=3, padx=10, pady=10)
        
        # Sound button
        self.sound_btn = RoundButton(inner_frame, "[ 🔊 ]",
                                    command=self.toggle_mute, width=80, height=35)
        self.sound_btn.grid(row=0, column=4, padx=10, pady=10)
        
        # Volume slider
        volume_frame = tk.Frame(inner_frame, bg=PinkConfig.CREAM)
        volume_frame.grid(row=0, column=5, padx=10, pady=10, sticky="ew")
        
        self.volume_scale = ttk.Scale(volume_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                                     command=self.on_volume_change)
        self.volume_scale.set(70)  # Default volume 70%
        self.volume_scale.pack(fill=tk.X, expand=True)
        
        # Store references
        self.control_frame = control_frame
        self.inner_frame = inner_frame
        
        # Configure column weights
        inner_frame.columnconfigure(2, weight=1)
        inner_frame.columnconfigure(5, weight=0)
        
        # Custom progress bar style
        self._style_progress_bar()
        
    def _style_progress_bar(self):
        """Custom progress bar style"""
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TScale',
                       background=PinkConfig.PINK_PRIMARY,
                       troughcolor=PinkConfig.PINK_LIGHT,
                       borderwidth=0,
                       lightcolor=PinkConfig.PINK_PRIMARY,
                       darkcolor=PinkConfig.PINK_PRIMARY)
                       
    def create_info_bar(self, parent):
        """Create info bar"""
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
            text="Welcome to Banana Player!",
            font=PinkConfig.FONT_SMALL,
            bg=PinkConfig.PINK_SOFT,
            fg=PinkConfig.PINK_DARK
        )
        info_frame.create_window(500, 20, window=self.info_label)
        
    def _on_window_resize(self, event=None):
        """窗口大小变化时自适应调整视频显示"""
        # 使用防抖，避免频繁重绘
        if hasattr(self, '_resize_job') and self._resize_job:
            self.root.after_cancel(self._resize_job)
        
        if self.decoder and self.current_frame_idx < self.metadata['frame_count']:
            self._resize_job = self.root.after(100, self._refresh_frame)
    
    def _refresh_frame(self):
        """刷新当前帧（用于窗口大小变化时）"""
        if self.decoder and self.current_frame_idx < self.metadata['frame_count']:
            self.display_frame(self.current_frame_idx, force=True)
        self._resize_job = None
    
    def add_heart_decorations(self):
        """Add heart decorations to background"""
        self.hearts = []
        
    def init_hearts_and_animate(self):
        """Initialize hearts and start animation"""
        self.add_heart_decorations()
        self.animate_hearts()
        
    def animate_hearts(self):
        """Heart pulsing animation"""
        import random
        def pulse():
            for heart in self.hearts:
                # Random color change for pulsing effect
                if random.random() > 0.5:
                    self.bg_canvas.itemconfig(heart, fill=PinkConfig.HEART_RED)
                else:
                    self.bg_canvas.itemconfig(heart, fill=PinkConfig.PINK_PRIMARY)
            self.root.after(500, pulse)
        pulse()
        
    def check_license_status(self):
        """Check license status"""
        valid, message = self.license_manager.check_license()
        self.license_label.config(text=message)
        if not valid:
            messagebox.showwarning("License Expired", "Your trial period has expired. Please activate Gold Member to continue!")
            
    def open_video(self):
        """打开视频文件 (使用流式解码器)"""
        valid, _ = self.license_manager.check_license()
        if not valid:
            messagebox.showerror("License Error", "Your license has expired. Please activate Gold Member!")
            return
        file_path = filedialog.askopenfilename(
            title="Select .ban video",
            filetypes=[("Banana video", f"*{PinkConfig.BAN_EXTENSION}"), ("All files", "*.*")]
        )
        if file_path:
            try:
                self.info_label.config(text="Loading video metadata...")
                self.root.update()
                
                # 停止当前音频
                self._stop_audio()
                
                # 使用流式解码器替代原有方法
                self.decoder = StreamingDecoder(
                    file_path, 
                    buffer_size=60, 
                    buffer_memory_mb=500
                )
                self.metadata = self.decoder.metadata
                
                # 创建帧预加载器
                self.preloader = FramePreloader(self.decoder, preload_window=30)
                
                # 检查是否有有效视频数据
                if not self.metadata or self.metadata['frame_count'] == 0:
                    messagebox.showerror("Error", "No valid video data in file!")
                    self.info_label.config(text="Error: No valid video")
                    return
                
                # 加载音频
                self._load_audio()
                    
                self.current_video = file_path
                self.current_frame_idx = 0
                self.progress.config(to=self.metadata['frame_count']-1)
                
                # 显示视频信息
                audio_info = " | Audio: Yes" if self.metadata.get('has_audio', False) else " | Audio: No"
                info_text = (f"Loaded: {os.path.basename(file_path)} | "
                           f"{self.metadata['width']}x{self.metadata['height']} | "
                           f"{self.metadata['fps']} FPS | {self.metadata['frame_count']} frames"
                           f"{audio_info}")
                self.info_label.config(text=info_text)
                
                # 根据视频分辨率调整窗口大小
                self._adjust_window_to_video_size()
                
                # 显示第一帧
                self.display_frame(0, force=True)
                
                messagebox.showinfo("Success", f"Video loaded successfully!\n\nFile: {os.path.basename(file_path)}\nResolution: {self.metadata['width']}x{self.metadata['height']}\nFPS: {self.metadata['fps']} FPS\nFrames: {self.metadata['frame_count']}\nAudio: {'Yes' if self.metadata.get('has_audio', False) else 'No'}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Cannot open video: {str(e)}")
                self.info_label.config(text="Error loading video")
                
    def convert_video(self):
        """Convert video to .ban format (with encryption)"""
        input_path = filedialog.askopenfilename(
            title="Select video to convert",
            filetypes=PinkConfig.SUPPORTED_INPUT_FORMATS
        )
        if input_path:
            output_path = filedialog.asksaveasfilename(
                title="Save .ban video",
                defaultextension=PinkConfig.BAN_EXTENSION,
                filetypes=[("Banana video", f"*{PinkConfig.BAN_EXTENSION}")]
            )
            if output_path:
                # 创建进度窗口
                progress_window = tk.Toplevel(self.root)
                progress_window.title("Converting...")
                progress_window.geometry("400x150")
                progress_window.configure(bg=PinkConfig.PINK_SOFT)
                progress_window.transient(self.root)
                progress_window.grab_set()
                
                # 进度条
                progress = ttk.Progressbar(progress_window, mode='determinate')
                progress.pack(fill=tk.X, padx=20, pady=20)
                
                # 标签
                label = tk.Label(progress_window, text="Starting conversion...",
                               font=PinkConfig.FONT_NORMAL,
                               bg=PinkConfig.PINK_SOFT, fg=PinkConfig.PINK_DARK)
                label.pack(pady=10)
                
                def update_progress(current, total):
                    """更新进度回调"""
                    if total > 0:
                        percent = (current / total) * 100
                        progress['value'] = percent
                        label.config(text=f"Converting: {current}/{total} frames ({percent:.1f}%)")
                        progress_window.update()
                
                def do_conversion():
                    """在单独线程中执行转换"""
                    try:
                        self.info_label.config(text="Converting video... Please wait")
                        SimpleBANCodec.encode_video(input_path, output_path, progress_callback=update_progress)
                        
                        # 转换完成
                        def on_success():
                            progress_window.destroy()
                            self.info_label.config(text="Conversion complete!")
                            messagebox.showinfo("Success", f"Video converted and encrypted successfully!\nSaved to: {output_path}")
                        self.root.after(0, on_success)
                    except Exception as e:
                        error_msg = str(e)
                        def on_error():
                            progress_window.destroy()
                            self.info_label.config(text="Conversion failed")
                            messagebox.showerror("Error", f"Conversion failed: {error_msg}")
                        self.root.after(0, on_error)
                
                # 在后台线程执行转换
                thread = threading.Thread(target=do_conversion, daemon=True)
                thread.start()
                    
    def _adjust_window_to_video_size(self):
        """根据视频分辨率调整窗口大小以适应播放内容"""
        if not self.metadata:
            return
            
        video_w = self.metadata['width']
        video_h = self.metadata['height']
        self.original_video_size = (video_w, video_h)
        
        # 计算目标窗口尺寸（保留一定边距用于UI控件）
        ui_reserve_w = 100  # 左右边距
        ui_reserve_h = 200  # 上下边距（头部、控制栏等）
        
        target_w = video_w + ui_reserve_w
        target_h = video_h + ui_reserve_h
        
        # 获取屏幕尺寸
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        
        # 如果视频太大，调整为屏幕尺寸的90%
        if target_w > screen_w * 0.9 or target_h > screen_h * 0.9:
            scale = min(screen_w * 0.9 / target_w, screen_h * 0.9 / target_h)
            target_w = int(target_w * scale)
            target_h = int(target_h * scale)
        
        # 最小窗口尺寸
        min_w = 800
        min_h = 600
        target_w = max(target_w, min_w)
        target_h = max(target_h, min_h)
        
        # 调整窗口大小并居中
        self.root.geometry(f"{target_w}x{target_h}")
        
        self.info_label.config(text=f"Window adjusted to: {target_w}x{target_h}")
    
    def _keep_video_proportion(self):
        """播放过程中保持视频比例适配窗口"""
        if not self.original_video_size or not self.decoder:
            return
            
        # 重新计算视频显示尺寸
        if self.current_frame_idx < self.metadata["frame_count"]:
            self.display_frame(self.current_frame_idx, force=True)
    
    def display_frame(self, frame_idx, force=False):
        """Display specified frame (from streaming decoder)"""
        if not self.decoder:
            return

        if frame_idx < 0 or frame_idx >= self.metadata['frame_count']:
            return

        # 从流式解码器获取帧（自动从缓存或磁盘加载）
        frame = self.decoder.get_frame(frame_idx)
        if frame is None:
            print(f"警告: 帧 {frame_idx} 解码失败")
            return

        # 更新预加载器位置
        if self.preloader:
            self.preloader.update_position(frame_idx)

        try:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        except Exception as e:
            print(f"错误: 无法转换帧 {frame_idx} 的颜色空间: {e}")
            return
        
        # 获取当前画布大小
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        
        # 如果画布大小未知，使用默认尺寸
        if canvas_w <= 1:
            canvas_w = 950
        if canvas_h <= 1:
            canvas_h = 420
        
        # 保持宽高比缩放图像
        img = Image.fromarray(frame_rgb)
        
        # 计算缩放尺寸，保持原始宽高比
        orig_w, orig_h = img.size
        target_ratio = canvas_w / canvas_h
        orig_ratio = orig_w / orig_h
        
        if orig_ratio > target_ratio:
            # 图像更宽，以宽度为基准
            new_w = canvas_w
            new_h = int(canvas_w / orig_ratio)
        else:
            # 图像更高，以高度为基准
            new_h = canvas_h
            new_w = int(canvas_h * orig_ratio)
        
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(image=img)
        
        # 保存引用到self，防止被垃圾回收
        if not hasattr(self, 'current_photo') or self.current_photo is None:
            self.current_photo = []
        self.current_photo.append(photo)
        # 限制保存的引用数量，避免内存泄漏
        if len(self.current_photo) > 10:
            self.current_photo = self.current_photo[-10:]
        
        self.canvas.delete("all")
        # 图像居中显示
        self.canvas.create_image(canvas_w//2, canvas_h//2, image=photo, anchor=tk.CENTER)
        # 强制刷新canvas
        self.canvas.update_idletasks()

        # Update progress bar and time (prevent recursion)
        if not self.seeking:
            self.seeking = True
            self.progress.set(frame_idx)
            self.seeking = False

        if self.metadata and self.metadata.get('fps', 0) > 0:
            current_time = frame_idx / self.metadata['fps']
            total_time = self.metadata['frame_count'] / self.metadata['fps']
            self.time_label.config(
                text=f"{self._format_time(current_time)} / {self._format_time(total_time)}"
            )
            
    def _format_time(self, seconds):
        """Format time as MM:SS"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
        
    def toggle_play(self):
        """Play/Pause toggle"""
        if not self.decoder:
            messagebox.showwarning("No Video", "Please open a .ban video first!")
            return

        self.is_playing = not self.is_playing
        if self.is_playing:
            self.play_btn.text = "[ Pause ]"
            self.play_btn.draw_button()
            # 播放音频
            self._play_audio()
            if self.play_thread is None or not self.play_thread.is_alive():
                self.play_thread = threading.Thread(target=self._play_video, daemon=True)
                self.play_thread.start()
        else:
            self.play_btn.text = "[ Play ]"
            self.play_btn.draw_button()
            # 暂停音频
            self._pause_audio()
    
    def toggle_mute(self):
        """切换静音状态"""
        if not self.audio_enabled:
            return
        
        muted = self._toggle_mute()
        if muted:
            self.sound_btn.text = "[ 🔇 ]"
        else:
            self.sound_btn.text = "[ 🔊 ]"
        self.sound_btn.draw_button()
    
    def on_volume_change(self, value):
        """音量滑块回调"""
        volume = float(value) / 100.0
        self._set_volume(volume)
            
    def _play_video(self):
        """Play video thread"""
        if not self.metadata or not self.decoder:
            return
        
        fps = self.metadata['fps']
        frame_delay = 1.0 / fps
        while self.is_playing and self.current_frame_idx < self.metadata["frame_count"]:
            start_time = time.time()
            self.root.after(0, self.display_frame, self.current_frame_idx)
            self.current_frame_idx += 1
            elapsed = time.time() - start_time
            sleep_time = frame_delay - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

        # Playback end handling
        if self.current_frame_idx >= self.metadata["frame_count"]:
            self.current_frame_idx = 0
            self.is_playing = False
            # 停止音频
            self._stop_audio()
            # Thread-safe UI update
            def update_button():
                self.play_btn.text = "[ Play ]"
                self.play_btn.draw_button()
            self.root.after(0, update_button)
            
    def stop_video(self):
        """Stop playback"""
        self.is_playing = False
        self.current_frame_idx = 0
        self.play_btn.text = "[ Play ]"
        self.play_btn.draw_button()
        # 停止音频
        self._stop_audio()
        if self.decoder:
            self.display_frame(0)
            
    def seek_video(self, value):
        """Seek to specified position"""
        if self.decoder and not self.seeking:
            self.seeking = True
            self.current_frame_idx = int(float(value))
            self.display_frame(self.current_frame_idx)
            
            # 同步音频跳转（重新加载音频并跳转到指定位置）
            if self.audio_enabled and self.metadata.get('has_audio', False):
                try:
                    # 计算音频跳转位置（秒）
                    audio_position = self.current_frame_idx / self.metadata['fps']
                    
                    # 停止当前音频
                    if self.audio_file:
                        pygame.mixer.music.stop()
                    elif hasattr(self, 'audio_sound') and self.audio_sound:
                        self.audio_sound.stop()
                    
                    # 重新加载音频
                    if self.audio_file:
                        pygame.mixer.music.load(self.audio_file)
                        pygame.mixer.music.set_volume(0.0 if self.audio_muted else self.audio_volume)
                        # 跳转到指定位置（pygame mixer 不支持精确跳转，只能重新播放）
                        if self.is_playing:
                            pygame.mixer.music.play(start=audio_position)
                    elif hasattr(self, 'audio_sound') and self.audio_sound:
                        # Sound 对象不支持跳转，只能重新播放
                        if self.is_playing:
                            self.audio_sound.play(loops=-1)
                except Exception as e:
                    print(f"音频跳转失败: {e}")
            
            self.seeking = False
            
    def activate_golden(self):
        """Gold member activation dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Activate Gold Member")
        dialog.geometry("450x250")
        dialog.configure(bg=PinkConfig.PINK_SOFT)
        # Center and make dialog modal
        dialog.transient(self.root)
        dialog.grab_set()
        tk.Label(
            dialog,
            text="Enter Gold Member activation code",
            font=PinkConfig.FONT_HEADING,
            bg=PinkConfig.PINK_SOFT,
            fg=PinkConfig.PINK_DARK
        ).pack(pady=20)
        # Entry container
        entry_frame = tk.Frame(dialog, bg=PinkConfig.WHITE, bd=0)
        entry_frame.pack(pady=10, padx=40, fill=tk.X)
        key_entry = tk.Entry(
            entry_frame,
            font=PinkConfig.FONT_NORMAL,
            justify='center',
            bg=PinkConfig.WHITE,
            fg=PinkConfig.PINK_DARK,
            relief=tk.FLAT,
            bd=2
        )
        key_entry.pack(ipady=8, padx=5, pady=5)
        # Hint
        hint = self.license_manager.get_golden_key_hint()
        tk.Label(
            dialog,
            text=f"Hint key: {hint}",
            font=PinkConfig.FONT_SMALL,
            bg=PinkConfig.PINK_SOFT,
            fg=PinkConfig.PURPLE_SOFT
        ).pack(pady=10)
        
        def activate():
            key = key_entry.get().strip()
            if self.license_manager.activate_golden_membership(key):
                messagebox.showinfo("Success", "Gold Member activated successfully!")
                self.check_license_status()
                dialog.destroy()
            else:
                messagebox.showerror("Error", "Invalid activation code")
                
        # Activate button
        activate_btn = RoundButton(dialog, "Activate Now", command=activate,
                                  width=150, height=40)
        activate_btn.pack(pady=20)

    def show_video_info(self):
        """Show current video info"""
        if not self.metadata or not self.decoder:
            messagebox.showinfo("Info", "Please open a .ban video first!")
            return

        info_text = f"""
Video Info

Filename: {os.path.basename(self.current_video) if self.current_video else 'Unknown'}

Resolution: {self.metadata['width']} x {self.metadata['height']}
FPS: {self.metadata['fps']} FPS
Total frames: {self.metadata["frame_count"]}
Duration: {self.metadata["frame_count"] / self.metadata['fps']:.2f} seconds

Current frame: {self.current_frame_idx + 1} / {self.metadata["frame_count"]}
        """
        messagebox.showinfo("Video Info", info_text.strip())

    def show_license_info(self):
        """Show license info"""
        info = self.license_manager.get_license_info()
        license_type = "Gold Member" if info['type'] == 'golden' else "Trial Version"

        if info['type'] == 'golden':
            detail_text = f"""
License Type: {license_type}
Status: Activated
Activation Date: {info['data'].get('activation_date', 'Unknown')[:10]}

You have permanent access to all features!
            """
        else:
            start_date = info['data'].get('start_date', '')[:10]
            expiry_date = info['data'].get('expiry_date', '')[:10]
            detail_text = f"""
License Type: {license_type}
Status: {'Valid' if info['valid'] else 'Expired'}
Start Date: {start_date}
Expiry Date: {expiry_date}

{info['message']}
            """

        messagebox.showinfo("License Info", detail_text.strip())

    def show_about(self):
        """Show about dialog"""
        about_text = f"""
Banana Player
Pink-themed video player

Version: {PinkConfig.APP_VERSION}
Author: {PinkConfig.APP_AUTHOR}

Features:
- Support for custom .ban video format
- Pink-themed UI design
- Smooth video playback experience
- Easy-to-use format conversion

Thanks for using Banana Player!
        """
        messagebox.showinfo("About Banana Player", about_text.strip())

    def show_help(self):
        """Show usage guide"""
        help_text = """
Banana Player Usage Guide

1. Convert Video
   File -> Convert video to .ban
   Supported formats: MP4, AVI, MOV, MKV, FLV, WMV

2. Open Video
   File -> Open .ban video
   Or click "Open Video" button on toolbar

3. Playback Controls
   - Play/Pause: Click play button or press Space
   - Stop: Click stop button or press Ctrl+S
   - Drag progress bar to seek

4. Shortcuts
   - Ctrl+O: Open video
   - Ctrl+T: Convert video
   - Ctrl+S: Stop playback
   - Space: Play/Pause
   - Ctrl+Q: Exit program

5. Activate Gold Member
   Tools -> Activate Gold Member
   Enter activation code for permanent access

Tip: 30-day trial available for new users
        """
        messagebox.showinfo("Usage Guide", help_text.strip())
