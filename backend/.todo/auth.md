# 登录模块 (auth) 开发 Todo List

> 规格来源：`backend/spec/auth_spec.md`
> 状态标记：`[ ]` 未开始　`[~]` 进行中　`[✔]` 已完成　`[✘]` 已取消

## Phase 1 · 环境与基础设施

- [ ] 创建 `backend/` 目录结构（app/{core,models,schemas,crud,services,api}、tests）
- [ ] 编写 `backend/requirements.txt`（fastapi、uvicorn、sqlalchemy、pymysql、pydantic、python-jose、passlib[bcrypt]、captcha、pytest、httpx）
- [ ] 激活 `dev_env` 并安装依赖
- [ ] 验证 `pytest --collect-only` 可正常收集（即使无用例）

## Phase 2 · 测试驱动 —— 全红 (backend/tests)

> 严格 TDD：根据规格先写全部测试，运行后必须全部 **FAIL**

- [ ] `test_auth.py`：编写以下用例，每个用例独立运行
- [ ] 用例清单（全部须为 **RED**）
  - [ ] TC01 获取验证码接口正常返回
  - [ ] TC02 验证码过期后无法使用
  - [ ] TC10 正常登录成功
  - [ ] TC11 用户名不存在返回 401
  - [ ] TC12 密码错误返回 401
  - [ ] TC13 验证码错误返回 400
  - [ ] TC14 验证码过期返回 400
  - [ ] TC15 禁用账号登录返回 403
  - [ ] TC16 锁定账号登录返回 403
  - [ ] TC17 锁定结束后可正常登录
  - [ ] TC18 登录成功后错误次数重置
  - [ ] TC20 有效 Token 登出成功
  - [ ] TC21 无效 Token 登出返回 401
  - [ ] TC30 有效 RefreshToken 刷新成功
  - [ ] TC31 已使用的 RefreshToken 返回 401
  - [ ] TC32 过期的 RefreshToken 返回 401
  - [ ] TC40 有效 Token 获取用户信息成功
  - [ ] TC41 无效 Token 获取用户信息返回 401
- [ ] 运行 `pytest backend/tests -v`，确认全部用例为 **RED**（连接失败/导入失败/断言失败均可）

## Phase 3 · 核心层 (backend/app/core)

- [ ] `config.py`：定义配置（数据库连接串、JWT 密钥、Token 有效期、错误上限、锁定时长、验证码有效期）
- [ ] `database.py`：SQLAlchemy 2.0 引擎、SessionLocal、Base、依赖注入
- [ ] `response.py`：统一响应格式 `{"code": 200, "message": "success", "data": null}` 及封装函数
- [ ] `security.py`：密码 bcrypt 加密/校验、JWT 生成与解码（access 2h / refresh 7d）、黑名单校验辅助

## Phase 4 · 数据模型 (backend/app/models)

- [ ] `sys_user.py`：按规格建表（含 error_count、locked_until、status 等字段）
- [ ] `sys_captcha.py`：按规格建表（含 expired_at、captcha_id 唯一索引）
- [ ] `__init__.py`：聚合模型便于 Base.metadata.create_all

## Phase 5 · 数据契约 (backend/app/schemas)

- [ ] `auth.py`：定义 `CaptchaOut`、`LoginIn`、`LoginOut`、`RefreshIn`、`UserOut` 等 Pydantic 模型

## Phase 6 · CRUD 层 (backend/app/crud)

- [ ] `auth.py`：按用户名查询、创建用户、更新错误次数/锁定时间/最后登录信息、验证码增删查

## Phase 7 · 业务层 (backend/app/services)

- [ ] `auth.py`：编排流程
  - [ ] 生成图形验证码（captcha 库 + Base64）+ 持久化 captcha_id/code
  - [ ] 登录：验证码校验 → 用户名校验 → 锁定状态校验 → 状态校验 → 密码校验 → 错误计数/锁定策略 → 重置计数 → 生成双 Token
  - [ ] 登出：将 jti 写入黑名单
  - [ ] 刷新：校验 refresh jti 未在黑名单且未过期 → 颁发新双 Token → 旧 refresh 拉黑
  - [ ] 当前用户：从 Token 解析 user_id → 查询返回

## Phase 8 · 接口层 (backend/app/api)

- [ ] `auth.py`：实现 5 个路由
  - [ ] `GET  /api/auth/captcha`
  - [ ] `POST /api/auth/login`
  - [ ] `POST /api/auth/logout`
  - [ ] `POST /api/auth/refresh`
  - [ ] `GET  /api/auth/me`
- [ ] 异常处理统一映射 400 / 401 / 403

## Phase 9 · 应用入口

- [ ] `main.py`：创建 FastAPI 实例、挂载路由、初始化默认管理员（admin/admin）、启动时建表

## Phase 10 · 测试驱动 —— 全绿

- [ ] 运行 `pytest backend/tests -v`，修复直到全部用例通过
- [ ] 补充覆盖率检查（行/分支）

## Phase 11 · 文档与契约输出

- [ ] 启动服务验证 `/docs` 自动生成的 OpenAPI 文档
- [ ] 导出 `openapi.json` 至 `backend/spec/openapi_auth.json` 供前端消费

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