"""登录模块测试用例（TC01~TC41）"""

import os

# 单元测试采用 dev 环境：所有配置直接来自 config/dev.yaml
# （SQLite 引擎由 engine fixture 注入到 app.core.database / app.main 模块，覆盖 dev.yaml 的 MySQL 配置）
os.environ.setdefault("APP_ENV", "dev")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import get_password_hash
from app.main import create_app
from app.models import SysUser  # noqa: F401


@pytest.fixture()
def engine():
    from app.core import database as db_module
    from app import main as main_module
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    new_session_local = sessionmaker(bind=eng, autoflush=False, autocommit=False, expire_on_commit=False)
    db_module.engine = eng
    db_module.SessionLocal = new_session_local
    main_module.engine = eng
    main_module.SessionLocal = new_session_local
    yield eng
    eng.dispose()


@pytest.fixture()
def session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


@pytest.fixture()
def client(session_factory, engine):
    def _override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()
    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def admin_user(session_factory):
    with session_factory() as db:
        u = SysUser(username="admin", password=get_password_hash("admin123"), nickname="管理员", role_id=1, status=1, error_count=0)
        db.add(u)
        db.commit()
        db.refresh(u)
        return {"id": u.id, "username": u.username, "password": "admin123"}


@pytest.fixture()
def disabled_user(session_factory):
    with session_factory() as db:
        u = SysUser(username="disabled", password=get_password_hash("disabled123"), nickname="禁用用户", role_id=1, status=0, error_count=0)
        db.add(u)
        db.commit()
        db.refresh(u)
        return {"id": u.id, "username": u.username, "password": "disabled123"}


def _fetch_captcha(client):
    r = client.get("/api/auth/captcha")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["code"] == 200
    return body["data"]["captcha_id"], body["data"]["captcha_code"], body["data"]["captcha_image"]


def _post_login(client, username, password, captcha_code="0000", captcha_id="fixed"):
    return client.post("/api/auth/login", json={"username": username, "password": password, "captcha_id": captcha_id, "captcha_code": captcha_code})


# TC01
def test_TC01_captcha_returns_id_and_base64_image(client):
    """TC01 获取验证码接口正常返回"""
    r = client.get("/api/auth/captcha")
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 200
    assert body["data"]["captcha_id"]
    assert body["data"]["captcha_code"]
    assert body["data"]["captcha_image"].startswith("data:image/png;base64,")


# TC02
def test_TC02_captcha_expired_cannot_be_used(client, admin_user):
    """TC02 验证码过期后无法使用"""
    captcha_id, captcha_code, _ = _fetch_captcha(client)
    from app.crud.auth import delete_captcha_by_id
    from app.core.database import SessionLocal
    with SessionLocal() as db:
        delete_captcha_by_id(db, captcha_id)
        db.commit()
    r = _post_login(client, admin_user["username"], admin_user["password"], captcha_code, captcha_id)
    assert r.status_code == 400
    assert r.json()["code"] == 400


# TC10
def test_TC10_login_success(client, admin_user):
    """TC10 正常登录成功"""
    captcha_id, captcha_code, _ = _fetch_captcha(client)
    r = _post_login(client, admin_user["username"], admin_user["password"], captcha_code, captcha_id)
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 200
    assert body["data"]["access_token"]
    assert body["data"]["refresh_token"]
    assert body["data"]["user"]["username"] == admin_user["username"]


# TC11
def test_TC11_login_username_not_found_returns_401(client, admin_user):
    """TC11 用户名不存在返回 401"""
    captcha_id, captcha_code, _ = _fetch_captcha(client)
    r = _post_login(client, "no_such_user", "whatever", captcha_code, captcha_id)
    assert r.status_code == 401
    assert r.json()["code"] == 401


# TC12
def test_TC12_login_wrong_password_returns_401(client, admin_user):
    """TC12 密码错误返回 401"""
    captcha_id, captcha_code, _ = _fetch_captcha(client)
    r = _post_login(client, admin_user["username"], "wrong_password", captcha_code, captcha_id)
    assert r.status_code == 401
    assert r.json()["code"] == 401


# TC13
def test_TC13_login_wrong_captcha_returns_400(client, admin_user):
    """TC13 验证码错误返回 400"""
    captcha_id, _captcha_code, _ = _fetch_captcha(client)
    r = _post_login(client, admin_user["username"], admin_user["password"], "9999", captcha_id)
    assert r.status_code == 400
    assert r.json()["code"] == 400


# TC14
def test_TC14_login_expired_captcha_returns_400(client, admin_user):
    """TC14 验证码过期返回 400"""
    captcha_id, captcha_code, _ = _fetch_captcha(client)
    _post_login(client, admin_user["username"], admin_user["password"], captcha_code, captcha_id)
    r = _post_login(client, admin_user["username"], admin_user["password"], captcha_code, captcha_id)
    assert r.status_code == 400
    assert r.json()["code"] == 400


# TC15
def test_TC15_login_disabled_account_returns_403(client, disabled_user):
    """TC15 禁用账号登录返回 403"""
    captcha_id, captcha_code, _ = _fetch_captcha(client)
    r = _post_login(client, disabled_user["username"], disabled_user["password"], captcha_code, captcha_id)
    assert r.status_code == 403
    assert r.json()["code"] == 403


