"""安全工具：密码哈希、JWT 生成与解码

- 密码：passlib + bcrypt
- JWT：python-jose
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError
from passlib.context import CryptContext

from app.core.config import settings


# ----------------------------- 密码 -----------------------------

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """生成密码 bcrypt 哈希"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """校验明文密码与哈希是否一致"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


# ----------------------------- JWT -----------------------------

def _now() -> datetime:
    """统一使用带时区的当前时间，避免 naive/aware 混用"""
    return datetime.now(timezone.utc)


def _create_token(
    subject: str,
    token_type: str,
    expires_delta: timedelta,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """生成 JWT 的内部方法

    参数:
        subject: 主题，通常是 user_id（字符串）
        token_type: 'access' 或 'refresh'
        expires_delta: 过期时间间隔
        extra_claims: 额外的载荷（例如 jti）
    """
    now = _now()
    expire = now + expires_delta
    payload: Dict[str, Any] = {
        "sub": str(subject),
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user_id: int, jti: str) -> str:
    """生成访问令牌（默认 2 小时）"""
    return _create_token(
        subject=user_id,
        token_type="access",
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        extra_claims={"jti": jti},
    )


def create_refresh_token(user_id: int, jti: str) -> str:
    """生成刷新令牌（默认 7 天）"""
    return _create_token(
        subject=user_id,
        token_type="refresh",
        expires_delta=timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES),
        extra_claims={"jti": jti},
    )


def decode_jwt(token: str, expected_type: Optional[str] = None) -> Dict[str, Any]:
    """解码并校验 JWT

    参数:
        token: 待解码的 token
        expected_type: 期望的 token 类型（'access' / 'refresh'），None 表示不限制

    返回:
        解码后的 payload dict

    异常:
        ExpiredSignatureError: token 已过期
        JWTError: 其他校验错误（签名错误、格式错误、类型不符等）
    """
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    if expected_type and payload.get("type") != expected_type:
        raise JWTError(f"Invalid token type, expected {expected_type}, got {payload.get('type')}")
    return payload


# ----------------------------- 异常透传辅助 -----------------------------

def jose_expired() -> ExpiredSignatureError:
    """提供 ExpiredSignatureError 工厂方法，便于 monkeypatch 测试"""
    return ExpiredSignatureError("expired")