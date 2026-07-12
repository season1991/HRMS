"""认证接口路由

Phase 10：所有 5 个 auth 路由完成
- GET  /api/auth/captcha
- POST /api/auth/login
- POST /api/auth/logout
- POST /api/auth/refresh
- GET  /api/auth/me
"""

from fastapi import APIRouter, Depends, Header, Request
from redis import Redis
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.redis_client import get_redis
from app.core.response import json_fail, success
from app.schemas.auth import CaptchaOut, LoginIn, LoginOut, RefreshIn, RefreshOut, UserOut
from app.services import auth as auth_service
from app.services.auth import AuthError

router = APIRouter(prefix="/api/auth", tags=["认证"])


def _client_ip(request: Request) -> str | None:
    """从 request 中提取客户端 IP（支持 X-Forwarded-For）"""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def _bearer_token(authorization: str | None) -> str:
    """从 Authorization 头中提取 Bearer Token

    异常:
        AuthError(401): 未提供或格式错误
    """
    if not authorization:
        raise AuthError("未提供 Authorization 头", code=401)
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthError("Authorization 头格式错误", code=401)
    return parts[1]


@router.get("/captcha", summary="获取图形验证码")
def get_captcha(redis: Redis = Depends(get_redis)):
    """生成图形验证码（4 位字母数字），写入 Redis（默认 5 分钟过期）"""
    data = auth_service.generate_captcha(redis)
    return success(CaptchaOut(**data).model_dump())


@router.post("/login", summary="用户登录")
def login(
    payload: LoginIn,
    request: Request,
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """完整登录：校验 captcha → 用户 → 状态 → 密码 → 双 Token。"""
    try:
        data = auth_service.login(
            db=db,
            redis=redis,
            username=payload.username,
            password=payload.password,
            captcha_id=payload.captcha_id,
            captcha_code=payload.captcha_code,
            login_ip=_client_ip(request),
        )
        return success(LoginOut(**data).model_dump())
    except AuthError as e:
        return json_fail(message=e.message, code=e.code)


@router.post("/logout", summary="用户登出")
def logout(
    authorization: str | None = Header(default=None),
    redis: Redis = Depends(get_redis),
):
    """将当前 access token 的 jti 加入 Redis 黑名单（TTL = 剩余有效时间）"""
    try:
        token = _bearer_token(authorization)
        auth_service.logout(redis=redis, token=token)
        return success(data=None, message="登出成功")
    except AuthError as e:
        return json_fail(message=e.message, code=e.code)


@router.post("/refresh", summary="刷新 Token")
def refresh(
    payload: RefreshIn,
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """校验 refresh_token，返回新双 Token；旧 refresh_token 立即失效（旋转策略）。"""
    try:
        data = auth_service.refresh_tokens(
            db=db, redis=redis, refresh_token=payload.refresh_token
        )
        return success(RefreshOut(**data).model_dump())
    except AuthError as e:
        return json_fail(message=e.message, code=e.code)


@router.get("/me", summary="获取当前登录用户信息")
def me(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """从 Authorization 头解析 access token，返回当前用户信息"""
    try:
        token = _bearer_token(authorization)
        user_dict = auth_service.get_current_user(db=db, redis=redis, token=token)
        return success(UserOut(**user_dict).model_dump())
    except AuthError as e:
        return json_fail(message=e.message, code=e.code)