# TC16
def test_TC16_login_locked_account_returns_403(client, admin_user, session_factory):
    """TC16 锁定账号登录返回 403"""
    from datetime import datetime, timedelta
    with session_factory() as db:
        u = db.get(SysUser, admin_user["id"])
        u.error_count = 5
        u.locked_until = datetime.utcnow() + timedelta(minutes=30)
        db.commit()
    captcha_id, captcha_code, _ = _fetch_captcha(client)
    r = _post_login(client, admin_user["username"], admin_user["password"], captcha_code, captcha_id)
    assert r.status_code == 403
    assert r.json()["code"] == 403


# TC17
def test_TC17_login_after_lock_expired_succeeds(client, admin_user, session_factory):
    """TC17 锁定结束后可正常登录"""
    from datetime import datetime, timedelta
    with session_factory() as db:
        u = db.get(SysUser, admin_user["id"])
        u.error_count = 5
        u.locked_until = datetime.utcnow() - timedelta(minutes=1)
        db.commit()
    captcha_id, captcha_code, _ = _fetch_captcha(client)
    r = _post_login(client, admin_user["username"], admin_user["password"], captcha_code, captcha_id)
    assert r.status_code == 200
    assert r.json()["code"] == 200


# TC18
def test_TC18_login_success_resets_error_count(client, admin_user, session_factory):
    """TC18 登录成功后错误次数重置"""
    with session_factory() as db:
        u = db.get(SysUser, admin_user["id"])
        u.error_count = 3
        db.commit()
    captcha_id, captcha_code, _ = _fetch_captcha(client)
    r = _post_login(client, admin_user["username"], admin_user["password"], captcha_code, captcha_id)
    assert r.status_code == 200
    with session_factory() as db:
        u = db.get(SysUser, admin_user["id"])
        assert u.error_count == 0


# TC20
def test_TC20_logout_with_valid_token_succeeds(client, admin_user):
    """TC20 有效 Token 登出成功"""
    captcha_id, captcha_code, _ = _fetch_captcha(client)
    r = _post_login(client, admin_user["username"], admin_user["password"], captcha_code, captcha_id)
    token = r.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    r = client.post("/api/auth/logout", headers=headers)
    assert r.status_code == 200
    assert r.json()["code"] == 200


# TC21
def test_TC21_logout_with_invalid_token_returns_401(client):
    """TC21 无效 Token 登出返回 401"""
    headers = {"Authorization": "Bearer this-is-not-a-jwt"}
    r = client.post("/api/auth/logout", headers=headers)
    assert r.status_code == 401
    assert r.json()["code"] == 401


# TC30
def test_TC30_refresh_with_valid_token_succeeds(client, admin_user):
    """TC30 有效 RefreshToken 刷新成功"""
    captcha_id, captcha_code, _ = _fetch_captcha(client)
    r = _post_login(client, admin_user["username"], admin_user["password"], captcha_code, captcha_id)
    refresh_token = r.json()["data"]["refresh_token"]
    r = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert r.status_code == 200
    body = r.json()
    assert body["data"]["access_token"]
    assert body["data"]["refresh_token"]
    assert body["data"]["refresh_token"] != refresh_token


# TC31
def test_TC31_refresh_with_used_token_returns_401(client, admin_user):
    """TC31 已使用的 RefreshToken 返回 401"""
    captcha_id, captcha_code, _ = _fetch_captcha(client)
    r = _post_login(client, admin_user["username"], admin_user["password"], captcha_code, captcha_id)
    refresh_token = r.json()["data"]["refresh_token"]
    r1 = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert r1.status_code == 200
    r2 = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert r2.status_code == 401
    assert r2.json()["code"] == 401


# TC32
def test_TC32_refresh_with_expired_token_returns_401(client, admin_user, monkeypatch):
    """TC32 过期的 RefreshToken 返回 401"""
    captcha_id, captcha_code, _ = _fetch_captcha(client)
    r = _post_login(client, admin_user["username"], admin_user["password"], captcha_code, captcha_id)
    refresh_token = r.json()["data"]["refresh_token"]
    from app.core import security
    def fake_decode(token, *args, **kwargs):
        raise security.jose_expired()
    monkeypatch.setattr(security, "decode_jwt", fake_decode)
    r = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert r.status_code == 401
    assert r.json()["code"] == 401


# TC40
def test_TC40_me_with_valid_token_succeeds(client, admin_user):
    """TC40 有效 Token 获取用户信息成功"""
    captcha_id, captcha_code, _ = _fetch_captcha(client)
    r = _post_login(client, admin_user["username"], admin_user["password"], captcha_code, captcha_id)
    token = r.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    r = client.get("/api/auth/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["data"]["username"] == admin_user["username"]


# TC41
def test_TC41_me_with_invalid_token_returns_401(client):
    """TC41 无效 Token 获取用户信息返回 401"""
    headers = {"Authorization": "Bearer garbage-token"}
    r = client.get("/api/auth/me", headers=headers)
    assert r.status_code == 401
    assert r.json()["code"] == 401