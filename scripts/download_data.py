#!/usr/bin/env python3
"""
数据下载脚本
Data download script
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from src.data.download_multi_source_data import main as download_main


if __name__ == "__main__":
    print("开始下载历史数据...")
    download_main()