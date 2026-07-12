"""数据库连接管理

封装 SQLAlchemy 2.0 风格的引擎、Session 工厂和 Base，并提供 FastAPI 依赖注入。
"""

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


# SQLite 需要特殊 connect_args 以支持跨线程
_connect_args: dict = {}
if settings.DATABASE_URL.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}


engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    connect_args=_connect_args,
    pool_pre_ping=True,
    future=True,
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)


class Base(DeclarativeBase):
    """SQLAlchemy 2.0 风格的声明基类"""
    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖：每个请求创建一个 Session，请求结束自动关闭"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()