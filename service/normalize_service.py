"""
数据标准化服务 - 系统核心模块
负责将不同数据源的原始数据统一转换为系统标准 Canonical Schema
"""
import logging
import pandas as pd
from typing import Dict, Optional
from datetime import datetime

from config import CANONICAL_SCHEMA, CANONICAL_DTYPES

# 日志配置
logger = logging.getLogger(__name__)


class NormalizeService:
    """
    数据标准化服务
    将不同数据源的原始数据统一转换为系统标准格式
    """
    
    # 东方财富字段映射表：中文字段 -> 标准英文字段
    EASTMONEY_MAPPING: Dict[str, str] = {
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
    
    # 腾讯字段映射表：英文字段 -> 标准英文字段
    TENCENT_MAPPING: Dict[str, str] = {
        "date": "date",
        "open": "open",
        "close": "close",
        "high": "high",
        "low": "low",
        "amount": "volume"  # 注意：腾讯的 amount 实际上是成交量（手）
    }
    
    @staticmethod
    def normalize_tencent(
        df: pd.DataFrame,
        code: str,
        source: str = "tencent",
        adjust: str = "qfq"
    ) -> pd.DataFrame:
        """
        标准化腾讯数据源的数据
        
        Args:
            df: 腾讯原始数据 DataFrame
            code: 股票代码
            source: 数据源名称
            adjust: 复权方式
            
        Returns:
            标准化后的 DataFrame，符合 Canonical Schema
        """
        if df.empty:
            logger.debug("输入数据为空，返回空 DataFrame")
            return pd.DataFrame()
        
        df = df.copy()
        logger.debug(f"开始标准化腾讯数据: {code}，原始列: {list(df.columns)}")
        
        # 1. 字段重命名
        df = df.rename(columns=NormalizeService.TENCENT_MAPPING)
        
        # 2. 添加缺失字段
        df["code"] = str(code).zfill(6)  # 确保股票代码是6位字符串
        df["amount"] = None  # 腾讯没有成交额，设为 None
        df["amplitude"] = None
        df["pct_change"] = None
        df["price_change"] = None
        df["turnover"] = None
        df["source"] = source
        df["adjust"] = adjust
        
        # 3. 日期格式转换
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        
        # 4. 确保只包含标准 schema 的列
        df = df[CANONICAL_SCHEMA].copy()
        
        # 5. 强制转换数据类型
        df = NormalizeService._enforce_dtypes(df)
        
        # 6. 数据质量检查
        NormalizeService._validate_dataframe(df, code)
        
        logger.debug(f"腾讯数据标准化完成: {code}，行数: {len(df)}")
        return df
    
    @staticmethod
    def normalize_eastmoney(
        df: pd.DataFrame,
        code: str,
        source: str = "eastmoney",
        adjust: str = "qfq"
    ) -> pd.DataFrame:
        """
        标准化东方财富数据源的数据
        
        Args:
            df: 东方财富原始数据 DataFrame
            code: 股票代码
            source: 数据源名称
            adjust: 复权方式
            
        Returns:
            标准化后的 DataFrame，符合 Canonical Schema
        """
        if df.empty:
            logger.debug("输入数据为空，返回空 DataFrame")
            return pd.DataFrame()
        
        df = df.copy()
        logger.debug(f"开始标准化东方财富数据: {code}，原始列: {list(df.columns)}")
        
        # 1. 字段重命名
        df = df.rename(columns=NormalizeService.EASTMONEY_MAPPING)
        
        # 2. 添加缺失字段
        df["code"] = str(code).zfill(6)  # 确保股票代码是6位字符串
        df["source"] = source
        df["adjust"] = adjust
        
        # 3. 日期格式转换
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        
        # 4. 确保只包含标准 schema 的列
        df = df[CANONICAL_SCHEMA].copy()
        
        # 5. 强制转换数据类型
        df = NormalizeService._enforce_dtypes(df)
        
        # 6. 数据质量检查
        NormalizeService._validate_dataframe(df, code)
        
        logger.debug(f"东方财富数据标准化完成: {code}，行数: {len(df)}")
        return df
    
    @staticmethod
    def normalize(
        df: pd.DataFrame,
        source: str,
        code: str,
        adjust: str = "qfq"
    ) -> pd.DataFrame:
        """
        根据数据源类型自动选择标准化方法
        
        Args:
            df: 原始数据 DataFrame
            source: 数据源名称 (tencent/eastmoney)
            code: 股票代码
            adjust: 复权方式
            
        Returns:
            标准化后的 DataFrame
            
        Raises:
            ValueError: 不支持的数据源
        """
        if source == "tencent":
            return NormalizeService.normalize_tencent(df, code, source, adjust)
        elif source == "eastmoney":
            return NormalizeService.normalize_eastmoney(df, code, source, adjust)
        else:
            raise ValueError(f"不支持的数据源: {source}")
    
    @staticmethod
    def _enforce_dtypes(df: pd.DataFrame) -> pd.DataFrame:
        """
        强制转换 DataFrame 的数据类型为标准类型
        
        Args:
            df: 输入 DataFrame
            
        Returns:
            类型转换后的 DataFrame
        """
        df = df.copy()
        
        for col, dtype in CANONICAL_DTYPES.items():
            if col not in df.columns:
                continue
            
            try:
                if dtype.startswith("datetime64"):
                    # 日期类型特殊处理
                    df[col] = pd.to_datetime(df[col], errors="coerce")
                elif dtype == "string":
                    # 字符串类型处理
                    df[col] = df[col].astype("string")
                else:
                    # 数值类型处理
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                    df[col] = df[col].astype(dtype)
            except Exception as e:
                logger.debug(f"列 {col} 类型转换失败，保持原样: {str(e)}")
        
        return df
    
    @staticmethod
    def _validate_dataframe(df: pd.DataFrame, code: str) -> None:
        """
        验证标准化后的 DataFrame 数据质量
        
        Args:
            df: 待验证的 DataFrame
            code: 股票代码
        """
        if df.empty:
            return
        
        # 检查 schema 完整性
        missing_cols = set(CANONICAL_SCHEMA) - set(df.columns)
        if missing_cols:
            logger.warning(f"股票 {code} 缺少列: {missing_cols}")
        
        # 检查重复日期
        if "date" in df.columns:
            duplicate_dates = df.duplicated(subset=["date"]).sum()
            if duplicate_dates > 0:
                logger.warning(f"股票 {code} 有 {duplicate_dates} 条重复日期")
        
        # 检查股票代码长度
        if "code" in df.columns:
            invalid_codes = df["code"].dropna().str.len() != 6
            if invalid_codes.any():
                logger.warning(f"股票 {code} 有 {invalid_codes.sum()} 条代码长度不是6位")
    
    @staticmethod
    def merge_dataframes(
        df_old: Optional[pd.DataFrame],
        df_new: pd.DataFrame,
        drop_duplicates: bool = True
    ) -> pd.DataFrame:
        """
        合并两个 DataFrame（旧数据 + 新数据）
        
        Args:
            df_old: 旧数据 DataFrame（可为 None）
            df_new: 新数据 DataFrame
            drop_duplicates: 是否去重（按日期）
            
        Returns:
            合并后的 DataFrame
        """
        if df_old is None or df_old.empty:
            return df_new.copy()
        
        if df_new.empty:
            return df_old.copy()
        
        # 合并数据
        df_merged = pd.concat([df_old, df_new], ignore_index=True)
        
        # 去重
        if drop_duplicates and "date" in df_merged.columns:
            # 保留新数据（最后出现的）
            df_merged = df_merged.drop_duplicates(subset=["date"], keep="last")
            # 按日期排序
            df_merged = df_merged.sort_values("date").reset_index(drop=True)
        
        return df_merged
