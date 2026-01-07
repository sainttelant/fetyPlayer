"""
🎀 Banana Player - 粉红少女版
程序入口文件
"""
import tkinter as tk
from src.player import BananaPlayerPink
def main():
   """主函数"""
   root = tk.Tk()
   # 尝试设置窗口图标
   try:
       root.iconbitmap('icon.ico')
   except:
       pass
   # 创建播放器实例
   app = BananaPlayerPink(root)
   # 启动主循环
   root.mainloop()

if __name__ == "__main__":
   main()