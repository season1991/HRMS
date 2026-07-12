"""FastAPI 应用入口（占位骨架）

仅提供测试 fixture 替换与 create_app() 调用所需的符号。
真实实现（路由挂载、lifespan 建表、默认管理员初始化）在后续 Phase 补齐。
"""

from fastapi import FastAPI

# 模块级占位，测试 fixture 会通过属性赋值替换为真实 engine / SessionLocal
engine = None
SessionLocal = None


def create_app() -> FastAPI:
    """工厂方法占位：返回最简 FastAPI 实例。"""
    return FastAPI()