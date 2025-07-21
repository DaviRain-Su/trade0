# NautilusTrader 量化交易系统项目

## 项目概述

这是一个基于 NautilusTrader 的量化交易系统项目，旨在构建一个模块化、可扩展的自动化交易平台。项目首先实现网格交易策略，后续将扩展更多策略类型。

### 项目目标

1. **短期目标**（1-2个月）
   - 实现稳定的网格交易策略
   - 支持 Bybit 交易所的永续合约和现货交易
   - 完善的风险管理和仓位控制
   - 实时监控和报警系统

2. **中期目标**（3-6个月）
   - 添加更多交易策略（趋势跟踪、套利等）
   - 支持多交易所（Binance、OKX 等）
   - 策略回测和优化框架
   - Web 管理界面

3. **长期目标**（6-12个月）
   - 机器学习驱动的策略
   - 分布式架构支持
   - 策略市场和社区

## 技术架构

### 核心技术栈

- **交易框架**: NautilusTrader 1.219.0
- **编程语言**: Python 3.11+
- **数据存储**: PostgreSQL (时序数据)，Redis (缓存)
- **消息队列**: RabbitMQ / Kafka
- **监控**: Grafana + Prometheus
- **部署**: Docker + Kubernetes

### 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Web Dashboard                           │
├─────────────────────────────────────────────────────────────┤
│                    Strategy Manager                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │Grid Strategy│  │Trend Strategy│  │ Arbitrage  │  ...    │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│                  NautilusTrader Core                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │Data Engine│  │Risk Engine│  │Exec Engine│  │ Portfolio │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
├─────────────────────────────────────────────────────────────┤
│                 Exchange Adapters                            │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐      │
│  │  Bybit  │  │ Binance │  │   OKX   │  │   ...   │      │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## 网格交易策略设计

### 策略原理

网格交易是一种在震荡市场中获利的策略，通过在预设的价格网格上下单，低买高卖赚取差价。

### 核心参数

```python
class GridStrategyConfig:
    # 交易对配置
    symbol: str = "BTCUSDT"
    exchange: str = "BYBIT"
    product_type: str = "LINEAR"  # LINEAR/SPOT
    
    # 网格参数
    grid_levels: int = 20          # 网格数量
    grid_spacing: float = 0.005    # 网格间距（百分比）
    
    # 价格范围
    upper_price: float = 50000     # 网格上限
    lower_price: float = 40000     # 网格下限
    
    # 资金管理
    total_amount: float = 10000    # 总投资额
    per_grid_amount: float = None  # 每格投资额（自动计算）
    
    # 风险控制
    stop_loss: float = 0.10        # 止损百分比
    take_profit: float = 0.30      # 止盈百分比
    max_positions: int = 10        # 最大持仓数
    
    # 执行参数
    order_type: str = "LIMIT"      # 订单类型
    time_in_force: str = "GTC"     # 订单有效期
```

### 策略逻辑

1. **初始化网格**
   - 计算网格价格点位
   - 分配每格资金
   - 设置初始订单

2. **订单管理**
   - 价格下跌时买入
   - 价格上涨时卖出
   - 成交后立即下反向订单

3. **风险控制**
   - 总仓位限制
   - 单网格亏损限制
   - 市场趋势检测

## 项目结构

```
trade0/
├── CLAUDE.md                  # 项目文档
├── README.md                  # 用户文档
├── requirements.txt           # 项目依赖
├── .env.example              # 环境变量示例
├── config/                   # 配置文件
│   ├── strategies/          # 策略配置
│   │   ├── grid.yaml
│   │   └── trend.yaml
│   └── exchanges/           # 交易所配置
│       ├── bybit.yaml
│       └── binance.yaml
├── src/                     # 源代码
│   ├── strategies/         # 策略实现
│   │   ├── base.py        # 基础策略类
│   │   ├── grid.py        # 网格策略
│   │   └── trend.py       # 趋势策略
│   ├── risk/              # 风险管理
│   │   ├── position.py    # 仓位管理
│   │   └── limits.py      # 限制管理
│   ├── utils/             # 工具函数
│   │   ├── indicators.py  # 技术指标
│   │   └── helpers.py     # 辅助函数
│   └── monitoring/        # 监控模块
│       ├── alerts.py      # 报警系统
│       └── metrics.py     # 性能指标
├── tests/                  # 测试代码
│   ├── unit/              # 单元测试
│   ├── integration/       # 集成测试
│   └── backtest/          # 回测脚本
├── scripts/               # 运维脚本
│   ├── deploy.sh         # 部署脚本
│   └── monitor.sh        # 监控脚本
└── notebooks/            # Jupyter notebooks
    ├── strategy_analysis.ipynb
    └── backtest_results.ipynb
```

## 开发计划

### Phase 1: 基础网格策略（第1-2周）

- [ ] 实现基础网格策略类
- [ ] 添加订单管理逻辑
- [ ] 实现资金分配算法
- [ ] 编写单元测试

### Phase 2: 风险管理（第3-4周）

