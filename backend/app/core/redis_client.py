"""Redis 客户端管理

提供 FastAPI 依赖注入 `get_redis`；测试可通过 app.dependency_overrides[get_redis] 注入 fakeredis。
"""

from typing import Generator

import redis
from redis import Redis

from app.core.config import settings


def _build_client() -> Redis:
    """根据 settings.REDIS_URL 构建 Redis 客户端"""
    return redis.from_url(settings.REDIS_URL, decode_responses=True)


def get_redis() -> Generator[Redis, None, None]:
    """FastAPI 依赖：返回一个 Redis 客户端连接"""
    client = _build_client()
    try:
        yield client
    finally:
        # redis-py 5.x 的 from_url 返回 ConnectionPool，无需显式 close
        pass