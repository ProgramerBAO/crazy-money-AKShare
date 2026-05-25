"""
图表服务
负责处理图表数据和技术指标
"""
import logging
import pandas as pd
from typing import Optional, List, Dict
import time
from collections import OrderedDict

from .data_service import DataService

logger = logging.getLogger(__name__)

class ChartService:
    """
    图表服务类
    """
    
    MAX_CACHE_SIZE = 100
    CACHE_TTL = 300
    
    def __init__(self):
        """
        初始化图表服务
        """
        self.data_service = DataService()
        self._cache = OrderedDict()
        logger.debug("图表服务初始化完成")
    
    def _get_cache_key(self, code: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        """生成缓存键"""
        return f"{code}_{start_date or 'none'}_{end_date or 'none'}"
    
    def _get_cached_data(self, cache_key: str) -> Optional[pd.DataFrame]:
        """获取缓存数据"""
        if cache_key in self._cache:
            cached_item = self._cache[cache_key]
            if time.time() - cached_item["timestamp"] < self.CACHE_TTL:
                self._cache.move_to_end(cache_key)
                logger.debug(f"命中缓存: {cache_key}")
                return cached_item["data"]
            else:
                del self._cache[cache_key]
                logger.debug(f"缓存过期: {cache_key}")
        return None
    
    def _set_cache(self, cache_key: str, data: pd.DataFrame) -> None:
        """设置缓存"""
        if len(self._cache) >= self.MAX_CACHE_SIZE:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            logger.debug(f"缓存已满，移除最旧项: {oldest_key}")
        
        self._cache[cache_key] = {
            "data": data,
            "timestamp": time.time()
        }
        logger.debug(f"设置缓存: {cache_key}")
    
    def get_kline_data(
        self,
        code: str,
        period: str = "day",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Optional[Dict]:
        """
        获取K线图数据
        
        Args:
            code: 股票代码
            period: 周期（day/week/month）
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            K线数据字典，包含 dates 和 items
        """
        df = self.data_service.get_stock_history(code, start_date, end_date)
        
        if df.empty:
            return None
        
        # 根据周期聚合数据
        if period != "day":
            df = self._aggregate_by_period(df, period)
        
        dates = []
        items = []
        
        for _, row in df.iterrows():
            date_str = row["date"].strftime("%Y-%m-%d") if hasattr(row["date"], "strftime") else str(row["date"])
            dates.append(date_str)
            items.append([
                float(row["open"]) if pd.notna(row["open"]) else 0,
                float(row["close"]) if pd.notna(row["close"]) else 0,
                float(row["low"]) if pd.notna(row["low"]) else 0,
                float(row["high"]) if pd.notna(row["high"]) else 0,
                float(row["volume"]) if "volume" in row and pd.notna(row["volume"]) else 0
            ])
        
        return {
            "dates": dates,
            "items": items
        }
    
    def _aggregate_by_period(self, df: pd.DataFrame, period: str) -> pd.DataFrame:
        """
        按周期聚合数据
        
        Args:
            df: 原始数据
            period: 周期
            
        Returns:
            聚合后的数据
        """
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        
        if period == "week":
            # 按周聚合
            df["period"] = df["date"].dt.isocalendar().week
            df["year"] = df["date"].dt.year
            group_key = ["year", "period"]
        elif period == "month":
            # 按月聚合
            df["period"] = df["date"].dt.month
            df["year"] = df["date"].dt.year
            group_key = ["year", "period"]
        else:
            return df
        
        # 聚合计算
        agg_df = df.groupby(group_key).agg({
            "date": "last",
            "open": "first",
            "close": "last",
            "high": "max",
            "low": "min",
            "volume": "sum"
        }).reset_index()
        
        return agg_df.sort_values("date")
    
    def get_ma_data(
        self,
        code: str,
        periods: List[int],
        period: str = "day",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict:
        """
        获取均线数据
        
        Args:
            code: 股票代码
            periods: 均线周期列表
            period: 数据周期（day/week/month）
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            均线数据字典
        """
        df = self.data_service.get_stock_history(code, start_date, end_date)
        
        if df.empty:
            return {}
        
        # 根据周期聚合数据
        if period != "day":
            df = self._aggregate_by_period(df, period)
        
        result = {
            "dates": []
        }
        
        for period_val in periods:
            df[f"ma{period_val}"] = df["close"].rolling(window=period_val).mean()
        
        for _, row in df.iterrows():
            date_str = row["date"].strftime("%Y-%m-%d") if hasattr(row["date"], "strftime") else str(row["date"])
            result["dates"].append(date_str)
            
            for period_val in periods:
                key = f"ma{period_val}"
                if key not in result:
                    result[key] = []
                result[key].append(round(float(row[key]), 2) if pd.notna(row[key]) else None)
        
        return result
    
    def get_volume_data(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Optional[Dict]:
        """
        获取成交量数据
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            成交量数据字典
        """
        df = self.data_service.get_stock_history(code, start_date, end_date)
        
        if df.empty:
            return None
        
        dates = []
        volumes = []
        colors = []
        
        for i, row in df.iterrows():
            date_str = row["date"].strftime("%Y-%m-%d") if hasattr(row["date"], "strftime") else str(row["date"])
            dates.append(date_str)
            
            volume = float(row["volume"]) if "volume" in row and pd.notna(row["volume"]) else 0
            volumes.append(volume)
            
            # 判断颜色（红涨绿跌）
            if i > 0:
                prev_close = float(df["close"].iloc[i-1])
                current_close = float(row["close"])
                colors.append("#ef4444" if current_close >= prev_close else "#22c55e")
            else:
                colors.append("#ef4444")
        
        return {
            "dates": dates,
            "volumes": volumes,
            "colors": colors
        }
    
    def get_indicators(
        self,
        code: str,
        indicators: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict:
        """
        获取技术指标数据
        
        Args:
            code: 股票代码
            indicators: 指标列表
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            技术指标数据字典
        """
        df = self.data_service.get_stock_history(code, start_date, end_date)
        
        if df.empty:
            return {}
        
        result = {
            "dates": []
        }
        
        # 计算各指标
        for indicator in indicators:
            if indicator.lower() == "macd":
                self._calculate_macd(df, result)
            elif indicator.lower() == "rsi":
                self._calculate_rsi(df, result)
            elif indicator.lower() == "boll":
                self._calculate_boll(df, result)
        
        # 添加日期
        for _, row in df.iterrows():
            date_str = row["date"].strftime("%Y-%m-%d") if hasattr(row["date"], "strftime") else str(row["date"])
            result["dates"].append(date_str)
        
        return result
    
    def _calculate_macd(self, df: pd.DataFrame, result: Dict) -> None:
        """
        计算MACD指标
        """
        # 12日EMA
        df["ema12"] = df["close"].ewm(span=12, adjust=False).mean()
        # 26日EMA
        df["ema26"] = df["close"].ewm(span=26, adjust=False).mean()
        # DIF = EMA12 - EMA26
        df["macd_dif"] = df["ema12"] - df["ema26"]
        # DEA = DIF的9日EMA
        df["macd_dea"] = df["macd_dif"].ewm(span=9, adjust=False).mean()
        # MACD = 2 * (DIF - DEA)
        df["macd_bar"] = 2 * (df["macd_dif"] - df["macd_dea"])
        
        result["macd_dif"] = [float(v) if pd.notna(v) else None for v in df["macd_dif"]]
        result["macd_dea"] = [float(v) if pd.notna(v) else None for v in df["macd_dea"]]
        result["macd_bar"] = [float(v) if pd.notna(v) else None for v in df["macd_bar"]]
    
    def _calculate_rsi(self, df: pd.DataFrame, result: Dict, period: int = 14) -> None:
        """
        计算RSI指标
        """
        delta = df["close"].diff(1)
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=period, min_periods=1).mean()
        avg_loss = loss.rolling(window=period, min_periods=1).mean()
        
        rs = avg_gain / avg_loss
        df["rsi"] = 100 - (100 / (1 + rs))
        
        result["rsi"] = [float(v) if pd.notna(v) else None for v in df["rsi"]]
    
    def _calculate_boll(self, df: pd.DataFrame, result: Dict, period: int = 20) -> None:
        """
        计算布林带指标
        """
        df["boll_mid"] = df["close"].rolling(window=period).mean()
        df["boll_std"] = df["close"].rolling(window=period).std()
        df["boll_up"] = df["boll_mid"] + 2 * df["boll_std"]
        df["boll_down"] = df["boll_mid"] - 2 * df["boll_std"]
        
        result["boll_up"] = [float(v) if pd.notna(v) else None for v in df["boll_up"]]
        result["boll_mid"] = [float(v) if pd.notna(v) else None for v in df["boll_mid"]]
        result["boll_down"] = [float(v) if pd.notna(v) else None for v in df["boll_down"]]
    
    def get_all_chart_data(
        self,
        code: str,
        period: str = "day",
        ma_periods: List[int] = None,
        indicators: List[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict:
        """
        获取所有图表数据（聚合接口）
        
        Args:
            code: 股票代码
            period: 周期（day/week/month）
            ma_periods: 均线周期列表
            indicators: 技术指标列表
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            包含所有图表数据的字典
        """
        if ma_periods is None:
            ma_periods = [5, 10, 20, 60]
        if indicators is None:
            indicators = ["macd", "rsi", "boll"]
        
        cache_key = self._get_cache_key(code, start_date, end_date)
        df = self._get_cached_data(cache_key)
        
        if df is None:
            df = self.data_service.get_stock_history(code, start_date, end_date)
            if not df.empty:
                self._set_cache(cache_key, df)
        
        if df.empty:
            return {
                "kline": None,
                "ma": {},
                "indicators": {}
            }
        
        df_period = self._aggregate_by_period(df, period) if period != "day" else df.copy()
        
        kline_data = self._process_kline_from_df(df_period)
        ma_data = self._process_ma_from_df(df_period, ma_periods)
        indicators_data = self._process_indicators_from_df(df, indicators)
        
        return {
            "kline": kline_data,
            "ma": ma_data,
            "indicators": indicators_data
        }
    
    def _process_kline_from_df(self, df: pd.DataFrame) -> Optional[Dict]:
        """从DataFrame处理K线数据"""
        if df.empty:
            return None
        
        dates = []
        items = []
        
        for _, row in df.iterrows():
            date_str = row["date"].strftime("%Y-%m-%d") if hasattr(row["date"], "strftime") else str(row["date"])
            dates.append(date_str)
            items.append([
                float(row["open"]) if pd.notna(row["open"]) else 0,
                float(row["close"]) if pd.notna(row["close"]) else 0,
                float(row["low"]) if pd.notna(row["low"]) else 0,
                float(row["high"]) if pd.notna(row["high"]) else 0,
                float(row["volume"]) if "volume" in row and pd.notna(row["volume"]) else 0
            ])
        
        return {
            "dates": dates,
            "items": items
        }
    
    def _process_ma_from_df(self, df: pd.DataFrame, periods: List[int]) -> Dict:
        """从DataFrame处理均线数据"""
        if df.empty:
            return {}
        
        result = {"dates": []}
        
        for period_val in periods:
            df[f"ma{period_val}"] = df["close"].rolling(window=period_val).mean()
        
        for _, row in df.iterrows():
            date_str = row["date"].strftime("%Y-%m-%d") if hasattr(row["date"], "strftime") else str(row["date"])
            result["dates"].append(date_str)
            
            for period_val in periods:
                key = f"ma{period_val}"
                if key not in result:
                    result[key] = []
                result[key].append(round(float(row[key]), 2) if pd.notna(row[key]) else None)
        
        return result
    
    def _process_indicators_from_df(self, df: pd.DataFrame, indicators: List[str]) -> Dict:
        """从DataFrame处理技术指标数据"""
        if df.empty:
            return {}
        
        result = {"dates": []}
        
        for indicator in indicators:
            if indicator.lower() == "macd":
                self._calculate_macd(df, result)
            elif indicator.lower() == "rsi":
                self._calculate_rsi(df, result)
            elif indicator.lower() == "boll":
                self._calculate_boll(df, result)
        
        for _, row in df.iterrows():
            date_str = row["date"].strftime("%Y-%m-%d") if hasattr(row["date"], "strftime") else str(row["date"])
            result["dates"].append(date_str)
        
        return result
