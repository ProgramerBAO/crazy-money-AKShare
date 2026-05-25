"""
CSV存储服务
用于将标准化数据保存为CSV格式（便于人工查看和调试）
"""
import logging
from pathlib import Path
import pandas as pd
from typing import Optional

from config import HISTORY_CSV_DIR, CSV_ENCODING, CSV_DATE_FORMAT

# 日志配置
logger = logging.getLogger(__name__)


class CSVStorage:
    """
    CSV存储服务
    负责保存和读取CSV格式的历史数据
    """
    
    def __init__(self, storage_dir: Optional[Path] = None):
        """
        初始化CSV存储服务
        
        Args:
            storage_dir: CSV存储目录，默认为配置中的 HISTORY_CSV_DIR
        """
        self.storage_dir = storage_dir or HISTORY_CSV_DIR
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"CSV存储服务初始化完成: {self.storage_dir}")
    
    def get_file_path(self, code: str) -> Path:
        """
        获取股票对应的CSV文件路径
        
        Args:
            code: 股票代码
            
        Returns:
            CSV文件路径
        """
        return self.storage_dir / f"{code}.csv"
    
    def save(self, code: str, df: pd.DataFrame) -> bool:
        """
        保存数据到CSV文件
        
        Args:
            code: 股票代码
            df: 要保存的 DataFrame（必须是标准化格式）
            
        Returns:
            是否保存成功
        """
        if df.empty:
            logger.debug(f"股票 {code} 数据为空，跳过保存")
            return False
        
        file_path = self.get_file_path(code)
        
        try:
            # 保存前确保日期格式化为字符串
            df_out = df.copy()
            if "date" in df_out.columns:
                df_out["date"] = df_out["date"].dt.strftime(CSV_DATE_FORMAT)
            
            # 保存CSV
            df_out.to_csv(
                file_path,
                index=False,
                encoding=CSV_ENCODING
            )
            
            logger.debug(f"成功保存股票 {code} 到 CSV: {len(df)} 条")
            return True
            
        except Exception as e:
            logger.error(f"保存股票 {code} 到 CSV 失败: {str(e)}")
            return False
    
    def load(self, code: str) -> Optional[pd.DataFrame]:
        """
        从CSV文件加载数据
        
        Args:
            code: 股票代码
            
        Returns:
            加载的 DataFrame，失败返回 None
        """
        file_path = self.get_file_path(code)
        
        if not file_path.exists():
            logger.debug(f"股票 {code} 的 CSV 文件不存在")
            return None
        
        try:
            df = pd.read_csv(
                file_path,
                encoding=CSV_ENCODING,
                dtype={"code": "string"}
            )
            
            # 解析日期
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"], errors="coerce")
            
            logger.debug(f"成功从 CSV 加载股票 {code}: {len(df)} 条")
            return df
            
        except Exception as e:
            logger.error(f"从 CSV 加载股票 {code} 失败: {str(e)}")
            return None
    
    def exists(self, code: str) -> bool:
        """
        检查股票CSV文件是否存在
        
        Args:
            code: 股票代码
            
        Returns:
            文件是否存在
        """
        return self.get_file_path(code).exists()
    
    def get_last_date(self, code: str) -> Optional[str]:
        """
        获取股票最新数据日期
        
        Args:
            code: 股票代码
            
        Returns:
            最新日期字符串 "YYYY-MM-DD"，无数据返回 None
        """
        df = self.load(code)
        if df is None or df.empty or "date" not in df.columns:
            return None
        
        last_date = df["date"].max()
        if pd.notna(last_date):
            return last_date.strftime("%Y-%m-%d")
        return None
    
    def delete(self, code: str) -> bool:
        """
        删除股票CSV文件
        
        Args:
            code: 股票代码
            
        Returns:
            是否删除成功
        """
        file_path = self.get_file_path(code)
        if file_path.exists():
            try:
                file_path.unlink()
                logger.debug(f"成功删除股票 {code} 的 CSV 文件")
                return True
            except Exception as e:
                logger.error(f"删除股票 {code} 的 CSV 文件失败: {str(e)}")
        return False
