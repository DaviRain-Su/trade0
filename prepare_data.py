#!/usr/bin/env python3
"""
准备回测数据
Prepare backtesting data
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os


def generate_forex_data(symbol="EURUSD", days=7):
    """生成模拟的外汇数据（用于测试）"""
    # 生成时间序列
    end = datetime.now()
    start = end - timedelta(days=days)
    
    # 每30秒一个数据点
    timestamps = pd.date_range(start=start, end=end, freq='30s')
    
    # 基础价格（根据symbol调整）
    if symbol == "BTCUSDT":
        base_price = 42000.0  # BTC基础价格
        volatility = 0.02    # 2%波动
    else:
        base_price = 1.0850  # EUR/USD基础价格
        volatility = 0.001   # 0.1%波动
    
    # 生成价格数据
    num_points = len(timestamps)
    # 使用更小的随机变化，避免累积效应过大
    price_changes = np.random.normal(0, volatility/100, num_points)
    cumulative_changes = np.cumsum(price_changes)
    
    # 添加均值回归，避免价格偏离太远
    mean_reversion_strength = 0.01
    cumulative_changes = cumulative_changes * (1 - mean_reversion_strength)
    
    # 计算价格
    prices = base_price * (1 + cumulative_changes)
    
    # 添加一些周期性波动（模拟市场周期）
    cycle = np.sin(np.linspace(0, 4*np.pi, num_points)) * base_price * 0.02
    prices = prices + cycle
    
    # 生成bid/ask价差
    spread = 0.0001 if symbol == "EURUSD" else 1.0  # BTC有更大的价差
    
    # 创建DataFrame
    if symbol == "BTCUSDT":
        # BTC quantities should be in BTC, not USD
        bid_sizes = np.random.uniform(0.01, 1.0, num_points)  # 0.01-1.0 BTC
        ask_sizes = np.random.uniform(0.01, 1.0, num_points)
    else:
        bid_sizes = np.random.uniform(100000, 1000000, num_points)
        ask_sizes = np.random.uniform(100000, 1000000, num_points)
    
    df = pd.DataFrame({
        'timestamp': timestamps,
        'bid_price': prices - spread/2,
        'ask_price': prices + spread/2,
        'bid_size': bid_sizes,
        'ask_size': ask_sizes,
    })
    
    # 设置时间戳为索引
    df.set_index('timestamp', inplace=True)
    
    # 添加一些市场特征
    # 1. 交易时段波动性
    hour = df.index.hour
    session_volatility = np.where(
        (hour >= 8) & (hour <= 16), 1.5,  # 活跃时段
        0.7  # 其他时段
    )
    
    # 调整价格波动
    df['bid_price'] = df['bid_price'] * (1 + np.random.normal(0, 0.0001, len(df)) * session_volatility)
    df['ask_price'] = df['ask_price'] * (1 + np.random.normal(0, 0.0001, len(df)) * session_volatility)
    
    return timestamps, df


def save_data(df, symbol="EURUSD"):
    """保存数据到文件"""
    # 创建数据目录
    os.makedirs("nautilus_data", exist_ok=True)
    
    # 保存为CSV
    csv_path = f"nautilus_data/{symbol}_quotes.csv"
    df.to_csv(csv_path)
    print(f"数据已保存到: {csv_path}")
    
    # 保存为Parquet
    parquet_path = f"nautilus_data/{symbol}_quotes.parquet"
    df.to_parquet(parquet_path)
    print(f"数据已保存到: {parquet_path}")
    
    return csv_path, parquet_path


def main():
    """生成并保存数据"""
    print("=== 生成回测数据 ===\n")
    
    # 生成BTC/USDT数据
    print("生成BTC/USDT数据...")
    timestamps, btc_df = generate_forex_data(symbol="BTCUSDT", days=7)
    
    print(f"生成了 {len(btc_df)} 个数据点")
    print(f"时间范围: {timestamps[0]} 到 {timestamps[-1]}")
    print(f"价格范围: ${btc_df['bid_price'].min():.2f} - ${btc_df['ask_price'].max():.2f}")
    
    # 保存数据
    csv_path, parquet_path = save_data(btc_df, symbol="BTCUSDT")
    
    # 显示数据样本
    print("\n数据样本:")
    print(btc_df.head())
    
    print("\n✅ 数据准备完成!")


if __name__ == "__main__":
    main()