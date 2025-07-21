#!/usr/bin/env python3
"""
网格交易策略实现
Grid Trading Strategy Implementation
"""

from decimal import Decimal
from typing import Optional, Dict, List, Set
import numpy as np
from datetime import timedelta

from nautilus_trader.config import StrategyConfig
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.enums import OrderSide, OrderType, TimeInForce
from nautilus_trader.model.objects import Price, Quantity
from nautilus_trader.model.events import OrderFilled


class GridStrategyConfig(StrategyConfig):
    """网格策略配置"""
    
    # 交易对配置
    instrument_id: str
    
    # 资金管理 (required fields first)
    total_amount: float                   # 总投资额
    
    # 网格参数
    grid_levels: int = 20                # 网格数量
    grid_spacing_type: str = "arithmetic" # arithmetic/geometric
    grid_spacing: float = 0.005          # 网格间距（百分比）
    
    # 价格范围
    upper_price: Optional[float] = None  # 网格上限（None表示自动计算）
    lower_price: Optional[float] = None  # 网格下限（None表示自动计算）
    price_range_ratio: float = 0.1       # 自动计算时的价格范围比例
    
    # 资金管理 (optional)
    base_currency_ratio: float = 0.5      # 基础货币占比（用于初始买入）
    
    # 订单设置
    order_type: OrderType = OrderType.LIMIT
    time_in_force: TimeInForce = TimeInForce.GTC
    post_only: bool = True               # 只做Maker
    
    # 风险控制
    max_positions: int = 20              # 最大持仓网格数
    stop_loss_ratio: float = 0.15        # 止损比例
    take_profit_ratio: float = 0.30      # 止盈比例
    enable_trailing_stop: bool = False   # 是否启用移动止损
    
    # 执行控制
    min_profit_ratio: float = 0.002      # 最小利润率（扣除手续费）
    rebalance_threshold: float = 0.05    # 再平衡阈值


