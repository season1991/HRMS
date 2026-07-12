"""认证模块 Pydantic 模型（请求 / 响应数据契约）

Phase 4 仅包含 CaptchaOut；后续 Phase 按 TC 逐步补齐。
"""

from pydantic import BaseModel, Field


class CaptchaOut(BaseModel):
    """获取图形验证码响应"""

    captcha_id: str = Field(..., description="验证码ID，前端登录时回传")
    captcha_code: str = Field(..., description="测试环境返回的明文答案（生产环境应仅存于后端）")
    captcha_image: str = Field(..., description="Base64 编码的 PNG 图片（data URI）")