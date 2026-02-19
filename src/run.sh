#!/bin/bash
# Travel CS AI - Quick Start Script

set -e

echo "🚀 Travel CS AI - 启动脚本"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 未安装"
    exit 1
fi

# Check if in virtual environment
if [[ -z "${VIRTUAL_ENV}" ]]; then
    echo "⚠️  建议创建虚拟环境:"
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
    echo ""
    read -p "是否继续? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Install dependencies
echo "📦 安装依赖..."
pip install -q -r requirements.txt

# Check environment
echo "🔧 检查配置..."
if [[ -z "${DEEPSEEK_API_KEY}" && -z "${OPENAI_API_KEY}" ]]; then
    echo "⚠️  警告: LLM API Key 未设置"
    echo "   设置方法: export DEEPSEEK_API_KEY=sk-xxxxxx"
    echo "   或创建 .env 文件"
    echo ""
fi

# Start server
echo ""
echo "✅ 启动服务..."
echo ""
echo "   聊天界面: http://localhost:8000/web/chat.html"
echo "   管理后台: http://localhost:8000/admin/dashboard.html"
echo "   API文档:  http://localhost:8000/docs"
echo ""

python api/main.py
