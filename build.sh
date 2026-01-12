#!/bin/bash
# Banana Player 打包脚本 - 生成 Windows 可执行文件

echo "🔨 Banana Player - PyInstaller 打包"
echo "================================"

# 检查依赖
echo "1. 检查依赖包..."
python3 -c "import pyinstaller; print('✅ PyInstaller 已安装')"
if [ $? -ne 0 ]; then
    echo "❌ PyInstaller 未安装"
    echo ""
    echo "安装 PyInstaller:"
    echo "   pip install pyinstaller"
    echo ""
    exit 1
fi

# 清理旧的构建文件
echo "2. 清理旧的构建文件..."
if [ -d "build" ]; then
    rm -rf build
    echo "✅ 旧构建文件已清理"
else
    echo "✅ 无旧构建文件"
fi

echo ""

# 运行 PyInstaller
echo "3. 开始打包..."
pyinstaller --clean BananaPlayer.spec

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 打包成功！"
    echo ""
    echo "📁 可执行文件:"
    echo "   dist/BananaPlayer.exe"
    echo ""
    echo "📋 文件大小:"
    ls -lh dist/BananaPlayer.exe | awk '{print $9}'
    echo ""
    echo "🎯 玩在可以运行 dist/BananaPlayer.exe"
else
    echo ""
    echo "❌ 打包失败"
    exit 1
fi