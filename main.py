"""
Banana Player - Main Entry Point
Run this file to start the application
"""
import tkinter as tk
from src.player import BananaPlayer
def main():
   """Main entry point for Banana Player"""
   root = tk.Tk()
   app = BananaPlayer(root)
   root.mainloop()
if __name__ == "__main__":
   main()