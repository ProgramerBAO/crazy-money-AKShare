# author: Bob Shen
# date : 11/05/2026 00:33
import akshare as ak
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import requests
import time
from utils.logger import setup_logger, log_exception, log_success, log_warning

logger = setup_logger(__name__)

# 注意：不要在这里初始化 rate_limiter，让 cli.py 统一初始化
# 这样可以保证整个程序使用同一个限流器实例
rate_limiter = None

# ===================== 配置 =====================
HISTORY_DIR: Path = Path("data/history")
HISTORY_DIR.mkdir(parents=True, exist_ok=True)

# 常量定义
DEFAULT_START_DATE = "2020-01-01"
DATE_FORMAT_DISPLAY = "%Y-%m-%d"
DATE_FORMAT_API = "%Y%m%d"
MAX_RETRIES = 3
TIMEOUT_SECONDS = 15

# 新增：复用requests session（减少TCP连接建立开销）
SESSION = requests.Session()
SESSION.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
})
ak.session = SESSION


# ===================== 工具函数 =====================
def to_symbol(code: str) -> str:
    """
    股票代码格式化: 000001 → sz000001; 600000 → sh600000
    
    Args:
        code: 股票代码
        
    Returns:
        格式化后的symbol
    """
    code = str(code).strip().zfill(6)
    return f"sh{code}" if code.startswith("6") else f"sz{code}"


def format_date_for_api(date_str: str) -> str:
    """
    日期格式转换: 2025-12-31 → 20251231 (接口专用)
    
    Args:
        date_str: 日期字符串
        
    Returns:
        格式化后的日期字符串
    """
    return date_str.replace("-", "") if date_str else ""


def get_next_day(date_str: str) -> Optional[str]:
    """
    获取下一个自然日
    
    Args:
        date_str: 日期字符串
        
    Returns:
        下一天的日期字符串，失败返回None
    """
    try:
        current_dt = datetime.strptime(date_str, DATE_FORMAT_DISPLAY)
        next_dt = current_dt + timedelta(days=1)
        return next_dt.strftime(DATE_FORMAT_DISPLAY)
    except (ValueError, TypeError):
        return None


def _exponential_backoff(retry: int, base_delay: float = 2, max_delay: float = 30) -> float:
    """
    指数退避算法
    
    Args:
        retry: 当前重试次数
        base_delay: 基础延迟（秒）
        max_delay: 最大延迟（秒）
        
    Returns:
        计算后的延迟时间
    """
    delay = min(base_delay * (2 ** retry), max_delay)
    # 添加随机抖动
    delay *= (0.8 + 0.4 * (retry % 3) / 3)
    return delay


def batch_get_last_trade_date(codes: List[str]) -> Dict[str, Optional[str]]:
    """
    批量读取本地CSV，返回{股票代码: 最后交易日}
    
    Args:
        codes: 股票代码列表
        
    Returns:
        股票代码到最后交易日的映射
    """
    last_date_map = {}
    for code in codes:
        last_date_map[code] = get_last_trade_date(code)
    return last_date_map


def get_last_trade_date(code: str) -> Optional[str]:
    """
    读取本地CSV，获取最后一条交易日
    
    Args:
        code: 股票代码
        
    Returns:
        最后交易日，文件不存在或读取失败返回None
    """
    file_path = HISTORY_DIR / f"{code}.csv"
    if not file_path.exists():
        return None

    try:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            lines = f.readlines()
            if len(lines) < 2:
                return None
            last_line = lines[-1].strip()
            parts = last_line.split(",")
            if parts:
                return parts[0]
        return None
    except Exception as e:
        logger.debug(f"读取 {code} 最后交易日失败: {e}")
        return None


def save_history_to_csv(code: str, df: pd.DataFrame) -> bool:
    """
    清洗、去重、排序后保存数据
    
    Args:
        code: 股票代码
        df: 数据DataFrame
        
    Returns:
        是否保存成功
    """
    if df.empty:
        logger.warning(f"⚠️ {code} 无有效数据，取消保存")
        return False

    try:
        file_path = HISTORY_DIR / f"{code}.csv"
        
        # 数据标准化处理
        df = df[["date", "open", "high", "low", "close", "amount"]].copy()
        df["date"] = df["date"].astype(str).str.strip()
        df = df.drop_duplicates(subset=["date"], keep="last")
        df = df.sort_values(by="date", ascending=True)

        df.to_csv(file_path, index=False, encoding="utf-8-sig")
        
        latest_date = df["date"].iloc[-1] if not df.empty else "未知"
        log_success(logger, f"{code} 保存成功 | 最新日期: {latest_date} | 数据条数: {len(df)}")
        return True
        
    except Exception as e:
        log_exception(logger, f"{code} 保存失败")
        return False


