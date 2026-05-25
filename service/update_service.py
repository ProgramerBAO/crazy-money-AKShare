"""
数据更新服务
负责单个/批量更新股票历史数据
"""
import logging
import sys
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

from datasource import get_data_source
from service.normalize_service import NormalizeService
from service.trade_date_service import TradeDateService
from storage import CSVStorage, ParquetStorage, MetadataStorage
from config import (
    DEFAULT_START_DATE, 
    MAX_WORKERS, 
    DATA_SOURCE_DEFAULT,
    ADJUST_DEFAULT
)
from utils.rate_limiter import SmartRateLimiter

# 日志配置
logger = logging.getLogger(__name__)


class UpdateService:
    """
    数据更新服务
    """
    
    def __init__(self):
        """
        初始化更新服务
        """
        self.data_source = get_data_source(DATA_SOURCE_DEFAULT)
        self.normalize_service = NormalizeService()
        self.trade_date_service = TradeDateService()
        self.csv_storage = CSVStorage()
        self.parquet_storage = ParquetStorage()
        self.metadata_storage = MetadataStorage()
        self.rate_limiter = SmartRateLimiter()
        
        logger.debug("更新服务初始化完成")
    
    def update_single(
        self, 
        code: str, 
        force_full: bool = False,
        source: Optional[str] = None,
        adjust: Optional[str] = None
    ) -> bool:
        """
        更新单个股票数据
        
        Args:
            code: 股票代码
            force_full: 是否强制全量下载
            source: 数据源
            adjust: 复权方式
            
        Returns:
            bool: 是否更新成功
            
        Raises:
            ValueError: 当股票无需更新时（用于批次处理判断）
        """
        code = str(code).zfill(6)
        source = source or DATA_SOURCE_DEFAULT
        adjust = adjust or ADJUST_DEFAULT
        
        # 检查是否需要更新
        if not force_full:
            last_trade_date = self._get_stock_last_date(code)
            if not self.trade_date_service.needs_update(last_trade_date):
                logger.debug(f"✅ {code} 数据已是最新，跳过下载")
                raise ValueError(f"{code} 数据已是最新，无需更新")
        
        # 确定下载日期范围
        if not force_full:
            last_trade_date = self._get_stock_last_date(code)
            start_date = self._get_next_day(last_trade_date) if last_trade_date else DEFAULT_START_DATE
        else:
            start_date = DEFAULT_START_DATE
        
        # 确定合适的结束日期（使用与交易日历相同的逻辑）
        end_date = self._get_appropriate_end_date()
        
        # 如果开始日期大于结束日期，说明无需更新
        if start_date and start_date > end_date:
            logger.debug(f"✅ {code} 数据已是最新，跳过下载")
            raise ValueError(f"{code} 数据已是最新，无需更新")
        
        logger.info(f"📥 {code} | 下载区间: {start_date} → {end_date}")
        sys.stdout.flush()
        sys.stderr.flush()
        
        # 下载新数据
        df_raw = self._download_with_retry(code, start_date, end_date, source, adjust)
        
        # 判断是否为新股票
        is_new_stock = not self.csv_storage.exists(code)
        
        if df_raw.empty:
            if is_new_stock:
                # 新股票下载失败
                logger.error(f"❌ {code} 下载失败：新股票但返回空数据")
                return False
            else:
                # 已有文件且返回空，说明数据已是最新
                logger.info(f"✅ {code} 数据已是最新，无需更新")
                return True
        
        logger.info(f"📊 {code} 新增数据: {len(df_raw)} 条")
        sys.stdout.flush()
        sys.stderr.flush()
        
        # 标准化数据
        df_normalized = self.normalize_service.normalize(df_raw, source, code, adjust)
        
        if df_normalized.empty:
            logger.error(f"❌ {code} 标准化后数据为空")
            return False
        
        # 合并历史数据
        df_final = self._merge_with_history(code, df_normalized)
        
        # 保存数据
        if self._save_stock_data(code, df_final, source, adjust):
            return True
        
        return False
    
    def batch_update(
        self,
        codes: List[str],
        force_full: bool = False,
        batch_size: Optional[int] = None,
        source: Optional[str] = None,
        adjust: Optional[str] = None
    ) -> Dict[str, int]:
        """
        批量更新股票数据
        
        Args:
            codes: 股票代码列表
            force_full: 是否强制全量下载
            batch_size: 批次大小（每批次处理多少只）
            source: 数据源
            adjust: 复权方式
            
        Returns:
            Dict: 统计结果 {success, failed, skipped}
        """
        stats = {
            "success": 0,
            "failed": 0,
            "skipped": 0
        }
        
        # 预处理：本地判断，过滤无需更新的
        codes_to_process = []
        for code in codes:
            try:
                last_trade_date = self._get_stock_last_date(code)
                if not force_full and not self.trade_date_service.needs_update(last_trade_date):
                    stats["skipped"] += 1
                    continue
                codes_to_process.append(code)
            except Exception as e:
                logger.debug(f"{code} 预处理判断失败: {e}")
                codes_to_process.append(code)
        
        total_to_process = len(codes_to_process)
        total_stocks = len(codes)
        
        logger.info(f"📋 总数: {total_stocks} | 跳过: {stats['skipped']} | 待处理: {total_to_process}")
        sys.stdout.flush()
        sys.stderr.flush()
        
        if not codes_to_process:
            logger.info("✅ 所有股票已是最新，无需更新")
            return stats
        
        # 逐只处理并实时打印进度
        processed_count = 0
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_code = {
                executor.submit(
                    self.update_single, 
                    code, 
                    force_full, 
                    source, 
                    adjust
                ): code 
                for code in codes_to_process
            }
            
            for future in as_completed(future_to_code):
                code = future_to_code[future]
                try:
                    success = future.result()
                    if success:
                        stats["success"] += 1
                    else:
                        stats["failed"] += 1
                except ValueError:
                    stats["skipped"] += 1
                except Exception as e:
                    logger.error(f"❌ {code} 更新异常: {e}")
                    stats["failed"] += 1
                
                processed_count += 1
                
                # 计算并显示进度
                progress = (processed_count / total_to_process) * 100
                logger.info(f"📊 进度: {processed_count}/{total_to_process} ({progress:.1f}%) | ✅成功: {stats['success']} | ❌失败: {stats['failed']} | ⏭️跳过: {stats['skipped']}")
                sys.stdout.flush()
                sys.stderr.flush()
        
        return stats
    
    def _process_batch(
        self, 
        codes: List[str], 
        force_full: bool,
        source: Optional[str],
        adjust: Optional[str]
    ) -> Dict[str, int]:
        """
        处理单个批次的股票（保留兼容性）
        
        Args:
            codes: 股票代码列表
            force_full: 是否强制全量下载
            source: 数据源
            adjust: 复权方式
            
        Returns:
            Dict: 统计结果
        """
        stats = {
            "success": 0,
            "failed": 0,
            "skipped": 0
        }
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_code = {
                executor.submit(
                    self.update_single, 
                    code, 
                    force_full, 
                    source, 
                    adjust
                ): code 
                for code in codes
            }
            
            for future in as_completed(future_to_code):
                code = future_to_code[future]
                try:
                    success = future.result()
                    if success:
                        stats["success"] += 1
                    else:
                        stats["failed"] += 1
                except ValueError:
                    stats["skipped"] += 1
                except Exception as e:
                    logger.error(f"❌ {code} 更新异常: {e}")
                    stats["failed"] += 1
        
        return stats
    
    def _get_stock_last_date(self, code: str) -> Optional[str]:
        """
        获取股票最后交易日
        
        Args:
            code: 股票代码
            
        Returns:
            Optional[str]: 最后交易日
        """
        # 优先从Parquet读取（更快）
        last_date = self.parquet_storage.get_last_date(code)
        if last_date:
            return last_date
        
        # 从CSV读取
        last_date = self.csv_storage.get_last_date(code)
        if last_date:
            return last_date
        
        return None
    
    def _get_next_day(self, date_str: Optional[str]) -> Optional[str]:
        """
        获取下一个自然日
        
        Args:
            date_str: 日期字符串
            
        Returns:
            Optional[str]: 下一天日期
        """
        if not date_str:
            return None
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return (dt + timedelta(days=1)).strftime("%Y-%m-%d")
        except Exception:
            return None
    
    def _get_appropriate_end_date(self) -> str:
        """
        获取合适的结束日期
        规则：
        - 如果现在是交易日且在15:30之后，返回今天
        - 否则，返回最近一个交易日
        
        Returns:
            str: 合适的结束日期
        """
        return self.trade_date_service.get_last_trade_day()
    
    def _download_with_retry(
        self, 
        code: str, 
        start_date: str, 
        end_date: str,
        source: str,
        adjust: str
    ) -> pd.DataFrame:
        """
        带重试的数据下载
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            source: 数据源
            adjust: 复权方式
            
        Returns:
            pd.DataFrame: 下载的原始数据
        """
        max_retries = 3
        
        for retry in range(max_retries):
            try:
                delay_ms = self.rate_limiter.before_request()
                
                # 使用数据源获取
                data_source = get_data_source(source)
                df = data_source.get_history(code, start_date, end_date, adjust)
                
                self.rate_limiter.after_request(success=True, delay_ms=delay_ms)
                
                if not df.empty:
                    logger.debug(f"{code} 下载成功，获取 {len(df)} 条数据")
                
                return df
                
            except Exception as e:
                self.rate_limiter.after_request(success=False)
                
                if retry < max_retries - 1:
                    delay = min(2 * (2 ** retry), 30)
                    import time
                    logger.warning(f"{code} 下载失败: {str(e)[:100]}，{delay:.1f}秒后重试 ({retry + 1}/{max_retries})")
                    time.sleep(delay)
                else:
                    logger.error(f"❌ {code} 下载失败，已达最大重试次数: {str(e)[:100]}")
        
        return pd.DataFrame()
    
    def _merge_with_history(self, code: str, df_new: pd.DataFrame) -> pd.DataFrame:
        """
        合并历史数据
        
        Args:
            code: 股票代码
            df_new: 新下载的数据
            
        Returns:
            pd.DataFrame: 合并后的数据
        """
        # 优先从Parquet读取历史数据
        df_old = self.parquet_storage.load(code)
        
        if df_old is None:
            # 从CSV读取
            df_old = self.csv_storage.load(code)
        
        if df_old is not None and not df_old.empty:
            # 合并并去重
            df_all = pd.concat([df_old, df_new], ignore_index=True)
            df_all = df_all.drop_duplicates(subset=["date"], keep="last")
            df_all = df_all.sort_values("date").reset_index(drop=True)
            return df_all
        
        return df_new
    
    def _save_stock_data(
        self, 
        code: str, 
        df: pd.DataFrame,
        source: str,
        adjust: str
    ) -> bool:
        """
        保存股票数据（CSV + Parquet）
        
        Args:
            code: 股票代码
            df: 数据
            source: 数据源
            adjust: 复权方式
            
        Returns:
            bool: 是否保存成功
        """
        if df.empty:
            return False
        
        try:
            # 保存CSV
            csv_success = self.csv_storage.save(code, df)
            
            # 保存Parquet
            parquet_success = self.parquet_storage.save(code, df)
            
            # 更新元数据
            last_date = df["date"].iloc[-1].strftime("%Y-%m-%d") if not df.empty else None
            storage_formats = []
            if csv_success:
                storage_formats.append("csv")
            if parquet_success:
                storage_formats.append("parquet")
            
            self.metadata_storage.update(
                code=code,
                source=source,
                adjust=adjust,
                rows=len(df),
                storage=storage_formats
            )
            
            latest_date = last_date or "未知"
            logger.info(f"✅ {code} 保存成功 | 最新日期: {latest_date} | 数据条数: {len(df)}")
            sys.stdout.flush()
            sys.stderr.flush()
            
            return csv_success or parquet_success
            
        except Exception as e:
            logger.error(f"❌ {code} 保存失败: {e}")
            return False
