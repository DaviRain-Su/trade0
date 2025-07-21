#!/usr/bin/env python3
"""
实盘交易运行脚本
Live trading runner script
"""

import sys
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from src.live.run_grid_strategy import main as live_main


if __name__ == "__main__":
    print("启动实盘交易...")
    live_main()