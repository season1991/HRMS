"""统一响应格式封装

规范：
    {
        "code": 200,        # 业务状态码：200 成功，4xx 客户端错误，5xx 服务端错误
        "message": "success",
        "data": null | {...}
    }
"""

from typing import Any, Optional

from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ApiResponse(BaseModel):
    """统一响应模型（用于 OpenAPI 文档展示）"""

    code: int = 200
    message: str = "success"
    data: Optional[Any] = None


def success(data: Any = None, message: str = "success", code: int = 200) -> dict:
    """构造成功响应字典（供 Service 层使用）"""
    return {"code": code, "message": message, "data": data}


def fail(message: str, code: int = 400, data: Any = None) -> dict:
    """构造失败响应字典"""
    return {"code": code, "message": message, "data": data}


def json_success(data: Any = None, message: str = "success", code: int = 200) -> JSONResponse:
    """构造 FastAPI 直接返回的成功响应"""
    return JSONResponse(status_code=code, content={"code": code, "message": message, "data": data})


def json_fail(message: str, code: int = 400, data: Any = None) -> JSONResponse:
    """构造 FastAPI 直接返回的失败响应（HTTP 状态码与业务码保持一致）"""
    return JSONResponse(status_code=code, content={"code": code, "message": message, "data": data})