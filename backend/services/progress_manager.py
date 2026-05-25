"""
进度管理器
负责管理 WebSocket 连接和实时推送下载进度
"""
import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ProgressManager:
    """
    进度管理器单例
    管理 WebSocket 连接池和进度广播
    """
    _instance: Optional['ProgressManager'] = None

    def __new__(cls) -> 'ProgressManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._connections: Dict[str, List[WebSocket]] = {}
        self._lock = asyncio.Lock()
        logger.info("进度管理器初始化完成")

    async def connect(self, websocket: WebSocket, channel: str = "download") -> None:
        """
        客户端连接

        Args:
            websocket: WebSocket 连接
            channel: 频道名称 (download, init, etc.)
        """
        await websocket.accept()
        async with self._lock:
            if channel not in self._connections:
                self._connections[channel] = []
            self._connections[channel].append(websocket)
        logger.info(f"WebSocket 客户端连接: channel={channel}, total={len(self._connections.get(channel, []))}")

    async def disconnect(self, websocket: WebSocket, channel: str = "download") -> None:
        """
        客户端断开连接

        Args:
            websocket: WebSocket 连接
            channel: 频道名称
        """
        async with self._lock:
            if channel in self._connections:
                try:
                    self._connections[channel].remove(websocket)
                    logger.info(f"WebSocket 客户端断开: channel={channel}, remaining={len(self._connections[channel])}")
                except ValueError:
                    pass

    async def broadcast(self, channel: str, data: Dict[str, Any]) -> None:
        """
        广播消息到指定频道的所有客户端

        Args:
            channel: 频道名称
            data: 消息数据
        """
        message = json.dumps(data, ensure_ascii=False)
        disconnected = []

        async with self._lock:
            connections = self._connections.get(channel, []).copy()

        for websocket in connections:
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.warning(f"发送消息失败: {e}")
                disconnected.append(websocket)

        if disconnected:
            async with self._lock:
                for ws in disconnected:
                    try:
                        self._connections[channel].remove(ws)
                    except ValueError:
                        pass

    def broadcast_sync(self, channel: str, data: Dict[str, Any]) -> None:
        """
        同步版本的广播（用于非异步上下文）
        会在新的事件循环中执行

        Args:
            channel: 频道名称
            data: 消息数据
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.broadcast(channel, data))
            else:
                loop.run_until_complete(self.broadcast(channel, data))
        except RuntimeError:
            logger.warning("无法广播：没有运行中的事件循环")

    async def send_progress(
        self,
        channel: str,
        task_id: str,
        progress: float,
        message: str,
        current: Optional[int] = None,
        total: Optional[int] = None,
        status: str = "running",
        extra: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        发送进度更新

        Args:
            channel: 频道名称
            task_id: 任务ID
            progress: 进度百分比 (0-100)
            message: 进度消息
            current: 当前处理数量
            total: 总数量
            status: 状态 (running, success, error)
            extra: 额外数据
        """
        data = {
            "type": "progress",
            "task_id": task_id,
            "progress": min(100, max(0, progress)),
            "message": message,
            "current": current,
            "total": total,
            "status": status,
            "timestamp": datetime.now().isoformat(),
        }
        if extra:
            data["extra"] = extra

        await self.broadcast(channel, data)

    async def send_log(
        self,
        channel: str,
        task_id: str,
        level: str,
        message: str
    ) -> None:
        """
        发送日志消息

        Args:
            channel: 频道名称
            task_id: 任务ID
            level: 日志级别 (info, warning, error)
            message: 日志消息
        """
        data = {
            "type": "log",
            "task_id": task_id,
            "level": level,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }
        await self.broadcast(channel, data)

    async def send_complete(
        self,
        channel: str,
        task_id: str,
        success: bool,
        message: str,
        stats: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        发送任务完成消息

        Args:
            channel: 频道名称
            task_id: 任务ID
            success: 是否成功
            message: 完成消息
            stats: 统计数据
        """
        data = {
            "type": "complete",
            "task_id": task_id,
            "success": success,
            "message": message,
            "stats": stats,
            "timestamp": datetime.now().isoformat(),
        }
        await self.broadcast(channel, data)


progress_manager = ProgressManager()