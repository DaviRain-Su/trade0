#!/usr/bin/env python3
"""
简化的网格策略回测
Simplified Grid Strategy Backtest
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from decimal import Decimal

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig
from nautilus_trader.config import LoggingConfig
from nautilus_trader.model.currencies import USDT
from nautilus_trader.model.enums import AccountType, OmsType
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.model.objects import Money
from nautilus_trader.test_kit.stubs.data import TestInstrumentProvider

from src.strategies.simple_grid import SimpleGridStrategy, SimpleGridStrategyConfig


def run_simple_grid_backtest():
    """运行简化的网格策略回测"""
    print("=== 简化网格策略回测 ===\n")
    
    # 1. 创建回测引擎
    config = BacktestEngineConfig(
        logging=LoggingConfig(log_level="WARNING"),  # 减少日志输出
    )
    engine = BacktestEngine(config=config)
    
    # 2. 创建交易工具
    instrument = TestInstrumentProvider.btcusdt_binance()
    venue = instrument.id.venue
    
    # 3. 添加交易场所 - 使用USDT作为基础货币
    engine.add_venue(
        venue=venue,
        oms_type=OmsType.NETTING,
        account_type=AccountType.MARGIN,
        base_currency=USDT,  # 使用USDT而不是USD
        starting_balances=[Money(10_000, USDT)],  # 1万USDT初始资金
    )
    
    # 4. 添加交易工具
    engine.add_instrument(instrument)
    
    # 5. 生成简单的测试数据（只用100个数据点）
    print("生成测试数据...")
    timestamps = pd.date_range(start='2025-01-01', periods=100, freq='1min')
    base_price = 42000.0
    prices = base_price + np.sin(np.linspace(0, 2*np.pi, 100)) * 500  # 价格在41500-42500之间波动
    
    from nautilus_trader.model.data import QuoteTick
    from nautilus_trader.model.objects import Price, Quantity
    
    ticks = []
    for i, ts in enumerate(timestamps):
        tick = QuoteTick(
            instrument_id=instrument.id,
            bid_price=Price.from_str(f"{prices[i] - 1:.2f}"),
            ask_price=Price.from_str(f"{prices[i] + 1:.2f}"),
            bid_size=Quantity.from_str("0.100000"),
            ask_size=Quantity.from_str("0.100000"),
            ts_event=ts.value,
            ts_init=ts.value,
        )
        ticks.append(tick)
    
    engine.add_data(ticks)
    print(f"加载了 {len(ticks)} 个数据点")
    
    # 6. 创建简化的网格策略
    strategy_config = SimpleGridStrategyConfig(
        instrument_id=str(instrument.id),
        total_amount=1000.0,  # 使用1000 USDT
        upper_price=42500.0,
        lower_price=41500.0,
        grid_levels=5,  # 只用5个网格
    )
    
    strategy = SimpleGridStrategy(config=strategy_config)
    engine.add_strategy(strategy=strategy)
    
    # 7. 运行回测
    print(f"\n运行回测: {timestamps[0]} 到 {timestamps[-1]}")
    engine.run(start=timestamps[0], end=timestamps[-1])
    
    # 8. 分析结果
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
    
    print(f"\n交易统计:")
    print(f"总订单数: {len(orders)}")
    print(f"总持仓数: {len(positions)}")
    
    # 显示前几个订单
    if orders:
        print("\n前5个订单:")
        for i, order in enumerate(orders[:5]):
            print(f"  {i+1}. {order.side.name} {order.quantity} @ {order.price}")
    
    # 清理
    engine.dispose()
    print("\n✅ 回测完成!")


if __name__ == "__main__":
    run_simple_grid_backtest()