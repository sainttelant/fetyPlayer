"""
🎀 UI组件库
包含圆角框架、圆形按钮、爱心装饰等
"""
import tkinter as tk
import numpy as np
from .config import PinkConfig

class RoundedFrame(tk.Canvas):
   """圆角边框框架组件"""
   def __init__(self, parent, radius=25, bg_color=PinkConfig.PINK_LIGHT,
                border_color=PinkConfig.PINK_PRIMARY, border_width=3, **kwargs):
       """初始化圆角框架
       Args:
           parent: 父组件
           radius: 圆角半径
           bg_color: 背景颜色
           border_color: 边框颜色
           border_width: 边框宽度
       """
       tk.Canvas.__init__(self, parent, highlightthickness=0, **kwargs)
       # 获取父组件背景色，如果为空则使用透明色
       parent_bg = parent['bg'] if parent['bg'] else 'systemTransparent'
       try:
           self.config(bg=parent_bg)
       except:
           # 如果设置失败，使用默认背景色
           self.config(bg=PinkConfig.PINK_SOFT)
       self.radius = radius
       self.bg_color = bg_color
       self.border_color = border_color
       self.border_width = border_width
       self.bind('<Configure>', self._draw_rounded_rect)
   def _draw_rounded_rect(self, event=None):
       """绘制圆角矩形"""
       self.delete('all')
       w = self.winfo_width()
       h = self.winfo_height()
       if w < 2 * self.radius or h < 2 * self.radius:
           return
       # 绘制背景
       # 四个圆角
       self.create_arc(0, 0, 2*self.radius, 2*self.radius,
                      start=90, extent=90, fill=self.bg_color, outline='')
       self.create_arc(w-2*self.radius, 0, w, 2*self.radius,
                      start=0, extent=90, fill=self.bg_color, outline='')
       self.create_arc(0, h-2*self.radius, 2*self.radius, h,
                      start=180, extent=90, fill=self.bg_color, outline='')
       self.create_arc(w-2*self.radius, h-2*self.radius, w, h,
                      start=270, extent=90, fill=self.bg_color, outline='')
       # 中间矩形
       self.create_rectangle(self.radius, 0, w-self.radius, h,
                           fill=self.bg_color, outline='')
       self.create_rectangle(0, self.radius, w, h-self.radius,
                           fill=self.bg_color, outline='')
       # 绘制边框
       if self.border_width > 0:
           # 四个圆角边框
           self.create_arc(0, 0, 2*self.radius, 2*self.radius,
                          start=90, extent=90, outline=self.border_color,
                          width=self.border_width, style='arc')
           self.create_arc(w-2*self.radius, 0, w, 2*self.radius,
                          start=0, extent=90, outline=self.border_color,
                          width=self.border_width, style='arc')
           self.create_arc(0, h-2*self.radius, 2*self.radius, h,
                          start=180, extent=90, outline=self.border_color,
                          width=self.border_width, style='arc')
           self.create_arc(w-2*self.radius, h-2*self.radius, w, h,
                          start=270, extent=90, outline=self.border_color,
                          width=self.border_width, style='arc')
           # 四条直线边框
           self.create_line(self.radius, 0, w-self.radius, 0,
                          fill=self.border_color, width=self.border_width)
           self.create_line(self.radius, h, w-self.radius, h,
                          fill=self.border_color, width=self.border_width)
           self.create_line(0, self.radius, 0, h-self.radius,
                          fill=self.border_color, width=self.border_width)
           self.create_line(w, self.radius, w, h-self.radius,
                          fill=self.border_color, width=self.border_width)

class RoundButton(tk.Canvas):
   """圆形渐变按钮组件"""
   def __init__(self, parent, text, command=None, width=120, height=40, **kwargs):
       """初始化圆形按钮
       Args:
           parent: 父组件
           text: 按钮文字
           command: 点击回调函数
           width: 按钮宽度
           height: 按钮高度
       """
       tk.Canvas.__init__(self, parent, width=width, height=height,
                         highlightthickness=0)
       # 获取父组件背景色
       parent_bg = parent.cget('bg') if hasattr(parent, 'cget') else PinkConfig.PINK_SOFT
       try:
           self.config(bg=parent_bg)
       except:
           self.config(bg=PinkConfig.PINK_SOFT)
       self.text = text
       self.command = command
       self.width = width
       self.height = height
       self.draw_button()
       self.bind('<Button-1>', self._on_click)
       self.bind('<Enter>', self._on_enter)
       self.bind('<Leave>', self._on_leave)
   def draw_button(self, hover=False):
       """绘制按钮"""
       self.delete('all')
       # 选择颜色
       color = PinkConfig.PINK_DARK if hover else PinkConfig.PINK_PRIMARY
       # 绘制圆角矩形
       radius = self.height // 2
       self.create_oval(0, 0, self.height, self.height, fill=color, outline='')
       self.create_oval(self.width-self.height, 0, self.width, self.height,
                       fill=color, outline='')
       self.create_rectangle(radius, 0, self.width-radius, self.height,
                           fill=color, outline='')
       # 绘制文字
       self.create_text(self.width//2, self.height//2, text=self.text,
                       fill=PinkConfig.WHITE, font=PinkConfig.FONT_BUTTON)
   def _on_click(self, event):
       """点击事件"""
       if self.command:
           self.command()
   def _on_enter(self, event):
       """鼠标进入事件"""
       self.draw_button(hover=True)
       self.config(cursor='hand2')
   def _on_leave(self, event):
       """鼠标离开事件"""
       self.draw_button(hover=False)
       self.config(cursor='')

def create_heart_decoration(canvas, x, y, size=20, color=PinkConfig.HEART_RED):
   """创建爱心装饰
   Args:
       canvas: Canvas对象
       x: X坐标
       y: Y坐标
       size: 爱心大小
       color: 爱心颜色
   Returns:
       爱心对象ID
   """
   # 使用多边形近似爱心形状
   points = []
   for i in range(100):
       t = i / 100 * 2 * np.pi
       px = size * 16 * (np.sin(t)**3)
       py = -size * (13*np.cos(t) - 5*np.cos(2*t) - 2*np.cos(3*t) - np.cos(4*t))
       points.extend([x + px, y + py])
   return canvas.create_polygon(points, fill=color, outline='', smooth=True)