"""数据库连接管理（占位骨架）

仅提供测试文件 import 所需的符号：Base / engine / SessionLocal / get_db。
真实实现（create_engine、Session 工厂、依赖注入）将在后续 Phase 补齐。
"""

from typing import Generator

from sqlalchemy.orm import DeclarativeBase, Session


class Base(DeclarativeBase):
    """SQLAlchemy 2.0 风格的声明基类。"""

    pass


engine = None
SessionLocal = None


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖占位 —— 测试中通过 app.dependency_overrides[get_db] 覆盖真实实现。"""
    raise RuntimeError("get_db 占位 stub 未被覆盖；测试应通过 dependency_overrides 注入 Session")