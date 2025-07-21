#!/usr/bin/env python3
"""
从Binance下载真实历史数据
Download real historical data from Binance
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


def download_binance_klines(symbol="BTCUSDT", interval="1m", start_time=None, end_time=None, limit=1000):
    """
    从Binance下载K线数据
    
    参数:
    - symbol: 交易对
    - interval: 时间间隔 (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)
    - start_time: 开始时间戳（毫秒）
    - end_time: 结束时间戳（毫秒）
    - limit: 数据条数（最大1000）
    """
    url = "https://api.binance.com/api/v3/klines"
    
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    
    if start_time:
        params["startTime"] = start_time
    if end_time:
        params["endTime"] = end_time
        
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        # 检查是否有错误
        if isinstance(data, dict) and 'code' in data:
            print(f"API错误: {data.get('msg', 'Unknown error')}")
            return None
            
        return data
    except Exception as e:
        print(f"请求失败: {e}")
        return None


def download_all_historical_data(symbol="BTCUSDT", start_date="2024-01-01", end_date=None, interval="1m"):
    """
    下载指定时间范围的所有历史数据
    """
    print(f"开始下载 {symbol} 历史数据...")
    print(f"时间范围: {start_date} 到 {end_date or '现在'}")
    
    # 转换日期
    start_timestamp = int(pd.Timestamp(start_date).timestamp() * 1000)
    if end_date:
        end_timestamp = int(pd.Timestamp(end_date).timestamp() * 1000)
    else:
        end_timestamp = int(datetime.now().timestamp() * 1000)
    
    all_klines = []
    current_start = start_timestamp
    
    while current_start < end_timestamp:
        # 下载数据
        klines = download_binance_klines(
            symbol=symbol,
            interval=interval,
            start_time=current_start,
            end_time=end_timestamp,
            limit=1000
        )
        
        if klines and isinstance(klines, list) and len(klines) > 0:
            all_klines.extend(klines)
            # 更新开始时间为最后一条数据的时间 + 1毫秒
            current_start = klines[-1][0] + 1
            
            # 显示进度
            progress_date = datetime.fromtimestamp(current_start/1000).strftime('%Y-%m-%d %H:%M')
            print(f"已下载到: {progress_date}, 共 {len(all_klines)} 条数据")
            
            # 避免请求过快
            time.sleep(0.2)
        else:
            break
    
    return all_klines


def klines_to_dataframe(klines):
    """
    将K线数据转换为DataFrame
    
    Binance K线格式:
    [
        [
            1499040000000,      # 开盘时间
            "0.01634790",       # 开盘价
            "0.80000000",       # 最高价
            "0.01575800",       # 最低价
            "0.01577100",       # 收盘价
            "148976.11427815",  # 成交量
            1499644799999,      # 收盘时间
            "2434.19055334",    # 成交额
            308,                # 成交笔数
            "1756.87402397",    # 主动买入成交量
            "28.46694368",      # 主动买入成交额
            "17928899.62484339" # 忽略
        ]
    ]
    """
    df = pd.DataFrame(klines, columns=[
        'open_time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_volume', 'trades', 'taker_buy_volume',
        'taker_buy_quote_volume', 'ignore'
    ])
    
    # 转换数据类型
    df['timestamp'] = pd.to_datetime(df['open_time'], unit='ms')
    numeric_columns = ['open', 'high', 'low', 'close', 'volume', 'quote_volume']
    for col in numeric_columns:
        df[col] = df[col].astype(float)
    
    # 设置时间戳为索引
    df.set_index('timestamp', inplace=True)
    
    return df


def create_quote_ticks_from_klines(df):
    """
    从K线数据创建QuoteTick格式数据
    使用更真实的价差计算
    """
    # 计算价差（基于波动性）
    volatility = (df['high'] - df['low']).rolling(window=60).mean()
    volatility = volatility.fillna((df['high'] - df['low']).mean())
    
    # 价差为波动性的1-2%
    spread = volatility * 0.015
    spread = spread.clip(lower=0.5, upper=5.0)  # 限制在0.5-5 USDT之间
    
    # 使用成交量估算报价量
    avg_volume = df['volume'].rolling(window=60).mean()
    avg_volume = avg_volume.fillna(df['volume'].mean())
    
    quote_df = pd.DataFrame({
        'bid_price': df['close'] - spread/2,
        'ask_price': df['close'] + spread/2,
        'bid_size': avg_volume * 0.001,  # 报价量约为成交量的0.1%
        'ask_size': avg_volume * 0.001,
    })
    
    return quote_df


def save_data(df, quote_df, symbol="BTCUSDT"):
    """保存数据"""
    # 创建目录
    os.makedirs("nautilus_data/historical", exist_ok=True)
    
    # 保存K线数据
    kline_path = f"nautilus_data/historical/{symbol}_klines.csv"
    df.to_csv(kline_path)
    print(f"K线数据已保存到: {kline_path}")
    
    # 保存Quote数据
    quote_csv_path = f"nautilus_data/historical/{symbol}_quotes.csv"
    quote_df.to_csv(quote_csv_path)
    print(f"Quote数据已保存到: {quote_csv_path}")
    
    quote_parquet_path = f"nautilus_data/historical/{symbol}_quotes.parquet"
    quote_df.to_parquet(quote_parquet_path)
    print(f"Quote数据已保存到: {quote_parquet_path}")
    
    return quote_csv_path, quote_parquet_path


def main():
    """主函数"""
    print("=== 从Binance下载BTC/USDT真实历史数据 ===\n")
    
    # 下载最近7天的1分钟数据（测试用）
    # 如果需要更多数据，可以修改start_date
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    klines = download_all_historical_data(
        symbol="BTCUSDT",
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d'),
        interval="1m"
    )
    
    if klines:
        print(f"\n成功下载 {len(klines)} 条K线数据")
        
        # 转换为DataFrame
        df = klines_to_dataframe(klines)
        
        # 创建QuoteTick数据
        quote_df = create_quote_ticks_from_klines(df)
        
        print(f"\n数据概览:")
        print(f"时间范围: {df.index[0]} 到 {df.index[-1]}")
        print(f"数据条数: {len(df)}")
        print(f"价格范围: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
        print(f"平均成交量: {df['volume'].mean():.6f} BTC")
        
        print("\nK线数据样本:")
        print(df[['open', 'high', 'low', 'close', 'volume']].head())
        
        print("\nQuote数据样本:")
        print(quote_df.head())
        
        # 保存数据
        save_data(df, quote_df)
        
        # 数据质量检查
        print("\n数据质量检查:")
        print(f"缺失值: {df.isnull().sum().sum()}")
        print(f"重复值: {df.index.duplicated().sum()}")
        print(f"数据完整性: {len(df) / ((df.index[-1] - df.index[0]).total_seconds() / 60):.2%}")
        
    else:
        print("下载数据失败")


if __name__ == "__main__":
    main()