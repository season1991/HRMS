"""登录业务编排层

Phase 5：
- generate_captcha：生成图形验证码 + Base64 + 写入 Redis
- login：仅校验 captcha（一次性消费），Phase 6+ 补全用户/密码/JWT

后续 Phase 按 TC 补齐 logout / refresh / me。
"""

import io
import uuid
from base64 import b64encode

from captcha.image import ImageCaptcha
from redis import Redis

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


# ============================= 工具 =============================


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


def login(redis: Redis, captcha_id: str, captcha_code: str) -> dict:
    """登录业务（Phase 5 骨架：仅校验 captcha，后续 Phase 补全用户/密码/JWT）

    流程：
        1. 查询 Redis 中 captcha_id 是否存在
        2. 不存在 → CaptchaInvalidError（400）
        3. 答案不一致 → CaptchaMismatchError（400）
        4. 一次性消费：校验通过后从 Redis 删除

    返回:
        dict: Phase 5 占位返回，Phase 6+ 替换为 LoginOut
    """
    stored_code = crud_auth.get_captcha_by_id(redis, captcha_id)
    if stored_code is None:
        raise CaptchaInvalidError()
    if stored_code.upper() != captcha_code.upper():
        raise CaptchaMismatchError()

    # 校验通过：消费 captcha
    crud_auth.delete_captcha_by_id(redis, captcha_id)

    # Phase 5 占位：captcha 校验通过，Phase 6+ 继续校验用户/密码并签发 Token
    return {
        "phase": "5-stub",
        "captcha_verified": True,
        "captcha_id": captcha_id,
    }