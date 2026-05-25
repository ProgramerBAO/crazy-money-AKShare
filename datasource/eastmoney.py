"""
东方财富数据源实现
使用 akshare 的 stock_zh_a_hist 接口
东方财富数据源字段：日期, 股票代码, 开盘, 收盘, 最高, 最低, 成交量, 成交额, 振幅, 涨跌幅, 涨跌额, 换手率
"""
import logging
import pandas as pd
from typing import Optional
import akshare as ak

from datasource.base import BaseDataSource

# 日志配置
logger = logging.getLogger(__name__)


class EastMoneyDataSource(BaseDataSource):
    """
    东方财富数据源实现
    使用 akshare 访问东方财富接口
    """
    
    def __init__(self):
        """
        初始化东方财富数据源
        """
        super().__init__()
        logger.debug("东方财富数据源初始化完成")
    
    def get_name(self) -> str:
        """
        获取数据源名称
        
        Returns:
            "eastmoney"
        """
        return "eastmoney"
    
    def format_code(self, code: str) -> str:
        """
        格式化股票代码，适配东方财富接口要求
        东方财富要求: 6位纯数字代码，如 "000001"
        
        Args:
            code: 原始股票代码
            
        Returns:
            东方财富格式的股票代码，如 "000001"
        """
        return str(code).zfill(6)
    
    def get_stock_list(self) -> pd.DataFrame:
        """
        获取股票列表
        
        Returns:
            DataFrame，包含股票代码、名称等信息
        """
        logger.info("从东方财富获取股票列表")
        
        try:
            # 使用 akshare 获取股票列表
            df = ak.stock_zh_a_spot_em()
            
            # 重命名列，统一格式
            if not df.empty:
                if "代码" in df.columns:
                    df = df.rename(columns={"代码": "code", "名称": "name"})
                
                # 确保股票代码是6位字符串
                df["code"] = df["code"].astype(str).str.zfill(6)
                
                # 只保留需要的列
                df = df[["code", "name"]].copy()
                logger.info(f"成功获取 {len(df)} 只股票")
            
            return df
            
        except Exception as e:
            logger.error(f"获取股票列表失败: {str(e)}")
            return pd.DataFrame()
    
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
            DataFrame，包含东方财富原始格式的历史数据
        """
        # 格式化股票代码
        eastmoney_code = self.format_code(code)
        
        # 格式化日期，东方财富接口需要格式 "YYYYMMDD"
        start_date_em = start_date.replace("-", "")
        end_date_em = end_date.replace("-", "")
        
        # 处理复权参数
        # 东方财富接口：qfq-前复权，hfq-后复权，""-不复权
        adjust_param = adjust if adjust != "none" else ""
        
        logger.debug(
            f"请求东方财富历史数据: code={eastmoney_code}, "
            f"start={start_date_em}, end={end_date_em}, adjust={adjust_param}"
        )
        
        try:
            # 调用 akshare 接口
            df = ak.stock_zh_a_hist(
                symbol=eastmoney_code,
                period="daily",
                start_date=start_date_em,
                end_date=end_date_em,
                adjust=adjust_param
            )
            
            if df.empty:
                logger.debug(f"股票 {code} 返回空数据")
                return pd.DataFrame()
            
            logger.debug(f"成功获取股票 {code} 的 {len(df)} 条历史数据")
            return df
            
        except Exception as e:
            logger.error(f"获取股票 {code} 历史数据失败: {str(e)}")
            return pd.DataFrame()
