"""
每日更新调度器
负责定时触发数据更新
"""
import logging
import time
from datetime import datetime
from typing import Optional

from service.stock_service import StockService
from service.update_service import UpdateService
from service.trade_date_service import TradeDateService

# 日志配置
logger = logging.getLogger(__name__)


class DailyUpdateScheduler:
    """
    每日更新调度器
    """
    
    def __init__(self):
        """
        初始化调度器
        """
        self.stock_service = StockService()
        self.update_service = UpdateService()
        self.trade_date_service = TradeDateService()
        
        logger.debug("每日更新调度器初始化完成")
    
    def run_daily_update(
        self,
        batch_size: Optional[int] = None,
        force_full: bool = False
    ):
        """
        执行每日更新
        
        Args:
            batch_size: 批次大小
            force_full: 是否强制全量下载
        """
        logger.info("=" * 60)
        logger.info("🚀 开始执行每日更新")
        logger.info(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)
        
        # 检查是否为交易日
        if not self.trade_date_service.is_trade_day():
            logger.info("📅 今天不是交易日，跳过更新")
            return
        
        # 获取股票列表
        logger.info("📋 正在获取股票列表...")
        df_stocks = self.stock_service.load_stock_list()
        
        if df_stocks.empty:
            logger.error("❌ 未获取到股票列表，退出")
            return
        
        codes = df_stocks["code"].tolist()
        logger.info(f"✅ 共获取 {len(codes)} 只股票")
        
        # 执行批量更新
        logger.info("🔄 开始批量更新...")
        stats = self.update_service.batch_update(
            codes=codes,
            force_full=force_full,
            batch_size=batch_size
        )
        
        # 输出统计
        logger.info("=" * 60)
        logger.info("📊 更新完成统计:")
        logger.info(f"   ✅ 成功: {stats['success']}")
        logger.info(f"   ❌ 失败: {stats['failed']}")
        logger.info(f"   ⏭️  跳过: {stats['skipped']}")
        logger.info(f"⏰ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)
        
        return stats
    
    def run_forever(
        self,
        check_interval: int = 3600,
        batch_size: Optional[int] = None
    ):
        """
        持续运行，定时检查并更新
        
        Args:
            check_interval: 检查间隔（秒）
            batch_size: 批次大小
        """
        logger.info("🚀 启动持续更新模式...")
        logger.info(f"⏱️  检查间隔: {check_interval}秒")
        
        last_update_date = None
        
        while True:
            try:
                now = datetime.now()
                today_str = now.strftime("%Y-%m-%d")
                
                # 检查是否需要更新
                if last_update_date != today_str:
                    # 检查是否在交易日的15:00之后
                    if self.trade_date_service.is_trade_day(today_str):
                        if now.time() >= datetime.strptime("15:00", "%H:%M").time():
                            logger.info(f"📅 今天是交易日，且已过15:00，开始更新...")
                            self.run_daily_update(batch_size=batch_size)
                            last_update_date = today_str
                        else:
                            logger.info(f"💤 今天是交易日，但还未到15:00，继续等待...")
                    else:
                        logger.info(f"💤 今天不是交易日，继续等待...")
                        last_update_date = today_str
                else:
                    logger.info(f"💤 今天已更新过，继续等待...")
                
                # 等待下一次检查
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                logger.info("👋 收到停止信号，退出...")
                break
            except Exception as e:
                logger.error(f"❌ 调度器异常: {e}", exc_info=True)
                time.sleep(60)  # 出错后等待1分钟再重试