class GridStrategy(Strategy):
    """
    网格交易策略
    
    特点：
    1. 在预设价格网格上自动下单
    2. 低买高卖，赚取网格利润
    3. 适合震荡市场
    4. 自动再平衡
    """
    
    def __init__(self, config: GridStrategyConfig):
        super().__init__(config)
        
        # 策略配置
        self.instrument_id = InstrumentId.from_str(config.instrument_id)
        self.grid_levels = config.grid_levels
        self.grid_spacing_type = config.grid_spacing_type
        self.grid_spacing = config.grid_spacing
        
        # 价格范围
        self.upper_price = config.upper_price
        self.lower_price = config.lower_price
        self.price_range_ratio = config.price_range_ratio
        
        # 资金管理
        self.total_amount = Decimal(str(config.total_amount))
        self.base_currency_ratio = config.base_currency_ratio
        
        # 订单设置
        self.order_type = config.order_type
        self.time_in_force = config.time_in_force
        self.post_only = config.post_only
        
        # 风险控制
        self.max_positions = config.max_positions
        self.stop_loss_ratio = config.stop_loss_ratio
        self.take_profit_ratio = config.take_profit_ratio
        
        # 内部状态
        self.grid_prices: List[float] = []          # 网格价格列表
        self.grid_orders: Dict[float, str] = {}     # 价格 -> 订单ID映射
        self.filled_grids: Set[float] = set()       # 已成交的网格价格
        self.active_orders: Dict[str, float] = {}   # 订单ID -> 价格映射
        
        # 统计信息
        self.total_trades = 0
        self.winning_trades = 0
        self.total_pnl = Decimal("0")
        
    def on_start(self):
        """策略启动初始化"""
        self.log.info("=" * 50)
        self.log.info(f"网格策略启动: {self.instrument_id}")
        self.log.info(f"网格数量: {self.grid_levels}")
        self.log.info(f"总资金: {self.total_amount}")
        self.log.info("=" * 50)
        
        # 订阅市场数据
        self.subscribe_quote_ticks(self.instrument_id)
        self.subscribe_trade_ticks(self.instrument_id)
        
        # 延迟初始化网格（等待市场数据）
        self.clock.set_timer(
            name="init_grid",
            interval=timedelta(seconds=2),  # 2秒后
            callback=self._initialize_grid,
        )
        
    def _initialize_grid(self, event):
        """初始化网格"""
        # 获取当前价格
        last_quote = self.cache.quote_tick(self.instrument_id)
        if not last_quote:
            self.log.error("无法获取当前价格，延迟初始化")
            self.clock.set_timer(
                name="init_grid_retry",
                interval=timedelta(seconds=5),
                callback=self._initialize_grid,
            )
            return
            
        current_price = float(last_quote.ask_price.as_decimal() + last_quote.bid_price.as_decimal()) / 2
        
        # 计算价格范围
        if self.upper_price is None or self.lower_price is None:
            price_range = current_price * self.price_range_ratio
            self.upper_price = current_price + price_range / 2
            self.lower_price = current_price - price_range / 2
            
        self.log.info(f"当前价格: {current_price:.2f}")
        self.log.info(f"网格范围: {self.lower_price:.2f} - {self.upper_price:.2f}")
        
        # 计算网格价格
        self._calculate_grid_prices()
        
        # 设置初始订单
        self._setup_initial_orders(current_price)
        
    def _calculate_grid_prices(self):
        """计算网格价格列表"""
        if self.grid_spacing_type == "arithmetic":
            # 等差网格
            self.grid_prices = np.linspace(
                self.lower_price,
                self.upper_price,
                self.grid_levels
            ).tolist()
        else:
            # 等比网格
            log_lower = np.log(self.lower_price)
            log_upper = np.log(self.upper_price)
            log_prices = np.linspace(log_lower, log_upper, self.grid_levels)
            self.grid_prices = np.exp(log_prices).tolist()
            
        self.log.info(f"网格价格计算完成: {len(self.grid_prices)} 个价格点")
        
    def _setup_initial_orders(self, current_price: float):
        """设置初始网格订单"""
        # 计算每格投资额
        amount_per_grid = float(self.total_amount) / self.grid_levels
        
        buy_orders_placed = 0
        sell_orders_placed = 0
        
        for grid_price in self.grid_prices:
            if abs(grid_price - current_price) / current_price < 0.001:
                # 跳过太接近当前价格的网格
                continue
                
            if grid_price < current_price:
                # 在当前价格下方放置买单
                self._place_grid_order(
                    price=grid_price,
                    side=OrderSide.BUY,
                    amount=amount_per_grid
                )
                buy_orders_placed += 1
                
            elif grid_price > current_price:
                # 在当前价格上方放置卖单
                # 需要先检查是否有足够的基础货币
                # 这里简化处理，实际应该根据持仓计算
                quantity = amount_per_grid / grid_price
                self._place_grid_order(
                    price=grid_price,
                    side=OrderSide.SELL,
                    amount=amount_per_grid
                )
                sell_orders_placed += 1
                
        self.log.info(f"初始订单设置完成: {buy_orders_placed} 买单, {sell_orders_placed} 卖单")
        
    def _place_grid_order(self, price: float, side: OrderSide, amount: float):
        """下网格订单"""
        # 计算订单数量
        quantity = amount / price if side == OrderSide.BUY else amount / price
        
        # 创建订单
        order = self.order_factory.limit(
            instrument_id=self.instrument_id,
            order_side=side,
            quantity=Quantity.from_str(f"{quantity:.6f}"),
            price=Price.from_str(f"{price:.2f}"),
            time_in_force=self.time_in_force,
            post_only=self.post_only,
        )
        
        # 提交订单
        self.submit_order(order)
        
        # 记录订单
        self.grid_orders[price] = order.client_order_id.value
        self.active_orders[order.client_order_id.value] = price
        
        self.log.info(f"下单: {side.name} {quantity:.6f} @ {price:.2f}")
        
    def on_order_filled(self, event: OrderFilled):
        """订单成交处理"""
        # 获取成交价格和信息
        filled_price = float(event.last_px)
        filled_qty = float(event.last_qty)
        order_side = event.order_side
        
        # 移除已成交订单
        if event.client_order_id.value in self.active_orders:
            grid_price = self.active_orders.pop(event.client_order_id.value)
            
            # 更新统计
            self.total_trades += 1
            
            # 下反向订单
            if order_side == OrderSide.BUY:
                # 买单成交，下卖单
                target_price = self._find_next_grid_price(filled_price, direction="up")
                if target_price:
                    self._place_grid_order(
                        price=target_price,
                        side=OrderSide.SELL,
                        amount=filled_qty * target_price
                    )
                    
            else:
                # 卖单成交，下买单
                target_price = self._find_next_grid_price(filled_price, direction="down")
                if target_price:
                    self._place_grid_order(
                        price=target_price,
                        side=OrderSide.BUY,
                        amount=filled_qty * filled_price
                    )
                    
            self.log.info(f"订单成交: {order_side.name} {filled_qty:.6f} @ {filled_price:.2f}")
            
    def _find_next_grid_price(self, current_price: float, direction: str) -> Optional[float]:
        """找到下一个网格价格"""
        if direction == "up":
            # 找到上方最近的网格价格
            for price in self.grid_prices:
                if price > current_price * 1.001 and price not in self.grid_orders:
                    return price
        else:
            # 找到下方最近的网格价格
            for price in reversed(self.grid_prices):
                if price < current_price * 0.999 and price not in self.grid_orders:
                    return price
                    
        return None
        
    def on_quote_tick(self, tick):
        """处理报价更新"""
        # 检查是否需要调整网格范围
        mid_price = float(tick.ask_price.as_decimal() + tick.bid_price.as_decimal()) / 2
        
        if mid_price > self.upper_price * 0.95 or mid_price < self.lower_price * 1.05:
            self.log.warning(f"价格接近网格边界: {mid_price:.2f}")
            # TODO: 实现网格范围自动调整
            
    def on_stop(self):
        """策略停止"""
        self.log.info("=" * 50)
        self.log.info("网格策略停止")
        self.log.info(f"总交易次数: {self.total_trades}")
        self.log.info(f"胜率: {self.winning_trades / max(self.total_trades, 1) * 100:.2f}%")
        self.log.info(f"总盈亏: {self.total_pnl}")
        self.log.info("=" * 50)
        
        # 取消所有未成交订单
        self._cancel_all_orders()
        
    def _cancel_all_orders(self):
        """取消所有未成交订单"""
        # 使用策略的cancel_all_orders方法
        self.cancel_all_orders(self.instrument_id)
            
    def reset(self):
        """重置策略状态"""
        super().reset()
        self.grid_orders.clear()
        self.filled_grids.clear()
        self.active_orders.clear()
        self.total_trades = 0
        self.winning_trades = 0
        self.total_pnl = Decimal("0")