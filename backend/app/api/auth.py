"""认证接口路由

Phase 4 仅挂载 GET /api/auth/captcha。
其他 4 个路由在后续 Phase 按 TC 补齐。
"""

from fastapi import APIRouter, Depends
from redis import Redis

from app.core.redis_client import get_redis
from app.core.response import success
from app.schemas.auth import CaptchaOut
from app.services import auth as auth_service

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.get("/captcha", summary="获取图形验证码")
def get_captcha(redis: Redis = Depends(get_redis)):
    """生成图形验证码（4 位字母数字），写入 Redis（默认 5 分钟过期）"""
    data = auth_service.generate_captcha(redis)
    return success(CaptchaOut(**data).model_dump())