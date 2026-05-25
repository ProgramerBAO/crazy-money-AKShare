"""
Crazy Money - A股量化数据平台
主程序入口
"""
import signal
import sys
from typing import List, Tuple, Dict

from utils.logger import setup_logger
from service import StockService, UpdateService
from scheduler import DailyUpdateScheduler
from service.convert_service import ConvertService
from config import (
    MAX_WORKERS,
    BATCH_SIZE,
    DATA_SOURCE_DEFAULT,
    ADJUST_DEFAULT
)

# 初始化日志
logger = setup_logger(__name__)


def print_help():
    """打印帮助信息"""
    help_text = """
============================================================
Crazy Money - A股量化数据平台
============================================================
用法:
  python3 cli.py [命令] [选项]

命令:
  init        - 初始化股票列表
  download    - 手动执行一次数据更新
  scheduler   - 启动自动增量更新调度器
  convert     - 格式转换 (csv2parquet / parquet2csv / sync)
  check       - 检查数据完整性
  help        - 显示此帮助信息

选项:
  --source=SRC     数据源: tencent | eastmoney (默认: tencent)
  --adjust=ADJ     复权方式: qfq | hfq | none (默认: qfq)
  --batch=N        批次大小 (默认: 100)
  --count=N        测试模式：仅下载前N只股票
  --force          强制全量下载

示例:
  python3 cli.py init                    # 初始化股票列表
  python3 cli.py download                # 正常更新所有股票
  python3 cli.py download --force        # 强制全量下载
  python3 cli.py download --count=100    # 测试下载前100只
  python3 cli.py scheduler               # 启动后台自动更新
  python3 cli.py convert sync            # 同步CSV和Parquet格式
============================================================
    """
    print(help_text.strip())


def _parse_args(args: List[str]) -> Tuple[str, Dict]:
    """
    解析命令行参数
    
    Args:
        args: 命令行参数列表（不含脚本名）
        
    Returns:
        (命令, 选项字典)
    """
    command = "help"
    options = {}
    
    for arg in args:
        if arg.startswith("--"):
            key_value = arg[2:].split("=")
            if len(key_value) == 2:
                options[key_value[0]] = key_value[1]
            else:
                options[key_value[0]] = True
        elif not arg.startswith("-"):
            command = arg
    
    return command, options


def init_stock_list(options: Dict) -> bool:
    """初始化股票列表"""
    logger.info("📥 初始化股票列表")
    service = StockService()
    df = service.get_and_save_stock_list(
        source=options.get("source", DATA_SOURCE_DEFAULT)
    )
    if not df.empty:
        logger.info(f"✅ 成功保存 {len(df)} 只股票")
        return True
    else:
        logger.error("❌ 股票列表获取失败")
        return False


def download_data(options: Dict) -> bool:
    """下载股票数据"""
    logger.info("🚀 开始下载股票数据")

    # 加载股票列表
    stock_service = StockService()
    df_stocks = stock_service.load_stock_list()

    if df_stocks.empty:
        logger.error("❌ 股票列表为空，请先执行 'python cli.py init'")
        return False

    # 根据配置决定是否截取测试数量
    test_count = options.get("count")
    if test_count:
        try:
            test_count = int(test_count)
            if test_count > 0 and test_count < len(df_stocks):
                logger.info(f"🧪 测试模式：仅处理前 {test_count} 只股票")
                df_stocks = df_stocks.head(test_count)
        except ValueError:
            logger.warning(f"⚠️ 无效的count参数: {test_count}")

    codes = df_stocks["code"].tolist()
    logger.info(f"📋 准备处理 {len(codes)} 只股票")

    # 执行更新
    update_service = UpdateService()
    batch_size = options.get("batch")
    if batch_size:
        try:
            batch_size = int(batch_size)
        except ValueError:
            batch_size = BATCH_SIZE

    stats = update_service.batch_update(
        codes=codes,
        force_full=options.get("force", False),
        batch_size=batch_size,
        source=options.get("source"),
        adjust=options.get("adjust")
    )

    # 输出统计
    logger.info("=" * 60)
    logger.info("📊 更新完成统计:")
    logger.info(f"   ✅ 成功: {stats['success']}")
    logger.info(f"   ❌ 失败: {stats['failed']}")
    logger.info(f"   ⏭️  跳过: {stats['skipped']}")
    logger.info("=" * 60)

    return stats['failed'] == 0


