#!/usr/bin/env python3
"""
统一的回测运行脚本
Unified backtest runner script
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from src.backtest.backtest_with_real_data import run_backtest_with_real_data
from src.backtest.simple_grid_backtest import run_simple_grid_backtest


def main():
    parser = argparse.ArgumentParser(description="运行策略回测")
    parser.add_argument(
        "--type",
        choices=["simple", "real"],
        default="simple",
        help="回测类型: simple(简单测试) 或 real(真实数据)"
    )
    parser.add_argument(
        "--data",
        type=str,
        help="历史数据文件路径（仅用于real类型）"
    )
    
    args = parser.parse_args()
    
    if args.type == "simple":
        print("运行简单回测...")
        run_simple_grid_backtest()
    else:
        data_file = args.data or "nautilus_data/historical/BTCUSDT_quotes.csv"
        print(f"使用真实数据运行回测: {data_file}")
        run_backtest_with_real_data(data_file)


if __name__ == "__main__":
    main()