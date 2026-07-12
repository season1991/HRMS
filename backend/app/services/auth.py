"""登录业务编排层

Phase 8 范围：
- generate_captcha：生成图形验证码 + Base64 + 写入 Redis
- login：完整登录流程（captcha → 用户 → 锁定 → 状态 → 密码 → 重置 → 双 Token）
- logout：将当前 access token 的 jti 加入 Redis 黑名单

后续 Phase 按 TC 补齐 refresh / me。
"""

import io
import uuid
from base64 import b64encode
from datetime import datetime, timedelta, timezone

from captcha.image import ImageCaptcha
from jose import JWTError
from jose.exceptions import ExpiredSignatureError
from redis import Redis
from sqlalchemy.orm import Session

from app.core import security
from app.core.config import settings
from app.crud import auth as crud_auth


# ============================= 业务异常 =============================


class AuthError(Exception):
    """认证相关业务异常基类"""

    def __init__(self, message: str, code: int = 400):
        super().__init__(message)
        self.message = message
        self.code = code


class CaptchaInvalidError(AuthError):
    """验证码不存在 / 已过期"""

    def __init__(self, message: str = "验证码无效或已过期"):
        super().__init__(message, code=400)


class CaptchaMismatchError(AuthError):
    """验证码答案错误"""

    def __init__(self, message: str = "验证码错误"):
        super().__init__(message, code=400)


class InvalidCredentialsError(AuthError):
    """用户名或密码错误"""

    def __init__(self, message: str = "用户名或密码错误"):
        super().__init__(message, code=401)


class UserDisabledError(AuthError):
    """账号被禁用"""

    def __init__(self, message: str = "账号已被禁用，请联系管理员"):
        super().__init__(message, code=403)


class UserLockedError(AuthError):
    """账号被锁定"""

    def __init__(self, message: str = "账号已被锁定，请稍后再试"):
        super().__init__(message, code=403)


class TokenInvalidError(AuthError):
    """Token 无效或已过期"""

    def __init__(self, message: str = "Token 无效或已过期"):
        super().__init__(message, code=401)


class TokenRevokedError(AuthError):
    """Token 已被吊销"""

    def __init__(self, message: str = "Token 已失效，请重新登录"):
        super().__init__(message, code=401)


# ============================= 工具 =============================


def _now() -> datetime:
    """带时区的当前时间"""
    return datetime.now(timezone.utc)


def _now_naive() -> datetime:
    """naive UTC 时间（与 SQLAlchemy 返回的 naive 时间统一比较）"""
    return datetime.utcnow()


def _strip_tz(dt: datetime) -> datetime:
    """将带时区时间转换为 naive UTC"""
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _gen_captcha_image(text: str) -> str:
    """使用 captcha 库生成 PNG 图片的 Base64 data URI"""
    image = ImageCaptcha(width=160, height=60)
    buf = io.BytesIO()
    image.write(text, buf)
    buf.seek(0)
    encoded = b64encode(buf.read()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


# ============================= 业务流程 =============================


def generate_captcha(redis: Redis) -> dict:
    """生成图形验证码

    返回:
        dict: 包含 captcha_id / captcha_code / captcha_image
    """
    import random

    charset = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"
    text = "".join(random.choices(charset, k=4)).upper()

    captcha_id = uuid.uuid4().hex
    expire_seconds = settings.CAPTCHA_EXPIRE_MINUTES * 60
    crud_auth.create_captcha(
        redis=redis,
        captcha_id=captcha_id,
        captcha_code=text,
        expire_seconds=expire_seconds,
    )
    captcha_image = _gen_captcha_image(text)
    return {
        "captcha_id": captcha_id,
        "captcha_code": text,
        "captcha_image": captcha_image,
    }


def login(
    db: Session,
    redis: Redis,
    username: str,
    password: str,
    captcha_id: str,
    captcha_code: str,
    login_ip: str | None = None,
) -> dict:
    """完整登录流程

    步骤：
        1. 验证码校验（存在 + 答案正确，一次性消费）
        2. 用户名校验（不存在 → 401）
        3. 锁定状态校验（locked_until 未过期 → 403）
        4. 账号状态校验（status != 1 → 403）
        5. 密码校验（错误则累计 error_count，达 MAX_LOGIN_ERROR_COUNT 则锁定 LOCK_MINUTES 分钟）
        6. 登录成功：重置错误计数 + 更新登录信息
        7. 生成 access / refresh 双 Token
    """
    # 1. 验证码校验
    stored_code = crud_auth.get_captcha_by_id(redis, captcha_id)
    if stored_code is None:
        raise CaptchaInvalidError()
    if stored_code.upper() != captcha_code.upper():
        raise CaptchaMismatchError()
    crud_auth.delete_captcha_by_id(redis, captcha_id)

    # 2. 用户查询
    user = crud_auth.get_user_by_username(db, username)
    if user is None:
        raise InvalidCredentialsError()

    # 3. 锁定检查
    if user.locked_until is not None and _strip_tz(user.locked_until) > _now_naive():
        raise UserLockedError()

    # 4. 状态检查
    if user.status != 1:
        raise UserDisabledError()

    # 5. 密码校验
    if not security.verify_password(password, user.password):
        crud_auth.increment_error_count(db, user)
        db.refresh(user)
        if user.error_count >= settings.MAX_LOGIN_ERROR_COUNT:
            lock_until = _now_naive() + timedelta(minutes=settings.LOCK_MINUTES)
            crud_auth.lock_user_until(db, user, lock_until)
            raise UserLockedError(
                f"连续输错 {settings.MAX_LOGIN_ERROR_COUNT} 次，账号已被锁定 {settings.LOCK_MINUTES} 分钟"
            )
        raise InvalidCredentialsError()

    # 6. 登录成功：重置 + 更新登录信息
    crud_auth.reset_login_state(db, user, login_time=_now_naive(), login_ip=login_ip)

    # 7. 生成双 Token
    access_jti = uuid.uuid4().hex
    refresh_jti = uuid.uuid4().hex
    access_token = security.create_access_token(user.id, access_jti)
    refresh_token = security.create_refresh_token(user.id, refresh_jti)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "role_id": user.role_id,
            "status": user.status,
            "login_time": user.login_time,
            "login_ip": user.login_ip,
        },
    }


