# 登录模块 (auth) 开发 Todo List

> 规格来源：`backend/spec/auth_spec.md`
> 状态标记：`[ ]` 未开始　`[~]` 进行中　`[✔]` 已完成　`[✘]` 已取消

## Phase 1 · 环境与基础设施

- [✔] 创建 `backend/` 目录结构（app/{core,models,schemas,crud,services,api}、tests）
- [✔] 编写 `backend/requirements.txt`（fastapi、uvicorn、sqlalchemy、pymysql、pydantic、python-jose、passlib[bcrypt]、captcha、pytest、httpx）
- [✔] 激活 `dev_env` 并安装依赖
- [✔] 验证 `pytest --collect-only` 可正常收集（即使无用例）

## Phase 2 · 测试驱动 —— 全红 (backend/tests)

> 严格 TDD：根据规格先写全部测试，运行后必须全部 **FAIL**

- [✔] `test_auth.py`：编写以下用例，每个用例独立运行
- [✔] 用例清单（全部须为 **RED**）
  - [✔] TC01 获取验证码接口正常返回
  - [✔] TC02 验证码过期后无法使用
  - [✔] TC10 正常登录成功
  - [✔] TC11 用户名不存在返回 401
  - [✔] TC12 密码错误返回 401
  - [✔] TC13 验证码错误返回 400
  - [✔] TC14 验证码过期返回 400
  - [✔] TC15 禁用账号登录返回 403
  - [✔] TC16 锁定账号登录返回 403
  - [✔] TC17 锁定结束后可正常登录
  - [✔] TC18 登录成功后错误次数重置
  - [✔] TC20 有效 Token 登出成功
  - [✔] TC21 无效 Token 登出返回 401
  - [✔] TC30 有效 RefreshToken 刷新成功
  - [✔] TC31 已使用的 RefreshToken 返回 401
  - [✔] TC32 过期的 RefreshToken 返回 401
  - [✔] TC40 有效 Token 获取用户信息成功
  - [✔] TC41 无效 Token 获取用户信息返回 401
- [✔] 运行 `pytest backend/tests -v`，确认全部用例为 **RED**（连接失败/导入失败/断言失败均可）

## Phase 3 · 最小可运行骨架（让测试可 RUN）

> 目标：搭好 FastAPI + SQLAlchemy 最小骨架，让 18 个用例可以被 pytest 收集并跑出 **RED**。
> 此阶段不实现任何业务逻辑，所有用例应仍处于失败状态。

- [✔] 创建 `backend/app/__init__.py`、`backend/tests/__init__.py`
- [✔] `backend/app/core/config.py`：从环境变量读取配置（DATABASE_URL、JWT_SECRET、Token 有效期等），默认值即可
- [✔] `backend/app/core/database.py`：SQLAlchemy 2.0 Base + engine + SessionLocal + `get_db` 依赖
- [✔] `backend/app/core/response.py`：`{"code","message","data"}` 字典工厂（`success` / `fail` / `json_fail`）
- [✔] `backend/app/main.py`：`create_app()` 工厂，挂载空路由，lifespan 建表，初始化默认 admin
- [✔] `backend/app/api/__init__.py`：空包
- [✔] 跑 `pytest backend/tests -v`，确认 18 用例全部仍为 **RED**（404 / 连接错误 / 断言失败均可）

## Phase 4 · TC01 → GREEN（验证码接口）

- [✔] TC01 维持 **RED**：跑测试，确认 `GET /api/auth/captcha` 用例失败
- [✔] `backend/app/models/sys_captcha.py`：`SysCaptcha` 表 + `captcha_id` 唯一索引
- [✔] `backend/app/models/__init__.py`：导出 `SysCaptcha` 让 Base 发现
- [✔] `backend/app/schemas/auth.py`：`CaptchaOut` Pydantic 模型
- [✔] `backend/app/crud/auth.py`：`create_captcha`、`get_captcha_by_id`
- [✔] `backend/app/services/auth.py`：`generate_captcha(db)` —— captcha 库生成图片 + Base64 + 持久化
- [✔] `backend/app/api/auth.py`：`GET /api/auth/captcha` 路由 + 统一响应
- [✔] TC01 转为 **GREEN**：仅 TC01 通过，其余 17 个仍 RED
- [✔ ] 提交（如用户授权）

## Phase 5 · TC02 → GREEN（验证码过期）

> 注：因 Phase 4 已迁移到 Redis（SETEX TTL 自动过期替代 `expired_at` 字段），
> 本阶段"配置/写入/删除"三项已实质完成。本阶段实际新增的是登录接口的 captcha 校验骨架。

