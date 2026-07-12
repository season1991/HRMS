"""认证模块 Pydantic 模型（请求 / 响应数据契约）

Phase 5：CaptchaOut + LoginIn
后续 Phase 按 TC 补齐 LoginOut / RefreshIn / RefreshOut / UserOut / LogoutOut
"""

from pydantic import BaseModel, Field


class CaptchaOut(BaseModel):
    """获取图形验证码响应"""

    captcha_id: str = Field(..., description="验证码ID，前端登录时回传")
    captcha_code: str = Field(..., description="测试环境返回的明文答案（生产环境应仅存于后端）")
    captcha_image: str = Field(..., description="Base64 编码的 PNG 图片（data URI）")


class LoginIn(BaseModel):
    """登录请求参数"""

    username: str = Field(..., min_length=1, max_length=50, description="登录用户名")
    password: str = Field(..., min_length=1, max_length=128, description="登录密码")
    captcha_id: str = Field(..., description="图形验证码ID")
    captcha_code: str = Field(..., min_length=1, max_length=10, description="图形验证码答案")