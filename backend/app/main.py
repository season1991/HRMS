"""FastAPI 应用入口（最小骨架）

Phase 3 职责：
- 创建 FastAPI 实例
- 启动时建表（开发环境）
- 提供基础健康检查接口

⚠️ 暂不挂载 /api/auth/* 路由，18 个测试应仍全部为 RED（404）。
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.core.response import json_fail


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时建表"""
    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    """工厂方法创建 FastAPI 实例（仅含健康检查，不挂载业务路由）"""
    app = FastAPI(
        title=f"{settings.APP_NAME} 认证服务",
        version="1.0.0",
        description="HRMS 登录认证模块：验证码、登录、Token 管理、登出",
        lifespan=lifespan,
    )

    @app.get("/", tags=["健康检查"], summary="服务探活")
    def root():
        return {"code": 200, "message": "ok", "data": {"service": settings.APP_NAME}}

    @app.get("/health", tags=["健康检查"], summary="健康检查")
    def health():
        return {"code": 200, "message": "ok", "data": {"status": "up"}}

    # 全局兜底异常处理
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        return json_fail(message=f"服务器内部错误: {exc}", code=500)

    return app


# uvicorn 入口：python -m app.main
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )