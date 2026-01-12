#!/bin/bash
# Flask 启动脚本 - fetyPlayer 虚拟环境
echo "🚀 启动 Flask 服务器..."
echo "===================="
echo ""

# 激活 conda 环境
source ~/anaconda3/etc/profile.d/conda.sh
conda activate fetyPlayer

if [ $? -ne 0 ]; then
    echo "❌ 无法激活 fetyPlayer conda 环境"
    exit 1
fi

echo "✅ 已激活 fetyPlayer 环境"
echo ""

# 检查 Flask 是否安装
python3 -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Flask 未安装，正在安装..."
    pip install Flask Werkzeug
    if [ $? -ne 0 ]; then
        echo "❌ Flask 安装失败"
        exit 1
    fi
    echo "✅ Flask 安装成功"
fi

echo "✅ Flask 已安装"
echo ""

# 检查视频目录
if [ ! -d "website/videos" ]; then
    echo "📁 创建视频目录..."
    mkdir -p website/videos
fi

# 检查是否有 .ban 文件
BAN_FILES=$(ls -1 *.ban 2>/dev/null | head -1)
if [ -n "$BAN_FILES" ]; then
    echo "📹 发现 .ban 文件: $BAN_FILES"
    echo "   复制到 website/videos/..."
    cp $BAN_FILES website/videos/
    echo "✅ 视频已复制"
else
    echo "⚠️  没有找到 .ban 文件"
    echo "   提示: 可以将 .ban 文件复制到 website/videos/ 目录"
fi

echo ""
echo "🎯 启动 Flask 服务器..."
echo "   访问地址: http://localhost:5000"
echo "   API 文档: http://localhost:5000/api/video/<filename>/info"
echo ""
echo "按 Ctrl+C 停止服务器"
echo ""
echo "===================="
echo ""

# 启动 Flask 应用
cd website
python3 app.py