- [✔] TC02 维持 **RED**
- [✔] `backend/app/core/config.py`：增加 `CAPTCHA_EXPIRE_MINUTES=5`（Phase 4 已加）
- [✔] `backend/app/services/auth.py`：`generate_captcha` 通过 SETEX TTL 自动过期（Phase 4 已实现）
- [✔] `backend/app/crud/auth.py`：`delete_captcha_by_id` 已实现；`cleanup_expired_captchas` 由 Redis TTL 替代，无需手动清理
- [✔] `backend/app/schemas/auth.py`：增加 `LoginIn`（登录入参）
- [✔] `backend/app/services/auth.py`：增加 `AuthError` / `CaptchaInvalidError` / `CaptchaMismatchError` + `login()` 骨架（仅校验 captcha，Phase 6+ 补全）
- [✔] `backend/app/api/auth.py`：增加 `POST /api/auth/login` 路由
- [✔] TC02 转为 **GREEN**
- [✔] 跑全套测试：TC01 / TC02 GREEN，**附带 TC13 / TC14 / TC17 也 GREEN**（captcha 校验副作用 + stub 不做用户校验）
  - 13 个 RED：TC10/11/12/15/16/18/20/21/30/31/32/40/41

## Phase 6 · TC10 → GREEN（登录成功 + 用户表 + JWT）

> 注：因完整 login 实现覆盖了所有错误分支，**附带 7 个 TC 同时转 GREEN**（TC11/12/13/14/15/16/17/18）。
> 这意味着 Phase 7 全部已被覆盖，可整体跳过。

- [✔] TC10 维持 **RED**
- [✔] `backend/app/models/sys_user.py`：补齐 `login_time` / `login_ip` / `create_time` / `update_time` 字段
- [✔] `backend/app/core/security.py`：bcrypt 哈希/校验 + JWT 编解码（access 2h / refresh 7d）+ jti + `jose_expired()` 工厂
- [✔] `backend/app/crud/auth.py`：`get_user_by_username` / `get_user_by_id` / `create_user` / `increment_error_count` / `lock_user_until` / `reset_login_state`
- [✔] `backend/app/schemas/auth.py`：`UserOut` + `LoginOut`
- [✔] `backend/app/services/auth.py`：`login(db, redis, username, password, captcha_id, captcha_code, login_ip)` —— 验证码 → 用户 → 锁定 → 状态 → 密码（含错误计数与锁定策略） → 重置 → 双 Token
- [✔] `backend/app/services/auth.py`：新增 `InvalidCredentialsError(401)` / `UserDisabledError(403)` / `UserLockedError(403)`
- [✔] `backend/app/api/auth.py`：`POST /api/auth/login` 接收 db/redis + 返回 LoginOut
- [✔] TC10 转为 **GREEN**
- [✔] 跑全套测试：**11 passed, 7 failed**
  - GREEN：TC01 / TC02 / TC10 / TC11 / TC12 / TC13 / TC14 / TC15 / TC16 / TC17 / TC18
  - RED：TC20 / TC21 / TC30 / TC31 / TC32 / TC40 / TC41（分别对应 logout / refresh / me）

## Phase 7 · TC11~TC18 → GREEN（登录错误分支，每个独立 RED→GREEN）

> **已整体跳过**：Phase 6 完整实现 login 时一次性覆盖了所有错误分支，TC11~18 全部转为 GREEN（参见 Phase 6 验收结果）。
> 本阶段无需任何代码改动。

- [✔] TC11 → GREEN：用户名校验失败时返回 401（用户名不存在）—— **Phase 6 已 GREEN**
- [✔] TC12 → GREEN：密码错误时返回 401，且不影响 TC10 —— **Phase 6 已 GREEN**
- [✔] TC13 → GREEN：验证码答案错误时返回 400 —— **Phase 5 已 GREEN**
- [ ] TC14 → GREEN：验证码被消费/不存在时返回 400
- [ ] TC15 → GREEN：账号被禁用（status=0）时返回 403
- [ ] TC16 → GREEN：账号被锁定（locked_until 未来）时返回 403
- [ ] TC17 → GREEN：locked_until 已过期时允许正常登录
- [ ] TC18 → GREEN：登录成功后 `error_count` 重置为 0
- [ ] 跑全套测试，确认 TC01~TC18 共 9 个 GREEN，其余 9 个仍 RED

