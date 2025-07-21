# 项目结构改进建议

## 当前结构分析

当前项目已经有了基本的结构，但仍有一些文件散落在根目录。以下是改进建议：

## 建议的项目结构

```
trade0/                              # 项目根目录
├── README.md                        # 项目说明
├── CLAUDE.md                        # 项目文档（AI助手参考）
├── PROJECT_STRUCTURE.md             # 项目结构说明（本文件）
├── pyproject.toml                   # Python项目配置
├── uv.lock                          # 依赖锁定文件
├── .env.example                     # 环境变量示例
├── .gitignore                       # Git忽略文件
│
├── src/                             # 源代码目录
│   ├── __init__.py
│   ├── strategies/                  # 策略实现
│   │   ├── __init__.py
│   │   ├── base.py                 # 策略基类
│   │   ├── grid.py                 # 网格策略
│   │   └── simple_grid.py          # 简化网格策略
│   ├── data/                        # 数据处理模块
│   │   ├── __init__.py
│   │   ├── downloader.py           # 数据下载器
│   │   └── converter.py            # 数据转换器
│   ├── backtest/                    # 回测模块
│   │   ├── __init__.py
│   │   ├── engine.py               # 回测引擎封装
│   │   └── analyzer.py             # 结果分析器
│   ├── live/                        # 实盘交易模块
│   │   ├── __init__.py
│   │   └── runner.py               # 策略运行器
│   ├── risk/                        # 风险管理
│   │   ├── __init__.py
│   │   └── manager.py              # 风险管理器
│   ├── monitoring/                  # 监控模块
│   │   ├── __init__.py
│   │   └── metrics.py              # 指标收集
│   └── utils/                       # 工具函数
│       ├── __init__.py
│       └── helpers.py              # 辅助函数
│
├── config/                          # 配置文件
│   ├── exchanges/                   # 交易所配置
│   │   ├── bybit.yaml
│   │   └── binance.yaml
│   └── strategies/                  # 策略配置
│       ├── grid_btcusdt.yaml
│       └── grid_ethusdt.yaml
│
├── scripts/                         # 可执行脚本
│   ├── download_data.py            # 数据下载脚本
│   ├── run_backtest.py             # 回测运行脚本
│   ├── run_live.py                 # 实盘运行脚本
│   └── setup_project.sh            # 项目设置脚本
│
├── tests/                           # 测试代码
│   ├── __init__.py
│   ├── unit/                        # 单元测试
│   │   ├── __init__.py
│   │   └── test_strategies.py
│   ├── integration/                 # 集成测试
│   │   ├── __init__.py
│   │   └── test_backtest.py
│   └── fixtures/                    # 测试数据
│       └── sample_data.csv
│
├── data/                            # 数据存储
│   ├── historical/                  # 历史数据
│   ├── cache/                       # 缓存数据
│   └── results/                     # 回测结果
│
├── logs/                            # 日志文件
│   ├── backtest/                    # 回测日志
│   └── live/                        # 实盘日志
│
├── notebooks/                       # Jupyter笔记本
│   ├── strategy_analysis.ipynb     # 策略分析
│   └── data_exploration.ipynb      # 数据探索
│
└── docs/                            # 文档
    ├── api/                         # API文档
    ├── guides/                      # 使用指南
    └── development/                 # 开发文档
```

## 需要进行的重构

### 1. 移动文件到合适的位置

```bash
# 创建新目录
mkdir -p src/data src/backtest src/live scripts/legacy

# 移动数据下载相关文件
mv download_*.py src/data/
mv prepare_data.py src/data/

# 移动回测相关文件
mv backtest_*.py simple_grid_backtest.py src/backtest/
mv complete_backtest.py src/backtest/

# 移动实盘运行相关文件
mv run_grid_strategy.py src/live/
mv bybit_*.py src/live/

# 移动到scripts目录
mv setup_project.sh scripts/
```

### 2. 创建缺失的模块

