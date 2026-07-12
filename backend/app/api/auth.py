"""认证接口路由

Phase 5：
- GET  /api/auth/captcha
- POST /api/auth/login（仅校验 captcha，Phase 6+ 补全业务）

其他 3 个路由在后续 Phase 按 TC 补齐。
"""

from fastapi import APIRouter, Depends
from redis import Redis

from app.core.redis_client import get_redis
from app.core.response import json_fail, success
from app.schemas.auth import CaptchaOut, LoginIn
from app.services import auth as auth_service
from app.services.auth import AuthError

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.get("/captcha", summary="获取图形验证码")
def get_captcha(redis: Redis = Depends(get_redis)):
    """生成图形验证码（4 位字母数字），写入 Redis（默认 5 分钟过期）"""
    data = auth_service.generate_captcha(redis)
    return success(CaptchaOut(**data).model_dump())


@router.post("/login", summary="用户登录")
def login(payload: LoginIn, redis: Redis = Depends(get_redis)):
    """Phase 5 骨架：仅校验 captcha；Phase 6+ 补全用户校验、密码校验、双 Token 颁发。"""
    try:
        data = auth_service.login(
            redis=redis,
            captcha_id=payload.captcha_id,
            captcha_code=payload.captcha_code,
        )
        return success(data)
    except AuthError as e:
        return json_fail(message=e.message, code=e.code)