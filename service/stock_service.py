"""
股票列表服务
负责获取和管理股票列表
"""
import logging
from pathlib import Path
import pandas as pd
from typing import List, Optional

from config import DATA_DIR
from datasource import get_data_source

# 日志配置
logger = logging.getLogger(__name__)


class StockService:
    """
    股票列表服务
    """
    
    def __init__(self):
        """
        初始化股票服务
        """
        self.stock_list_file = DATA_DIR / "stock_list.csv"
        logger.debug("股票服务初始化完成")
    
    def get_and_save_stock_list(self, source: str = "tencent") -> pd.DataFrame:
        """
        获取并保存股票列表
        
        Args:
            source: 数据源
            
        Returns:
            股票列表DataFrame
        """
        logger.info(f"从 {source} 获取股票列表")
        
        # 从数据源获取
        data_source = get_data_source(source)
        df = data_source.get_stock_list()
        
        if df.empty:
            logger.warning("获取股票列表失败")
            return pd.DataFrame()
        
        # 保存到文件
        self._save_stock_list(df)
        logger.info(f"成功保存 {len(df)} 只股票")
        return df
    
    def load_stock_list(self) -> pd.DataFrame:
        """
        加载本地股票列表
        
        Returns:
            股票列表DataFrame
        """
        if not self.stock_list_file.exists():
            logger.warning("股票列表文件不存在，尝试获取")
            return self.get_and_save_stock_list()
        
        try:
            df = pd.read_csv(self.stock_list_file, dtype={"code": "string"})
            logger.info(f"成功加载 {len(df)} 只股票")
            return df
        except Exception as e:
            logger.error(f"加载股票列表失败: {str(e)}")
            return pd.DataFrame()
    
    def _save_stock_list(self, df: pd.DataFrame) -> None:
        """
        保存股票列表到文件
        
        Args:
            df: 股票列表DataFrame
        """
        try:
            df.to_csv(self.stock_list_file, index=False, encoding="utf-8-sig")
        except Exception as e:
            logger.error(f"保存股票列表失败: {str(e)}")
    
    def get_stock_by_code(self, code: str) -> Optional[pd.Series]:
        """
        根据代码获取股票信息
        
        Args:
            code: 股票代码
            
        Returns:
            股票信息Series，不存在返回None
        """
        df = self.load_stock_list()
        if df.empty:
            return None
        
        code = str(code).zfill(6)
        result = df[df["code"] == code]
        if not result.empty:
            return result.iloc[0]
        return None
