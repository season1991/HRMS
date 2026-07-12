"""认证相关 Redis 操作

Phase 4 仅提供：
- create_captcha / get_captcha_by_id / delete_captcha_by_id：图形验证码 CRUD（Redis）

存储结构：
- Key:   {REDIS_CAPTCHA_KEY_PREFIX}{captcha_id}
- Value: captcha_code（大写）
- TTL:   CAPTCHA_EXPIRE_MINUTES 分钟（由调用方在 set 时指定）
"""

from typing import Optional

from redis import Redis

from app.core.config import settings


def _key(captcha_id: str) -> str:
    """构造 Redis 键"""
    return f"{settings.REDIS_CAPTCHA_KEY_PREFIX}{captcha_id}"


def create_captcha(redis: Redis, captcha_id: str, captcha_code: str, expire_seconds: int) -> None:
    """写入验证码：SETEX key ttl value

    expire_seconds 由调用方从 settings.CAPTCHA_EXPIRE_MINUTES * 60 计算得到。
    """
    redis.setex(_key(captcha_id), expire_seconds, captcha_code.upper())


def get_captcha_by_id(redis: Redis, captcha_id: str) -> Optional[str]:
    """根据 captcha_id 查询验证码答案；不存在或已过期返回 None"""
    return redis.get(_key(captcha_id))


def delete_captcha_by_id(redis: Redis, captcha_id: str) -> int:
    """根据 captcha_id 删除（验证码一次性消费）；返回删除条数"""
    return int(redis.delete(_key(captcha_id)))