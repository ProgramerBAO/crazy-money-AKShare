"""
交易日历服务
负责管理交易日历、判断交易日、获取最近交易日等
"""
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Set, List

from config import DATA_DIR

# 日志配置
logger = logging.getLogger(__name__)


class TradeDateService:
    """
    交易日历服务
    """
    
    def __init__(self):
        """
        初始化交易日服务
        """
        self.calendar_file = DATA_DIR / "trade_calendar.csv"
        self._trade_dates_cache: Set[str] = set()
        self._trade_dates_cache_date: Optional[str] = None
        self._CACHE_EXPIRE_DAYS = 7
        
        logger.debug("交易日服务初始化完成")
        self._ensure_cache()
    
    def _ensure_cache(self) -> None:
        """
        确保交易日历缓存已加载且未过期
        """
        # 优先从本地文件加载
        if not self._trade_dates_cache:
            if self.calendar_file.exists():
                self._load_from_file()
            else:
                self._load_fallback_calendar()
                self._save_to_file()
        elif self._trade_dates_cache_date:
            cache_age = (datetime.now() - datetime.strptime(self._trade_dates_cache_date, "%Y-%m-%d")).days
            if cache_age >= self._CACHE_EXPIRE_DAYS:
                logger.info(f"📅 交易日历缓存已过期（{cache_age}天），重新加载...")
                self._load_fallback_calendar()
                self._save_to_file()
    
    def _save_to_file(self) -> None:
        """
        保存交易日历到本地文件
        """
        try:
            # 创建包含所有交易日的DataFrame并保存
            import pandas as pd
            dates = sorted(self._trade_dates_cache)
            df = pd.DataFrame({"trade_date": dates})
            df.to_csv(self.calendar_file, index=False, encoding="utf-8-sig")
            self._trade_dates_cache_date = datetime.now().strftime("%Y-%m-%d")
            logger.debug(f"✅ 交易日历已保存到本地，共 {len(dates)} 个交易日")
        except Exception as e:
            logger.warning(f"❌ 保存交易日历失败: {e}")
    
    def _load_from_file(self) -> None:
        """
        从本地文件加载交易日历
        """
        try:
            import pandas as pd
            df = pd.read_csv(self.calendar_file, encoding="utf-8-sig")
            self._trade_dates_cache = set(df['trade_date'].astype(str).tolist())
            self._trade_dates_cache_date = datetime.now().strftime("%Y-%m-%d")
            logger.info(f"✅ 从本地加载交易日历，共 {len(self._trade_dates_cache)} 个交易日")
        except Exception as e:
            logger.warning(f"❌ 从本地加载交易日历失败: {e}")
            self._load_fallback_calendar()
    
    def _load_fallback_calendar(self) -> None:
        """
        加载本地备选日历
        """
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
        self._trade_dates_cache = trade_dates
        self._trade_dates_cache_date = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"✅ 已加载本地备选日历，共 {len(self._trade_dates_cache)} 个交易日")
    
    def is_trade_day(self, date: Optional[str] = None) -> bool:
        """
        判断某一天是否为交易日
        
        Args:
            date: 日期字符串，格式 YYYY-MM-DD，默认为今天
            
        Returns:
            bool: 是否为交易日
        """
        self._ensure_cache()
        
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        return date in self._trade_dates_cache
    
    def get_last_trade_day(self, check_date: Optional[str] = None) -> str:
        """
        获取最近一个交易日（相对于检查日期）
        规则：
        - 如果检查日期不是今天，直接从检查日期往前找
        - 如果检查日期是今天：
            - 如果现在是交易日且在15:30之后，基准日期是今天
            - 否则，基准日期往前推一天后再找
        
        Args:
            check_date: 检查日期，默认为现在
            
        Returns:
            str: 最后一个交易日，格式 YYYY-MM-DD
        """
        self._ensure_cache()
        
        now = datetime.now()
        
        if check_date is None:
            check_dt = now
            is_today = True
        else:
            check_dt = datetime.strptime(check_date, "%Y-%m-%d")
            is_today = check_date == now.strftime("%Y-%m-%d")
        
        # 处理今天的特殊情况
        if is_today:
            current_time = now.time()
            today_str = now.strftime("%Y-%m-%d")
            is_today_trade_day = today_str in self._trade_dates_cache
            cutoff_time = datetime.strptime("15:30", "%H:%M").time()
            
            if is_today_trade_day and current_time >= cutoff_time:
                # 今天是交易日且过了15:30，基准日期是今天
                logger.debug(f"当前时间在15:30后，且今天({today_str})是交易日，基准日期为今天")
                check_dt = now
            else:
                # 否则，基准日期往前推一天
                logger.debug(f"当前时间在15:30前或今天不是交易日，基准日期往前推一天")
                check_dt = check_dt - timedelta(days=1)
        
        # 向前找，直到找到交易日
        current = check_dt
        for _ in range(365):
            date_str = current.strftime("%Y-%m-%d")
            if date_str in self._trade_dates_cache:
                return date_str
            current = current - timedelta(days=1)
        
        return check_dt.strftime("%Y-%m-%d")
    
    def needs_update(self, last_trade_date: Optional[str], check_date: Optional[str] = None) -> bool:
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
        
        latest_trade_day = self.get_last_trade_day(check_date)
        return last_trade_date < latest_trade_day