## Phase 8 · TC20~TC21 → GREEN（登出）

- [ ] TC20 维持 **RED**
- [ ] `backend/app/models/token_blacklist.py`：`TokenBlacklist` 表（jti / token_type / user_id / expired_at）
- [ ] `backend/app/crud/auth.py`：`add_to_blacklist`、`is_jti_blacklisted`
- [ ] `backend/app/api/auth.py`：从 `Authorization: Bearer <token>` 解析 token 的依赖工具
- [ ] `backend/app/services/auth.py`：`logout(db, token)` —— 解码 access → jti 写入黑名单
- [ ] `backend/app/api/auth.py`：`POST /api/auth/logout` 路由
- [ ] TC20 → GREEN
- [ ] TC21 维持 **RED**
- [ ] `backend/app/services/auth.py`：解码失败时抛出 `TokenInvalidError`
- [ ] `backend/app/api/auth.py`：将 `AuthError` 映射为 HTTP 状态码（400/401/403）+ `json_fail` 响应
- [ ] TC21 → GREEN
- [ ] 跑全套测试，确认 TC01~TC18 + TC20 + TC21 共 11 个 GREEN，其余 7 个仍 RED

## Phase 9 · TC30~TC32 → GREEN（刷新 Token）

- [ ] TC30 维持 **RED**
- [ ] `backend/app/schemas/auth.py`：`RefreshIn`、`RefreshOut`
- [ ] `backend/app/services/auth.py`：`refresh_tokens(db, refresh_token)` —— 校验 → 颁发新双 Token → 旧 refresh 拉黑（旋转策略）
- [ ] `backend/app/api/auth.py`：`POST /api/auth/refresh` 路由
- [ ] TC30 → GREEN
- [ ] TC31 维持 **RED**
- [ ] 已有 `is_jti_blacklist`，确认刷新流程对已拉黑的 refresh 抛 `TokenRevokedError`（401）
- [ ] TC31 → GREEN
- [ ] TC32 维持 **RED**
- [ ] `decode_jwt` 已处理 `ExpiredSignatureError`，服务层转 `TokenInvalidError`，API 层返回 401
- [ ] TC32 → GREEN
- [ ] 跑全套测试，确认 TC01~TC21 + TC30~TC32 共 14 个 GREEN，其余 4 个仍 RED

## Phase 10 · TC40~TC41 → GREEN（当前用户）

- [ ] TC40 维持 **RED**
- [ ] `backend/app/services/auth.py`：`get_current_user(db, token)` —— 解码 access → 黑名单校验 → 查询用户
- [ ] `backend/app/api/auth.py`：`GET /api/auth/me` 路由
- [ ] TC40 → GREEN
- [ ] TC41 维持 **RED**：解码失败 → 401
- [ ] TC41 → GREEN
- [ ] 跑全套测试，确认 18 个用例全部 **GREEN**

## Phase 11 · 全量回归 & 契约输出

- [ ] 跑 `pytest backend/tests -v`，确认 18/18 通过
- [ ] 启动 `uvicorn app.main:app`，访问 `/docs` 验证 Swagger UI 正常
- [ ] 导出 `backend/spec/openapi_auth.json` 供前端消费

## Phase 12 · 前端开发 (frontend/)

> 技术栈：Vue 3 + Element Plus + Pinia + Vue Router + Axios + Vite
> 按 `openapi.json` 契约生成接口封装与页面

- [ ] 创建 `frontend/` 目录（Vite + Vue 3 初始化）
- [ ] 安装依赖：vue、vue-router、pinia、element-plus、axios、sass
- [ ] `src/api/auth.ts`：根据 OpenAPI 生成 5 个接口的 TS 封装（captcha / login / logout / refresh / me）
- [ ] `src/utils/request.ts`：Axios 实例 + 请求拦截器（注入 Bearer Token）+ 响应拦截器（401 跳转登录）
- [ ] `src/stores/auth.ts`：Pinia 状态（access_token / refresh_token / userInfo）+ 持久化
- [ ] `src/router/index.ts`：路由表 + 全局守卫（未登录拦截）
- [ ] `src/views/Login.vue`：登录页（用户名/密码/图形验证码 + 切换验证码）
- [ ] `src/views/Profile.vue` 或相关页面：调用 `/api/auth/me` 展示当前用户
- [ ] `src/layout/AppHeader.vue`：登出按钮调用 `/api/auth/logout`
- [ ] 本地启动 `npm run dev` 联调后端，验证登录 / 登出 / 刷新 / me 流程