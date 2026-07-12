"""认证相关数据库操作（占位骨架）

仅提供测试 import 所需的符号 delete_captcha_by_id。
真实实现在后续 Phase 按规格补齐（用户 CRUD、验证码 CRUD、黑名单 CRUD）。
"""

from sqlalchemy.orm import Session


def delete_captcha_by_id(db: Session, captcha_id: str) -> int:
    """占位：返回 0，不做实际删除。"""
    return 0