import logging
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler
from typing import Optional


LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# 日志配置常量
LOG_CONFIG = {
    "console_level": logging.INFO,
    "file_level": logging.DEBUG,
    "backup_days": 30,  # 保留最近30天的日志
    "max_bytes": 10 * 1024 * 1024,  # 单个日志文件最大10MB
    "encoding": "utf-8",
}


def _clean_old_logs():
    """清理过期的日志文件"""
    try:
        cutoff_date = datetime.now() - timedelta(days=LOG_CONFIG["backup_days"])
        cutoff_str = cutoff_date.strftime("%Y%m%d")
        
        for log_file in LOG_DIR.glob("app_*.log"):
            # 提取日期部分
            filename = log_file.name
            if filename.startswith("app_") and filename.endswith(".log"):
                date_str = filename[4:-4]
                if date_str < cutoff_str:
                    log_file.unlink()
                    logging.debug(f"清理过期日志: {log_file}")
                    
    except Exception as e:
        # 如果清理失败，只是记录警告，不影响程序运行
        print(f"清理过期日志失败: {e}")


def setup_logger(name: str = "crazy-money") -> logging.Logger:
    """
    创建并配置日志记录器
    
    Args:
        name: 日志记录器名称
    
    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)

    # 如果已经配置过，直接返回
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    # 日志格式：时间 | 级别 | 模块:行号 | 进程ID | 线程ID | 消息
    log_format = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | "
        "PID:%(process)d | TID:%(thread)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(LOG_CONFIG["console_level"])
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)

    # 文件处理器 - 按天轮转
    log_file = LOG_DIR / "app.log"
    file_handler = TimedRotatingFileHandler(
        log_file,
        when="midnight",           # 每天午夜轮转
        interval=1,               # 间隔1天
        backupCount=LOG_CONFIG["backup_days"],  # 保留备份数量
        encoding=LOG_CONFIG["encoding"],
        delay=False
    )
    file_handler.setLevel(LOG_CONFIG["file_level"])
    file_handler.setFormatter(log_format)
    
    # 设置文件名后缀格式
    file_handler.suffix = "%Y%m%d.log"
    
    logger.addHandler(file_handler)

    # 清理过期日志
    _clean_old_logs()

    return logger


def get_log_file_path(date: Optional[str] = None) -> Path:
    """
    获取指定日期的日志文件路径
    
    Args:
        date: 日期字符串，格式 YYYYMMDD，默认为今天
    
    Returns:
        日志文件路径
    """
    if date is None:
        date = datetime.now().strftime("%Y%m%d")
    
    # 检查是否是今天，如果是今天返回当前日志文件
    today = datetime.now().strftime("%Y%m%d")
    if date == today:
        return LOG_DIR / "app.log"
    
    # 否则返回归档文件
    return LOG_DIR / f"app.{date}.log"


def log_exception(logger: logging.Logger, message: str, exc_info=True):
    """
    统一的异常日志记录
    
    Args:
        logger: 日志记录器
        message: 错误消息
        exc_info: 是否包含异常信息
    """
    logger.error(f"❌ {message}", exc_info=exc_info)


def log_success(logger: logging.Logger, message: str):
    """
    统一的成功日志记录
    
    Args:
        logger: 日志记录器
        message: 成功消息
    """
    logger.info(f"✅ {message}")


def log_warning(logger: logging.Logger, message: str):
    """
    统一的警告日志记录
    
    Args:
        logger: 日志记录器
        message: 警告消息
    """
    logger.warning(f"⚠️ {message}")


def log_progress(logger: logging.Logger, current: int, total: int, message: str = ""):
    """
    统一的进度日志记录
    
    Args:
        logger: 日志记录器
        current: 当前进度
        total: 总数
        message: 附加消息
    """
    percentage = (current / total) * 100 if total > 0 else 0
    logger.info(f"📊 进度: {current}/{total} ({percentage:.1f}%) {message}")
