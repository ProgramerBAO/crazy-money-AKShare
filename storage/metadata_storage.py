"""
元数据存储服务
用于管理每只股票的元数据信息
记录数据源、更新时间、数据行数、存储格式等
"""
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from config import METADATA_DIR

# 日志配置
logger = logging.getLogger(__name__)


class StockMetadata:
    """
    单只股票的元数据
    """
    
    def __init__(
        self,
        code: str,
        source: str = "tencent",
        adjust: str = "qfq",
        last_update: Optional[str] = None,
        rows: int = 0,
        storage: Optional[List[str]] = None
    ):
        """
        初始化股票元数据
        
        Args:
            code: 股票代码
            source: 数据源
            adjust: 复权方式
            last_update: 最后更新日期
            rows: 数据行数
            storage: 存储格式列表 ["csv", "parquet"]
        """
        self.code = code
        self.source = source
        self.adjust = adjust
        self.last_update = last_update or datetime.now().strftime("%Y-%m-%d")
        self.rows = rows
        self.storage = storage or ["csv", "parquet"]
    
    def to_dict(self) -> Dict:
        """
        转换为字典
        
        Returns:
            元数据字典
        """
        return {
            "code": self.code,
            "source": self.source,
            "adjust": self.adjust,
            "last_update": self.last_update,
            "rows": self.rows,
            "storage": self.storage
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "StockMetadata":
        """
        从字典创建元数据对象
        
        Args:
            data: 元数据字典
            
        Returns:
            StockMetadata 对象
        """
        return cls(
            code=data.get("code", ""),
            source=data.get("source", "tencent"),
            adjust=data.get("adjust", "qfq"),
            last_update=data.get("last_update"),
            rows=data.get("rows", 0),
            storage=data.get("storage")
        )


class MetadataStorage:
    """
    元数据存储服务
    负责保存和读取所有股票的元数据
    """
    
    def __init__(self, storage_dir: Optional[Path] = None):
        """
        初始化元数据存储服务
        
        Args:
            storage_dir: 元数据存储目录，默认为配置中的 METADATA_DIR
        """
        self.storage_dir = storage_dir or METADATA_DIR
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._index_file = self.storage_dir / "index.json"
        self._metadata_cache: Dict[str, StockMetadata] = {}
        self._load_index()
        logger.debug(f"元数据存储服务初始化完成: {self.storage_dir}")
    
    def _load_index(self) -> None:
        """
        加载元数据索引
        """
        if not self._index_file.exists():
            logger.debug("元数据索引文件不存在")
            return
        
        try:
            with open(self._index_file, "r", encoding="utf-8") as f:
                index_data = json.load(f)
            
            for code, data in index_data.items():
                self._metadata_cache[code] = StockMetadata.from_dict(data)
            
            logger.debug(f"成功加载 {len(self._metadata_cache)} 条元数据")
            
        except Exception as e:
            logger.error(f"加载元数据索引失败: {str(e)}")
    
    def _save_index(self) -> None:
        """
        保存元数据索引
        """
        try:
            index_data = {
                code: meta.to_dict()
                for code, meta in self._metadata_cache.items()
            }
            
            with open(self._index_file, "w", encoding="utf-8") as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"成功保存 {len(index_data)} 条元数据")
            
        except Exception as e:
            logger.error(f"保存元数据索引失败: {str(e)}")
    
    def get(self, code: str) -> Optional[StockMetadata]:
        """
        获取股票元数据
        
        Args:
            code: 股票代码
            
        Returns:
            StockMetadata 对象，不存在返回 None
        """
        return self._metadata_cache.get(code)
    
    def save(self, metadata: StockMetadata) -> None:
        """
        保存股票元数据
        
        Args:
            metadata: 股票元数据对象
        """
        code = metadata.code
        self._metadata_cache[code] = metadata
        self._save_index()
        logger.debug(f"保存元数据: {code}")
    
    def update(
        self,
        code: str,
        source: Optional[str] = None,
        adjust: Optional[str] = None,
        rows: Optional[int] = None,
        storage: Optional[List[str]] = None
    ) -> None:
        """
        更新股票元数据
        
        Args:
            code: 股票代码
            source: 数据源（可选）
            adjust: 复权方式（可选）
            rows: 数据行数（可选）
            storage: 存储格式列表（可选）
        """
        metadata = self.get(code)
        if not metadata:
            metadata = StockMetadata(code=code)
        
        if source is not None:
            metadata.source = source
        if adjust is not None:
            metadata.adjust = adjust
        if rows is not None:
            metadata.rows = rows
        if storage is not None:
            metadata.storage = storage
        
        metadata.last_update = datetime.now().strftime("%Y-%m-%d")
        self.save(metadata)
    
    def delete(self, code: str) -> bool:
        """
        删除股票元数据
        
        Args:
            code: 股票代码
            
        Returns:
            是否删除成功
        """
        if code in self._metadata_cache:
            del self._metadata_cache[code]
            self._save_index()
            logger.debug(f"删除元数据: {code}")
            return True
        return False
    
    def list_all(self) -> List[StockMetadata]:
        """
        列出所有股票元数据
        
        Returns:
            StockMetadata 对象列表
        """
        return list(self._metadata_cache.values())
    
    def get_stale_stocks(self, latest_trade_day: str) -> List[str]:
        """
        获取需要更新的股票列表
        
        Args:
            latest_trade_day: 最新交易日
            
        Returns:
            需要更新的股票代码列表
        """
        stale_codes = []
        
        for code, metadata in self._metadata_cache.items():
            if metadata.last_update < latest_trade_day:
                stale_codes.append(code)
        
        return stale_codes
