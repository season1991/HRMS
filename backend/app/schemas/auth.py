"""认证模块 Pydantic 模型（请求 / 响应数据契约）

Phase 6：CaptchaOut / LoginIn / UserOut / LoginOut
后续 Phase 按需补齐 RefreshIn / RefreshOut / LogoutOut
"""

from datetime import datetime
from typing import Optional

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


class UserOut(BaseModel):
    """用户信息"""

    id: int
    username: str
    nickname: Optional[str] = None
    role_id: int
    status: int
    login_time: Optional[datetime] = None
    login_ip: Optional[str] = None


class LoginOut(BaseModel):
    """登录成功响应"""

    access_token: str = Field(..., description="访问令牌，2 小时有效")
    refresh_token: str = Field(..., description="刷新令牌，7 天有效")
    token_type: str = Field(default="bearer", description="Token 类型")
    user: UserOut = Field(..., description="当前登录用户信息")


class RefreshIn(BaseModel):
    """刷新 Token 请求参数"""

    refresh_token: str = Field(..., description="用于刷新的 refresh_token")


class RefreshOut(BaseModel):
    """刷新 Token 响应"""

    access_token: str = Field(..., description="新的访问令牌")
    refresh_token: str = Field(..., description="新的刷新令牌（旧 refresh 已失效）")
    token_type: str = Field(default="bearer", description="Token 类型")