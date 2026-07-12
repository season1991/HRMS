"""系统用户表模型"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SysUser(Base):
    """系统用户表"""

    __tablename__ = "sys_user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # 主键，自增
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)  # 用户名，唯一
    password: Mapped[str] = mapped_column(String(255), nullable=False)  # 密码（bcrypt 加密）
    nickname: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 昵称
    role_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 角色ID
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=1)  # 状态：0-禁用，1-启用
    error_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 连续错误次数
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # 锁定截止时间
    login_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # 最后登录时间
    login_ip: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 最后登录IP
    create_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )  # 创建时间
    update_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )  # 更新时间

    def __repr__(self) -> str:
        return f"<SysUser id={self.id} username={self.username!r} status={self.status}>"