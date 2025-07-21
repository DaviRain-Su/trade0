#!/bin/bash
# 项目目录结构初始化脚本

echo "=== 初始化量化交易项目目录结构 ==="

# 创建源代码目录
echo "创建源代码目录..."
mkdir -p src/strategies
mkdir -p src/risk
mkdir -p src/utils
mkdir -p src/monitoring

# 创建配置目录
echo "创建配置目录..."
mkdir -p config/strategies
mkdir -p config/exchanges

# 创建测试目录
echo "创建测试目录..."
mkdir -p tests/unit
mkdir -p tests/integration
mkdir -p tests/backtest

# 创建运维脚本目录
echo "创建脚本目录..."
mkdir -p scripts

# 创建notebook目录
echo "创建notebook目录..."
mkdir -p notebooks

# 创建日志目录
echo "创建日志目录..."
mkdir -p logs

# 创建数据目录
echo "创建数据目录..."
mkdir -p data/historical
mkdir -p data/cache

# 创建 __init__.py 文件
echo "创建 __init__.py 文件..."
touch src/__init__.py
touch src/strategies/__init__.py
touch src/risk/__init__.py
touch src/utils/__init__.py
touch src/monitoring/__init__.py
touch tests/__init__.py

# 设置脚本权限
chmod +x run_grid_strategy.py
chmod +x bybit_quickstart.py

echo "✅ 目录结构创建完成！"
echo ""
echo "项目结构："
echo "trade0/"
echo "├── src/              # 源代码"
echo "│   ├── strategies/   # 策略实现"
echo "│   ├── risk/         # 风险管理"
echo "│   ├── utils/        # 工具函数"
echo "│   └── monitoring/   # 监控模块"
echo "├── config/           # 配置文件"
echo "├── tests/            # 测试代码"
echo "├── logs/             # 日志文件"
echo "├── data/             # 数据存储"
echo "└── notebooks/        # Jupyter notebooks"