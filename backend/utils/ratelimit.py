"""轻量级内存频次限流工具（仅适用于单进程开发部署）

固定窗口策略：在 window_sec 秒内同一 key 最多允许 limit 次。
- 单进程：dict + Lock，无需 Redis
- 生产部署多进程时建议替换为 Redis / memcached 后端

调用示例：
    if not rate_limit(f'nl_query:{user.id}', limit=10, window_sec=60):
        return error('请求过于频繁', 429)
"""
from collections import defaultdict
from threading import Lock
from time import time
from typing import DefaultDict, List


_buckets: DefaultDict[str, List[float]] = defaultdict(list)
_lock = Lock()


def rate_limit(key: str, limit: int, window_sec: int) -> bool:
    """检查是否允许通过；超出限制时返回 False（不抛异常，调用方自行返回 429）。"""
    if limit <= 0 or window_sec <= 0:
        return True
    now = time()
    cutoff = now - window_sec
    with _lock:
        bucket = [t for t in _buckets[key] if t > cutoff]
        if len(bucket) >= limit:
            _buckets[key] = bucket
            return False
        bucket.append(now)
        _buckets[key] = bucket
    return True
