import time
import threading
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
from utils.logger import setup_logger

logger = setup_logger(__name__)

# 延迟导入以避免循环导入
from utils.date_utils import (
    is_trade_day,
    get_last_trade_day,
    is_trade_time,
    is_after_market_close,
    needs_update,
    clear_cache as clear_date_cache
)
from utils.rate_limiter import get_rate_limiter

# ==================== 配置常量 ====================
SCHEDULER_CONFIG = {
    "update_interval_seconds": 60,  # 检查间隔（秒）
    "batch_size": 100,              # 每批处理数量
    "batch_pause_seconds": 30,      # 批次间休息时间
    "max_workers": 12,              # 并发线程数
    "retry_count": 3,               # 失败重试次数
    "fail_log_file": "data/failed_stocks.json",  # 失败记录文件
    "progress_file": "data/update_progress.json",  # 进度记录文件
}


class UpdateScheduler:
    """
    自动增量更新调度器
    
    功能：
    - 自动识别交易日
    - 收盘后自动更新
    - 并发更新股票
    - 自动重试失败任务
    - 断点续传
    - 数据完整性检查
    """
    
    def __init__(self):
        self._running = False
        self._thread = None
        self._rate_limiter = get_rate_limiter()
        self._lock = threading.Lock()
        self._progress = self._load_progress()
        self._failed_stocks = self._load_failed_stocks()
    
    def _load_progress(self) -> Dict:
        """加载上次更新进度"""
        progress_file = Path(SCHEDULER_CONFIG["progress_file"])
        if progress_file.exists():
            try:
                with open(progress_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载进度文件失败: {e}")
        return {"last_update_date": None, "completed_codes": [], "in_progress": False}
    
    def _save_progress(self):
        """保存更新进度"""
        progress_file = Path(SCHEDULER_CONFIG["progress_file"])
        try:
            with open(progress_file, "w", encoding="utf-8") as f:
                json.dump(self._progress, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存进度文件失败: {e}")
    
    def _load_failed_stocks(self) -> Dict:
        """加载失败股票记录"""
        fail_file = Path(SCHEDULER_CONFIG["fail_log_file"])
        if fail_file.exists():
            try:
                with open(fail_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载失败记录文件失败: {e}")
        return {}
    
    def _save_failed_stocks(self):
        """保存失败股票记录"""
        fail_file = Path(SCHEDULER_CONFIG["fail_log_file"])
        try:
            with open(fail_file, "w", encoding="utf-8") as f:
                json.dump(self._failed_stocks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存失败记录文件失败: {e}")
    
    def _should_run_update(self) -> bool:
        """判断是否应该执行更新"""
        # 检查是否在交易日
        today = datetime.now().strftime("%Y-%m-%d")
        if not is_trade_day(today):
            logger.debug(f"今日 {today} 非交易日，跳过更新")
            return False
        
        # 检查是否收盘后（15:00之后）
        if not is_after_market_close():
            logger.debug("市场尚未收盘，等待中...")
            return False
        
        # 检查是否今天已经更新过
        if self._progress.get("last_update_date") == today:
            logger.debug(f"今日 {today} 已完成更新，跳过")
            return False
        
        return True
    
    def _update_single_stock(self, code: str, name: str, last_date_map: Dict) -> bool:
        """更新单只股票数据"""
        # 延迟导入以避免循环导入
        from service.history_service import download_stock_history
        
        code = str(code).zfill(6)
        try:
            download_stock_history(code, last_date=last_date_map.get(code))
            return True
        except Exception as e:
            logger.error(f"{code} {name} 更新失败: {e}")
            return False
    
    def _run_update(self):
        """执行更新任务"""
        # 延迟导入以避免循环导入
        from service.stock_service import load_stock_list
        from service.history_service import batch_get_last_trade_date
        
        logger.info("===== 开始自动增量更新 =====")
        
        # 加载股票列表
        stock_df = load_stock_list()
        if stock_df.empty:
            logger.error("股票列表为空，无法更新")
            return
        
        # 获取真正的最后交易日
        latest_trade_day = get_last_trade_day()
        logger.info(f"📅 基准交易日: {latest_trade_day}")
        
        # 批量获取所有股票的最后交易日
        codes = [str(row.code).zfill(6) for row in stock_df.itertuples(index=False)]
        names = [row.name for row in stock_df.itertuples(index=False)]
        last_date_map = batch_get_last_trade_date(codes)
        
        # 区分需要更新和不需要更新的股票
        need_update = []
        already_latest = []
        
        for code, name in zip(codes, names):
            last_date = last_date_map.get(code)
            if last_date and not needs_update(last_date):
                already_latest.append((code, name))
            else:
                need_update.append((code, name))
        
        # 进一步过滤：通过本地判断移除无需调用API的股票
        truly_need_update = []
        for code, name in need_update:
            last_date = last_date_map.get(code)
            # 本地快速判断：如果最后交易日就是今天，无需更新
            if last_date and last_date >= latest_trade_day:
                already_latest.append((code, name))
            else:
                truly_need_update.append((code, name))
        
        need_update = truly_need_update
        
        logger.info(f"📊 总计: {len(codes)} 只 | 需更新: {len(need_update)} 只 | 已是最新: {len(already_latest)} 只")
        
        if not need_update:
            logger.info("🎉 所有股票都已是最新，无需更新！")
            self._progress["last_update_date"] = datetime.now().strftime("%Y-%m-%d")
            self._save_progress()
            return
        
        # 执行更新
        success_count = len(already_latest)
        fail_count = 0
        failed_stocks = {}
        
        batch_size = SCHEDULER_CONFIG["batch_size"]
        max_workers = SCHEDULER_CONFIG["max_workers"]
        pause_time = SCHEDULER_CONFIG["batch_pause_seconds"]
        
        for batch_start in range(0, len(need_update), batch_size):
            batch_end = min(batch_start + batch_size, len(need_update))
            batch_stocks = need_update[batch_start:batch_end]
            
            logger.info(f"\n----- 处理批次 {batch_start//batch_size + 1}/{(len(need_update) + batch_size - 1)//batch_size} "
                        f"({batch_start + 1}-{batch_end}/{len(need_update)}) -----")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_stock = {
                    executor.submit(self._update_single_stock, code, name, last_date_map): (code, name)
                    for code, name in batch_stocks
                }
                
                for future in as_completed(future_to_stock):
                    code, name = future_to_stock[future]
                    try:
                        if future.result():
                            success_count += 1
                        else:
                            fail_count += 1
                            failed_stocks[code] = {
                                "name": name,
                                "error": "未知错误",
                                "retry_count": 0,
                                "last_attempt": datetime.now().isoformat()
                            }
                    except ValueError as e:
                        # 股票无需更新，从批次中跳过
                        if "数据已是最新" in str(e):
                            success_count += 1
                            logger.debug(f"⏭️ {code} {name} 无需更新，已跳过")
                        else:
                            fail_count += 1
                            failed_stocks[code] = {
                                "name": name,
                                "error": str(e),
                                "retry_count": 0,
                                "last_attempt": datetime.now().isoformat()
                            }
                    except Exception as e:
                        fail_count += 1
                        failed_stocks[code] = {
                            "name": name,
                            "error": str(e),
                            "retry_count": 0,
                            "last_attempt": datetime.now().isoformat()
                        }
            
            # 批次间休息
            if batch_end < len(need_update):
                logger.info(f"批次完成，休息 {pause_time} 秒...")
                time.sleep(pause_time)
        
        # 重试失败的股票
        if failed_stocks:
            logger.info(f"\n----- 重试失败股票 ({len(failed_stocks)} 只) -----")
            retry_count = SCHEDULER_CONFIG["retry_count"]
            
            for code, info in list(failed_stocks.items()):
                for retry in range(retry_count):
                    logger.info(f"重试 {code} {info['name']} ({retry + 1}/{retry_count})")
                    if self._update_single_stock(code, info["name"], last_date_map):
                        success_count += 1
                        fail_count -= 1
                        del failed_stocks[code]
                        break
                    else:
                        info["retry_count"] += 1
                        info["last_attempt"] = datetime.now().isoformat()
            
            self._failed_stocks.update(failed_stocks)
            self._save_failed_stocks()
        
        # 更新进度
        self._progress["last_update_date"] = datetime.now().strftime("%Y-%m-%d")
        self._progress["completed_codes"] = [c for c, _ in need_update if c not in failed_stocks]
        self._save_progress()
        
        # 输出统计报告
        logger.info("\n" + "=" * 50)
        logger.info("自动增量更新完成")
        logger.info(f"✅ 成功/已是最新: {success_count} 只")
        logger.info(f"❌ 失败: {fail_count} 只")
        if failed_stocks:
            logger.info(f"⚠️ 失败股票已记录，下次启动时会重试")
        logger.info("=" * 50)
    
    def _scheduler_loop(self):
        """调度器主循环"""
        while self._running:
            try:
                if self._should_run_update():
                    self._run_update()
                
                # 等待下一次检查
                time.sleep(SCHEDULER_CONFIG["update_interval_seconds"])
            
            except Exception as e:
                logger.error(f"调度器循环异常: {e}", exc_info=True)
                time.sleep(SCHEDULER_CONFIG["update_interval_seconds"])
    
    def start(self):
        """启动调度器"""
        with self._lock:
            if self._running:
                logger.warning("调度器已经在运行")
                return
            
            self._running = True
            self._thread = threading.Thread(target=self._scheduler_loop, daemon=True)
            self._thread.start()
            
            logger.info("✅ 自动增量更新调度器已启动")
            logger.info(f"📅 检查间隔: {SCHEDULER_CONFIG['update_interval_seconds']}秒")
            logger.info(f"🔄 会在收盘后自动更新")
    
    def stop(self):
        """停止调度器"""
        with self._lock:
            if not self._running:
                logger.warning("调度器已经停止")
                return
            
            self._running = False
            if self._thread:
                self._thread.join(timeout=5)
            
            logger.info("🛑 自动增量更新调度器已停止")
    
    def force_update(self):
        """强制立即执行更新（不检查时间）"""
        logger.info("⚠️ 收到强制更新指令")
        self._run_update()
    
    def check_integrity(self) -> Dict:
        """
        检查数据完整性
        
        Returns:
            Dict: 完整性检查结果
        """
        # 延迟导入以避免循环导入
        from service.stock_service import load_stock_list
        from service.history_service import batch_get_last_trade_date
        
        logger.info("🔍 开始数据完整性检查")
        
        stock_df = load_stock_list()
        codes = [str(row.code).zfill(6) for row in stock_df.itertuples(index=False)]
        
        last_date_map = batch_get_last_trade_date(codes)
        latest_trade_day = get_last_trade_day()
        
        complete_count = 0
        incomplete_count = 0
        missing_count = 0
        incomplete_details = []
        
        for code in codes:
            last_date = last_date_map.get(code)
            if not last_date:
                missing_count += 1
                incomplete_details.append({"code": code, "status": "missing", "last_date": None})
            elif needs_update(last_date):
                incomplete_count += 1
                incomplete_details.append({"code": code, "status": "outdated", "last_date": last_date})
            else:
                complete_count += 1
        
        result = {
            "total_stocks": len(codes),
            "latest_trade_day": latest_trade_day,
            "complete": complete_count,
            "incomplete": incomplete_count,
            "missing": missing_count,
            "incomplete_details": incomplete_details[:100],  # 最多返回100条详情
            "check_time": datetime.now().isoformat()
        }
        
        logger.info(f"📊 完整性检查完成")
        logger.info(f"  总计: {result['total_stocks']} 只")
        logger.info(f"  完整: {result['complete']} 只")
        logger.info(f"  过时: {result['incomplete']} 只")
        logger.info(f"  缺失: {result['missing']} 只")
        
        return result
    
    def get_status(self) -> Dict:
        """获取调度器状态"""
        return {
            "running": self._running,
            "last_update_date": self._progress.get("last_update_date"),
            "pending_failures": len(self._failed_stocks),
            "config": SCHEDULER_CONFIG
        }


# 全局调度器实例
_global_scheduler: Optional[UpdateScheduler] = None


def get_scheduler() -> UpdateScheduler:
    """获取全局调度器实例"""
    global _global_scheduler
    if _global_scheduler is None:
        _global_scheduler = UpdateScheduler()
    return _global_scheduler


# 扩展 date_utils 功能
def is_after_market_close(check_time: Optional[str] = None) -> bool:
    """
    判断是否已收盘（15:00之后）
    
    Args:
        check_time: 时间字符串，格式 HH:MM，默认为当前时间
    
    Returns:
        bool: 是否已收盘
    """
    if check_time is None:
        current_time = datetime.now().time()
    else:
        current_time = datetime.strptime(check_time, "%H:%M").time()
    
    market_close = datetime.strptime("15:00", "%H:%M").time()
    return current_time >= market_close
