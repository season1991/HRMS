"""登录业务编排层

Phase 4 仅实现 generate_captcha：生成图形验证码 + Base64 + 写入 Redis。
其他业务（login / logout / refresh / me）在后续 Phase 按 TC 补齐。
"""

import io
import uuid
from base64 import b64encode

from captcha.image import ImageCaptcha
from redis import Redis

from app.core.config import settings
from app.crud import auth as crud_auth


def _gen_captcha_image(text: str) -> str:
    """使用 captcha 库生成 PNG 图片的 Base64 data URI"""
    image = ImageCaptcha(width=160, height=60)
    buf = io.BytesIO()
    image.write(text, buf)
    buf.seek(0)
    encoded = b64encode(buf.read()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def generate_captcha(redis: Redis) -> dict:
    """生成图形验证码

    返回:
        dict: 包含 captcha_id / captcha_code / captcha_image

    业务规则：
        - 4 位字符（去易混字符 0/o/1/l/i）
        - 有效期 CAPTCHA_EXPIRE_MINUTES（默认 5 分钟），由 Redis SETEX 自动过期
        - captcha_code 写入 Redis；captcha_image 返回前端
        - 测试环境 captcha_code 直接随响应返回（便于自动化），生产应仅存后端
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