def logout(redis: Redis, token: str) -> None:
    """登出：将当前 access token 的 jti 加入 Redis 黑名单

    流程：
        1. 解码 access token 拿到 jti / user_id / exp
        2. 计算"剩余有效秒数"
        3. SETEX blacklist:{jti} <剩余秒数> <token_type>，由 Redis TTL 自动清理
    """
    try:
        payload = security.decode_jwt(token, expected_type="access")
    except ExpiredSignatureError as e:
        raise TokenInvalidError("Token 已过期") from e
    except JWTError as e:
        raise TokenInvalidError("Token 无效") from e

    jti = payload.get("jti")
    if not jti:
        raise TokenInvalidError("Token 缺少 jti")
    user_id = int(payload.get("sub", 0))

    exp_ts = int(payload.get("exp", 0))
    now_ts = int(datetime.now(timezone.utc).timestamp())
    expire_seconds = max(1, exp_ts - now_ts)

    crud_auth.add_to_blacklist(
        redis=redis,
        jti=jti,
        token_type="access",
        user_id=user_id,
        expire_seconds=expire_seconds,
    )


def refresh_tokens(db: Session, redis: Redis, refresh_token: str) -> dict:
    """刷新 Token：校验 refresh → 颁发新双 Token → 旧 refresh 拉黑

    旋转策略（refresh token rotation）：
        - 每次成功刷新后，旧 refresh_token 立即失效（写入黑名单）
        - 下次再用旧 refresh_token 调用本接口会抛 TokenRevokedError(401)

    流程：
        1. 解码 refresh token（校验签名 + 类型 + 未过期）
        2. 黑名单检查：若 jti 已在黑名单 → TokenRevokedError
        3. 用户状态检查：用户不存在或被禁用 → TokenInvalidError
        4. 旧 refresh 拉黑
        5. 颁发新 access / refresh Token
    """
    try:
        payload = security.decode_jwt(refresh_token, expected_type="refresh")
    except ExpiredSignatureError as e:
        raise TokenInvalidError("Refresh Token 已过期") from e
    except JWTError as e:
        raise TokenInvalidError("Refresh Token 无效") from e

    jti = payload.get("jti")
    if not jti:
        raise TokenInvalidError("Refresh Token 缺少 jti")
    user_id = int(payload.get("sub", 0))

    # 黑名单检查（必须在解码通过后，否则无法判断 jti）
    if crud_auth.is_jti_blacklisted(redis, jti):
        raise TokenRevokedError("Refresh Token 已失效")

    # 用户状态检查
    user = crud_auth.get_user_by_id(db, user_id)
    if user is None or user.status != 1:
        raise TokenInvalidError("用户不存在或已被禁用")

    # 旧 refresh 拉黑
    exp_ts = int(payload.get("exp", 0))
    now_ts = int(datetime.now(timezone.utc).timestamp())
    expire_seconds = max(1, exp_ts - now_ts)
    crud_auth.add_to_blacklist(
        redis=redis,
        jti=jti,
        token_type="refresh",
        user_id=user_id,
        expire_seconds=expire_seconds,
    )

    # 颁发新双 Token
    new_access_jti = uuid.uuid4().hex
    new_refresh_jti = uuid.uuid4().hex
    return {
        "access_token": security.create_access_token(user_id, new_access_jti),
        "refresh_token": security.create_refresh_token(user_id, new_refresh_jti),
        "token_type": "bearer",
    }


def get_current_user(db: Session, redis: Redis, token: str) -> dict:
    """从 access token 中解析当前用户

    流程：
        1. 解码 access token（校验签名 + 类型 + 未过期）
        2. 黑名单检查：jti 已被吊销 → TokenRevokedError(401)
        3. 查询用户；不存在或被禁用 → TokenInvalidError(401)
        4. 返回 UserOut 字典
    """
    try:
        payload = security.decode_jwt(token, expected_type="access")
    except ExpiredSignatureError as e:
        raise TokenInvalidError("Token 已过期") from e
    except JWTError as e:
        raise TokenInvalidError("Token 无效") from e

    jti = payload.get("jti")
    if jti and crud_auth.is_jti_blacklisted(redis, jti):
        raise TokenRevokedError("Token 已失效")

    user_id = int(payload.get("sub", 0))
    user = crud_auth.get_user_by_id(db, user_id)
    if user is None or user.status != 1:
        raise TokenInvalidError("用户不存在或已被禁用")

    return {
        "id": user.id,
        "username": user.username,
        "nickname": user.nickname,
        "role_id": user.role_id,
        "status": user.status,
        "login_time": user.login_time,
        "login_ip": user.login_ip,
    }