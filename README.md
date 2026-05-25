# Crazy Money - A股量化数据平台

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-green.svg)
![Next.js](https://img.shields.io/badge/next.js-14.0-black.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

**一个现代化的A股量化数据可视化平台**

[功能特性](#功能特性) • [快速开始](#快速开始) • [API文档](#api文档) • [部署指南](#部署指南)

</div>

---

## 项目简介

Crazy Money 是一个功能完整的A股量化数据平台，采用前后端分离架构，提供股票数据查询、K线图可视化、技术指标分析、实时进度跟踪等服务管理功能。系统支持CSV和Parquet双格式存储，具备高性能的数据处理能力。

### 核心优势

- 🚀 **高性能存储**：采用Parquet列式存储，读取速度比CSV快10倍
- 📊 **丰富图表**：支持K线图、均线、MACD、RSI、布林带等多种技术指标
- 🔄 **实时进度**：WebSocket推送下载进度，任务状态实时跟踪
- 📱 **响应式设计**：完美适配桌面端和移动端
- 🌐 **局域网访问**：支持手机等设备通过局域网访问
- 💾 **智能缓存**：多层缓存机制，显著提升响应速度
- ⚙️ **服务管理**：一键启停前后端服务，支持热重启
- 📝 **任务持久化**：任务状态保存到localStorage，刷新页面不丢失

---

## 功能特性

### 1. 股票数据管理

- ✅ 股票列表展示（支持分页搜索）
- ✅ 股票搜索（代码/名称模糊搜索）
- ✅ 实时搜索建议
- ✅ 股票详情查看
- ✅ 历史数据查询
- ✅ 数据完整性检查

### 2. K线图可视化

- ✅ 日K线、周K线、月K线切换
- ✅ 均线显示（MA5/MA10/MA20/MA60）
- ✅ 成交量柱状图
- ✅ 缩放和拖拽交互
- ✅ 十字光标追踪

### 3. 技术指标分析

- ✅ **MACD**（指数平滑异同移动平均线）
  - DIF线、DEA线、MACD柱状图
- ✅ **RSI**（相对强弱指标）
  - RSI(6)、RSI(12)、RSI(24)
- ✅ **布林带**（BOLL）
  - 上轨、中轨、下轨

### 4. 数据更新功能

- ✅ 初始化股票列表
- ✅ 批量下载股票数据
- ✅ 强制全量下载模式
- ✅ 测试模式（下载前N只）
- ✅ 数据格式转换（CSV↔Parquet）
- ✅ 数据完整性检查

### 5. 系统管理与监控

- ✅ **服务启停控制**：前后端服务可视化启停
- ✅ **服务热重启**：支持前后端服务在线重启
- ✅ **服务状态监控**：实时显示PID、运行时间、端口占用
- ✅ **任务状态持久化**：localStorage存储，刷新不丢失
- ✅ **并发任务控制**：同一时间只允许一个任务运行
- ✅ **WebSocket进度推送**：实时显示下载进度
- ✅ **详细日志输出**：每只股票更新情况清晰展示
- ✅ **统计信息展示**：成功/失败/跳过数量实时更新

### 6. 定时调度功能

- ✅ 交易日自动更新（15:00后执行）
- ✅ 支持手动启动/停止调度器
- ✅ 异常自动重试机制

---

## 技术架构

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        前端层 (Next.js)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │  首页       │  │  股票详情   │  │  系统管理   │          │
│  │  StockList │  │  KLineChart│  │  AdminPage  │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
                            ↓ HTTP REST API + WebSocket
┌─────────────────────────────────────────────────────────────┐
│                      后端层 (FastAPI)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │  股票路由   │  │  图表路由   │  │  系统路由   │          │
│  │  /stocks    │  │  /charts    │  │  /system    │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              进度管理器 (WebSocket)                     │    │
│  │              ProgressManager                            │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            ↓ 文件系统
┌─────────────────────────────────────────────────────────────┐
│                      数据层 (CSV/Parquet)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │  历史数据   │  │  股票列表   │  │  元数据     │          │
│  │  5500+股票  │  │  stock_list │  │  metadata   │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### 技术栈

| 层级 | 技术 | 版本 | 说明 |
|------|------|------|------|
| **前端框架** | Next.js | 14.0.4 | React服务端渲染框架 |
| **UI库** | React | 18.2.0 | 用户界面构建库 |
| **图表库** | ECharts | 5.4.3 | 数据可视化图表库 |
| **样式框架** | Tailwind CSS | 3.4.0 | 原子化CSS框架 |
| **HTTP客户端** | Axios | 1.6.2 | HTTP请求库 |
| **后端框架** | FastAPI | 0.104.1 | 高性能Python Web框架 |
| **数据处理** | Pandas | 2.1.4 | 数据分析库 |
| **数据存储** | PyArrow | 14.0.1 | Parquet文件处理 |
| **ASGI服务器** | Uvicorn | 0.24.0 | 异步HTTP服务器 |
| **进程管理** | psutil | 7.2.2 | 系统进程管理 |

---

## 项目结构

```
crazy-money-AKShare/
├── backend/                         # 后端服务根目录
│   ├── routers/                      # API路由模块
│   │   ├── __init__.py
│   │   ├── stocks.py                # 股票数据接口
│   │   ├── charts.py               # 图表数据接口
│   │   └── system.py               # 系统控制接口
│   ├── services/                    # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── data_service.py         # 数据服务
│   │   ├── chart_service.py        # 图表计算服务
│   │   └── progress_manager.py     # WebSocket进度管理
│   ├── app.py                       # FastAPI应用入口
│   └── requirements.txt             # Python依赖
│
├── frontend/                        # 前端应用根目录
│   ├── components/                  # React组件
│   │   ├── Header.tsx              # 导航栏组件
│   │   ├── StockList.tsx           # 股票列表组件
│   │   ├── StockCard.tsx           # 股票卡片组件
│   │   ├── StockSummaryCard.tsx    # 股票摘要卡片
│   │   ├── KLineChart.tsx          # K线图组件
│   │   ├── IndicatorChart.tsx      # 技术指标图组件
│   │   └── StatsCard.tsx           # 统计卡片组件
│   ├── pages/                       # 页面路由
│   │   ├── _app.tsx               # 应用入口
│   │   ├── _document.tsx           # HTML文档
│   │   ├── index.tsx               # 首页
│   │   ├── admin.tsx               # 系统管理页
│   │   ├── test-chart.tsx          # 图表测试页
│   │   └── stock/
│   │       └── [code].tsx          # 股票详情页
│   ├── utils/                       # 工具函数
│   │   └── api.ts                  # API调用封装和WebSocket客户端
│   ├── styles/                      # 样式文件
│   │   └── globals.css             # 全局样式
│   ├── .env.local                  # 环境变量配置
│   ├── next.config.js              # Next.js配置
│   ├── tailwind.config.js          # Tailwind配置
│   └── package.json                # Node.js依赖
│
├── config/                         # 配置模块
│   ├── __init__.py
│   └── settings.py                 # 系统配置参数
│
├── service/                        # 业务服务层
│   ├── __init__.py
│   ├── stock_service.py           # 股票列表服务
│   ├── update_service.py          # 数据更新服务
│   ├── normalize_service.py       # 数据标准化服务
│   ├── trade_date_service.py      # 交易日历服务
│   └── convert_service.py         # 格式转换服务
│
├── datasource/                     # 数据源模块
│   ├── __init__.py
│   ├── base.py                    # 数据源基类
│   ├── tencent.py                 # 腾讯数据源
│   └── eastmoney.py              # 东方财富数据源
│
├── storage/                        # 存储模块
│   ├── __init__.py
│   ├── csv_storage.py             # CSV存储
│   ├── parquet_storage.py         # Parquet存储
│   └── metadata_storage.py       # 元数据存储
│
├── scheduler/                      # 调度器模块
│   ├── __init__.py
│   └── daily_update.py           # 每日更新调度器
│
├── utils/                          # 工具模块
│   ├── __init__.py
│   ├── logger.py                  # 日志配置
│   ├── rate_limiter.py           # 智能限流器
│   ├── date_utils.py             # 日期工具
│   └── scheduler.py             # 调度工具
│
├── data/                          # 数据存储目录
│   ├── history_csv/              # CSV格式历史数据
│   ├── history_parquet/          # Parquet格式历史数据
│   ├── stock_list.csv            # 股票列表文件
│   └── metadata/                 # 元数据目录
│
├── logs/                          # 日志目录
│
├── cli.py                         # 命令行入口
├── restart.sh                     # 服务重启脚本
├── requirements.txt              # Python依赖
└── README.md                    # 项目文档
```

---

## 快速开始

### 环境要求

| 环境 | 版本要求 | 说明 |
|------|----------|------|
| Python | 3.10+ | 后端运行环境 |
| Node.js | 18.0+ | 前端运行环境 |
| npm | 9.0+ | 包管理器 |

### 安装步骤

#### 1. 克隆项目

```bash
git clone https://github.com/yourusername/crazy-money-AKShare.git
cd crazy-money-AKShare
```

#### 2. 后端安装

```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装Python依赖
pip install -r requirements.txt

# 启动后端服务
cd backend
python3 app.py
```

后端服务将在 `http://localhost:8000` 启动

#### 3. 前端安装

```bash
# 新开终端
cd frontend

# 安装Node.js依赖
npm install

# 开发模式启动
npm run dev
```

前端服务将在 `http://localhost:3000` 启动

#### 4. 一键重启脚本

项目提供了 `restart.sh` 脚本，可一键重启前后端服务：

```bash
# 添加执行权限
chmod +x restart.sh

# 执行重启
./restart.sh
```

### 初始化数据

首次使用需要初始化股票列表并下载数据：

```bash
# 初始化股票列表
python3 cli.py init

# 下载所有股票数据（首次建议使用测试模式）
python3 cli.py download --count=100  # 测试下载前100只

# 强制全量下载
python3 cli.py download --force
```

---

## CLI命令详解

### 命令列表

| 命令 | 说明 | 示例 |
|------|------|------|
| `init` | 初始化股票列表 | `python3 cli.py init` |
| `download` | 下载股票数据 | `python3 cli.py download` |
| `scheduler` | 启动定时调度器 | `python3 cli.py scheduler` |
| `convert` | 格式转换 | `python3 cli.py convert sync` |
| `check` | 检查数据完整性 | `python3 cli.py check` |
| `help` | 显示帮助信息 | `python3 cli.py help` |

### 下载命令选项

| 选项 | 说明 | 示例 |
|------|------|------|
| `--count=N` | 测试模式，下载前N只股票 | `--count=100` |
| `--force` | 强制全量下载 | `--force` |
| `--batch=N` | 批处理大小 | `--batch=50` |
| `--source=SRC` | 数据源（tencent/eastmoney） | `--source=tencent` |
| `--adjust=ADJ` | 复权方式（qfq/hfq/none） | `--adjust=qfq` |

### 转换命令选项

| 命令 | 说明 |
|------|------|
| `csv2parquet` | CSV转Parquet |
| `parquet2csv` | Parquet转CSV |
| `sync` | 双向同步 |

---

## API文档

### 基础信息

- **Base URL**: `http://localhost:8000/api`
- **WebSocket URL**: `ws://localhost:8000/ws/{channel}`
- **响应格式**: JSON
- **字符编码**: UTF-8

### 通用响应格式

```json
{
  "code": 200,
  "data": { ... },
  "message": "success"
}
```

### 错误响应格式

```json
{
  "code": 500,
  "detail": "错误详细信息",
  "message": "error"
}
```

---

### 股票数据接口

#### 1. 获取股票列表

```
GET /api/stocks/list
```

**参数**:
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | int | 否 | 1 | 页码 |
| limit | int | 否 | 50 | 每页数量（1-10000） |
| keyword | string | 否 | - | 搜索关键词（代码或名称） |

**响应示例**:
```json
{
  "code": 200,
  "data": {
    "list": [
      {"code": "000001", "name": "平安银行"},
      {"code": "000002", "name": "万科A"}
    ],
    "total": 5514,
    "page": 1,
    "limit": 50
  },
  "message": "success"
}
```

#### 2. 获取股票详情

```
GET /api/stocks/{code}
```

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| code | string | 6位股票代码 |

**响应示例**:
```json
{
  "code": 200,
  "data": {
    "code": "000001",
    "name": "平安银行",
    "latest_close": 10.50,
    "latest_date": "2024-01-15"
  },
  "message": "success"
}
```

#### 3. 获取股票历史数据

```
GET /api/stocks/{code}/history
```

**参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| start_date | string | 否 | 开始日期（YYYY-MM-DD） |
| end_date | string | 否 | 结束日期（YYYY-MM-DD） |
| limit | int | 否 | 返回条数（默认100，最大500） |

**响应示例**:
```json
{
  "code": 200,
  "data": [
    {
      "date": "2024-01-15",
      "open": 10.00,
      "close": 10.50,
      "high": 10.80,
      "low": 9.90,
      "volume": 1000000,
      "amount": 10500000
    }
  ],
  "message": "success"
}
```

#### 4. 获取股票统计摘要

```
GET /api/stocks/{code}/summary
```

**响应示例**:
```json
{
  "code": 200,
  "data": {
    "code": "000001",
    "name": "平安银行",
    "latest_close": 10.50,
    "latest_date": "2024-01-15",
    "avg_close": 11.20,
    "max_close": 15.80,
    "min_close": 8.50,
    "std_close": 1.50,
    "total_days": 1000
  },
  "message": "success"
}
```

---

### 图表数据接口

#### 5. 获取K线数据

```
GET /api/charts/{code}/kline
```

**参数**:
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| period | string | 否 | day | 周期（day/week/month） |
| start_date | string | 否 | - | 开始日期 |
| end_date | string | 否 | - | 结束日期 |

**响应示例**:
```json
{
  "code": 200,
  "data": {
    "dates": ["2024-01-01", "2024-01-02"],
    "items": [
      {
        "open": 10.00,
        "close": 10.50,
        "high": 10.80,
        "low": 9.90,
        "volume": 1000000
      }
    ]
  },
  "message": "success"
}
```

#### 6. 获取均线数据

```
GET /api/charts/{code}/ma
```

**参数**:
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| periods | string | 否 | 5,10,20,60 | 均线周期（逗号分隔） |
| period | string | 否 | day | 数据周期 |
| start_date | string | 否 | - | 开始日期 |
| end_date | string | 否 | - | 结束日期 |

#### 7. 获取成交量数据

```
GET /api/charts/{code}/volume
```

**参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| start_date | string | 否 | 开始日期 |
| end_date | string | 否 | 结束日期 |

#### 8. 获取技术指标

```
GET /api/charts/{code}/indicators
```

**参数**:
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| indicators | string | 否 | macd,rsi,boll | 指标列表（逗号分隔） |

**响应示例**:
```json
{
  "code": 200,
  "data": {
    "macd": {
      "dif": [0.1, 0.2],
      "dea": [0.1, 0.15],
      "macd": [0.0, 0.05]
    },
    "rsi": {
      "rsi6": [50.0, 55.0],
      "rsi12": [48.0, 52.0],
      "rsi24": [45.0, 50.0]
    },
    "boll": {
      "upper": [12.0, 12.5],
      "middle": [11.0, 11.2],
      "lower": [10.0, 9.9]
    }
  },
  "message": "success"
}
```

#### 9. 聚合接口（推荐）

```
GET /api/charts/{code}/all
```

**参数**:
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| period | string | 否 | day | 数据周期 |
| ma_periods | string | 否 | 5,10,20,60 | 均线周期 |
| indicators | string | 否 | macd,rsi,boll | 技术指标 |
| start_date | string | 否 | - | 开始日期 |
| end_date | string | 否 | - | 结束日期 |

**优势**: 一次请求获取K线、均线、技术指标所有数据，减少HTTP请求次数。

---

### 系统控制接口

#### 10. 获取服务状态

```
GET /api/system/status
```

**响应示例**:
```json
{
  "code": 200,
  "data": {
    "backend": {
      "running": true,
      "pid": 12345,
      "uptime": "30分钟",
      "port": 8000,
      "status": "running"
    },
    "frontend": {
      "running": true,
      "pid": 12346,
      "uptime": "30分钟",
      "port": 3000,
      "status": "running"
    },
    "scheduler": {
      "running": false,
      "pid": null,
      "uptime": null,
      "port": null
    },
    "ports": {
      "backend": {"in_use": true, "port": 8000},
      "frontend": {"in_use": true, "port": 3000}
    }
  },
  "message": "success"
}
```

#### 11. 启动后端服务

```
POST /api/system/start/backend
```

**响应示例**:
```json
{
  "code": 200,
  "data": {"running": true, "pid": 12345},
  "message": "后端服务启动成功"
}
```

#### 12. 停止后端服务

```
POST /api/system/stop/backend
```

#### 13. 重启后端服务

```
POST /api/system/restart/backend
```

#### 14. 启动前端服务

```
POST /api/system/start/frontend
```

#### 15. 停止前端服务

```
POST /api/system/stop/frontend
```

#### 16. 重启前端服务

```
POST /api/system/restart/frontend
```

#### 17. 启动调度器

```
POST /api/system/start/scheduler
```

#### 18. 停止调度器

```
POST /api/system/stop/scheduler
```

---

### CLI命令执行接口

#### 19. 执行CLI命令（同步）

```
POST /api/system/cli
```

**请求体**:
```json
{
  "command": "download",
  "options": {
    "count": 100,
    "force": true
  }
}
```

**响应示例**:
```json
{
  "code": 200,
  "data": {
    "success": true,
    "returncode": 0,
    "stdout": "...",
    "stderr": ""
  },
  "message": "命令执行成功"
}
```

#### 20. 执行CLI命令（流式进度）

```
POST /api/system/cli/stream
```

**请求体**: 同上

**WebSocket进度消息格式**:

```typescript
interface ProgressMessage {
  type: 'progress' | 'log' | 'complete';
  task_id: string;
  progress?: number;        // 0-100
  message?: string;         // 进度消息
  current?: number;        // 当前处理数
  total?: number;          // 总数
  status?: 'running' | 'success' | 'error';
  success?: boolean;        // 最终是否成功
  level?: 'info' | 'warning' | 'error';
  stats?: {
    success: number;       // 成功数
    failed: number;        // 失败数
    skipped: number;       // 跳过数
  };
}
```

---

## 前端组件

### 页面结构

| 页面 | 路由 | 说明 |
|------|------|------|
| 首页 | `/` | 股票列表、搜索功能 |
| 股票详情 | `/stock/[code]` | K线图、技术指标 |
| 系统管理 | `/admin` | 服务控制、任务管理 |

### 核心组件

#### 1. Header（导航栏）

**功能特性**:
- Logo和标题显示
- 实时搜索输入框
- 搜索建议下拉框
- 键盘导航支持（↑/↓/Enter/Escape）
- 移动端响应式适配

#### 2. KLineChart（K线图组件）

**功能特性**:
- ECharts渲染，支持缩放拖拽
- 动态导入避免SSR问题
- 日K/周K/月K周期切换
- MA均线叠加显示
- 成交量柱状图联动

#### 3. IndicatorChart（技术指标组件）

**支持指标**:
- **MACD**: DIF线(12,26,9)、DEA线、MACD柱
- **RSI**: RSI(6)、RSI(12)、RSI(24)
- **BOLL**: 上轨(20,2)、中轨、下轨

#### 4. AdminPage（系统管理页面）

**功能特性**:
- 服务状态卡片展示
- 一键启停/重启按钮
- 任务执行面板
- WebSocket进度实时显示
- localStorage任务持久化
- 任务并发控制

---

## 数据格式

### Canonical Schema（标准数据结构）

系统内部统一使用以下字段定义：

| 字段 | 类型 | 说明 |
|------|------|------|
| date | datetime64 | 交易日，格式YYYY-MM-DD |
| code | string | 股票代码，6位字符串 |
| open | float64 | 开盘价，单位元 |
| close | float64 | 收盘价，单位元 |
| high | float64 | 最高价，单位元 |
| low | float64 | 最低价，单位元 |
| volume | int64 | 成交量，单位手 |
| amount | float64 | 成交额，单位元 |
| amplitude | float64 | 振幅，单位% |
| pct_change | float64 | 涨跌幅，单位% |
| price_change | float64 | 涨跌额，单位元 |
| turnover | float64 | 换手率，单位% |
| source | string | 数据来源标识 |
| adjust | string | 复权方式：qfq/hfq/none |

### CSV文件格式

```csv
date,code,open,close,high,low,volume,amount,amplitude,pct_change,price_change,turnover,source,adjust
2024-01-15,000001,10.00,10.50,10.80,9.90,1000000,10500000,9.00,5.00,0.50,2.50,tencent,qfq
```

### Parquet文件格式

- **引擎**: PyArrow
- **压缩算法**: Snappy
- **优势**: 读取速度比CSV快10倍，占用空间更小

---

## 配置说明

### 后端配置

**文件位置**: `config/settings.py`

```python
# ========== 数据源配置 ==========
DEFAULT_DATA_SOURCE = "tencent"       # 主数据源
FALLBACK_DATA_SOURCE = "eastmoney"    # 备用数据源
DEFAULT_ADJUST = "qfq"                # 复权方式
DEFAULT_START_DATE = "2020-01-01"     # 默认起始日期

# ========== 并发配置 ==========
CONCURRENT_WORKERS = 10               # 并发下载线程数
BATCH_SIZE = 100                     # 批处理大小
BATCH_PAUSE_SECONDS = 30             # 批次间休息时间

# ========== 限流配置 ==========
RATE_LIMIT_MODE = "fast"             # 限流模式
MAX_RETRIES = 3                      # 最大重试次数
RETRY_DELAY = 2                      # 重试等待时间

# ========== 存储配置 ==========
CSV_ENCODING = "utf-8-sig"           # CSV编码
PARQUET_ENGINE = "pyarrow"           # Parquet引擎
PARQUET_COMPRESSION = "snappy"       # 压缩方式

# ========== 日志配置 ==========
LOG_LEVEL = "INFO"                   # 日志级别
LOG_BACKUP_DAYS = 30                 # 日志保留天数
```

### 前端配置

**文件位置**: `frontend/.env.local`

```bash
# 开发环境API地址
NEXT_PUBLIC_API_URL=http://localhost:8000/api

# 生产环境局域网访问（替换为实际IP）
# NEXT_PUBLIC_API_URL=http://192.168.1.100:8000/api
```

### 重启脚本配置

**文件位置**: `restart.sh`

脚本支持以下环境变量自定义：

```bash
BACKEND_PORT=8000       # 后端端口
FRONTEND_PORT=3000      # 前端端口
BACKEND_DIR=./backend   # 后端目录
FRONTEND_DIR=./frontend # 前端目录
VENV_PYTHON=.venv/bin/python  # Python虚拟环境
MAX_WAIT=10             # 最大等待秒数
```

---

## 开发指南

### 添加新技术指标

#### 1. 后端实现

在 `backend/services/chart_service.py` 中添加计算方法：

```python
def calculate_new_indicator(self, df: pd.DataFrame) -> Dict[str, List]:
    """
    计算新技术指标

    Args:
        df: 股票数据DataFrame

    Returns:
        技术指标数据字典
    """
    # 计算逻辑实现
    return {"new_indicator": values}
```

在 `GET /charts/{code}/indicators` 接口中注册：

```python
if "new_indicator" in indicators.split(","):
    result["new_indicator"] = self.chart_service.calculate_new_indicator(df)
```

#### 2. 前端实现

创建指标图表组件：

```typescript
// frontend/components/NewIndicatorChart.tsx
export const NewIndicatorChart = ({ data }) => {
  // 使用ECharts渲染新技术指标
  return <div ref={chartRef} style={{ width: '100%', height: '400px' }} />;
};
```

### 添加新的API接口

#### 1. 定义路由

在 `backend/routers/` 中创建新路由文件：

```python
# backend/routers/new_feature.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/endpoint")
async def new_endpoint():
    return {"message": "success"}
```

#### 2. 注册路由

在 `backend/app.py` 中引入并注册：

```python
from routers import stocks, charts, system, new_feature

app.include_router(new_feature.router, prefix="/api/new_feature", tags=["新功能"])
```

### 修改数据源

如需添加新的数据源：

1. 在 `datasource/` 目录创建新的数据源类
2. 继承 `BaseDataSource` 基类
3. 实现 `get_history()` 和 `get_stock_list()` 方法
4. 在 `datasource/__init__.py` 中注册

---

## 系统管理

### 访问系统管理页面

```
http://localhost:3000/admin
```

或点击导航栏右侧的"管理"按钮进入。

### 服务控制

| 操作 | 说明 |
|------|------|
| 启动服务 | 启动指定服务进程 |
| 停止服务 | 立即终止服务进程 |
| 重启服务 | 先停止再启动（会中断连接） |

### 任务管理

#### 可执行任务

| 任务 | 命令 | 说明 |
|------|------|------|
| 初始化股票列表 | `init` | 从数据源获取股票列表 |
| 下载股票数据 | `download` | 下载/更新股票历史数据 |
| 检查数据完整性 | `check` | 检查本地数据完整性 |
| 同步格式数据 | `convert sync` | CSV和Parquet双向同步 |

#### 任务选项

| 选项 | 说明 |
|------|------|
| 测试模式 | 下载前N只股票 |
| 强制全量 | 忽略已有数据重新下载 |
| 指定数据源 | tencent/eastmoney |
| 指定复权方式 | qfq/hfq/none |

#### 进度显示

任务执行时实时显示：
- 总体进度百分比
- 当前处理进度（X/Y格式）
- 成功/失败/跳过统计
- 每只股票的详细日志

---

## 部署指南

### 开发环境部署

```bash
# 1. 克隆代码
git clone <repository-url>
cd crazy-money-AKShare

# 2. 安装后端
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. 安装前端
cd frontend
npm install

# 4. 启动服务（两个终端）
# 终端1: 后端
cd backend && python3 app.py

# 终端2: 前端
cd frontend && npm run dev
```

### 生产环境部署

#### 后端部署

```bash
# 使用supervisor管理进程
[program:crazy-money-backend]
command=/path/to/.venv/bin/python /path/to/backend/app.py
directory=/path/to/crazy-money-AKShare
user=www-data
autostart=true
autorestart=true
```

#### 前端部署

```bash
# 构建生产版本
cd frontend
npm run build
npm run start -p 3000
```

### 局域网访问配置

```bash
# 1. 查看本机IP
ifconfig | grep "inet " | grep -v 127.0.0.1

# 2. 修改frontend/.env.local
NEXT_PUBLIC_API_URL=http://192.168.1.100:8000/api

# 3. 修改frontend/next.config.js
async rewrites() {
  return [{
    source: '/api/:path*',
    destination: 'http://192.168.1.100:8000/api/:path*'
  }];
}

# 4. 重新构建
npm run build
HOST=0.0.0.0 PORT=3000 npm run start
```

### Nginx反向代理配置

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        proxy_pass http://127.0.0.1:3000;
    }

    # 后端API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 常见问题

### Q: 下载数据进度条一直显示100%？

**A**: 这是因为tqdm进度条干扰了日志解析。已修复代码忽略tqdm格式，请更新到最新版本后重启服务。

### Q: WebSocket连接失败？

**A**: 请确保后端服务正在运行，检查端口8000是否被占用，查看后端日志获取详细信息。

### Q: 数据下载失败怎么办？

**A**: 1. 检查网络连接 2. 尝试更换数据源 `--source=eastmoney` 3. 使用测试模式 `--count=10` 4. 查看详细错误日志

### Q: 如何清理旧数据？

**A**: 删除 `data/history_csv/` 和 `data/history_parquet/` 目录，然后重新执行下载。

### Q: 前端页面空白？

**A**: 1. 清除浏览器缓存 2. 检查浏览器控制台错误 3. 确认后端API正常运行

### Q: 如何查看服务日志？

**A**: 查看 `logs/app.log` 文件，或在终端运行 `tail -f logs/app.log`。

---

## 更新日志

### v1.0.1 (2024-01)

**新增功能**:
- 修复进度条显示100%的问题
- 增加每只股票详细更新日志
- 优化WebSocket进度推送逻辑
- 添加restart.sh一键重启脚本

**优化改进**:
- 重构update_service.py的批次处理逻辑
- 优化_should_send_log函数过滤tqdm进度条
- 改进_extract_message函数的消息提取

### v1.0.0 (2024-01)

**初始版本**:
- 股票列表查询和搜索
- K线图和技术指标展示
- 数据下载和更新功能
- 前后端服务启停控制
- WebSocket实时进度推送
- 任务状态持久化

---

## 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

---

## 联系方式

- **项目主页**: https://github.com/yourusername/crazy-money-AKShare
- **问题反馈**: https://github.com/yourusername/crazy-money-AKShare/issues

---

<div align="center">

**Crazy Money - 让量化数据触手可及**

</div>
