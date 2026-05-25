from datetime import datetime, timedelta
from typing import Optional, Set
import akshare as ak
from utils.logger import setup_logger

logger = setup_logger(__name__)

# ==================== 缓存机制 ====================
_trade_dates_cache: Set[str] = set()
_trade_dates_cache_date: Optional[str] = None
_CACHE_EXPIRE_DAYS = 7  # 缓存有效期7天


def _load_trade_calendar() -> None:
    """
    从 AKShare 加载交易日历并缓存
    
    使用 akshare 的 tool_trade_date_hist_sina 接口获取完整的交易日历
    """
    global _trade_dates_cache, _trade_dates_cache_date
    
    try:
        # 使用 AKShare 获取交易日历
        df = ak.tool_trade_date_hist_sina()
        
        # 转换为日期字符串集合
        _trade_dates_cache = set(df['trade_date'].astype(str).tolist())
        _trade_dates_cache_date = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"✅ 成功加载交易日历，共 {len(_trade_dates_cache)} 个交易日")
        
    except Exception as e:
        logger.warning(f"❌ 从 AKShare 获取交易日历失败: {e}")
        # 如果 AKShare 接口失败，使用本地节假日数据作为备选
        _load_fallback_calendar()


def _load_fallback_calendar() -> None:
    """
    加载本地备选日历（当 AKShare 接口失败时使用）
    """
    global _trade_dates_cache, _trade_dates_cache_date
    
    logger.info("⚠️ 使用本地备选交易日历")
    
    # 生成基础交易日历（周一到周五）
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2030, 12, 31)
    
    trade_dates = set()
    current = start_date
    
    while current <= end_date:
        # 周末跳过
        if current.weekday() < 5:
            date_str = current.strftime("%Y-%m-%d")
            trade_dates.add(date_str)
        current += timedelta(days=1)
    
    # 移除节假日
    holidays = {
        # 2024年
        "2024-01-01", "2024-02-10", "2024-02-11", "2024-02-12", "2024-02-13", "2024-02-14",
        "2024-04-04", "2024-04-05", "2024-04-06",
        "2024-05-01", "2024-05-02", "2024-05-03",
        "2024-06-10", "2024-06-11", "2024-06-12",
        "2024-09-15", "2024-09-16", "2024-09-17",
        "2024-10-01", "2024-10-02", "2024-10-03", "2024-10-04", "2024-10-05", "2024-10-06", "2024-10-07",
        # 2025年
        "2025-01-01", "2025-01-29", "2025-01-30", "2025-01-31", "2025-02-01", "2025-02-02", "2025-02-03",
        "2025-04-04", "2025-04-05", "2025-04-06",
        "2025-05-01", "2025-05-02", "2025-05-03", "2025-05-04", "2025-05-05",
        "2025-06-08", "2025-06-09", "2025-06-10",
        "2025-09-29", "2025-09-30", "2025-10-01", "2025-10-02", "2025-10-03", "2025-10-04", "2025-10-05", "2025-10-06", "2025-10-07", "2025-10-08",
        # 2026年
        "2026-01-01", "2026-01-28", "2026-01-29", "2026-01-30", "2026-01-31", "2026-02-01", "2026-02-02",
        "2026-04-04", "2026-04-05", "2026-04-06",
        "2026-05-01", "2026-05-02", "2026-05-03", "2026-05-04", "2026-05-05",
        "2026-06-19", "2026-06-20", "2026-06-21",
        "2026-10-01", "2026-10-02", "2026-10-03", "2026-10-04", "2026-10-05", "2026-10-06", "2026-10-07", "2026-10-08",
    }
    
    trade_dates -= holidays
    _trade_dates_cache = trade_dates
    _trade_dates_cache_date = datetime.now().strftime("%Y-%m-%d")
    
    logger.info(f"✅ 已加载本地备选日历，共 {len(_trade_dates_cache)} 个交易日")


def _ensure_cache() -> None:
    """
    确保交易日历缓存已加载且未过期
    """
    global _trade_dates_cache, _trade_dates_cache_date
    
    # 如果缓存为空或过期，重新加载
    if not _trade_dates_cache:
        _load_trade_calendar()
    elif _trade_dates_cache_date:
        cache_age = (datetime.now() - datetime.strptime(_trade_dates_cache_date, "%Y-%m-%d")).days
        if cache_age >= _CACHE_EXPIRE_DAYS:
            logger.info(f"📅 交易日历缓存已过期（{cache_age}天），重新加载...")
            _load_trade_calendar()


# ==================== 对外接口 ====================

def is_trade_day(date: Optional[str] = None) -> bool:
    """
    判断某一天是否为交易日
    
    Args:
        date: 日期字符串，格式 YYYY-MM-DD，默认为今天
    
    Returns:
        bool: 是否为交易日
    """
    _ensure_cache()
    
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    return date in _trade_dates_cache


def get_last_trade_day(check_date: Optional[str] = None) -> str:
    """
    获取最近一个交易日（相对于检查日期）
    
    Args:
        check_date: 检查日期，默认为现在
    
    Returns:
        str: 最后一个交易日，格式 YYYY-MM-DD
    """
    _ensure_cache()
    
    now = datetime.now()
    
    if check_date is None:
        check_dt = now
    else:
        check_dt = datetime.strptime(check_date, "%Y-%m-%d")
    
    # 如果是在15:00之前，基准日期取昨天
    if check_date is None or check_date == now.strftime("%Y-%m-%d"):
        current_time = now.time()
        if current_time < datetime.strptime("15:00", "%H:%M").time():
            logger.debug("当前时间在15:00前，基准日期取昨天")
            check_dt = check_dt - timedelta(days=1)
    
    # 向前找，直到找到交易日
    current = check_dt
    for _ in range(365):
        date_str = current.strftime("%Y-%m-%d")
        if date_str in _trade_dates_cache:
            return date_str
        current = current - timedelta(days=1)
    
    # 找不到的话返回检查日期
    return check_dt.strftime("%Y-%m-%d")


