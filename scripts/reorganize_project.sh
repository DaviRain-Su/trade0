#!/bin/bash
# 项目重组脚本
# 将现有文件整理到合适的目录结构中

echo "=== 开始重组项目结构 ==="

# 1. 创建新的目录结构
echo "创建新目录..."
mkdir -p src/data
mkdir -p src/backtest
mkdir -p src/live
mkdir -p scripts/legacy
mkdir -p data/results
mkdir -p logs/backtest
mkdir -p logs/live
mkdir -p docs/api
mkdir -p docs/guides
mkdir -p docs/development
mkdir -p tests/fixtures

# 2. 移动数据相关文件
echo "整理数据处理模块..."
if [ -f "download_historical_data.py" ]; then
    mv download_historical_data.py src/data/
fi
if [ -f "download_binance_data.py" ]; then
    mv download_binance_data.py src/data/
fi
if [ -f "download_multi_source_data.py" ]; then
    mv download_multi_source_data.py src/data/
fi
if [ -f "prepare_data.py" ]; then
    mv prepare_data.py src/data/
fi

# 3. 移动回测相关文件
echo "整理回测模块..."
if [ -f "backtest_grid_strategy.py" ]; then
    mv backtest_grid_strategy.py src/backtest/
fi
if [ -f "backtest_with_real_data.py" ]; then
    mv backtest_with_real_data.py src/backtest/
fi
if [ -f "simple_grid_backtest.py" ]; then
    mv simple_grid_backtest.py src/backtest/
fi
if [ -f "complete_backtest.py" ]; then
    mv complete_backtest.py src/backtest/
fi
if [ -f "backtest_with_data.py" ]; then
    mv backtest_with_data.py src/backtest/
fi

# 4. 移动实盘相关文件
echo "整理实盘交易模块..."
if [ -f "run_grid_strategy.py" ]; then
    mv run_grid_strategy.py src/live/
fi
if [ -f "bybit_config.py" ]; then
    mv bybit_config.py src/live/
fi
if [ -f "bybit_quickstart.py" ]; then
    mv bybit_quickstart.py src/live/
fi

# 5. 移动其他脚本到legacy
echo "整理其他脚本..."
for file in *.py; do
    if [ -f "$file" ] && [ "$file" != "main.py" ]; then
        echo "移动 $file 到 scripts/legacy/"
        mv "$file" scripts/legacy/
    fi
done

# 6. 创建 __init__.py 文件
echo "创建 __init__.py 文件..."
touch src/data/__init__.py
touch src/backtest/__init__.py
touch src/live/__init__.py
touch tests/fixtures/__init__.py

# 7. 创建示例配置文件
echo "创建示例配置..."
cat > .env.example << EOF
# Bybit API配置
BYBIT_API_KEY=your_api_key_here
BYBIT_API_SECRET=your_api_secret_here
BYBIT_TESTNET_API_KEY=your_testnet_api_key_here
BYBIT_TESTNET_API_SECRET=your_testnet_api_secret_here

# 其他配置
LOG_LEVEL=INFO
EOF

# 8. 创建改进的.gitignore
echo "更新.gitignore..."
cat > .gitignore << EOF
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
ENV/

# 环境变量
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# 数据文件
data/historical/*
data/cache/*
!data/historical/.gitkeep
!data/cache/.gitkeep

# 日志
logs/*.log
logs/**/*.log

# 测试
.pytest_cache/
.coverage
htmlcov/

# Jupyter
.ipynb_checkpoints/

# 临时文件
*.tmp
*.bak

# macOS
.DS_Store
EOF

# 9. 创建.gitkeep文件保持空目录
echo "创建.gitkeep文件..."
touch data/historical/.gitkeep
touch data/cache/.gitkeep
touch data/results/.gitkeep
touch logs/backtest/.gitkeep
touch logs/live/.gitkeep
touch notebooks/.gitkeep
touch docs/api/.gitkeep
touch docs/guides/.gitkeep
touch docs/development/.gitkeep

# 10. 显示新的项目结构
echo ""
echo "✅ 项目重组完成！"
echo ""
echo "新的项目结构："
tree -I '__pycache__|*.pyc|.venv|uv.lock' -L 3

echo ""
echo "下一步："
echo "1. 检查移动的文件是否正确"
echo "2. 更新Python文件中的导入路径"
echo "3. 运行测试确保功能正常"
echo "4. 提交更改到Git"