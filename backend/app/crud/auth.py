"""认证相关 Redis / 数据库操作

Phase 6 范围：
- 验证码（Redis）：create_captcha / get_captcha_by_id / delete_captcha_by_id
- 用户（DB）：get_user_by_username / get_user_by_id / create_user /
              increment_error_count / lock_user_until / reset_login_state

后续 Phase 按需追加（如 token 黑名单等）。
"""

from datetime import datetime
from typing import Optional

from redis import Redis
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import SysUser


# ============================= Redis: 验证码 =============================


def _key(captcha_id: str) -> str:
    """构造 Redis 键"""
    return f"{settings.REDIS_CAPTCHA_KEY_PREFIX}{captcha_id}"


def create_captcha(redis: Redis, captcha_id: str, captcha_code: str, expire_seconds: int) -> None:
    """写入验证码：SETEX key ttl value"""
    redis.setex(_key(captcha_id), expire_seconds, captcha_code.upper())


def get_captcha_by_id(redis: Redis, captcha_id: str) -> Optional[str]:
    """根据 captcha_id 查询验证码答案；不存在或已过期返回 None"""
    return redis.get(_key(captcha_id))


def delete_captcha_by_id(redis: Redis, captcha_id: str) -> int:
    """根据 captcha_id 删除（验证码一次性消费）；返回删除条数"""
    return int(redis.delete(_key(captcha_id)))


# ============================= Redis: Token 黑名单 =============================


def _blacklist_key(jti: str) -> str:
    """构造黑名单 Redis 键"""
    return f"blacklist:{jti}"


def add_to_blacklist(
    redis: Redis,
    jti: str,
    token_type: str,
    user_id: int,
    expire_seconds: int,
) -> None:
    """将 jti 加入黑名单

    expire_seconds 通常等于"原 token 剩余有效时间"，让 Redis 自动清理过期条目，
    避免黑名单无限增长。
    """
    redis.setex(_blacklist_key(jti), max(1, expire_seconds), token_type)


def is_jti_blacklisted(redis: Redis, jti: str) -> bool:
    """判断 jti 是否在黑名单中"""
    return redis.exists(_blacklist_key(jti)) > 0


# ============================= DB: 用户 =============================


def get_user_by_username(db: Session, username: str) -> Optional[SysUser]:
    """根据用户名精确查询用户"""
    stmt = select(SysUser).where(SysUser.username == username)
    return db.execute(stmt).scalar_one_or_none()


def get_user_by_id(db: Session, user_id: int) -> Optional[SysUser]:
    """根据主键查询用户"""
    return db.get(SysUser, user_id)


def create_user(
    db: Session,
    username: str,
    password_hash: str,
    nickname: Optional[str] = None,
    role_id: int = 0,
    status: int = 1,
) -> SysUser:
    """创建新用户"""
    user = SysUser(
        username=username,
        password=password_hash,
        nickname=nickname,
        role_id=role_id,
        status=status,
        error_count=0,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def increment_error_count(db: Session, user: SysUser) -> SysUser:
    """将用户的连续错误次数 +1"""
    user.error_count = (user.error_count or 0) + 1
    db.commit()
    db.refresh(user)
    return user


def lock_user_until(db: Session, user: SysUser, locked_until: datetime) -> SysUser:
    """将用户锁定到指定时间"""
    user.locked_until = locked_until
    db.commit()
    db.refresh(user)
    return user


def reset_login_state(
    db: Session,
    user: SysUser,
    login_time: Optional[datetime] = None,
    login_ip: Optional[str] = None,
) -> SysUser:
    """登录成功：重置错误计数、清除锁定时间、更新登录信息"""
    user.error_count = 0
    user.locked_until = None
    if login_time is not None:
        user.login_time = login_time
    if login_ip is not None:
        user.login_ip = login_ip
    db.commit()
    db.refresh(user)
    return user