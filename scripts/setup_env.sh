#!/bin/bash
# Environment setup script for Agent Skills Framework

set -e

echo "================================================"
echo "Agent Skills Framework - 环境设置"
echo "================================================"

# Check Python version
echo ""
echo "检查 Python 版本..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "当前版本: $python_version"

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo ""
    echo "创建虚拟环境..."
    python3 -m venv venv
    echo "✓ 虚拟环境已创建"
else
    echo ""
    echo "虚拟环境已存在"
fi

# Activate virtual environment
echo ""
echo "激活虚拟环境..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "升级 pip..."
pip install --upgrade pip > /dev/null 2>&1

# Install dependencies
echo ""
echo "安装依赖..."
pip install -r requirements.txt

# Copy .env.example if .env doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "创建 .env 文件..."
    cp .env.example .env
    echo "✓ .env 文件已创建（请编辑填写 API Key）"
else
    echo ""
    echo ".env 文件已存在"
fi

# Create skills directory if not exists
mkdir -p skills

echo ""
echo "================================================"
echo "设置完成！"
echo "================================================"
echo ""
echo "下一步："
echo "1. 编辑 .env 文件，设置 LLM_API_KEY"
echo "2. 激活虚拟环境: source venv/bin/activate"
echo "3. 运行演示: python main.py --demo"
echo "4. 交互模式: python main.py"
echo ""
