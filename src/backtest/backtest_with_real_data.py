#!/usr/bin/env python3
"""
使用真实历史数据进行回测
Backtest with real historical data
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from decimal import Decimal
import os

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig
from nautilus_trader.config import LoggingConfig
from nautilus_trader.model.currencies import USDT
from nautilus_trader.model.enums import AccountType, OmsType
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.model.objects import Money
from nautilus_trader.test_kit.stubs.data import TestInstrumentProvider
from nautilus_trader.model.data import QuoteTick
from nautilus_trader.model.objects import Price, Quantity

from src.strategies.simple_grid import SimpleGridStrategy, SimpleGridStrategyConfig


def load_historical_quotes(file_path):
    """加载历史报价数据"""
    print(f"加载数据: {file_path}")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"数据文件不存在: {file_path}")
    
    # 读取CSV文件
    df = pd.read_csv(file_path, index_col='timestamp', parse_dates=True)
    
    print(f"加载了 {len(df)} 条数据")
    print(f"时间范围: {df.index[0]} 到 {df.index[-1]}")
    print(f"价格范围: ${df['bid_price'].min():.2f} - ${df['ask_price'].max():.2f}")
    
    return df


def create_quote_ticks(df, instrument):
    """将DataFrame转换为QuoteTick对象"""
    ticks = []
    
    for timestamp, row in df.iterrows():
        tick = QuoteTick(
            instrument_id=instrument.id,
            bid_price=Price.from_str(f"{row['bid_price']:.2f}"),
            ask_price=Price.from_str(f"{row['ask_price']:.2f}"),
            bid_size=Quantity.from_str(f"{row['bid_size']:.6f}"),
            ask_size=Quantity.from_str(f"{row['ask_size']:.6f}"),
            ts_event=timestamp.value,
            ts_init=timestamp.value,
        )
        ticks.append(tick)
    
    return ticks


def analyze_price_range(df):
    """分析价格范围，为网格策略提供参考"""
    mid_prices = (df['bid_price'] + df['ask_price']) / 2
    
    stats = {
        'mean': mid_prices.mean(),
        'std': mid_prices.std(),
        'min': mid_prices.min(),
        'max': mid_prices.max(),
        'range': mid_prices.max() - mid_prices.min(),
        'volatility': mid_prices.std() / mid_prices.mean() * 100
    }
    
    print("\n价格分析:")
    print(f"平均价格: ${stats['mean']:.2f}")
    print(f"价格范围: ${stats['min']:.2f} - ${stats['max']:.2f}")
    print(f"价格波动: ${stats['range']:.2f}")
    print(f"波动率: {stats['volatility']:.2f}%")
    
    # 建议的网格范围（平均值 ± 1.5倍标准差）
    suggested_lower = stats['mean'] - 1.5 * stats['std']
    suggested_upper = stats['mean'] + 1.5 * stats['std']
    
    print(f"\n建议的网格范围:")
    print(f"下限: ${suggested_lower:.2f}")
    print(f"上限: ${suggested_upper:.2f}")
    
    return stats, suggested_lower, suggested_upper


def run_backtest_with_real_data(data_file="nautilus_data/historical/BTCUSDT_quotes.csv"):
    """使用真实数据运行回测"""
    print("=== 使用真实历史数据回测 ===\n")
    
    # 1. 加载历史数据
    try:
        df = load_historical_quotes(data_file)
    except FileNotFoundError:
        print("\n错误: 未找到历史数据文件!")
        print("请先运行以下命令下载数据:")
        print("  python download_binance_data.py")
        print("或")
        print("  python download_historical_data.py")
        return
    
    # 2. 分析价格范围
    stats, suggested_lower, suggested_upper = analyze_price_range(df)
    
    # 3. 创建回测引擎
    config = BacktestEngineConfig(
        logging=LoggingConfig(log_level="INFO"),
    )
    engine = BacktestEngine(config=config)
    
    # 4. 创建交易工具
    instrument = TestInstrumentProvider.btcusdt_binance()
    venue = instrument.id.venue
    
    # 5. 添加交易场所
    engine.add_venue(
        venue=venue,
        oms_type=OmsType.NETTING,
        account_type=AccountType.MARGIN,
        base_currency=USDT,
        starting_balances=[Money(10_000, USDT)],  # 1万USDT初始资金
    )
    
    # 6. 添加交易工具
    engine.add_instrument(instrument)
    
    # 7. 转换数据为QuoteTick
    print("\n转换数据格式...")
    ticks = create_quote_ticks(df, instrument)
    
    # 限制数据量以加快回测速度（可以调整）
    max_ticks = min(len(ticks), 10000)  # 最多使用10000个数据点
    ticks = ticks[:max_ticks]
    
    engine.add_data(ticks)
    print(f"使用 {len(ticks)} 个数据点进行回测")
    
    # 8. 创建网格策略
    # 使用分析得出的价格范围
    strategy_config = SimpleGridStrategyConfig(
        instrument_id=str(instrument.id),
        total_amount=2000.0,  # 使用2000 USDT
        grid_levels=10,       # 10个网格
        upper_price=min(suggested_upper, stats['mean'] + 500),  # 限制范围
        lower_price=max(suggested_lower, stats['mean'] - 500),
    )
    
    print(f"\n网格策略配置:")
    print(f"投资金额: {strategy_config.total_amount} USDT")
    print(f"网格数量: {strategy_config.grid_levels}")
    print(f"价格范围: ${strategy_config.lower_price:.2f} - ${strategy_config.upper_price:.2f}")
    
    strategy = SimpleGridStrategy(config=strategy_config)
    engine.add_strategy(strategy=strategy)
    
    # 9. 运行回测
    start_time = df.index[0]
    end_time = df.index[min(len(df)-1, max_ticks-1)]
    
    print(f"\n运行回测: {start_time} 到 {end_time}")
    engine.run(start=start_time, end=end_time)
    
    # 10. 分析结果
    print("\n=== 回测结果 ===")
    
    # 账户信息
    account = engine.portfolio.account(venue)
    starting_balance = 10_000
    ending_balance = float(account.balance_total(USDT).as_decimal())
    
    print(f"初始资金: {starting_balance:,.2f} USDT")
    print(f"最终资金: {ending_balance:,.2f} USDT")
    print(f"总收益: {ending_balance - starting_balance:,.2f} USDT")
    print(f"收益率: {((ending_balance / starting_balance) - 1) * 100:.2f}%")
    
    # 交易统计
    positions = engine.cache.positions()
    orders = engine.cache.orders()
    filled_orders = [o for o in orders if o.status.name == "FILLED"]
    
    print(f"\n交易统计:")
    print(f"总订单数: {len(orders)}")
    print(f"成交订单数: {len(filled_orders)}")
    print(f"总持仓数: {len(positions)}")
    
    # 计算更多统计信息
    if filled_orders:
        buy_orders = [o for o in filled_orders if o.side.name == "BUY"]
        sell_orders = [o for o in filled_orders if o.side.name == "SELL"]
        
        print(f"买单成交: {len(buy_orders)}")
        print(f"卖单成交: {len(sell_orders)}")
        
        if buy_orders:
            avg_buy_price = sum(float(o.avg_px) for o in buy_orders) / len(buy_orders)
            print(f"平均买入价格: ${avg_buy_price:.2f}")
            
        if sell_orders:
            avg_sell_price = sum(float(o.avg_px) for o in sell_orders) / len(sell_orders)
            print(f"平均卖出价格: ${avg_sell_price:.2f}")
    
    # 计算时间相关指标
    duration = (end_time - start_time).total_seconds() / 3600
    print(f"\n回测时长: {duration:.1f} 小时")
    
    if duration > 0:
        hourly_return = ((ending_balance / starting_balance) ** (1 / duration) - 1) * 100
        print(f"小时收益率: {hourly_return:.4f}%")
    
    # 清理
    engine.dispose()
    print("\n✅ 回测完成!")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="使用真实历史数据进行回测")
    parser.add_argument(
        "--data",
        type=str,
        default="nautilus_data/historical/BTCUSDT_quotes.csv",
        help="历史数据文件路径"
    )
    
    args = parser.parse_args()
    
    # 运行回测
    run_backtest_with_real_data(args.data)


if __name__ == "__main__":
    main()