"""安全工具（占位骨架）

仅提供测试 import 所需的符号：get_password_hash / decode_jwt / jose_expired。
真实实现（bcrypt、python-jose 签名）将在后续 Phase 补齐。
"""

from typing import Any, Dict, Optional


def get_password_hash(password: str) -> str:
    """密码哈希占位：原样返回明文（仅用于让测试种子代码可运行）。"""
    return password


def decode_jwt(token: str, expected_type: Optional[str] = None) -> Dict[str, Any]:
    """JWT 解码占位：未实现。"""
    raise NotImplementedError("decode_jwt 占位 stub，真实实现在后续 Phase")


def jose_expired():
    """提供给 TC32 monkeypatch 测试使用的 ExpiredSignatureError 工厂占位。"""
    from jose.exceptions import ExpiredSignatureError

    return ExpiredSignatureError("expired")