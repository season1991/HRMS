"""模型聚合入口

通过 `from app.models import SysUser` 等方式导入模型，
确保 Base.metadata.create_all 能发现全部已注册的表。
"""

from app.models.sys_user import SysUser

__all__ = ["SysUser"]