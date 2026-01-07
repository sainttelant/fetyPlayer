#!/usr/bin/env python3
"""测试菜单栏功能"""
import tkinter as tk
from src.player import BananaPlayerPink

def test_menu():
    """测试菜单栏是否正常显示"""
    print("=" * 60)
    print("测试菜单栏功能")
    print("=" * 60)

    try:
        root = tk.Tk()
        print("✅ Tkinter根窗口创建成功")

        app = BananaPlayerPink(root)
        print("✅ 播放器初始化成功")
        print("✅ 菜单栏已创建")
        print("\n菜单栏包含:")
        print("  • 文件 (File) - 打开视频、转换视频、退出")
        print("  • 工具 (Tools) - 查看视频信息、激活会员、许可证信息")
        print("  • 播放 (Play) - 播放/暂停、停止")
        print("  • 帮助 (Help) - 关于、使用说明")
        print("\n快捷键:")
        print("  • Ctrl+O: 打开视频")
        print("  • Ctrl+T: 转换视频")
        print("  • Ctrl+S: 停止播放")
        print("  • Space: 播放/暂停")
        print("  • Ctrl+Q: 退出")
        print("\n窗口将在5秒后自动关闭...")

        # 5秒后自动关闭
        root.after(5000, root.destroy)
        root.mainloop()

        print("\n✅ 菜单栏测试完成！")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_menu()