#### src/strategies/base.py
```python
"""策略基类"""
from abc import ABC, abstractmethod
from nautilus_trader.trading.strategy import Strategy

class BaseGridStrategy(Strategy, ABC):
    """网格策略基类"""
    
    @abstractmethod
    def calculate_grid_levels(self):
        """计算网格价位"""
        pass
    
    @abstractmethod
    def place_grid_orders(self):
        """放置网格订单"""
        pass
```

#### src/data/downloader.py
```python
"""数据下载器统一接口"""
from abc import ABC, abstractmethod
import pandas as pd

class DataDownloader(ABC):
    """数据下载器基类"""
    
    @abstractmethod
    def download(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """下载历史数据"""
        pass

class CryptoCompareDownloader(DataDownloader):
    """CryptoCompare数据下载器"""
    # 实现代码...

class BybitDownloader(DataDownloader):
    """Bybit数据下载器"""
    # 实现代码...
```

#### src/backtest/engine.py
```python
"""回测引擎封装"""
from nautilus_trader.backtest.engine import BacktestEngine
from typing import Dict, Any

class GridBacktestEngine:
    """网格策略回测引擎"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.engine = None
        
    def setup(self):
        """设置回测环境"""
        pass
        
    def run(self, data, strategy):
        """运行回测"""
        pass
        
    def analyze_results(self):
        """分析回测结果"""
        pass
```

### 3. 配置文件管理

创建统一的配置加载器：

#### src/utils/config_loader.py
```python
"""配置文件加载器"""
import yaml
from pathlib import Path
from typing import Dict, Any

class ConfigLoader:
    """配置加载器"""
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        
    def load_strategy_config(self, name: str) -> Dict[str, Any]:
        """加载策略配置"""
        path = self.config_dir / "strategies" / f"{name}.yaml"
        with open(path, 'r') as f:
            return yaml.safe_load(f)
            
    def load_exchange_config(self, name: str) -> Dict[str, Any]:
        """加载交易所配置"""
        path = self.config_dir / "exchanges" / f"{name}.yaml"
        with open(path, 'r') as f:
            return yaml.safe_load(f)
```

### 4. 创建主入口脚本

#### scripts/run_backtest.py
```python
#!/usr/bin/env python3
"""统一的回测运行脚本"""
import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.backtest.engine import GridBacktestEngine
from src.utils.config_loader import ConfigLoader

def main():
    parser = argparse.ArgumentParser(description="运行策略回测")
    parser.add_argument("--strategy", required=True, help="策略配置名称")
    parser.add_argument("--data", required=True, help="数据文件路径")
    args = parser.parse_args()
    
    # 加载配置
    config_loader = ConfigLoader(Path("config"))
    strategy_config = config_loader.load_strategy_config(args.strategy)
    
    # 运行回测
    engine = GridBacktestEngine(strategy_config)
    engine.setup()
    # ... 运行逻辑
    
if __name__ == "__main__":
    main()
```

## 实施步骤

1. **备份当前代码**
   ```bash
   git add .
   git commit -m "备份：重构前的代码"
   ```

2. **创建新的目录结构**
   ```bash
   bash scripts/reorganize_project.sh
   ```

3. **逐步移动和重构代码**
   - 先移动独立的模块
   - 更新导入路径
   - 运行测试确保功能正常

4. **更新文档**
   - 更新README.md
   - 更新CLAUDE.md中的文件路径引用

5. **添加测试**
   - 为每个模块添加单元测试
   - 添加集成测试

## 优势

1. **更清晰的代码组织**
   - 相关功能聚合在一起
   - 易于查找和维护

2. **更好的可扩展性**
   - 模块化设计便于添加新策略
   - 易于添加新的数据源和交易所

3. **更专业的项目结构**
   - 符合Python项目最佳实践
   - 便于团队协作

4. **更容易测试**
   - 清晰的模块边界
   - 便于编写单元测试

是否需要我帮你实施这个重构计划？