#!/usr/bin/env python3
"""
网格交易策略运行脚本
Grid Trading Strategy Runner
"""

import os
import sys
import asyncio
import yaml
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from nautilus_trader.config import TradingNodeConfig
from nautilus_trader.live.node import TradingNode
from nautilus_trader.adapters.bybit.common.enums import BybitProductType

from src.strategies.grid import GridStrategy, GridStrategyConfig


# 加载环境变量
load_dotenv()


def load_strategy_config(config_path: str) -> dict:
    """加载策略配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def create_grid_strategy_config(yaml_config: dict) -> GridStrategyConfig:
    """从YAML配置创建策略配置对象"""
    trading = yaml_config['trading']
    grid = yaml_config['grid']
    price_range = yaml_config['price_range']
    capital = yaml_config['capital']
    order = yaml_config['order']
    risk = yaml_config['risk']
    
    return GridStrategyConfig(
        instrument_id=trading['instrument_id'],
        
        # 网格参数
        grid_levels=grid['levels'],
        grid_spacing_type=grid['spacing_type'],
        grid_spacing=grid['spacing'],
        
        # 价格范围
        upper_price=price_range['upper_price'],
        lower_price=price_range['lower_price'],
        price_range_ratio=price_range['range_ratio'],
        
        # 资金管理
        total_amount=capital['total_amount'],
        base_currency_ratio=capital['base_currency_ratio'],
        
        # 风险控制
        max_positions=risk['max_positions'],
        stop_loss_ratio=risk['stop_loss_ratio'],
        take_profit_ratio=risk['take_profit_ratio'],
    )


def create_trading_node_config(
    strategy_config: GridStrategyConfig,
    testnet: bool = True
) -> TradingNodeConfig:
    """创建交易节点配置"""
    
    # 获取API密钥
    if testnet:
        api_key = os.getenv("BYBIT_TESTNET_API_KEY", "")
        api_secret = os.getenv("BYBIT_TESTNET_API_SECRET", "")
    else:
        api_key = os.getenv("BYBIT_API_KEY", "")
        api_secret = os.getenv("BYBIT_API_SECRET", "")
        
    if not api_key or not api_secret:
        raise ValueError("请设置 Bybit API 密钥环境变量")
        
    # 确定产品类型
    product_types = []
    if "LINEAR" in strategy_config.instrument_id:
        product_types.append(BybitProductType.LINEAR)
    if "SPOT" in strategy_config.instrument_id:
        product_types.append(BybitProductType.SPOT)
        
    return TradingNodeConfig(
        trader_id=f"GRID-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        
        logging={
            "log_level": "INFO",
            "log_to_file": True,
            "log_file_path": f"logs/grid_{datetime.now().strftime('%Y%m%d')}.log",
        },
        
        data_clients={
            "BYBIT": {
                "api_key": api_key,
                "api_secret": api_secret,
                "testnet": testnet,
                "product_types": product_types,
            },
        },
        
        exec_clients={
            "BYBIT": {
                "api_key": api_key,
                "api_secret": api_secret,
                "testnet": testnet,
                "product_types": product_types,
            },
        },
        
        strategies=[strategy_config],
    )


async def run_grid_strategy(config_path: str, testnet: bool = True):
    """运行网格策略"""
    print(f"\n{'='*60}")
    print(f"网格交易策略启动器")
    print(f"{'='*60}")
    print(f"配置文件: {config_path}")
    print(f"使用{'测试网' if testnet else '主网'}")
    print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # 加载配置
    yaml_config = load_strategy_config(config_path)
    strategy_name = yaml_config['strategy']['name']
    
    print(f"策略名称: {strategy_name}")
    print(f"交易对: {yaml_config['trading']['instrument_id']}")
    print(f"网格数量: {yaml_config['grid']['levels']}")
    print(f"投资金额: {yaml_config['capital']['total_amount']} USDT")
    
    # 创建策略配置
    strategy_config = create_grid_strategy_config(yaml_config)
    
    # 创建交易节点配置
    node_config = create_trading_node_config(strategy_config, testnet)
    
    # 创建并运行交易节点
    try:
        print("\n正在初始化交易节点...")
        node = TradingNode(config=node_config)
        
        print("连接到交易所...")
        print("\n策略开始运行，按 Ctrl+C 停止\n")
        
        # 运行节点
        await node.run_async()
        
    except KeyboardInterrupt:
        print("\n\n接收到停止信号，正在安全关闭...")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n策略已停止")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="运行网格交易策略")
    parser.add_argument(
        "--config",
        type=str,
        default="config/strategies/grid_btcusdt.yaml",
        help="策略配置文件路径"
    )
    parser.add_argument(
        "--testnet",
        action="store_true",
        default=True,
        help="使用测试网（默认）"
    )
    parser.add_argument(
        "--mainnet",
        action="store_true",
        help="使用主网（谨慎使用）"
    )
    
    args = parser.parse_args()
    
    # 确定使用测试网还是主网
    use_testnet = not args.mainnet
    
    if not use_testnet:
        print("\n⚠️  警告: 您即将在主网运行策略，这将使用真实资金！")
        confirm = input("确认继续？(yes/no): ")
        if confirm.lower() != "yes":
            print("已取消")
            return
            
    # 检查配置文件
    if not os.path.exists(args.config):
        print(f"错误: 配置文件不存在: {args.config}")
        return
        
    # 创建日志目录
    os.makedirs("logs", exist_ok=True)
    
    # 运行策略
    asyncio.run(run_grid_strategy(args.config, use_testnet))


if __name__ == "__main__":
    main()