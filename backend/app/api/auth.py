"""认证接口路由

Phase 6：
- GET  /api/auth/captcha
- POST /api/auth/login（完整登录：captcha + user + password + JWT）

其他 3 个路由在后续 Phase 按 TC 补齐。
"""

from fastapi import APIRouter, Depends, Request
from redis import Redis
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.redis_client import get_redis
from app.core.response import json_fail, success
from app.schemas.auth import CaptchaOut, LoginIn, LoginOut
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