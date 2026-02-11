# 30周均线交易系统

基于史丹·温斯坦《一条均线定乾坤》（How to Make Money in Stocks）的量化交易系统。

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)
![React](https://img.shields.io/badge/React-18+-61DAFB.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**项目灵感视频**：https://www.bilibili.com/video/BV1twFSzNE75/

## 系统简介

本系统严格遵循史丹·温斯坦的阶段分析法，通过**30周均线**判断股票所处的四个阶段，并结合成交量、大盘趋势等多重因素，生成买入/卖出交易信号。

### 核心设计理念

> "不要试图抄底摸顶，只在第二阶段（上升趋势）买入，在第四阶段（下降趋势）远离。" —— 史丹·温斯坦

## 功能特性

### 核心功能
- **阶段分析引擎**：自动识别股票四个阶段（底部/上升/顶部/下降）
- **买入信号检测**：放量突破 + 30周均线向上 + 大盘配合
- **卖出信号检测**：均线走平/向下、跌破均线、成交量异常
- **风险管理模块**：止损位设置、仓位控制、金字塔加仓法
- **智能提醒系统**：钉钉/飞书webhook实时推送
- **AI分析集成**：OpenAI兼容大模型智能分析
- **Web管理后台**：可视化监控面板

### 技术亮点
- 异步架构，高性能数据处理
- 模块化设计，易于扩展
- RESTful API，支持二次开发
- 响应式Web界面，支持移动端

## 交易规则详解

### 四个阶段识别

```
第一阶段（底部/冬天）
├── 30周均线走平或略微向下
├── 股价在均线上下震荡
├── 成交量萎缩
└── 策略：观察，不买入

第二阶段（上升/春夏）
├── 股价放量突破底部区间
├── 30周均线开始向上
├── 成交量持续放大
└── 策略：买入并持有

第三阶段（顶部/秋天）
├── 30周均线走平
├── 股价震荡，波动加大
├── 成交量不规则
└── 策略：考虑分批卖出

第四阶段（下降/冬天）
├── 30周均线向下
├── 股价在均线下方运行
├── 成交量可能放大（恐慌盘）
└── 策略：远离，不持有
```

### 买入条件（必须同时满足）

| 条件 | 说明 | 权重 |
|------|------|------|
| 阶段突破 | 股价突破第一阶段底部区间 | 必需 |
| 均线方向 | 30周均线向上倾斜 | 必需 |
| 成交量确认 | 突破时成交量放大2倍以上 | 必需 |
| 大盘配合 | 大盘指数也在第二阶段 | 重要 |
| 相对强度 | 相对大盘表现强势 | 加分 |

### 卖出条件（满足任一即卖出）

- 30周均线走平或向下
- 股价跌破30周均线且3周内无法站回
- 成交量异常放大但股价不涨（出货信号）
- 股价达到预设止盈位

### 风险管理规则

```
单笔交易规则：
├── 最大亏损 ≤ 总资金的 2-3%
├── 止损位设置在支撑位下方
├── 止损位只能上移，不能下移
└── 盈利后才考虑加仓

仓位管理：
├── 首次建仓：计划仓位的50%
├── 第一次加仓：盈利5%后，加30%
├── 第二次加仓：盈利10%后，加20%
└── 最多持有 5-10 只股票
```

## 快速开始

### 环境要求

- Python 3.9+
- Node.js 18+ (前端)
- Windows/Linux/macOS

### 1. 克隆项目

```bash
cd d:/www/stock/30zhouxian
git clone <repository-url>
cd 30zhouxian
```

### 2. 安装Python依赖

```bash
cd trading_system
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# ==========================================
# 数据源配置（tdx-api）
# ==========================================
TDX_API_BASE_URL=http://43.138.33.77:8080

# ==========================================
# 钉钉Webhook配置（可选）
# ==========================================
DINGTALK_WEBHOOK_URL=https://oapi.dingtalk.com/robot/send?access_token=your_token
DINGTALK_SECRET=your_secret

# ==========================================
# 飞书Webhook配置（可选）
# ==========================================
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/your_token

# ==========================================
# OpenAI配置（可选）
# ==========================================
OPENAI_API_KEY=your_api_key
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4

# ==========================================
# 股票池配置
# ==========================================
STOCK_POOL=000001,000002,000333,000858,002594,300750,600000,600519,601012,601318

# ==========================================
# 调度配置
# ==========================================
SCHEDULE_DAY=5      # 0=周日, 1-5=周一到周五
SCHEDULE_TIME=15:30

# ==========================================
# 风险控制配置
# ==========================================
MAX_LOSS_PERCENT=2.0        # 单笔最大亏损%
STOP_LOSS_PERCENT=8.0       # 止损比例%
MAX_POSITIONS=10            # 最大持仓数
SINGLE_POSITION_MAX=20.0    # 单股最大仓位%
```

### 4. 启动后端服务

```bash
# 开发模式（自动重载）
cd trading_system
python main.py --serve

# 生产模式
python main.py --serve --host 0.0.0.0 --port 8000
```

### 5. 启动前端界面

```bash
cd trading-dashboard
npm install
npm run dev
```

访问 http://localhost:3002 查看管理后台。

## 使用指南

### 命令行模式

```bash
# 执行完整分析（扫描股票池）
python main.py --run

# 分析单只股票
python main.py --stock 000001

# 分析多只指定股票
python main.py --stocks 000001,000002,600519

# 分析所有股票（沪深A股）
python main.py --all

# 发送测试通知
python main.py --test-notify
```

### API接口

启动服务后，访问 http://localhost:8000/docs 查看API文档。

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 系统信息 |
| `/health` | GET | 健康检查 |
| `/api/analyze/run` | POST | 执行分析任务 |
| `/api/analyze/stock/{code}` | GET | 分析单只股票 |
| `/api/signals` | GET | 获取交易信号列表 |
| `/api/signals/{code}` | GET | 获取单只股票信号 |
| `/api/market/context` | GET | 获取市场环境 |
| `/api/ai/analyze/{code}` | POST | AI智能分析 |
| `/api/notify` | POST | 发送测试通知 |
| `/api/config` | GET | 获取系统配置 |

### API调用示例

```bash
# 获取系统信息
curl http://localhost:8000/

# 分析单只股票
curl http://localhost:8000/api/analyze/stock/000001

# 执行完整分析
curl -X POST http://localhost:8000/api/analyze/run

# AI分析
curl -X POST http://localhost:8000/api/ai/analyze/000001
```

### Python SDK使用

```python
import asyncio
from scheduler import TradingSystem

async def main():
    # 初始化交易系统
    trading = TradingSystem()
    
    # 分析单只股票
    result = await trading.analyze_single_stock("000001", "平安银行")
    print(f"阶段: {result.phase}")
    print(f"信号: {result.signals}")
    
    # 分析股票池
    await trading.run_analysis()
    
    # 获取所有信号
    for signal in trading.trade_signals:
        print(f"{signal.stock_name}: {signal.signal_type.value}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 项目结构

```
30zhouxian/
├── trading_system/              # Python后端
│   ├── config/                  # 配置模块
│   │   ├── __init__.py
│   │   └── settings.py          # 配置管理
│   ├── core/                    # 核心引擎
│   │   ├── __init__.py
│   │   ├── data_collector.py    # 数据获取（tdx-api）
│   │   ├── phase_analyzer.py    # 30周均线阶段分析
│   │   ├── signal_generator.py  # 交易信号生成
│   │   └── risk_manager.py      # 风险管理
│   ├── services/                # 服务层
│   │   ├── __init__.py
│   │   ├── notifier.py          # 钉钉/飞书通知
│   │   └── ai_analyzer.py       # AI分析服务
│   ├── scheduler/               # 定时任务
│   │   ├── __init__.py
│   │   └── task_scheduler.py    # 任务调度器
│   ├── models/                  # 数据模型
│   │   ├── __init__.py
│   │   └── schemas.py           # Pydantic模型
│   ├── tests/                   # 测试
│   ├── main.py                  # 主入口
│   ├── requirements.txt         # 依赖
│   ├── .env.example             # 环境变量示例
│   └── README.md                # 后端文档
│
├── trading-dashboard/           # React前端
│   ├── src/
│   │   ├── components/          # React组件
│   │   │   ├── Dashboard.tsx    # 仪表盘
│   │   │   ├── Signals.tsx      # 信号列表
│   │   │   ├── StockDetail.tsx  # 股票详情
│   │   │   └── Settings.tsx     # 设置
│   │   ├── App.tsx              # 应用入口
│   │   ├── index.css            # 样式
│   │   └── main.tsx             # 主入口
│   ├── package.json             # 依赖
│   ├── vite.config.ts           # Vite配置
│   └── tailwind.config.js       # Tailwind配置
│
└── README.md                    # 本文件
```

## 配置详解

### 钉钉Webhook配置

1. 打开钉钉群 → 群设置 → 智能群助手
2. 添加机器人 → 自定义（通过Webhook接入）
3. 复制Webhook地址和Secret
4. 填入 `.env` 文件

### 飞书Webhook配置

1. 打开飞书群 → 设置 → 群机器人
2. 添加自定义机器人
3. 复制Webhook地址
4. 填入 `.env` 文件

### OpenAI配置

支持所有OpenAI兼容的API：

**OpenAI官方：**
```env
OPENAI_API_KEY=sk-xxxxxxxx
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4
```

**DeepSeek：**
```env
OPENAI_API_KEY=sk-xxxxxxxx
OPENAI_API_BASE=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
```

**自定义API：**
```env
OPENAI_API_KEY=your_key
OPENAI_API_BASE=https://your-api-endpoint.com/v1
OPENAI_MODEL=your-model
```

## 技术栈

### 后端
| 技术 | 用途 |
|------|------|
| Python 3.9+ | 编程语言 |
| FastAPI | Web框架 |
| Pandas/NumPy | 数据分析 |
| APScheduler | 定时任务 |
| httpx | 异步HTTP |
| Pydantic | 数据验证 |
| Loguru | 日志 |

### 前端
| 技术 | 用途 |
|------|------|
| React 18 | UI框架 |
| TypeScript | 类型安全 |
| Vite | 构建工具 |
| Tailwind CSS | 样式 |
| Framer Motion | 动画 |
| Recharts | 图表 |
| Lucide React | 图标 |

### 数据源
- **tdx-api**: 通达信数据接口 (http://43.138.33.77:8080)

## 定时任务

系统默认每周五收盘后（15:30）自动执行分析：

```python
# 默认配置
SCHEDULE_DAY=5      # 周五
SCHEDULE_TIME=15:30 # 收盘后
```

自定义调度：
```env
# 每天15:30执行
SCHEDULE_DAY=*
SCHEDULE_TIME=15:30

# 每周一、三、五执行
SCHEDULE_DAY=1,3,5
SCHEDULE_TIME=09:30
```

## 开发指南

### 添加新的通知渠道

1. 在 `services/notifier.py` 中继承 `NotifierService`：

```python
class WeComNotifier(NotifierService):
    """企业微信通知器"""
    
    async def send_text(self, text: str, title: Optional[str] = None) -> bool:
        # 实现发送逻辑
        pass
    
    async def send_markdown(self, title: str, content: str) -> bool:
        # 实现发送逻辑
        pass
```

2. 在 `MultiNotifier` 中添加初始化。

### 自定义信号策略

在 `core/signal_generator.py` 中修改策略：

```python
def _check_custom_buy_signal(self, data: pd.DataFrame) -> Tuple[bool, str]:
    """自定义买入信号检测"""
    # 你的逻辑
    return True, "自定义买入理由"
```

## 常见问题

### Q: 如何获取股票代码？

A: 系统使用标准A股代码格式：
- 深市：000001（平安银行）、000333（美的集团）
- 沪市：600000（浦发银行）、600519（贵州茅台）
- 创业板：300750（宁德时代）
- 科创板：688XXX

### Q: 为什么收不到通知？

A: 检查以下几点：
1. Webhook地址是否正确
2. 密钥是否配置正确
3. 网络是否连通
4. 查看日志文件 `logs/trading_system.log`

### Q: 如何关闭AI分析？

A: 不配置 `OPENAI_API_KEY` 即可，系统会自动跳过AI分析步骤。

### Q: 数据更新频率？

A: 依赖tdx-api数据源，通常日线数据每日收盘后更新。

## 更新日志

### v1.0.0 (2024-02-10)
- 初始版本发布
- 实现30周均线阶段分析
- 支持钉钉/飞书通知
- 集成OpenAI分析
- Web管理后台

## 免责声明

**重要提示：**

1. 本系统仅供学习和研究使用，不构成任何投资建议
2. 股市有风险，投资需谨慎
3. 过往表现不代表未来收益
4. 请根据自身风险承受能力谨慎决策
5. 使用本系统产生的任何盈亏均由用户自行承担

## 许可证

MIT License

Copyright (c) 2024 30周均线交易系统

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.

---

## Docker 部署

### 快速开始

1. **克隆项目**
```bash
git clone <repository-url>
cd 30zhouxian
```

2. **构建并启动**
```bash
# 构建前端（需要先安装Node.js）
cd trading-dashboard
npm install
npm run build
cd ..

# 启动Docker容器
docker-compose up -d
```

3. **访问系统**
- Web界面：http://localhost
- API文档：http://localhost:8000/docs

### 单独部署后端

```bash
# 构建镜像
docker build -t trading-system .

# 运行容器
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/data:/app/trading_system/data \
  -v $(pwd)/logs:/app/trading_system/logs \
  -e TDX_API_URL=http://43.138.33.77:8080 \
  --name trading-system \
  trading-system
```

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `TDX_API_URL` | TDX行情API地址 | http://43.138.33.77:8080 |
| `LOG_LEVEL` | 日志级别 | INFO |
| `DINGTALK_WEBHOOK_URL` | 钉钉Webhook地址 | - |
| `DINGTALK_SECRET` | 钉钉Secret | - |
| `OPENAI_API_KEY` | OpenAI API Key | - |

### 数据持久化

Docker部署时，以下数据会持久化保存：
- `./data/` - SQLite数据库文件
- `./logs/` - 系统日志文件

---

**作者**: Claude AI Assistant  
**基于**: 史丹·温斯坦《一条均线定乾坤》  
**项目地址**: https://github.com/yourusername/30zhouxian
