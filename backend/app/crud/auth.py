"""认证相关数据库操作（最小骨架）

Phase 3 仅提供：
- delete_captcha_by_id：测试 TC02 直接调用

其他 CRUD 函数（用户 CRUD、验证码 CRUD、黑名单 CRUD 等）在后续 Phase 按规格补齐。
"""

from sqlalchemy.orm import Session


def delete_captcha_by_id(db: Session, captcha_id: str) -> int:
    """占位：返回 0，不做实际删除（真实实现在后续 Phase）"""
    return 0