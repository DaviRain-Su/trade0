#!/usr/bin/env python3
"""
下载真实的历史数据
Download real historical data from exchanges
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import time
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent))


def download_bybit_klines(symbol="BTCUSDT", interval="1", limit=1000, start_time=None):
    """
    从Bybit下载K线数据
    
    参数:
    - symbol: 交易对 (默认 BTCUSDT)
    - interval: K线间隔 (1, 3, 5, 15, 30, 60, 120, 240, 360, 720, D, W, M)
    - limit: 每次请求的数据条数 (最大1000)
    - start_time: 开始时间戳（毫秒）
    """
    url = "https://api.bybit.com/v5/market/kline"
    
    params = {
        "category": "linear",  # 永续合约
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    
    if start_time:
        params["start"] = start_time
        
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if data["retCode"] == 0:
            return data["result"]["list"]
        else:
            print(f"Error: {data['retMsg']}")
            return None
    except Exception as e:
        print(f"Request failed: {e}")
        return None


def download_historical_data(symbol="BTCUSDT", days=30, interval="1"):
    """
    下载历史数据
    
    参数:
    - symbol: 交易对
    - days: 下载天数
    - interval: K线间隔（分钟）
    """
    print(f"开始下载 {symbol} 最近 {days} 天的历史数据...")
    
    all_data = []
    end_time = int(datetime.now().timestamp() * 1000)
    start_time = end_time - (days * 24 * 60 * 60 * 1000)
    
    current_start = start_time
    
    while current_start < end_time:
        print(f"下载数据: {datetime.fromtimestamp(current_start/1000)}")
        
        klines = download_bybit_klines(
            symbol=symbol,
            interval=interval,
            limit=1000,
            start_time=current_start
        )
        
        if klines:
            all_data.extend(klines)
            # 获取最后一条数据的时间作为下一次请求的开始时间
            if klines:
                current_start = int(klines[0][0]) + 60000  # 加1分钟
            else:
                break
        else:
            break
            
        # 避免请求过快
        time.sleep(0.1)
        
        # 检查是否已经获取到足够的数据
        if all_data and int(all_data[0][0]) >= end_time:
            break
    
    return all_data


def convert_to_quote_ticks(klines_data):
    """
    将K线数据转换为QuoteTick格式
    
    Bybit K线数据格式:
    [
        [timestamp, open, high, low, close, volume, turnover],
        ...
    ]
    """
    if not klines_data:
        return pd.DataFrame()
        
    # 转换为DataFrame
    df = pd.DataFrame(klines_data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'
    ])
    
    # 转换数据类型
    df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
    for col in ['open', 'high', 'low', 'close', 'volume', 'turnover']:
        df[col] = df[col].astype(float)
    
    # 排序（Bybit返回的数据是倒序的）
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    # 创建QuoteTick格式的数据
    # 使用close价格，添加小的价差
    spread = 1.0  # 1 USDT的价差
    
    quote_df = pd.DataFrame({
        'timestamp': df['timestamp'],
        'bid_price': df['close'] - spread/2,
        'ask_price': df['close'] + spread/2,
        'bid_size': df['volume'] / len(df) * 0.1,  # 估算的报价量
        'ask_size': df['volume'] / len(df) * 0.1,
    })
    
    quote_df.set_index('timestamp', inplace=True)
    
    return quote_df


def save_historical_data(quote_df, symbol="BTCUSDT"):
    """保存历史数据"""
    if quote_df.empty:
        print("没有数据可保存")
        return
        
    # 创建数据目录
    os.makedirs("nautilus_data/historical", exist_ok=True)
    
    # 保存为CSV
    csv_path = f"nautilus_data/historical/{symbol}_quotes.csv"
    quote_df.to_csv(csv_path)
    print(f"数据已保存到: {csv_path}")
    
    # 保存为Parquet
    parquet_path = f"nautilus_data/historical/{symbol}_quotes.parquet"
    quote_df.to_parquet(parquet_path)
    print(f"数据已保存到: {parquet_path}")
    
    return csv_path, parquet_path


def main():
    """主函数"""
    print("=== 下载BTC/USDT真实历史数据 ===\n")
    
    # 下载最近30天的1分钟K线数据
    klines = download_historical_data(
        symbol="BTCUSDT",
        days=30,
        interval="1"
    )
    
    if klines:
        print(f"\n成功下载 {len(klines)} 条K线数据")
        
        # 转换为QuoteTick格式
        quote_df = convert_to_quote_ticks(klines)
        
        print(f"\n转换后的数据:")
        print(f"时间范围: {quote_df.index[0]} 到 {quote_df.index[-1]}")
        print(f"数据条数: {len(quote_df)}")
        print(f"价格范围: ${quote_df['bid_price'].min():.2f} - ${quote_df['ask_price'].max():.2f}")
        
        # 显示数据样本
        print("\n数据样本:")
        print(quote_df.head())
        
        # 保存数据
        save_historical_data(quote_df)
        
        # 显示一些统计信息
        print("\n数据统计:")
        print(f"平均价格: ${quote_df[['bid_price', 'ask_price']].mean().mean():.2f}")
        print(f"价格标准差: ${quote_df[['bid_price', 'ask_price']].std().mean():.2f}")
        print(f"最高价: ${quote_df['ask_price'].max():.2f}")
        print(f"最低价: ${quote_df['bid_price'].min():.2f}")
        
    else:
        print("下载数据失败")


if __name__ == "__main__":
    main()