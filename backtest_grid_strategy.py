#!/usr/bin/env python3
"""
网格策略回测脚本
Grid Strategy Backtesting Script
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from decimal import Decimal

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig
from nautilus_trader.config import LoggingConfig
from nautilus_trader.model.currencies import USD
from nautilus_trader.model.enums import AccountType, OmsType
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.model.objects import Money
from nautilus_trader.test_kit.stubs.data import TestInstrumentProvider

from src.strategies.grid import GridStrategy, GridStrategyConfig


def run_grid_backtest():
    """运行网格策略回测"""
    print("=== 网格策略回测 ===\n")
    
    # 1. 创建回测引擎
    config = BacktestEngineConfig(
        logging=LoggingConfig(log_level="INFO"),
    )
    engine = BacktestEngine(config=config)
    
    # 2. 创建交易工具（使用BTC/USDT作为示例）
    instrument = TestInstrumentProvider.btcusdt_binance()
    venue = instrument.id.venue
    
    # 3. 添加交易场所
    engine.add_venue(
        venue=venue,
        oms_type=OmsType.NETTING,  # 单向持仓
        account_type=AccountType.MARGIN,
        base_currency=USD,
        starting_balances=[Money(100_000, USD)],  # 10万美元初始资金
    )
    
    # 4. 添加交易工具
    engine.add_instrument(instrument)
    
    # 5. 加载历史数据（使用之前准备的数据）
    print("加载历史数据...")
    # 这里应该加载实际的历史数据
    # 暂时使用之前的方法生成模拟数据
    from prepare_data import generate_forex_data
    _, df = generate_forex_data(symbol="BTCUSDT", days=1)  # 使用1天数据进行快速测试
    
    # 将数据转换为QuoteTick格式
    from nautilus_trader.model.data import QuoteTick
    from nautilus_trader.model.objects import Price, Quantity
    
    ticks = []
    for _, row in df.iterrows():
        tick = QuoteTick(
            instrument_id=instrument.id,
            bid_price=Price.from_str(f"{row['bid_price']:.2f}"),  # BTC uses 2 decimal places
            ask_price=Price.from_str(f"{row['ask_price']:.2f}"),  # BTC uses 2 decimal places
            bid_size=Quantity.from_str(f"{row['bid_size']:.6f}"),  # BTC uses 6 decimal places for size
            ask_size=Quantity.from_str(f"{row['ask_size']:.6f}"),  # BTC uses 6 decimal places for size
            ts_event=row.name.value,  # 使用index作为时间戳
            ts_init=row.name.value,
        )
        ticks.append(tick)
    
    engine.add_data(ticks[:10000])  # 只使用前10000个数据点测试
    print(f"加载了 {len(ticks[:10000])} 个数据点")
    
    # 6. 创建网格策略
    strategy_config = GridStrategyConfig(
        instrument_id=str(instrument.id),
        
        # 网格参数
        grid_levels=10,  # 简化为10个网格
        grid_spacing_type="arithmetic",
        grid_spacing=0.005,
        
        # 价格范围（基于BTC数据调整）
        upper_price=43000.0,
        lower_price=41000.0,
        
        # 资金管理
        total_amount=10000.0,  # 1万美元
        base_currency_ratio=0.5,
        
        # 风险控制
        max_positions=10,
        stop_loss_ratio=0.10,
        take_profit_ratio=0.20,
    )
    
    strategy = GridStrategy(config=strategy_config)
    engine.add_strategy(strategy=strategy)
    
    # 7. 运行回测
    start = df.index[0]
    end = df.index[min(9999, len(df)-1)]
    
    print(f"\n运行回测: {start} 到 {end}")
    engine.run(start=start, end=end)
    
    # 8. 分析结果
    print("\n=== 回测结果 ===")
    
    # 账户信息
    account = engine.portfolio.account(venue)
    starting_balance = 100_000
    ending_balance = float(account.balance_total(USD).as_decimal())
    
    print(f"初始资金: ${starting_balance:,.2f}")
    print(f"最终资金: ${ending_balance:,.2f}")
    print(f"总收益: ${ending_balance - starting_balance:,.2f}")
    print(f"收益率: {((ending_balance / starting_balance) - 1) * 100:.2f}%")
    
    # 交易统计
    positions = engine.cache.positions()
    orders = engine.cache.orders()
    
    print(f"\n交易统计:")
    print(f"总订单数: {len(orders)}")
    print(f"总持仓数: {len(positions)}")
    
    # 计算其他指标
    if len(positions) > 0:
        # 计算胜率
        winning_positions = [p for p in positions if p.realized_pnl > Money(0, USD)]
        win_rate = len(winning_positions) / len(positions) * 100
        
        # 计算平均盈亏
        total_pnl = sum([float(p.realized_pnl.as_decimal()) for p in positions])
        avg_pnl = total_pnl / len(positions)
        
        print(f"胜率: {win_rate:.2f}%")
        print(f"平均盈亏: ${avg_pnl:.2f}")
        
        # 最大单笔盈利/亏损
        pnls = [float(p.realized_pnl.as_decimal()) for p in positions]
        if pnls:
            print(f"最大盈利: ${max(pnls):.2f}")
            print(f"最大亏损: ${min(pnls):.2f}")
    
    # 清理
    engine.dispose()
    print("\n✅ 回测完成!")


def analyze_grid_performance(engine: BacktestEngine):
    """分析网格策略性能"""
    # TODO: 实现更详细的性能分析
    # - 夏普比率
    # - 最大回撤
    # - 盈亏比
    # - 月度收益
    pass


if __name__ == "__main__":
    # 检查依赖
    try:
        from prepare_data import generate_forex_data
    except ImportError:
        print("错误: 需要 prepare_data.py 文件来生成数据")
        print("请确保已运行: python prepare_data.py")
        sys.exit(1)
        
    # 运行回测
    run_grid_backtest()