def start_scheduler(options: Dict):
    """启动调度器"""
    logger.info("🔄 启动自动增量更新调度器")
    
    scheduler = DailyUpdateScheduler()
    batch_size = options.get("batch")
    if batch_size:
        try:
            batch_size = int(batch_size)
        except ValueError:
            batch_size = BATCH_SIZE
    
    scheduler.run_forever(
        check_interval=3600,
        batch_size=batch_size
    )


def convert_data(options: Dict) -> bool:
    """数据格式转换"""
    convert_service = ConvertService()

    # 获取转换类型
    convert_type = options.get("type", "sync")
    if "type" not in options and len(sys.argv) > 2:
        # 从第二个参数获取
        if sys.argv[2] in ["csv2parquet", "parquet2csv", "sync"]:
            convert_type = sys.argv[2]

    # 加载股票列表
    stock_service = StockService()
    df_stocks = stock_service.load_stock_list()

    if df_stocks.empty:
        logger.error("❌ 股票列表为空，请先执行 'python cli.py init'")
        return False

    codes = df_stocks["code"].tolist()
    failed = 0

    if convert_type == "sync":
        logger.info("🔄 同步CSV和Parquet格式...")
        success, failed = convert_service.batch_sync_all(codes)
        logger.info(f"✅ 同步完成: 成功={success}, 失败={failed}")
    elif convert_type == "csv2parquet":
        logger.info("🔄 CSV -> Parquet 转换...")
        success = 0
        for code in codes:
            if not convert_service.csv_to_parquet(code):
                failed += 1
            else:
                success += 1
        logger.info(f"✅ 转换完成: 成功={success}, 失败={failed}")
    elif convert_type == "parquet2csv":
        logger.info("🔄 Parquet -> CSV 转换...")
        success = 0
        for code in codes:
            if not convert_service.parquet_to_csv(code):
                failed += 1
            else:
                success += 1
        logger.info(f"✅ 转换完成: 成功={success}, 失败={failed}")
    else:
        logger.error(f"❌ 未知的转换类型: {convert_type}")
        print_help()
        return False

    return failed == 0


def check_data(options: Dict) -> bool:
    """检查数据完整性"""
    logger.info("🔍 检查数据完整性")

    # 加载股票列表
    stock_service = StockService()
    df_stocks = stock_service.load_stock_list()

    if df_stocks.empty:
        logger.error("❌ 股票列表为空")
        return False

    # 获取交易日服务
    from service.trade_date_service import TradeDateService
    trade_date_service = TradeDateService()
    latest_trade_day = trade_date_service.get_last_trade_day()

    # 统计
    total = len(df_stocks)
    complete = 0
    incomplete = 0
    missing = 0

    from storage import CSVStorage, ParquetStorage
    csv_storage = CSVStorage()
    parquet_storage = ParquetStorage()

    for code in df_stocks["code"]:
        csv_exists = csv_storage.exists(code)
        parquet_exists = parquet_storage.exists(code)

        if not csv_exists and not parquet_exists:
            missing += 1
        else:
            last_date = parquet_storage.get_last_date(code) or csv_storage.get_last_date(code)
            if last_date and last_date >= latest_trade_day:
                complete += 1
            else:
                incomplete += 1

    print("\n📊 数据完整性报告:")
    print(f"  总计股票: {total} 只")
    print(f"  基准交易日: {latest_trade_day}")
    print(f"  ✅ 完整: {complete} 只")
    print(f"  ⚠️ 过时: {incomplete} 只")
    print(f"  ❌ 缺失: {missing} 只")

    if incomplete > 0 or missing > 0:
        print(f"\n💡 提示: 运行 'python cli.py download' 来更新数据")

    return missing == 0


def signal_handler(signum, frame):
    """处理 SIGINT/SIGTERM 信号"""
    logger.info("🛑 收到停止信号，正在优雅退出...")
    sys.exit(0)


if __name__ == "__main__":
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 解析命令行参数
    command, options = _parse_args(sys.argv[1:])
    
    # 执行命令
    success = False
    if command == "init":
        success = init_stock_list(options)
    elif command == "download":
        success = download_data(options)
    elif command == "scheduler":
        start_scheduler(options)
        success = True
    elif command == "convert":
        success = convert_data(options)
    elif command == "check":
        success = check_data(options)
    elif command == "help":
        print_help()
    else:
        print(f"❌ 未知命令: {command}")
        print_help()
        sys.exit(1)

    sys.exit(0 if success else 1)
