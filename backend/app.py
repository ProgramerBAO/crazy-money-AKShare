"""
Crazy Money - A股量化数据平台 API 服务
FastAPI 后端服务入口
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Crazy Money API",
    description="A股量化数据平台 API 服务",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routers import stocks, charts, system
from services.progress_manager import progress_manager

app.include_router(stocks.router, prefix="/api/stocks", tags=["股票数据"])
app.include_router(charts.router, prefix="/api/charts", tags=["图表数据"])
app.include_router(system.router, prefix="/api/system", tags=["系统控制"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "crazy-money-api"}

@app.get("/")
async def root():
    return {
        "message": "Crazy Money API Service",
        "version": "1.0.0"
    }

@app.websocket("/ws/{channel}")
async def websocket_endpoint(websocket: WebSocket, channel: str):
    """
    WebSocket 端点，用于实时进度推送

    Args:
        channel: 频道名称，如 'download', 'init' 等
    """
    await progress_manager.connect(websocket, channel)
    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"收到 WebSocket 消息: channel={channel}, data={data}")
    except WebSocketDisconnect:
        logger.info(f"WebSocket 客户端断开: channel={channel}")
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}")
    finally:
        await progress_manager.disconnect(websocket, channel)

if __name__ == "__main__":
    import uvicorn
    logger.info("启动 Crazy Money API 服务...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