- [ ] 实现仓位管理器
- [ ] 添加止损止盈逻辑
- [ ] 实现最大回撤控制
- [ ] 添加紧急停止机制

### Phase 3: 回测优化（第5-6周）

- [ ] 构建回测框架
- [ ] 实现参数优化器
- [ ] 生成回测报告
- [ ] 性能分析工具

### Phase 4: 实盘部署（第7-8周）

- [ ] 配置生产环境
- [ ] 实现监控告警
- [ ] 部署到云服务器
- [ ] 性能调优

## 网格策略实现示例

```python
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.model.enums import OrderSide, OrderType
from nautilus_trader.model.objects import Price, Quantity
import numpy as np


class GridStrategy(Strategy):
    """
    网格交易策略
    在预设的价格网格上自动买卖
    """
    
    def __init__(self, config: GridStrategyConfig):
        super().__init__(config)
        self.config = config
        
        # 计算网格价格
        self.grid_prices = self._calculate_grid_prices()
        self.grid_orders = {}  # 网格订单追踪
        self.filled_grids = set()  # 已成交的网格
        
    def _calculate_grid_prices(self):
        """计算网格价格点位"""
        return np.linspace(
            self.config.lower_price,
            self.config.upper_price,
            self.config.grid_levels
        )
        
    def on_start(self):
        """策略启动时初始化网格"""
        self.log.info(f"启动网格策略: {self.config.symbol}")
        self.log.info(f"网格范围: {self.config.lower_price} - {self.config.upper_price}")
        self.log.info(f"网格数量: {self.config.grid_levels}")
        
        # 获取当前价格
        # 根据当前价格设置初始订单
        self._setup_initial_orders()
        
    def _setup_initial_orders(self):
        """设置初始网格订单"""
        # 实现初始订单逻辑
        pass
        
    def on_order_filled(self, event):
        """订单成交后立即下反向订单"""
        # 实现订单成交逻辑
        pass
```

## 配置管理

### 策略配置示例 (config/strategies/grid.yaml)

```yaml
grid_strategy:
  # 交易配置
  trading:
    symbol: "BTCUSDT"
    exchange: "BYBIT"
    product_type: "LINEAR"
    
  # 网格参数
  grid:
    levels: 20
    spacing_type: "arithmetic"  # arithmetic/geometric
    spacing_value: 100  # 价格间距（USDT）
    
  # 价格范围
  price_range:
    upper: 50000
    lower: 40000
    auto_adjust: true  # 自动调整范围
    
  # 资金管理
  capital:
    total_amount: 10000
    reserve_ratio: 0.1  # 保留资金比例
    
  # 风险参数
  risk:
    max_positions: 10
    stop_loss: 0.10
    take_profit: 0.30
    max_drawdown: 0.20
```

## 监控和告警

### 关键指标

1. **策略性能**
   - PnL（盈亏）
   - 胜率
   - 夏普比率
   - 最大回撤

2. **系统健康**
   - API 延迟
   - 订单执行率
   - 内存/CPU 使用率
   - 错误率

3. **市场状态**
   - 波动率
   - 成交量
   - 价格偏离度

### 告警规则

```python
alerts = {
    "drawdown_alert": {
        "condition": "drawdown > 15%",
        "action": "email + telegram",
        "severity": "high"
    },
    "api_error": {
        "condition": "error_rate > 5%",
        "action": "telegram",
        "severity": "medium"
    },
    "position_limit": {
        "condition": "positions >= max_positions",
        "action": "log + email",
        "severity": "low"
    }
}
```

## 部署指南

### 开发环境

```bash
# 克隆项目
git clone <repository>
cd trade0

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件
```

### 生产环境

```bash
# 使用 Docker
docker build -t nautilus-grid .
docker run -d --name grid-bot nautilus-grid

# 使用 Docker Compose
docker-compose up -d

# 监控日志
docker logs -f grid-bot
```

## 安全考虑

1. **API 密钥管理**
   - 使用环境变量
   - 限制 API 权限
   - 定期轮换密钥

2. **资金安全**
   - 设置提币白名单
   - 使用子账户交易
   - 限制最大仓位

3. **系统安全**
   - 使用 VPN/专线
   - 启用双因素认证
   - 定期安全审计

## 常见问题

### Q: 网格策略适合什么市场？
A: 网格策略最适合震荡市场，在单边趋势市场中可能会产生较大亏损。

### Q: 如何选择网格参数？
A: 可以通过历史数据回测，结合市场波动率和资金量来优化参数。

### Q: 如何处理极端行情？
A: 设置严格的止损，使用断路器机制，在极端行情时自动停止策略。

## 联系和支持

- 项目维护者: [你的名字]
- Email: [你的邮箱]
- Discord: [Discord 链接]

## 更新日志

### 2024-01-21
- 初始化项目结构
- 完成 NautilusTrader 集成
- 实现基础回测功能

### 计划更新
- 网格策略核心逻辑
- 风险管理模块
- Web 管理界面