"""
Main video player GUI application
"""
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2
from PIL import Image, ImageTk
import os
import threading
import time
from .config import Config
from .codec import BANCodec
from .license_manager import LicenseManager

class BananaPlayer:
   """Main video player application"""
   def __init__(self, root):
       self.root = root
       self.root.title(Config.APP_NAME)
       self.root.geometry(f"{Config.WINDOW_WIDTH}x{Config.WINDOW_HEIGHT}")
       self.root.configure(bg=Config.WINDOW_BG_COLOR)
       # License manager
       self.license_manager = LicenseManager()
       # Video state
       self.current_video = None
       self.frames = []
       self.metadata = None
       self.current_frame_idx = 0
       self.is_playing = False
       self.play_thread = None
       self.setup_ui()
       self.check_license_status()
   def setup_ui(self):
       """Setup user interface"""
       self._create_menu()
       self._create_license_bar()
       self._create_video_canvas()
       self._create_controls()
       self._create_info_bar()
   def _create_menu(self):
       """Create menu bar"""
       menubar = tk.Menu(self.root)
       self.root.config(menu=menubar)
       # File menu
       file_menu = tk.Menu(menubar, tearoff=0)
       menubar.add_cascade(label="File", menu=file_menu)
       file_menu.add_command(label="Open .ban Video", command=self.open_video)
       file_menu.add_command(label="Convert Video to .ban", command=self.convert_video)
       file_menu.add_separator()
       file_menu.add_command(label="Exit", command=self.root.quit)
       # License menu
       license_menu = tk.Menu(menubar, tearoff=0)
       menubar.add_cascade(label="License", menu=license_menu)
       license_menu.add_command(label="Activate Golden Membership", command=self.activate_golden)
       license_menu.add_command(label="License Status", command=self.show_license_status)
       # Help menu
       help_menu = tk.Menu(menubar, tearoff=0)
       menubar.add_cascade(label="Help", menu=help_menu)
       help_menu.add_command(label="About", command=self.show_about)
   def _create_license_bar(self):
       """Create license status bar"""
       top_frame = tk.Frame(self.root, bg=Config.WINDOW_BG_COLOR)
       top_frame.pack(fill=tk.X, padx=10, pady=5)
       self.license_label = tk.Label(
           top_frame,
           text="",
           bg=Config.WINDOW_BG_COLOR,
           fg=Config.COLOR_WARNING,
           font=('Arial', 10)
       )
       self.license_label.pack(side=tk.LEFT)
   def _create_video_canvas(self):
       """Create video display canvas"""
       self.video_frame = tk.Frame(
           self.root,
           bg=Config.CANVAS_BG_COLOR,
           width=Config.CANVAS_WIDTH,
           height=Config.CANVAS_HEIGHT
       )
       self.video_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
       self.canvas = tk.Canvas(
           self.video_frame,
           bg=Config.CANVAS_BG_COLOR,
           highlightthickness=0
       )
       self.canvas.pack(fill=tk.BOTH, expand=True)
   def _create_controls(self):
       """Create control panel"""
       control_frame = tk.Frame(self.root, bg=Config.CONTROL_BG_COLOR)
       control_frame.pack(fill=tk.X, padx=10, pady=5)
       # Play/Pause button
       self.play_button = tk.Button(
           control_frame,
           text="▶ Play",
           command=self.toggle_play,
           bg=Config.BUTTON_BG_COLOR,
           fg=Config.BUTTON_FG_COLOR,
           font=('Arial', 12),
           width=10
       )
       self.play_button.pack(side=tk.LEFT, padx=5)
       # Stop button
       self.stop_button = tk.Button(
           control_frame,
           text="■ Stop",
           command=self.stop_video,
           bg=Config.BUTTON_BG_COLOR,
           fg=Config.BUTTON_FG_COLOR,
           font=('Arial', 12),
           width=10
       )
       self.stop_button.pack(side=tk.LEFT, padx=5)
       # Progress bar
       self.progress = ttk.Scale(
           control_frame,
           from_=0,
           to=100,
           orient=tk.HORIZONTAL,
           command=self.seek_video
       )
       self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
       # Time label
       self.time_label = tk.Label(
           control_frame,
           text="00:00 / 00:00",
           bg=Config.CONTROL_BG_COLOR,
           fg=Config.BUTTON_FG_COLOR,
           font=('Arial', 10)
       )
       self.time_label.pack(side=tk.RIGHT, padx=5)
   def _create_info_bar(self):
       """Create info bar"""
       self.info_label = tk.Label(
           self.root,
           text="No video loaded",
           bg=Config.WINDOW_BG_COLOR,
           fg=Config.COLOR_INFO,
           font=('Arial', 9)
       )
       self.info_label.pack(pady=5)
       
   def check_license_status(self):
        """Check and display license status"""
        valid, message = self.license_manager.check_license()
        if valid:
            self.license_label.config(text=f"✓ {message}", fg=Config.COLOR_SUCCESS)
        else:
            self.license_label.config(text=f"✗ {message}", fg=Config.COLOR_ERROR)
            messagebox.showwarning(
               "License Expired",
               "Your trial has expired. Please activate Golden Membership to continue using Banana Player."
           )
            
   def open_video(self):
       """Open .ban video file"""
       valid, _ = self.license_manager.check_license()
       if not valid:
           messagebox.showerror(
               "License Error",
               "Your license has expired. Please activate Golden Membership."
           )
           return
       file_path = filedialog.askopenfilename(
           title="Select .ban video",
           filetypes=[("Banana Videos", f"*{Config.BAN_EXTENSION}"), ("All Files", "*.*")]
       )
       if file_path:
           try:
               self.info_label.config(text="Loading video...")
               self.root.update()
               self.metadata, self.frames = BANCodec.decode_video(file_path)
               self.current_video = file_path
               self.current_frame_idx = 0
               self.progress.config(to=len(self.frames)-1)
               info_text = (
                   f"Loaded: {os.path.basename(file_path)} | "
                   f"{self.metadata['width']}x{self.metadata['height']} | "
                   f"{self.metadata['fps']} FPS | "
                   f"{len(self.frames)} frames"
               )
               self.info_label.config(text=info_text)
               self.display_frame(0)
           except Exception as e:
               messagebox.showerror("Error", f"Could not open video: {str(e)}")
   def convert_video(self):
       """Convert standard video to .ban format"""
       input_path = filedialog.askopenfilename(
           title="Select video to convert",
           filetypes=Config.SUPPORTED_INPUT_FORMATS
       )
       if input_path:
           output_path = filedialog.asksaveasfilename(
               title="Save .ban video",
               defaultextension=Config.BAN_EXTENSION,
               filetypes=[("Banana Videos", f"*{Config.BAN_EXTENSION}")]
           )
           if output_path:
               try:
                   self.info_label.config(text="Converting video... Please wait.")
                   self.root.update()
                   BANCodec.encode_video(input_path, output_path)
                   self.info_label.config(text="Conversion complete!")
                   messagebox.showinfo(
                       "Success",
                       f"Video converted successfully to:\n{output_path}"
                   )
               except Exception as e:
                   messagebox.showerror("Error", f"Conversion failed: {str(e)}")
   def display_frame(self, frame_idx):
       """Display specific frame"""
       if not self.frames or frame_idx >= len(self.frames):
           return
       frame = self.frames[frame_idx]
       frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
       # Resize to fit canvas
       canvas_width = self.canvas.winfo_width()
       canvas_height = self.canvas.winfo_height()
       if canvas_width > 1 and canvas_height > 1:
           frame_height, frame_width = frame_rgb.shape[:2]
           aspect_ratio = frame_width / frame_height
           if canvas_width / canvas_height > aspect_ratio:
               new_height = canvas_height
               new_width = int(canvas_height * aspect_ratio)
           else:
               new_width = canvas_width
               new_height = int(canvas_width / aspect_ratio)
           frame_resized = cv2.resize(frame_rgb, (new_width, new_height))
           # Convert to PhotoImage
           img = Image.fromarray(frame_resized)
           photo = ImageTk.PhotoImage(image=img)
           # Display on canvas
           self.canvas.delete("all")
           self.canvas.create_image(
               canvas_width//2,
               canvas_height//2,
               image=photo,
               anchor=tk.CENTER
           )
           self.canvas.image = photo
           # Update progress and time
           self.progress.set(frame_idx)
           current_time = frame_idx / self.metadata['fps']
           total_time = len(self.frames) / self.metadata['fps']
           self.time_label.config(
               text=f"{self._format_time(current_time)} / {self._format_time(total_time)}"
           )
   def _format_time(self, seconds):
       """Format seconds to MM:SS"""
       minutes = int(seconds // 60)
       secs = int(seconds % 60)
       return f"{minutes:02d}:{secs:02d}"
   def toggle_play(self):
       """Toggle play/pause"""
       if not self.frames:
           messagebox.showwarning("No Video", "Please open a .ban video first.")
           return
       self.is_playing = not self.is_playing
       if self.is_playing:
           self.play_button.config(text="⏸ Pause")
           if self.play_thread is None or not self.play_thread.is_alive():
               self.play_thread = threading.Thread(target=self._play_video)
               self.play_thread.daemon = True
               self.play_thread.start()
       else:
           self.play_button.config(text="▶ Play")
   def _play_video(self):
       """Play video in separate thread"""
       fps = self.metadata['fps']
       frame_delay = 1.0 / fps
       while self.is_playing and self.current_frame_idx < len(self.frames):
           start_time = time.time()
           self.root.after(0, self.display_frame, self.current_frame_idx)
           self.current_frame_idx += 1
           # Maintain frame rate
           elapsed = time.time() - start_time
           sleep_time = frame_delay - elapsed
           if sleep_time > 0:
               time.sleep(sleep_time)
       if self.current_frame_idx >= len(self.frames):
           self.current_frame_idx = 0
           self.is_playing = False
           self.root.after(0, lambda: self.play_button.config(text="▶ Play"))
   def stop_video(self):
       """Stop video playback"""
       self.is_playing = False
       self.current_frame_idx = 0
       self.play_button.config(text="▶ Play")
       if self.frames:
           self.display_frame(0)
   def seek_video(self, value):
       """Seek to specific frame"""
       if self.frames:
           self.current_frame_idx = int(float(value))
           self.display_frame(self.current_frame_idx)
   def activate_golden(self):
       """Show golden membership activation dialog"""
       dialog = tk.Toplevel(self.root)
       dialog.title("Activate Golden Membership")
       dialog.geometry("400x200")
       dialog.configure(bg=Config.WINDOW_BG_COLOR)
       tk.Label(
           dialog,
           text="Enter Golden Membership Key:",
           bg=Config.WINDOW_BG_COLOR,
           fg='white',
           font=('Arial', 12)
       ).pack(pady=20)
       key_entry = tk.Entry(dialog, font=('Arial', 12), width=30)
       key_entry.pack(pady=10)
       hint = self.license_manager.get_golden_key_hint()
       tk.Label(
           dialog,
           text=f"Hint for demo: {hint}",
           bg=Config.WINDOW_BG_COLOR,
           fg='#888888',
           font=('Arial', 8)
       ).pack(pady=5)
       def activate():
           key = key_entry.get().strip()
           if self.license_manager.activate_golden_membership(key):
               messagebox.showinfo("Success", "Golden Membership activated successfully!")
               self.check_license_status()
               dialog.destroy()
           else:
               messagebox.showerror("Error", "Invalid activation key.")
       tk.Button(
           dialog,
           text="Activate",
           command=activate,
           bg=Config.BUTTON_BG_COLOR,
           fg='white',
           font=('Arial', 12),
           width=15
       ).pack(pady=10)
   def show_license_status(self):
       """Show detailed license information"""
       info = self.license_manager.get_license_info()
       license_type = info['type']
       message = info['message']
       data = info['data']
       info_text = f"License Type: {license_type.upper()}\nStatus: {message}\n\n"
       if license_type == 'trial':
           start = data.get('start_date', '')
           expiry = data.get('expiry_date', '')
           info_text += f"Trial Started: {start[:10]}\nExpires: {expiry[:10]}"
       elif license_type == 'golden':
           activated = data.get('activation_date', '')
           info_text += f"Activated: {activated[:10]}\nLifetime Access"
       messagebox.showinfo("License Status", info_text)
   def show_about(self):
       """Show about dialog"""
       about_text = f"""{Config.APP_NAME} v{Config.APP_VERSION}
        Custom video player for .ban format
        Features:
        • Custom .ban video format
        • Golden Membership system
        • {Config.TRIAL_DAYS}-day free trial
        • Video conversion tool
        © 2024 {Config.APP_AUTHOR}"""
       messagebox.showinfo(f"About {Config.APP_NAME}", about_text)