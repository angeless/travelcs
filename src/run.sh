#!/bin/bash
# 旅游客服AI - 启动脚本

echo "🚀 启动旅游客服AI服务..."

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 需要先安装Python3"
    exit 1
fi

# 创建工作目录
cd "$(dirname "$0")"
mkdir -p data

# 检查依赖
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "📦 安装依赖..."
pip install -q fastapi uvicorn requests 2>/dev/null

echo ""
echo "✅ 启动成功！"
echo ""
echo "📱 网页聊天: http://localhost:8000/web/chat.html"
echo "⚙️ 管理后台: http://localhost:8000/admin/dashboard.html"
echo "📚 API文档: http://localhost:8000/docs"
echo ""

# 启动服务
python api/main.py