def get_stock_history_tx(code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    腾讯数据源：获取股票历史K线（前复权）
    
    Args:
        code: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        股票历史数据DataFrame
    """
    global rate_limiter
    if rate_limiter is None:
        from utils.rate_limiter import get_rate_limiter
        rate_limiter = get_rate_limiter()
    
    symbol = to_symbol(code)
    logger.debug(f"🔄 开始下载 {code} ({symbol}) | 区间: {start_date} ~ {end_date}")

    for retry in range(MAX_RETRIES):
        try:
            delay_ms = rate_limiter.before_request()

            api_start = format_date_for_api(start_date)
            api_end = format_date_for_api(end_date)

            df = ak.stock_zh_a_hist_tx(
                symbol=symbol,
                start_date=api_start,
                end_date=api_end,
                adjust="qfq",
                timeout=TIMEOUT_SECONDS
            )

            rate_limiter.after_request(success=True, delay_ms=delay_ms)
            
            if df.empty:
                logger.debug(f"{code} 返回数据为空")
            else:
                logger.debug(f"{code} 下载成功，获取 {len(df)} 条数据")
                
            return df if not df.empty else pd.DataFrame()

        except requests.exceptions.Timeout:
            rate_limiter.after_request(success=False)
            if retry < MAX_RETRIES - 1:
                delay = _exponential_backoff(retry, base_delay=2, max_delay=30)
                log_warning(logger, f"{code} 下载超时，{delay:.1f}秒后重试 ({retry + 1}/{MAX_RETRIES})")
                time.sleep(delay)
            else:
                logger.error(f"❌ {code} 下载超时，已达最大重试次数")

        except requests.exceptions.HTTPError as e:
            rate_limiter.after_request(success=False)
            status_code = e.response.status_code if e.response else 0
            
            if status_code == 429:
                delay = _exponential_backoff(retry, base_delay=5, max_delay=60)
                log_warning(logger, f"{code} 触发限流 (429)，{delay:.1f}秒后重试 ({retry + 1}/{MAX_RETRIES})")
                time.sleep(delay)
            elif retry < MAX_RETRIES - 1:
                delay = _exponential_backoff(retry, base_delay=2, max_delay=30)
                log_warning(logger, f"{code} HTTP错误 {status_code}，{delay:.1f}秒后重试 ({retry + 1}/{MAX_RETRIES})")
                time.sleep(delay)
            else:
                logger.error(f"❌ {code} HTTP错误，已达最大重试次数: {e}")

        except Exception as e:
            rate_limiter.after_request(success=False)
            if retry < MAX_RETRIES - 1:
                delay = _exponential_backoff(retry, base_delay=2, max_delay=30)
                log_warning(logger, f"{code} 下载失败: {str(e)[:100]}，{delay:.1f}秒后重试 ({retry + 1}/{MAX_RETRIES})")
                time.sleep(delay)
            else:
                logger.error(f"❌ {code} 下载失败，已达最大重试次数: {str(e)[:100]}")

    return pd.DataFrame()


def download_stock_history(code: str, force_full: bool = False, last_date: Optional[str] = None) -> bool:
    """
    智能增量下载股票历史数据
    
    Args:
        code: 股票代码
        force_full: 是否强制全量下载
        last_date: 已知的最后交易日（用于优化，避免重复IO）
        
    Returns:
        是否下载成功
        
    Raises:
        ValueError: 当股票无需更新时（用于批次处理判断）
    """
    code = str(code).zfill(6)
    end_date = datetime.now().strftime(DATE_FORMAT_DISPLAY)

    # 确定开始日期
    if not force_full:
        last_trade_date = last_date or get_last_trade_date(code)
        start_date = get_next_day(last_trade_date) if last_trade_date else DEFAULT_START_DATE
    else:
        start_date = DEFAULT_START_DATE

    # 如果开始日期大于结束日期，说明无需更新
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, DATE_FORMAT_DISPLAY)
            end_dt = datetime.strptime(end_date, DATE_FORMAT_DISPLAY)
            if start_dt > end_dt:
                logger.debug(f"✅ {code} 数据已是最新，跳过下载")
                raise ValueError(f"{code} 数据已是最新，无需更新")
        except ValueError as e:
            if "数据已是最新" in str(e):
                raise
            pass

    logger.info(f"📥 {code} | 下载区间: {start_date} → {end_date}")

    # 下载新数据
    df_new = get_stock_history_tx(code, start_date, end_date)
    
    # 判断是否为新股票（文件不存在）
    file_path = HISTORY_DIR / f"{code}.csv"
    is_new_stock = not file_path.exists()
    
    if df_new.empty:
        if is_new_stock:
            # 新股票下载失败，返回False
            logger.error(f"❌ {code} 下载失败：新股票但返回空数据")
            return False
        else:
            # 已有文件且返回空，说明数据已是最新（API已调用但无新数据）
            logger.info(f"✅ {code} 数据已是最新，无需更新")
            return True

    logger.info(f"📊 {code} 新增数据: {len(df_new)} 条")

    # 合并历史数据
    file_path = HISTORY_DIR / f"{code}.csv"
    if file_path.exists():
        try:
            df_old = pd.read_csv(
                file_path,
                usecols=["date", "open", "high", "low", "close", "amount"],
                dtype={"date": str}
            )
            df_all = pd.concat([df_old, df_new], ignore_index=True)
        except Exception as e:
            log_exception(logger, f"{code} 读取历史数据失败，仅保存新数据")
            df_all = df_new
    else:
        df_all = df_new

    # 保存最终数据
    return save_history_to_csv(code, df_all)



