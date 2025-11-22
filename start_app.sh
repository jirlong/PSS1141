#!/bin/bash

# AI 智能助手平台 - 快速啟動腳本

echo "=================================="
echo "  AI 智能助手平台 - 啟動程序"
echo "=================================="
echo ""

# 檢查 Python 是否安裝
if ! command -v python3 &> /dev/null; then
    echo "❌ 錯誤：未找到 Python3"
    echo "請先安裝 Python 3.7 或更高版本"
    exit 1
fi

echo "✅ Python 已安裝"
python3 --version
echo ""

# 檢查虛擬環境
if [ ! -d "venv" ]; then
    echo "📦 創建虛擬環境..."
    python3 -m venv venv
    echo "✅ 虛擬環境創建完成"
else
    echo "✅ 虛擬環境已存在"
fi
echo ""

# 啟動虛擬環境
echo "🔄 啟動虛擬環境..."
source venv/bin/activate
echo "✅ 虛擬環境已啟動"
echo ""

# 安裝依賴
echo "📥 檢查並安裝依賴套件..."
pip install --upgrade pip > /dev/null 2>&1
pip install -q flask openai pydantic
echo "✅ 依賴套件安裝完成"
echo ""

# 檢查必要檔案
if [ ! -f "flask_app.py" ]; then
    echo "❌ 錯誤：找不到 flask_app.py"
    exit 1
fi

if [ ! -d "templates" ] || [ ! -f "templates/index.html" ]; then
    echo "❌ 錯誤：找不到 templates/index.html"
    exit 1
fi

if [ ! -d "static" ] || [ ! -f "static/style.css" ] || [ ! -f "static/script.js" ]; then
    echo "❌ 錯誤：找不到 static 資源檔案"
    exit 1
fi

echo "✅ 所有必要檔案檢查完成"
echo ""

# 啟動應用
echo "=================================="
echo "🚀 啟動 Flask 應用..."
echo "=================================="
echo ""
echo "📍 服務位址: http://localhost:5001"
echo "💡 提示：按 Ctrl+C 停止服務"
echo ""
echo "=================================="
echo ""

python3 flask_app.py