def get_next_trade_day(check_date: Optional[str] = None) -> str:
    """
    获取下一个交易日（相对于检查日期）
    
    Args:
        check_date: 检查日期，默认为今天
    
    Returns:
        str: 下一个交易日，格式 YYYY-MM-DD
    """
    _ensure_cache()
    
    if check_date is None:
        check_dt = datetime.now()
    else:
        check_dt = datetime.strptime(check_date, "%Y-%m-%d")
    
    # 向后找，直到找到交易日
    current = check_dt
    for _ in range(365):
        date_str = current.strftime("%Y-%m-%d")
        if date_str in _trade_dates_cache:
            return date_str
        current = current + timedelta(days=1)
    
    # 找不到的话返回检查日期
    return check_dt.strftime("%Y-%m-%d")


def is_trade_time(check_time: Optional[str] = None) -> bool:
    """
    判断当前是否为交易时间
    
    A股交易时间：
    - 上午：09:30 - 11:30
    - 下午：13:00 - 15:00
    
    Args:
        check_time: 时间字符串，格式 HH:MM，默认为当前时间
    
    Returns:
        bool: 是否为交易时间
    """
    now = datetime.now()
    
    # 首先检查是否为交易日
    today_str = now.strftime("%Y-%m-%d")
    if not is_trade_day(today_str):
        return False
    
    # 获取当前时间
    if check_time is None:
        current_time = now.time()
    else:
        current_time = datetime.strptime(check_time, "%H:%M").time()
    
    # 定义交易时间段
    morning_start = datetime.strptime("09:30", "%H:%M").time()
    morning_end = datetime.strptime("11:30", "%H:%M").time()
    afternoon_start = datetime.strptime("13:00", "%H:%M").time()
    afternoon_end = datetime.strptime("15:00", "%H:%M").time()
    
    # 判断是否在交易时间内
    is_morning = morning_start <= current_time <= morning_end
    is_afternoon = afternoon_start <= current_time <= afternoon_end
    
    return is_morning or is_afternoon


def is_before_market_open(check_time: Optional[str] = None) -> bool:
    """
    判断是否在开盘前（09:30之前）
    
    Args:
        check_time: 时间字符串，格式 HH:MM，默认为当前时间
    
    Returns:
        bool: 是否在开盘前
    """
    if check_time is None:
        current_time = datetime.now().time()
    else:
        current_time = datetime.strptime(check_time, "%H:%M").time()
    
    market_open = datetime.strptime("09:30", "%H:%M").time()
    return current_time < market_open


def is_lunch_break(check_time: Optional[str] = None) -> bool:
    """
    判断是否在午间休市（11:30-13:00）
    
    Args:
        check_time: 时间字符串，格式 HH:MM，默认为当前时间
    
    Returns:
        bool: 是否在午间休市
    """
    if check_time is None:
        current_time = datetime.now().time()
    else:
        current_time = datetime.strptime(check_time, "%H:%M").time()
    
    lunch_start = datetime.strptime("11:30", "%H:%M").time()
    lunch_end = datetime.strptime("13:00", "%H:%M").time()
    
    return lunch_start <= current_time < lunch_end


def is_after_market_close(check_time: Optional[str] = None) -> bool:
    """
    判断是否已收盘（15:00之后）
    
    Args:
        check_time: 时间字符串，格式 HH:MM，默认为当前时间
    
    Returns:
        bool: 是否已收盘
    """
    if check_time is None:
        current_time = datetime.now().time()
    else:
        current_time = datetime.strptime(check_time, "%H:%M").time()
    
    market_close = datetime.strptime("15:00", "%H:%M").time()
    return current_time >= market_close


def needs_update(last_trade_date: Optional[str], check_date: Optional[str] = None) -> bool:
    """
    判断股票数据是否需要更新
    
    Args:
        last_trade_date: 股票数据的最后交易日
        check_date: 检查日期，默认为现在
    
    Returns:
        bool: 是否需要更新
    """
    if not last_trade_date:
        return True
    
    latest_trade_day = get_last_trade_day(check_date)
    return last_trade_date < latest_trade_day


def get_trade_days(start_date: str, end_date: str) -> list:
    """
    获取指定日期范围内的所有交易日
    
    Args:
        start_date: 开始日期，YYYY-MM-DD
        end_date: 结束日期，YYYY-MM-DD
    
    Returns:
        list: 交易日列表，按日期升序排列
    """
    _ensure_cache()
    
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    trade_days = []
    current = start
    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        if date_str in _trade_dates_cache:
            trade_days.append(date_str)
        current = current + timedelta(days=1)
    
    return trade_days


def clear_cache() -> None:
    """
    清除交易日历缓存
    """
    global _trade_dates_cache, _trade_dates_cache_date
    _trade_dates_cache = set()
    _trade_dates_cache_date = None
    logger.info("🗑️ 交易日历缓存已清除")
