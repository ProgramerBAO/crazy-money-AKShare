import time
import random
import threading
from datetime import datetime, timedelta
from typing import Optional
from collections import deque
from utils.logger import setup_logger

logger = setup_logger(__name__)


class TokenBucket:
    """令牌桶限流器 - 控制请求速率"""

    def __init__(self, rate: float = 2.0, capacity: float = 5.0):
        """
        初始化令牌桶
        :param rate: 每秒生成的令牌数（建议 1-3）
        :param capacity: 桶的最大容量（建议 3-10）
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = threading.Lock()

    def acquire(self, tokens: float = 1.0) -> None:
        """获取令牌，阻塞直到获取成功"""
        with self.lock:
            while True:
                now = time.time()
                elapsed = now - self.last_refill
                self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
                self.last_refill = now

                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return
                else:
                    wait_time = (tokens - self.tokens) / self.rate
                    time.sleep(wait_time)


class SmartRateLimiter:
    """智能限流器 - 综合多种限流策略"""

    def __init__(
        self,
        requests_per_second: float = 1.5,
        max_concurrent: int = 3,
        min_delay: float = 0.3,
        max_delay: float = 1.5,
        burst_capacity: int = 5
    ):
        """
        初始化智能限流器
        :param requests_per_second: 每秒最大请求数
        :param max_concurrent: 最大并发数
        :param min_delay: 最小随机延迟（秒）
        :param max_delay: 最大随机延迟（秒）
        :param burst_capacity: 突发容量
        """
        self.token_bucket = TokenBucket(rate=requests_per_second, capacity=burst_capacity)
        self.semaphore = threading.Semaphore(max_concurrent)
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.request_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.total_delay_ms = 0
        self.lock = threading.Lock()
        self.request_history = deque(maxlen=100)

    def before_request(self) -> float:
        """请求前的限流处理，返回实际延迟时间"""
        self.token_bucket.acquire()
        self.semaphore.acquire()

        with self.lock:
            self.request_count += 1
            self.request_history.append(time.time())

        delay = random.uniform(self.min_delay, self.max_delay)
        if delay > 0:
            time.sleep(delay)
        
        return delay * 1000  # 返回毫秒

    def after_request(self, success: bool = True, delay_ms: float = 0) -> None:
        """请求后的处理"""
        self.semaphore.release()

        with self.lock:
            if success:
                self.success_count += 1
                self.total_delay_ms += delay_ms
            else:
                self.failure_count += 1

        if not success:
            logger.warning("请求失败，增加延迟")

    def get_stats(self) -> dict:
        """获取统计信息"""
        now = time.time()
        with self.lock:
            recent = [t for t in self.request_history if now - t < 60]
            total = self.success_count + self.failure_count
            success_rate = self.success_count / total if total > 0 else 0.0
            avg_delay = self.total_delay_ms / self.success_count if self.success_count > 0 else 0.0
            
            return {
                "total_requests": self.request_count,
                "success_count": self.success_count,
                "failure_count": self.failure_count,
                "success_rate": success_rate,
                "avg_delay_ms": avg_delay,
                "requests_last_60s": len(recent)
            }


def exponential_backoff(
    retry: int,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    factor: float = 2.0,
    jitter: bool = True
) -> float:
    """
    指数退避算法
    :param retry: 当前重试次数（从0开始）
    :param base_delay: 基础延迟
    :param max_delay: 最大延迟
    :param factor: 退避因子
    :param jitter: 是否添加随机抖动
    :return: 延迟时间（秒）
    """
    delay = min(base_delay * (factor ** retry), max_delay)
    if jitter:
        delay = delay * (0.5 + random.random())
    return delay


# 全局限流器实例
_global_limiter: Optional[SmartRateLimiter] = None


def get_rate_limiter(mode: str = "balanced") -> SmartRateLimiter:
    """
    获取全局限流器
    
    Args:
        mode: 限流模式
            - "safe": 最安全，速度最慢
            - "balanced": 平衡模式（默认）
            - "fast": 快速模式，有一定风险
            - "extreme": 极速模式，高风险
    """
    global _global_limiter
    if _global_limiter is None:
        configs = {
            "safe": {
                "requests_per_second": 1.0,
                "max_concurrent": 2,
                "min_delay": 0.5,
                "max_delay": 1.5,
                "burst_capacity": 3
            },
            "balanced": {
                "requests_per_second": 3.0,
                "max_concurrent": 6,
                "min_delay": 0.2,
                "max_delay": 0.5,
                "burst_capacity": 8
            },
            "fast": {
                "requests_per_second": 5.0,
                "max_concurrent": 10,
                "min_delay": 0.1,
                "max_delay": 0.3,
                "burst_capacity": 15
            },
            "extreme": {
                "requests_per_second": 8.0,
                "max_concurrent": 15,
                "min_delay": 0.05,
                "max_delay": 0.15,
                "burst_capacity": 20
            }
        }
        
        config = configs.get(mode, configs["balanced"])
        _global_limiter = SmartRateLimiter(**config)
        logger.info(f"全局限流器已初始化 - 模式: {mode}, 速率: {config['requests_per_second']}/s, 并发: {config['max_concurrent']}")
    return _global_limiter
