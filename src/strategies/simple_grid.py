#!/usr/bin/env python3
"""
极简网格交易策略
Minimal Grid Trading Strategy for Testing
"""

from decimal import Decimal
from typing import Optional, Dict, List
import numpy as np

from nautilus_trader.config import StrategyConfig
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.enums import OrderSide, OrderType, TimeInForce
from nautilus_trader.model.objects import Price, Quantity
from nautilus_trader.model.events import OrderFilled


class SimpleGridStrategyConfig(StrategyConfig):
    """极简网格策略配置"""
    instrument_id: str
    total_amount: float
    upper_price: float
    lower_price: float
    grid_levels: int = 5


class SimpleGridStrategy(Strategy):
    """
    极简网格交易策略
    只在初始化时下单，不进行复杂的订单管理
    """
    
    def __init__(self, config: SimpleGridStrategyConfig):
        super().__init__(config)
        
        self.instrument_id = InstrumentId.from_str(config.instrument_id)
        self.total_amount = Decimal(str(config.total_amount))
        self.grid_levels = config.grid_levels
        self.upper_price = config.upper_price
        self.lower_price = config.lower_price
        
        # 网格价格
        self.grid_prices: List[float] = []
        self.orders_placed = False
        
    def on_start(self):
        """策略启动"""
        self.log.info(f"极简网格策略启动: {self.instrument_id}")
        self.log.info(f"网格数量: {self.grid_levels}")
        self.log.info(f"价格范围: {self.lower_price} - {self.upper_price}")
        
        # 订阅市场数据
        self.subscribe_quote_ticks(self.instrument_id)
        
        # 计算网格价格
        self.grid_prices = np.linspace(
            self.lower_price,
            self.upper_price,
            self.grid_levels
        ).tolist()
        
    def on_quote_tick(self, tick):
        """处理报价"""
        # 只在第一次收到报价时下单
        if not self.orders_placed:
            self.orders_placed = True
            self._place_initial_orders(tick)
            
    def _place_initial_orders(self, tick):
        """放置初始订单"""
        current_price = float(tick.ask_price.as_decimal() + tick.bid_price.as_decimal()) / 2
        self.log.info(f"当前价格: {current_price:.2f}, 开始放置网格订单")
        
        # 每个网格的投资额
        amount_per_grid = float(self.total_amount) / self.grid_levels
        
        placed_count = 0
        for grid_price in self.grid_prices:
            # 跳过太接近当前价格的网格
            if abs(grid_price - current_price) < 10:  # 10 USDT的缓冲区
                continue
                
            if grid_price < current_price:
                # 在当前价格下方放置买单
                quantity = amount_per_grid / grid_price
                order = self.order_factory.limit(
                    instrument_id=self.instrument_id,
                    order_side=OrderSide.BUY,
                    quantity=Quantity.from_str(f"{quantity:.6f}"),
                    price=Price.from_str(f"{grid_price:.2f}"),
                    time_in_force=TimeInForce.GTC,
                    post_only=False,  # 不使用POST_ONLY避免被拒绝
                )
                self.submit_order(order)
                placed_count += 1
                self.log.info(f"下买单: {quantity:.6f} @ {grid_price:.2f}")
                
        self.log.info(f"初始订单放置完成，共 {placed_count} 个订单")
        
    def on_order_filled(self, event: OrderFilled):
        """订单成交处理"""
        self.log.info(
            f"订单成交: {event.order_side.name} "
            f"{event.last_qty} @ {event.last_px}"
        )
        # 简单策略不做任何后续操作
        
    def on_stop(self):
        """策略停止"""
        self.log.info("极简网格策略停止")
        self.cancel_all_orders(self.instrument_id)
        
    def reset(self):
        """重置策略"""
        super().reset()
        self.orders_placed = False