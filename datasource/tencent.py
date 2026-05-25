"""
腾讯数据源实现
使用 akshare 的 stock_zh_a_hist_tx 接口
腾讯数据源字段：date, open, close, high, low, amount
注意：腾讯的 amount 实际是成交量（手），不是成交额
"""
import logging
import pandas as pd
from typing import Optional
import akshare as ak

from datasource.base import BaseDataSource

# 日志配置
logger = logging.getLogger(__name__)


class TencentDataSource(BaseDataSource):
    """
    腾讯数据源实现
    使用 akshare 访问腾讯财经接口
    """

    def __init__(self):
        """
        初始化腾讯数据源
        """
        super().__init__()
        logger.debug("腾讯数据源初始化完成")

    def get_name(self) -> str:
        """
        获取数据源名称

        Returns:
            "tencent"
        """
        return "tencent"

    def format_code(self, code: str) -> str:
        """
        格式化股票代码，适配腾讯接口要求
        腾讯要求: sz000001 或 sh600519 或 bj920108

        Args:
            code: 原始股票代码，如 "000001"

        Returns:
            腾讯格式的股票代码，如 "sz000001"
        """
        code = str(code).zfill(6)

        # 北京证券交易所股票代码: 8xxxxx, 4xxxxx (新代码)
        # 注意: 920xxx 也是北交所，但腾讯接口用 bj 前缀
        if code.startswith("8") or code.startswith("4"):
            # 4, 8 开头是北京证券交易所
            return f"bj{code}"
        elif code.startswith("6") or code.startswith("68"):
            # 6, 68 开头是上海主板/科创板
            return f"sh{code}"
        elif code.startswith("9"):
            # 9 开头: 900xxx 是上海B股, 920xxx 是北交所
            # 北交所用 bj 前缀
            if code.startswith("92") or code.startswith("93"):
                return f"bj{code}"
            else:
                return f"sh{code}"
        else:
            # 0, 2, 3 开头是深圳主板/中小板/创业板
            return f"sz{code}"

    def get_stock_list(self) -> pd.DataFrame:
        """
        获取股票列表

        Returns:
            DataFrame，包含股票代码、名称等信息
        """
        logger.info("从腾讯获取股票列表")

        try:
            # 使用 akshare 获取股票列表
            df = ak.stock_info_a_code_name()

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
            DataFrame，包含腾讯原始格式的历史数据
        """
        # 格式化股票代码为腾讯格式
        tencent_code = self.format_code(code)

        # 格式化日期，腾讯接口需要格式 "YYYYMMDD"
        start_date_tencent = start_date.replace("-", "")
        end_date_tencent = end_date.replace("-", "")

        # 处理复权参数
        # 腾讯接口：qfq-前复权，hfq-后复权，""-不复权
        adjust_param = adjust if adjust != "none" else ""

        logger.debug(
            f"请求腾讯历史数据: code={tencent_code}, "
            f"start={start_date_tencent}, end={end_date_tencent}, adjust={adjust_param}"
        )

        try:
            # 调用 akshare 接口
            df = ak.stock_zh_a_hist_tx(
                symbol=tencent_code,
                start_date=start_date_tencent,
                end_date=end_date_tencent,
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