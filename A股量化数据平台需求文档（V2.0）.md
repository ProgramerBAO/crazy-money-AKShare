## **项目名称**
```plain
A股量化数据平台（Stock Analyzer）
```

---

# **一、项目目标**
构建一个：

```plain
可扩展、可维护、支持增量更新、多数据源、多存储格式的A股量化数据平台
```

系统目标：

+ 数据采集
+ 数据标准化
+ 数据存储
+ 数据转换
+ 增量更新
+ 数据调度
+ 数据校验
+ 后续策略/回测/AI分析

---

# **二、核心设计思想**
## **2.1 系统核心**
系统核心不是：

```plain
CSV 文件
```

也不是：

```plain
AkShare 接口
```

真正核心是：

# **🚀**** Canonical Data（标准化数据）**
---

## **2.2 数据流设计**
```plain
外部数据源
(Tencent / EastMoney / Tushare)
                │
                ▼
        Normalize Layer
         数据标准化层
                │
                ▼
      Canonical DataFrame
         标准化数据对象
                │
      ┌─────────┴─────────┐
      ▼                   ▼
    CSV               Parquet
 (调试/兼容)          (高性能分析)
```

---

# **三、项目目录结构**
```plain
stock-analyzer/
│
├── cli.py
│
├── config/
│   └── settings.py
│
├── datasource/
│   ├── base.py
│   ├── tencent.py
│   ├── eastmoney.py
│   └── tushare.py
│
├── service/
│   ├── stock_service.py
│   ├── history_service.py
│   ├── update_service.py
│   ├── trade_date_service.py
│   ├── normalize_service.py
│   ├── convert_service.py
│   └── scheduler_service.py
│
├── storage/
│   ├── csv_storage.py
│   ├── parquet_storage.py
│   └── metadata_storage.py
│
├── scheduler/
│   └── daily_update.py
│
├── data/
│   ├── stock_list.csv
│   ├── trade_calendar.csv
│   ├── history_csv/
│   ├── history_parquet/
│   └── metadata/
│
├── logs/
│
├── strategy/
│
├── requirements.txt
│
└── README.md
```

---

# **四、数据源设计**
## **4.1 数据源必须抽象化**
禁止：

```plain
业务层直接调用 akshare
```

必须：

```plain
通过 datasource 层访问
```

---

# **五、数据源接口规范**
## **datasource/base.py**
```python
class BaseDataSource:

    def get_stock_list(self):
        pass

    def get_history(
        self,
        code: str,
        start_date: str,
        end_date: str,
        adjust: str = "qfq"
    ):
        pass
```

---

# **六、腾讯数据源设计**
文件：

```plain
datasource/tencent.py
```

---

## **输入规范**
腾讯接口要求：

```python
symbol = "sz000001"
```

而不是：

```python
000001
```

---

## **股票代码转换规则**
| **股票代码** | **转换结果** |
| --- | --- |
| 000001 | sz000001 |
| 300001 | sz300001 |
| 600519 | sh600519 |
| 688001 | sh688001 |


---

## **腾讯接口**
```python
ak.stock_zh_a_hist_tx()
```

---

## **腾讯返回字段**
```python
[
    "date",
    "open",
    "close",
    "high",
    "low",
    "amount"
]
```

---

## **腾讯字段问题**
腾讯：

```plain
amount
```

实际含义：

```plain
成交量（手）
```

不是：

```plain
成交额
```

---

# **七、东方财富数据源设计**
文件：

```plain
datasource/eastmoney.py
```

---

## **东方财富接口**
```python
ak.stock_zh_a_hist()
```

---

## **东方财富输入**
```python
symbol="000001"
```

---

## **东方财富返回字段**
```python
[
    "日期",
    "股票代码",
    "开盘",
    "收盘",
    "最高",
    "最低",
    "成交量",
    "成交额",
    "振幅",
    "涨跌幅",
    "涨跌额",
    "换手率"
]
```

---

# **八、多数据源兼容设计**
## **8.1 数据源差异**
| **项目** | **腾讯** | **东方财富** |
| --- | --- | --- |
| 股票代码 | 带市场前缀 | 不带 |
| 字段名 | 英文 | 中文 |
| 成交额 | 无 | 有 |
| 换手率 | 无 | 有 |
| 涨跌幅 | 无 | 有 |


---

## **8.2 系统要求**
必须：

```plain
不同数据源统一标准 schema
```

---

# **九、标准化层设计（核心）**
文件：

```plain
service/normalize_service.py
```

---

# **十、Canonical Schema（全系统统一）**
系统内部统一字段：

```python
[
    "date",
    "code",
    "open",
    "close",
    "high",
    "low",
    "volume",
    "amount",
    "amplitude",
    "pct_change",
    "price_change",
    "turnover",
    "source",
    "adjust"
]
```

---

# **十一、标准字段说明**
| **字段** | **类型** | **含义** |
| --- | --- | --- |
| date | datetime64 | 交易日 |
| code | string | 股票代码 |
| open | float64 | 开盘价 |
| close | float64 | 收盘价 |
| high | float64 | 最高价 |
| low | float64 | 最低价 |
| volume | int64 | 成交量（手） |
| amount | float64 | 成交额（元） |
| amplitude | float64 | 振幅 |
| pct_change | float64 | 涨跌幅 |
| price_change | float64 | 涨跌额 |
| turnover | float64 | 换手率 |
| source | string | 数据源 |
| adjust | string | 复权方式 |


---

