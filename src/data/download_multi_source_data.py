#!/usr/bin/env python3
"""
从多个数据源下载真实历史数据
Download real historical data from multiple sources
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import time
from pathlib import Path
import json

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))


def download_cryptocompare_data(symbol="BTC", currency="USDT", limit=2000):
    """
    从CryptoCompare下载历史数据（免费，无需API密钥）
    
    参数:
    - symbol: 基础货币 (BTC, ETH等)
    - currency: 报价货币 (USDT, USD等)
    - limit: 数据条数（最大2000）
    """
    # 分钟数据
    url = "https://min-api.cryptocompare.com/data/v2/histominute"
    
    params = {
        "fsym": symbol,
        "tsym": currency,
        "limit": limit,
        "aggregate": 1  # 1分钟
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if data.get("Response") == "Success":
            return data["Data"]["Data"]
        else:
            print(f"CryptoCompare错误: {data.get('Message', 'Unknown error')}")
            return None
    except Exception as e:
        print(f"请求失败: {e}")
        return None


def download_coingecko_data(coin_id="bitcoin", vs_currency="usd", days=30):
    """
    从CoinGecko下载历史数据（免费，有速率限制）
    
    参数:
    - coin_id: 币种ID (bitcoin, ethereum等)
    - vs_currency: 报价货币 (usd, usdt等)
    - days: 天数（1, 7, 14, 30, 90, 180, 365, max）
    """
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    
    params = {
        "vs_currency": vs_currency,
        "days": days,
        "interval": "minutely" if days <= 1 else "hourly"
    }
    
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0"  # 避免被拒绝
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("prices", [])
        else:
            print(f"CoinGecko错误: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"请求失败: {e}")
        return None


def download_kraken_data(pair="XBTUSD", interval=1):
    """
    从Kraken下载OHLC数据（公开API）
    
    参数:
    - pair: 交易对 (XBTUSD, XBTUSDT等)
    - interval: 时间间隔（分钟）- 1, 5, 15, 30, 60, 240, 1440, 10080, 21600
    """
    url = "https://api.kraken.com/0/public/OHLC"
    
    params = {
        "pair": pair,
        "interval": interval
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if not data.get("error"):
            # Kraken返回的数据格式特殊，需要处理
            result_key = list(data["result"].keys())[0]
            return data["result"][result_key]
        else:
            print(f"Kraken错误: {data['error']}")
            return None
    except Exception as e:
        print(f"请求失败: {e}")
        return None


def download_coinbase_data(product_id="BTC-USD", granularity=60):
    """
    从Coinbase下载历史数据（公开API）
    
    参数:
    - product_id: 产品ID (BTC-USD, BTC-USDT等)
    - granularity: 时间粒度（秒）- 60, 300, 900, 3600, 21600, 86400
    """
    url = f"https://api.exchange.coinbase.com/products/{product_id}/candles"
    
    # 获取最近300条数据
    params = {
        "granularity": granularity
    }
    
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Coinbase错误: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"请求失败: {e}")
        return None


def convert_cryptocompare_to_df(data):
    """转换CryptoCompare数据为DataFrame"""
    if not data:
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['time'], unit='s')
    df = df.rename(columns={
        'open': 'open',
        'high': 'high', 
        'low': 'low',
        'close': 'close',
        'volumefrom': 'volume'
    })
    df.set_index('timestamp', inplace=True)
    return df[['open', 'high', 'low', 'close', 'volume']]


def convert_coingecko_to_df(data):
    """转换CoinGecko数据为DataFrame"""
    if not data:
        return pd.DataFrame()
    
    df = pd.DataFrame(data, columns=['timestamp', 'price'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    # CoinGecko只有价格数据，创建简单的OHLC
    df['open'] = df['price']
    df['high'] = df['price']
    df['low'] = df['price']
    df['close'] = df['price']
    df['volume'] = 0  # 没有成交量数据
    
    df.set_index('timestamp', inplace=True)
    return df[['open', 'high', 'low', 'close', 'volume']]


def convert_kraken_to_df(data):
    """转换Kraken数据为DataFrame"""
    if not data:
        return pd.DataFrame()
    
    # Kraken数据格式: [time, open, high, low, close, vwap, volume, count]
    df = pd.DataFrame(data, columns=['time', 'open', 'high', 'low', 'close', 'vwap', 'volume', 'count'])
    df['timestamp'] = pd.to_datetime(df['time'], unit='s')
    
    # 转换为数值类型
    numeric_cols = ['open', 'high', 'low', 'close', 'volume']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col])
    
    df.set_index('timestamp', inplace=True)
    return df[['open', 'high', 'low', 'close', 'volume']]


def convert_coinbase_to_df(data):
    """转换Coinbase数据为DataFrame"""
    if not data:
        return pd.DataFrame()
    
    # Coinbase数据格式: [time, low, high, open, close, volume]
    df = pd.DataFrame(data, columns=['time', 'low', 'high', 'open', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['time'], unit='s')
    
    df.set_index('timestamp', inplace=True)
    return df[['open', 'high', 'low', 'close', 'volume']]


def create_quote_data_from_ohlc(df):
    """从OHLC数据创建Quote数据"""
    if df.empty:
        return pd.DataFrame()
    
    # 使用close价格，添加真实的价差
    spread_ratio = 0.0002  # 0.02%的价差
    spread = df['close'] * spread_ratio
    
    # 使用成交量估算报价量
    if 'volume' in df.columns and df['volume'].sum() > 0:
        avg_volume = df['volume'].rolling(window=60, min_periods=1).mean()
    else:
        avg_volume = 0.1  # 默认值
    
    quote_df = pd.DataFrame({
        'bid_price': df['close'] - spread/2,
        'ask_price': df['close'] + spread/2,
        'bid_size': avg_volume * 0.001,
        'ask_size': avg_volume * 0.001,
    })
    
    return quote_df


def main():
    """主函数"""
    print("=== 从多个数据源下载BTC历史数据 ===\n")
    
    # 创建数据目录
    os.makedirs("nautilus_data/historical", exist_ok=True)
    
    success = False
    
    # 1. 尝试CryptoCompare（推荐）
    print("1. 尝试从CryptoCompare下载数据...")
    cc_data = download_cryptocompare_data("BTC", "USDT", limit=2000)
    if cc_data:
        df = convert_cryptocompare_to_df(cc_data)
        print(f"✅ 成功! 获取了 {len(df)} 条数据")
        print(f"时间范围: {df.index[0]} 到 {df.index[-1]}")
        success = True
    else:
        print("❌ CryptoCompare下载失败")
    
    # 2. 尝试CoinGecko
    if not success:
        print("\n2. 尝试从CoinGecko下载数据...")
        time.sleep(1)  # 避免速率限制
        cg_data = download_coingecko_data("bitcoin", "usd", days=7)
        if cg_data:
            df = convert_coingecko_to_df(cg_data)
            print(f"✅ 成功! 获取了 {len(df)} 条数据")
            print(f"时间范围: {df.index[0]} 到 {df.index[-1]}")
            success = True
        else:
            print("❌ CoinGecko下载失败")
    
    # 3. 尝试Kraken
    if not success:
        print("\n3. 尝试从Kraken下载数据...")
        kraken_data = download_kraken_data("XBTUSD", 1)
        if kraken_data:
            df = convert_kraken_to_df(kraken_data)
            print(f"✅ 成功! 获取了 {len(df)} 条数据")
            print(f"时间范围: {df.index[0]} 到 {df.index[-1]}")
            success = True
        else:
            print("❌ Kraken下载失败")
    
    # 4. 尝试Coinbase
    if not success:
        print("\n4. 尝试从Coinbase下载数据...")
        cb_data = download_coinbase_data("BTC-USD", 60)
        if cb_data:
            df = convert_coinbase_to_df(cb_data)
            print(f"✅ 成功! 获取了 {len(df)} 条数据")
            print(f"时间范围: {df.index[0]} 到 {df.index[-1]}")
            success = True
        else:
            print("❌ Coinbase下载失败")
    
    # 处理和保存数据
    if success and not df.empty:
        print("\n数据概览:")
        print(f"价格范围: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
        print(f"平均价格: ${df['close'].mean():.2f}")
        
        print("\n数据样本:")
        print(df.head())
        
        # 创建Quote数据
        quote_df = create_quote_data_from_ohlc(df)
        
        # 保存数据
        print("\n保存数据...")
        
        # 保存OHLC数据
        ohlc_path = "nautilus_data/historical/BTCUSDT_ohlc.csv"
        df.to_csv(ohlc_path)
        print(f"OHLC数据已保存到: {ohlc_path}")
        
        # 保存Quote数据
        quote_path = "nautilus_data/historical/BTCUSDT_quotes.csv"
        quote_df.to_csv(quote_path)
        print(f"Quote数据已保存到: {quote_path}")
        
        # 保存Parquet格式
        parquet_path = "nautilus_data/historical/BTCUSDT_quotes.parquet"
        quote_df.to_parquet(parquet_path)
        print(f"Parquet数据已保存到: {parquet_path}")
        
        print("\n✅ 数据下载成功!")
        print("\n现在可以运行以下命令使用真实数据进行回测:")
        print("python backtest_with_real_data.py")
        
    else:
        print("\n❌ 所有数据源都下载失败")
        print("\n可能的原因:")
        print("1. 网络连接问题")
        print("2. API服务暂时不可用")
        print("3. 地区限制")
        print("\n建议:")
        print("1. 检查网络连接")
        print("2. 稍后再试")
        print("3. 使用VPN或代理")


if __name__ == "__main__":
    main()