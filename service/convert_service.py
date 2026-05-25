"""
数据转换服务
用于在CSV和Parquet格式之间互相转换
核心原则：不重复请求网络接口，最大化复用本地数据
"""
import logging
from typing import Optional
import pandas as pd

from storage import CSVStorage, ParquetStorage
from config import CANONICAL_SCHEMA

# 日志配置
logger = logging.getLogger(__name__)


class ConvertService:
    """
    数据转换服务
    提供CSV和Parquet格式之间的互相转换
    """
    
    def __init__(self):
        """
        初始化转换服务
        """
        self.csv_storage = CSVStorage()
        self.parquet_storage = ParquetStorage()
        logger.debug("转换服务初始化完成")
    
    def csv_to_parquet(self, code: str) -> bool:
        """
        将CSV转换为Parquet
        从本地CSV读取，不请求网络
        
        Args:
            code: 股票代码
            
        Returns:
            是否转换成功
        """
        logger.debug(f"CSV -> Parquet: {code}")
        
        # 检查CSV是否存在
        if not self.csv_storage.exists(code):
            logger.warning(f"股票 {code} 的CSV不存在，无法转换")
            return False
        
        # 读取CSV
        df = self.csv_storage.load(code)
        if df is None or df.empty:
            logger.warning(f"股票 {code} 的CSV为空，无法转换")
            return False
        
        # 验证数据完整性
        if not self._validate_schema(df):
            logger.warning(f"股票 {code} 的数据schema不完整")
        
        # 保存为Parquet
        success = self.parquet_storage.save(code, df)
        if success:
            logger.info(f"成功转换 CSV -> Parquet: {code}")
        
        return success
    
    def parquet_to_csv(self, code: str) -> bool:
        """
        将Parquet转换为CSV
        从本地Parquet读取，不请求网络
        
        Args:
            code: 股票代码
            
        Returns:
            是否转换成功
        """
        logger.debug(f"Parquet -> CSV: {code}")
        
        # 检查Parquet是否存在
        if not self.parquet_storage.exists(code):
            logger.warning(f"股票 {code} 的Parquet不存在，无法转换")
            return False
        
        # 读取Parquet
        df = self.parquet_storage.load(code)
        if df is None or df.empty:
            logger.warning(f"股票 {code} 的Parquet为空，无法转换")
            return False
        
        # 保存为CSV
        success = self.csv_storage.save(code, df)
        if success:
            logger.info(f"成功转换 Parquet -> CSV: {code}")
        
        return success
    
    def sync_both(self, code: str) -> bool:
        """
        同步两种格式
        确保CSV和Parquet都有数据，优先从Parquet读取（更快）
        
        Args:
            code: 股票代码
            
        Returns:
            是否同步成功
        """
        csv_exists = self.csv_storage.exists(code)
        parquet_exists = self.parquet_storage.exists(code)
        
        if not csv_exists and not parquet_exists:
            logger.warning(f"股票 {code} 没有任何本地数据")
            return False
        
        # 优先从Parquet同步到CSV（性能更好）
        if parquet_exists and not csv_exists:
            return self.parquet_to_csv(code)
        
        # 如果CSV存在但Parquet不存在，从CSV同步到Parquet
        if csv_exists and not parquet_exists:
            return self.csv_to_parquet(code)
        
        # 两者都存在，视为同步完成
        logger.debug(f"股票 {code} 两种格式都存在，无需同步")
        return True
    
    def batch_sync_all(self, codes: list[str]) -> tuple[int, int]:
        """
        批量同步所有股票
        
        Args:
            codes: 股票代码列表
            
        Returns:
            (成功数量, 失败数量)
        """
        success_count = 0
        fail_count = 0
        
        logger.info(f"开始批量同步 {len(codes)} 只股票")
        
        for code in codes:
            if self.sync_both(code):
                success_count += 1
            else:
                fail_count += 1
        
        logger.info(f"批量同步完成: 成功 {success_count}, 失败 {fail_count}")
        return success_count, fail_count
    
    def _validate_schema(self, df: pd.DataFrame) -> bool:
        """
        验证DataFrame的schema是否完整
        
        Args:
            df: 待验证的DataFrame
            
        Returns:
            schema是否完整
        """
        missing_cols = set(CANONICAL_SCHEMA) - set(df.columns)
        if missing_cols:
            logger.warning(f"缺少列: {missing_cols}")
            return False
        return True
