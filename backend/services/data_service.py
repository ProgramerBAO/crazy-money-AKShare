"""
数据服务
负责读取和处理股票数据
"""
import logging
import time
from pathlib import Path
import pandas as pd
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

class DataService:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent.resolve()
        self.data_dir = self.project_root / "data"
        self.history_csv_dir = self.data_dir / "history_csv"
        self.history_parquet_dir = self.data_dir / "history_parquet"
        self.stock_list_file = self.data_dir / "stock_list.csv"
        self.stock_list_parquet_file = self.data_dir / "stock_list.parquet"
        
        self._stock_list_cache = None
        self._stock_list_cache_time = 0
        
        logger.debug(f"数据服务初始化完成，数据目录: {self.data_dir}")
    
    def get_stock_list(self) -> List[Dict]:
        cache_ttl = 3600
        
        if self._stock_list_cache is not None and (time.time() - self._stock_list_cache_time) < cache_ttl:
            return self._stock_list_cache
        
        if not self.stock_list_file.exists():
            logger.warning("股票列表文件不存在")
            return []
        
        try:
            if self.stock_list_parquet_file.exists():
                df = pd.read_parquet(self.stock_list_parquet_file)
                logger.debug("从Parquet读取股票列表")
            else:
                df = pd.read_csv(self.stock_list_file, dtype={"code": "string"})
                df.to_parquet(self.stock_list_parquet_file, index=False)
                logger.debug("从CSV读取股票列表并转换为Parquet")
            
            df["code"] = df["code"].astype(str).str.zfill(6)
            
            stocks = []
            for _, row in df.iterrows():
                stocks.append({
                    "code": row["code"],
                    "name": row.get("name", "")
                })
            
            self._stock_list_cache = stocks
            self._stock_list_cache_time = time.time()
            
            return stocks
        except Exception as e:
            logger.error(f"读取股票列表失败: {str(e)}")
            return []
    
    def get_stock_by_code(self, code: str) -> Optional[Dict]:
        stocks = self.get_stock_list()
        for stock in stocks:
            if stock["code"] == code:
                return stock
        return None
    
    def get_stock_history(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        parquet_path = self.history_parquet_dir / f"{code}.parquet"
        csv_path = self.history_csv_dir / f"{code}.csv"
        
        df = pd.DataFrame()
        
        try:
            if parquet_path.exists():
                df = pd.read_parquet(parquet_path)
                logger.debug(f"从Parquet读取股票 {code} 数据")
            elif csv_path.exists():
                df = pd.read_csv(
                    csv_path,
                    dtype={"code": "string"},
                    parse_dates=["date"]
                )
                logger.debug(f"从CSV读取股票 {code} 数据")
                
                if not df.empty and not self.history_parquet_dir.exists():
                    self.history_parquet_dir.mkdir(parents=True, exist_ok=True)
                
                if not df.empty:
                    try:
                        df.to_parquet(parquet_path, index=False)
                        logger.debug(f"已将股票 {code} 数据转换为Parquet格式")
                    except Exception as e:
                        logger.warning(f"转换Parquet格式失败: {str(e)}")
            else:
                logger.warning(f"股票 {code} 的历史数据文件不存在")
                return pd.DataFrame()
            
            if not df.empty:
                if "date" not in df.columns:
                    logger.error(f"股票 {code} 数据缺少date列")
                    return pd.DataFrame()
                
                if not pd.api.types.is_datetime64_any_dtype(df["date"]):
                    df["date"] = pd.to_datetime(df["date"])
                
                if start_date:
                    df = df[df["date"] >= start_date]
                if end_date:
                    df = df[df["date"] <= end_date]
                
                df = df.sort_values("date")
            
            return df
        except Exception as e:
            logger.error(f"读取股票 {code} 历史数据失败: {str(e)}")
            return pd.DataFrame()
    
    def get_stock_summary(self, code: str) -> Optional[Dict]:
        df = self.get_stock_history(code)
        
        if df.empty:
            return None
        
        latest = df.iloc[-1]
        
        summary = {
            "code": code,
            "name": self.get_stock_by_code(code).get("name", ""),
            "latest_date": latest["date"].strftime("%Y-%m-%d") if hasattr(latest["date"], "strftime") else str(latest["date"]),
            "latest_open": float(latest["open"]),
            "latest_close": float(latest["close"]),
            "latest_high": float(latest["high"]),
            "latest_low": float(latest["low"]),
            "latest_volume": float(latest["volume"]) if "volume" in latest and pd.notna(latest["volume"]) else None,
            "latest_amount": float(latest["amount"]) if "amount" in latest and pd.notna(latest["amount"]) else None,
            "total_records": len(df),
            "start_date": df["date"].iloc[0].strftime("%Y-%m-%d") if hasattr(df["date"].iloc[0], "strftime") else str(df["date"].iloc[0]),
            "end_date": df["date"].iloc[-1].strftime("%Y-%m-%d") if hasattr(df["date"].iloc[-1], "strftime") else str(df["date"].iloc[-1]),
            "avg_close": float(df["close"].mean()),
            "max_close": float(df["close"].max()),
            "min_close": float(df["close"].min()),
            "std_close": float(df["close"].std())
        }
        
        if len(df) >= 2:
            prev_close = float(df["close"].iloc[-2])
            summary["change"] = float(latest["close"]) - prev_close
            summary["change_pct"] = (summary["change"] / prev_close) * 100
        else:
            summary["change"] = 0.0
            summary["change_pct"] = 0.0
        
        return summary