# **十二、标准化规则**
## **12.1 东方财富字段映射**
```python
EASTMONEY_MAPPING = {
    "日期": "date",
    "股票代码": "code",
    "开盘": "open",
    "收盘": "close",
    "最高": "high",
    "最低": "low",
    "成交量": "volume",
    "成交额": "amount",
    "振幅": "amplitude",
    "涨跌幅": "pct_change",
    "涨跌额": "price_change",
    "换手率": "turnover"
}
```

---

## **12.2 腾讯字段映射**
```python
TENCENT_MAPPING = {
    "date": "date",
    "open": "open",
    "close": "close",
    "high": "high",
    "low": "low",
    "amount": "volume"
}
```

---

## **12.3 腾讯特殊处理**
腾讯：

```plain
amount = 成交量（手）
```

标准化时：

```python
df["volume"] = df["amount"]
df["amount"] = None
```

---

# **十三、缺失字段规范**
不同数据源缺失字段：

必须：

```plain
使用 None / NaN 填充
```

禁止：

```plain
随意删除字段
```

---

# **十四、存储层设计**
系统同时支持：

| **格式** | **用途** |
| --- | --- |
| CSV | 调试/人工查看 |
| Parquet | 高性能分析 |


---

# **十五、CSV存储规范**
文件：

```plain
storage/csv_storage.py
```

---

## **CSV要求**
| **项目** | **要求** |
| --- | --- |
| 编码 | utf-8-sig |
| 股票代码 | 保持字符串 |
| 日期格式 | yyyy-mm-dd |


---

# **十六、Parquet存储规范**
文件：

```plain
storage/parquet_storage.py
```

---

## **Parquet要求**
必须：

```plain
保留 schema
```

必须：

```plain
保留 dtype
```

必须支持：

```plain
高性能读取
```

---

# **十七、本地数据最大化复用**
核心原则：

# **❗**** 不重复请求接口**
---

## **正确流程**
```plain
CSV → DataFrame → Parquet
```

或者：

```plain
Parquet → DataFrame → CSV
```

---

## **禁止**
```plain
重新请求网络接口进行格式转换
```

---

# **十八、数据转换服务**
文件：

```plain
service/convert_service.py
```

---

## **必须实现**
| **功能** | **必须** |
| --- | --- |
| csv_to_parquet | ✅ |
| parquet_to_csv | ✅ |
| schema校验 | ✅ |
| dtype校验 | ✅ |


---

# **十九、增量更新系统**
文件：

```plain
service/update_service.py
```

---

## **核心逻辑**
```plain
1. 读取本地数据
2. 获取最后交易日
3. start_date = last_date + 1
4. 拉取增量数据
5. 标准化
6. merge
7. 日期去重
8. 保存 CSV
9. 保存 Parquet
```

---

## **去重规则**
```python
drop_duplicates(subset=["date"])
```

---

# **二十、交易日系统**
文件：

```plain
service/trade_date_service.py
```

---

## **功能要求**
| **功能** | **必须** |
| --- | --- |
| 获取交易日历 | ✅ |
| 判断交易日 | ✅ |
| 获取最近交易日 | ✅ |
| 判断是否开盘 | ✅ |


---

# **二十一、调度系统**
文件：

```plain
scheduler/daily_update.py
```

---

## **调度要求**
交易日：

```plain
15:30
```

自动执行：

```plain
增量更新
```

---

## **非交易日**
自动跳过。

---

# **二十二、并发更新系统**
使用：

```python
ThreadPoolExecutor
```

---

## **默认配置**
```python
max_workers=5
```

---

## **防止**
+ 风控
+ 网络阻塞
+ CPU过高

---

# **二十三、fallback机制**
必须支持：

```plain
腾讯失败 → 东方财富
```

---

# **二十四、重试机制**
每只股票：

```plain
最多重试3次
```

失败后：

```plain
sleep(2)
```

---

# **二十五、日志系统**
使用：

```python
logging
```

---

## **日志目录**
```plain
logs/app.log
```

---

## **日志级别**
| **级别** | **用途** |
| --- | --- |
| INFO | 正常 |
| WARNING | 空数据 |
| ERROR | 下载失败 |


---

# **二十六、Metadata设计（新增）**
文件：

```plain
storage/metadata_storage.py
```

---

## **每只股票 metadata**
```json
{
  "code": "000001",
  "source": "eastmoney",
  "adjust": "qfq",
  "last_update": "2026-05-11",
  "rows": 5210,
  "storage": [
    "csv",
    "parquet"
  ]
}
```

---

# **二十七、数据质量要求**
必须检查：

| **项目** | **必须** |
| --- | --- |
| 空DataFrame | ✅ |
| 重复日期 | ✅ |
| 日期格式 | ✅ |
| 股票代码长度 | ✅ |
| schema完整性 | ✅ |


---

# **二十八、错误处理要求**
所有网络请求：

必须：

```python
try / except
```

---

## **禁止**
```plain
程序整体崩溃
```

---

# **二十九、性能目标**
| **项目** | **目标** |
| --- | --- |
| 股票列表获取 | <10秒 |
| 单只股票更新 | <3秒 |
| 5000只股票支持并发 | ✅ |
| CSV转Parquet | 秒级 |


---

# **三十、未来扩展规划**
| **功能** | **版本** |
| --- | --- |
| 技术指标 | V2 |
| 回测系统 | V2 |
| 因子系统 | V3 |
| DuckDB | V3 |
| ClickHouse | V4 |
| 实时行情 | V4 |
| Web UI | V5 |


---

# **三十一、系统定位总结**
本系统不是：

```plain
简单股票脚本
```

而是：

# **🚀**** “工程化量化数据基础设施”**
核心思想：

```plain
数据稳定性 > 策略复杂度
```

系统目标：

```plain
最大化复用本地数据
最小化网络请求
统一多数据源 schema
构建标准化金融数据平台
```
