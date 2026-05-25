"""
数据源基类
定义所有数据源必须实现的接口
业务层通过此基类统一访问不同数据源
"""
from abc import ABC, abstractmethod
from typing import Optional
import pandas as pd


class BaseDataSource(ABC):
    """
    数据源抽象基类
    所有具体数据源必须继承此类并实现抽象方法
    """
    
    @abstractmethod
    def get_name(self) -> str:
        """
        获取数据源名称
        
        Returns:
            数据源名称字符串，如 "tencent" 或 "eastmoney"
        """
        pass
    
    @abstractmethod
    def get_stock_list(self) -> pd.DataFrame:
        """
        获取股票列表
        
        Returns:
            DataFrame，包含所有股票的基本信息
            通常包含字段: code, name, market 等
        """
        pass
    
    @abstractmethod
    def get_history(
        self,
        code: str,
        start_date: str,
        end_date: str,
        adjust: str = "qfq"
    ) -> pd.DataFrame:
        """
        获取股票历史数据
        
        Args:
            code: 股票代码，如 "000001"
            start_date: 开始日期，格式 "YYYY-MM-DD"
            end_date: 结束日期，格式 "YYYY-MM-DD"
            adjust: 复权方式，可选 "qfq"(前复权), "hfq"(后复权), "none"(不复权)
            
        Returns:
            DataFrame，包含指定日期范围的历史数据
            返回的是原始数据，需要通过标准化层处理
        """
        pass
    
    def format_code(self, code: str) -> str:
        """
        格式化股票代码，适配当前数据源要求
        默认实现：直接返回原代码，子类可覆盖
        
        Args:
            code: 原始股票代码
            
        Returns:
            适配当前数据源的股票代码
        """
        return code
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.get_name()})"
