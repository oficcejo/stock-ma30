# 30周均线交易系统

基于史丹·温斯坦《一条均线定乾坤》（How to Make Money in Stocks）的量化交易系统。

## 核心功能

- **阶段分析引擎**：自动识别股票四个阶段（底部/上升/顶部/下降），基于30周均线和成交量判断
- **买入信号检测**：股价放量突破第一阶段底部区间、30周均线向上、成交量放大2倍以上
- **卖出信号检测**：30周均线走平/向下、股价跌破均线且无法站回、成交量异常放大
- **风险管理模块**：止损位设置、仓位控制（单笔亏损不超过总资金2-3%）、金字塔加仓法
- **智能提醒系统**：支持钉钉/飞书webhook推送交易信号提醒
- **AI分析集成**：调用OpenAI兼容大模型进行市场分析和交易建议
- **Web管理后台**：可视化监控面板，实时查看交易信号和股票分析

## 交易规则（来自书中）

### 四个阶段
1. **第一阶段（底部/冬天）**：30周均线走平，股价横盘，观察不买
2. **第二阶段（上升/春夏）**：股价放量突破，30周均线向上，买入持有
3. **第三阶段（顶部/秋天）**：30周均线走平，股价震荡，考虑卖出
4. **第四阶段（下降/冬天）**：30周均线向下，股价在其下，远离或做空

### 买入条件
- 股价突破第一阶段底部区间进入第二阶段
- 突破时成交量明显放大（2倍以上）
- 30周均线开始向上倾斜
- 大盘也在第二阶段

### 卖出条件
- 30周均线走平或向下
- 股价跌破30周均线且无法站回
- 成交量异常放大但股价不涨

### 风险管理
- 每笔交易亏损不超过总资金2-3%
- 止损位只能上移，不能下移
- 金字塔加仓法：只在盈利时加仓，每次加仓量递减

## 快速开始

### 1. 安装依赖

```bash
cd trading_system
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env`，并填写你的配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# 钉钉Webhook配置
DINGTALK_WEBHOOK_URL=https://oapi.dingtalk.com/robot/send?access_token=your_token
DINGTALK_SECRET=your_secret

# 飞书Webhook配置
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/your_token

# OpenAI配置
OPENAI_API_KEY=your_api_key
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4

# 股票池
STOCK_POOL=000001,000002,000333,000858,002594,300750,600000,600519,601012,601318
```

### 3. 运行系统

#### 命令行模式

```bash
# 执行单次分析
python main.py --run

# 分析单只股票
python main.py --stock 000001

# 启动API服务
python main.py --serve
```

#### API服务模式

```bash
python main.py --serve --host 0.0.0.0 --port 8000
```

API端点：
- `GET /` - 系统信息
- `POST /api/analyze/run` - 执行分析任务
- `POST /api/analyze/stock` - 分析单只股票
- `GET /api/signals` - 获取交易信号
- `GET /api/market/context` - 获取市场环境
- `POST /api/notify` - 发送测试通知
- `POST /api/ai/analyze` - 运行AI分析
- `GET /api/config` - 获取配置信息

### 4. 启动Web管理后台

```bash
cd trading-dashboard
npm install
npm run dev
```

访问 http://localhost:3002 查看管理后台。

## 项目结构

```
trading_system/
├── config/              # 配置文件
│   ├── __init__.py
│   └── settings.py      # 系统配置
├── core/                # 核心模块
│   ├── data_collector.py    # 数据获取（tdx-api）
│   ├── phase_analyzer.py    # 30周均线阶段分析
│   ├── signal_generator.py  # 交易信号生成
│   └── risk_manager.py      # 风险管理
├── services/            # 服务模块
│   ├── notifier.py      # 钉钉/飞书通知
│   └── ai_analyzer.py   # AI分析服务
├── scheduler/           # 定时任务
│   └── task_scheduler.py
├── models/              # 数据模型
│   └── schemas.py
├── tests/               # 测试
├── main.py              # 主入口
├── requirements.txt     # Python依赖
└── .env.example         # 环境变量示例

trading-dashboard/       # Web管理后台
├── src/
│   ├── components/      # React组件
│   │   ├── Dashboard.tsx
│   │   ├── Signals.tsx
│   │   ├── StockDetail.tsx
│   │   └── Settings.tsx
│   ├── App.tsx
│   └── index.css
├── package.json
└── vite.config.ts
```

## 技术栈

### 后端
- **Python 3.9+**
- **FastAPI** - Web框架
- **Pandas/NumPy** - 数据处理
- **APScheduler** - 定时任务
- **OpenAI** - AI分析
- **httpx** - HTTP客户端

### 前端
- **React 18 + TypeScript**
- **Vite** - 构建工具
- **Tailwind CSS** - 样式
- **Framer Motion** - 动画
- **Recharts** - 图表
- **Lucide React** - 图标

### 数据源
- **tdx-api** - 股票行情数据 (http://43.138.33.77:8080)

## 配置说明

### 钉钉Webhook配置

1. 在钉钉群中添加机器人
2. 获取Webhook地址和Secret
3. 填入 `.env` 文件

### 飞书Webhook配置

1. 在飞书群中添加机器人
2. 获取Webhook地址
3. 填入 `.env` 文件

### OpenAI配置

支持OpenAI兼容的API，包括：
- OpenAI官方API
- DeepSeek API
- 其他兼容OpenAI格式的API

```env
OPENAI_API_KEY=your_key
OPENAI_API_BASE=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
```

## 定时任务

系统默认每周五15:30执行自动分析，可通过环境变量配置：

```env
SCHEDULE_DAY=5      # 0=周日, 5=周五
SCHEDULE_TIME=15:30
```

## 免责声明

本系统仅供学习和研究使用，不构成投资建议。股市有风险，投资需谨慎。

## 许可证

MIT License
