"""
配置模块 - A股量化数据平台核心配置
包含所有系统级配置参数
"""
from pathlib import Path
from typing import Dict, Any, List

# ========== 基础目录配置 ==========
# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# 数据根目录
DATA_DIR = PROJECT_ROOT / "data"

# 子数据目录
HISTORY_CSV_DIR = DATA_DIR / "history_csv"  # CSV格式历史数据
HISTORY_PARQUET_DIR = DATA_DIR / "history_parquet"  # Parquet格式历史数据
METADATA_DIR = DATA_DIR / "metadata"  # 元数据存储

# 日志目录
LOGS_DIR = PROJECT_ROOT / "logs"

# 确保目录存在
for directory in [DATA_DIR, HISTORY_CSV_DIR, HISTORY_PARQUET_DIR, METADATA_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ========== Canonical Schema（全系统统一数据结构） ==========
# 系统内部统一使用的字段定义
# 所有数据源都需要标准化为此 schema
CANONICAL_SCHEMA: List[str] = [
    "date",         # 交易日 (datetime64)
    "code",         # 股票代码 (string)
    "open",         # 开盘价 (float64)
    "close",        # 收盘价 (float64)
    "high",         # 最高价 (float64)
    "low",          # 最低价 (float64)
    "volume",       # 成交量（手） (int64)
    "amount",       # 成交额（元） (float64)
    "amplitude",    # 振幅 (float64)
    "pct_change",   # 涨跌幅 (float64)
    "price_change", # 涨跌额 (float64)
    "turnover",     # 换手率 (float64)
    "source",       # 数据源 (string)
    "adjust"        # 复权方式 (string)
]

# Canonical Schema 对应的数据类型
CANONICAL_DTYPES: Dict[str, str] = {
    "date": "datetime64[ns]",
    "code": "string",
    "open": "float64",
    "close": "float64",
    "high": "float64",
    "low": "float64",
    "volume": "int64",
    "amount": "float64",
    "amplitude": "float64",
    "pct_change": "float64",
    "price_change": "float64",
    "turnover": "float64",
    "source": "string",
    "adjust": "string"
}

# ========== 数据源配置 ==========
# 默认数据源优先级: 腾讯 -> 东方财富
DEFAULT_DATA_SOURCE = "tencent"  # 主数据源
FALLBACK_DATA_SOURCE = "eastmoney"  # 备用数据源

# 复权方式: qfq(前复权), hfq(后复权), none(不复权)
DEFAULT_ADJUST = "qfq"

# 默认起始日期
DEFAULT_START_DATE = "2020-01-01"

# ========== 并发与限流配置 ==========
# 线程池配置
CONCURRENT_WORKERS = 10  # 并发下载线程数
BATCH_SIZE = 100  # 每批处理股票数
BATCH_PAUSE_SECONDS = 30  # 批次间休息时间

# 限流器配置
RATE_LIMIT_MODE = "fast"  # 限流模式: safe/balanced/fast/extreme
MAX_RETRIES = 3  # 单只股票最大重试次数
RETRY_DELAY = 2  # 失败后重试等待时间(秒)

# ========== 调度器配置 ==========
SCHEDULER_UPDATE_TIME = "15:30"  # 交易日自动更新时间

# ========== CSV存储配置 ==========
CSV_ENCODING = "utf-8-sig"  # CSV文件编码
CSV_DATE_FORMAT = "%Y-%m-%d"  # CSV日期格式

# ========== Parquet存储配置 ==========
PARQUET_ENGINE = "pyarrow"  # Parquet引擎: pyarrow/fastparquet
PARQUET_COMPRESSION = "snappy"  # 压缩方式: snappy/gzip/brotli/none

# ========== 日志配置 ==========
LOG_LEVEL = "INFO"  # 日志级别: DEBUG/INFO/WARNING/ERROR
LOG_BACKUP_DAYS = 30  # 日志文件保留天数

# ========== 全局配置字典 ==========
CONFIG: Dict[str, Any] = {
    "data_dir": str(DATA_DIR),
    "history_csv_dir": str(HISTORY_CSV_DIR),
    "history_parquet_dir": str(HISTORY_PARQUET_DIR),
    "metadata_dir": str(METADATA_DIR),
    "logs_dir": str(LOGS_DIR),
    "canonical_schema": CANONICAL_SCHEMA,
    "canonical_dtypes": CANONICAL_DTYPES,
    "default_data_source": DEFAULT_DATA_SOURCE,
    "fallback_data_source": FALLBACK_DATA_SOURCE,
    "default_adjust": DEFAULT_ADJUST,
    "concurrent_workers": CONCURRENT_WORKERS,
    "batch_size": BATCH_SIZE,
    "batch_pause_seconds": BATCH_PAUSE_SECONDS,
    "rate_limit_mode": RATE_LIMIT_MODE,
    "max_retries": MAX_RETRIES,
    "retry_delay": RETRY_DELAY,
    "scheduler_update_time": SCHEDULER_UPDATE_TIME,
    "csv_encoding": CSV_ENCODING,
    "csv_date_format": CSV_DATE_FORMAT,
    "parquet_engine": PARQUET_ENGINE,
    "parquet_compression": PARQUET_COMPRESSION,
    "log_level": LOG_LEVEL,
    "log_backup_days": LOG_BACKUP_DAYS
}

# ========== 便捷访问函数 ==========
def get_config(key: str, default: Any = None) -> Any:
    """
    获取配置值
    
    Args:
        key: 配置键
        default: 默认值
        
    Returns:
        配置值
    """
    return CONFIG.get(key, default)

def set_config(key: str, value: Any) -> None:
    """
    设置配置值
    
    Args:
        key: 配置键
        value: 配置值
    """
    CONFIG[key] = value
