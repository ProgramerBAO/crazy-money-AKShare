"""
数据源模块
提供多数据源抽象访问接口
"""
from datasource.base import BaseDataSource
from datasource.tencent import TencentDataSource
from datasource.eastmoney import EastMoneyDataSource

__all__ = [
    'BaseDataSource',
    'TencentDataSource',
    'EastMoneyDataSource'
]

# 数据源工厂
_DATA_SOURCE_CLASSES = {
    "tencent": TencentDataSource,
    "eastmoney": EastMoneyDataSource
}

def get_data_source(source_name: str = "tencent") -> BaseDataSource:
    """
    获取数据源实例
    
    Args:
        source_name: 数据源名称 (tencent/eastmoney)
        
    Returns:
        数据源实例
        
    Raises:
        ValueError: 不支持的数据源
    """
    source_cls = _DATA_SOURCE_CLASSES.get(source_name)
    if not source_cls:
        raise ValueError(f"不支持的数据源: {source_name}，支持的数据源: {list(_DATA_SOURCE_CLASSES.keys())}")
    return source_cls()

