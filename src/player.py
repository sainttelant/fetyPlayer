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
from .config import PinkConfig
from .license_manager import LicenseManager
from .codec import BANCodec
from .ui_components import RoundedFrame, RoundButton, create_heart_decoration

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
        # Set gradient background
        self.setup_gradient_background()
        # Create menu bar
        self.create_menu_bar()
        # Initialize license manager
        self.license_manager = LicenseManager()
        # Video state variables
        self.current_video = None
        self.frames = []
        self.metadata = None
        self.current_frame_idx = 0
        self.is_playing = False
        self.play_thread = None
        self.seeking = False  # Prevent progress bar recursive update
        # Create UI
        self.setup_ui()
        # Check license status
        self.check_license_status()
        # Start heart animation
        self.animate_hearts()
        
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
        
    def create_controls(self, parent):
        """Create control panel"""
        control_frame = RoundedFrame(
            parent,
            radius=PinkConfig.RADIUS_SMALL,
            bg_color=PinkConfig.CREAM,
            border_color=PinkConfig.PINK_PRIMARY,
            border_width=PinkConfig.BORDER_NORMAL,
            height=PinkConfig.CONTROL_PANEL_HEIGHT
        )
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        # Play button
        self.play_btn = RoundButton(control_frame, "[ Play ]",
                                    command=self.toggle_play, width=100, height=35)
        control_frame.create_window(100, 40, window=self.play_btn)
        # Stop button
        stop_btn = RoundButton(control_frame, "[ Stop ]",
                              command=self.stop_video, width=100, height=35)
        control_frame.create_window(220, 40, window=stop_btn)
        # Progress bar
        self.progress = ttk.Scale(control_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                                 command=self.seek_video)
        control_frame.create_window(600, 40, window=self.progress, width=600, height=30)
        # Time display - use FONT_NORMAL for Chinese support
        self.time_label = tk.Label(control_frame, text="00:00 / 00:00",
                                   font=PinkConfig.FONT_NORMAL,
                                   bg=PinkConfig.CREAM, fg=PinkConfig.PINK_DARK)
        control_frame.create_window(900, 40, window=self.time_label)
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
        
    def add_heart_decorations(self):
        """Add heart decorations"""
        self.hearts = []
        for x, y in PinkConfig.HEART_POSITIONS:
            heart = create_heart_decoration(self.bg_canvas, x, y, size=PinkConfig.HEART_SIZE)
            self.hearts.append(heart)
            
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
        """打开视频文件"""
        valid, _ = self.license_manager.check_license()
        if not valid:
            messagebox.showerror("License Error", "Your license has expired. Please activate Gold Member!")
            return
        file_path = filedialog.askopenfilename(
            title="Select .ban video",
            filetypes=[("Banana video", f"*{PinkConfig.BAN_EXTENSION}"), ("All files", "*.*")]
        )
        if file_path:
            print(f"[DEBUG] 用户选择的文件: {file_path}")
            try:
                self.info_label.config(text="Loading video... Please wait...")
                self.root.update()
                print(f"[DEBUG] 开始解码视频文件...")
                self.metadata, self.frames = BANCodec.decode_video(file_path)
                print(f"[DEBUG] ✅ 视频解码完成!")
                print(f"[DEBUG] 元数据: {self.metadata}")
                print(f"[DEBUG] 帧数量: {len(self.frames)}")
                
                # 检查是否有有效帧数据
                if not self.frames:
                    messagebox.showerror("Error", "视频文件解析成功，但没有有效的帧数据！\n可能是文件损坏或格式不兼容。")
                    self.info_label.config(text="Error: No valid frames")
                    return
                    
                self.current_video = file_path
                self.current_frame_idx = 0
                self.progress.config(to=len(self.frames)-1)
                
                # 显示视频信息
                info_text = (f"✅ Loaded: {os.path.basename(file_path)} | "
                           f"{self.metadata['width']}x{self.metadata['height']} | "
                           f"{self.metadata['fps']} FPS | "
                           f"{len(self.frames)} frames")
                self.info_label.config(text=info_text)
                print(f"[DEBUG] 视频信息: {info_text}")
                
                # 显示第一帧
                self.display_frame(0)
                print(f"[DEBUG] ✅ 第一帧已显示!")
                
                # 弹出成功提示框
                messagebox.showinfo("Success", f"视频加载成功！\n\n文件: {os.path.basename(file_path)}\n分辨率: {self.metadata['width']}x{self.metadata['height']}\n帧率: {self.metadata['fps']} FPS\n帧数: {len(self.frames)}")
                
            except Exception as e:
                print(f"[DEBUG] ❌ 加载视频出错: {e}")
                import traceback
                traceback.print_exc()
                messagebox.showerror("Error", f"Cannot open video: {str(e)}")
                self.info_label.config(text="Error loading video")
                
    def convert_video(self):
        """Convert video to .ban format"""
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
                try:
                    self.info_label.config(text="Converting video... Please wait")
                    self.root.update()
                    BANCodec.encode_video(input_path, output_path)
                    self.info_label.config(text="Conversion complete!")
                    messagebox.showinfo("Success", f"Video converted successfully!\nSaved to: {output_path}")
                except Exception as e:
                    messagebox.showerror("Error", f"Conversion failed: {str(e)}")
                    
    def display_frame(self, frame_idx):
        """Display specified frame"""
        if not self.frames or frame_idx >= len(self.frames) or frame_idx < 0:
            return

        frame = self.frames[frame_idx]
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Resize to fit canvas
        img = Image.fromarray(frame_rgb)
        img = img.resize((950, 420), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(image=img)
        
        # 保存引用到self，防止被垃圾回收
        if not hasattr(self, 'current_photo') or self.current_photo is None:
            self.current_photo = []
        self.current_photo.append(photo)
        
        self.canvas.delete("all")
        # 视频画布现在占满整个容器，图像居中显示
        canvas_w = self.canvas.winfo_width() or 950
        canvas_h = self.canvas.winfo_height() or 420
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
            total_time = len(self.frames) / self.metadata['fps']
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
        if not self.frames:
            messagebox.showwarning("No Video", "Please open a .ban video first!")
            return

        self.is_playing = not self.is_playing
        if self.is_playing:
            self.play_btn.text = "[ Pause ]"
            self.play_btn.draw_button()
            if self.play_thread is None or not self.play_thread.is_alive():
                self.play_thread = threading.Thread(target=self._play_video, daemon=True)
                self.play_thread.start()
        else:
            self.play_btn.text = "[ Play ]"
            self.play_btn.draw_button()
            
    def _play_video(self):
        """Play video thread"""
        if not self.metadata or not self.frames:
            return
        
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

        # Playback end handling
        if self.current_frame_idx >= len(self.frames):
            self.current_frame_idx = 0
            self.is_playing = False
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
        if self.frames:
            self.display_frame(0)
            
    def seek_video(self, value):
        """Seek to specified position"""
        if self.frames and not self.seeking:
            self.seeking = True
            self.current_frame_idx = int(float(value))
            self.display_frame(self.current_frame_idx)
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
        if not self.metadata or not self.frames:
            messagebox.showinfo("Info", "Please open a .ban video first!")
            return

        info_text = f"""
Video Info

Filename: {os.path.basename(self.current_video) if self.current_video else 'Unknown'}

Resolution: {self.metadata['width']} x {self.metadata['height']}
FPS: {self.metadata['fps']} FPS
Total frames: {len(self.frames)}
Duration: {len(self.frames) / self.metadata['fps']:.2f} seconds

Current frame: {self.current_frame_idx + 1} / {len(self.frames)}
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
