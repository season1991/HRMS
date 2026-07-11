# 登录模块规格

## Summary

实现 HRMS 系统的登录认证模块，包含图形验证码、用户登录、Token 管理、登出等功能。

## Key Changes

### 新增文件

| 文件路径 | 说明 |
|----------|------|
| backend/app/core/config.py | 配置文件 |
| backend/app/core/security.py | 安全工具 |
| backend/app/core/database.py | 数据库连接 |
| backend/app/models/sys_user.py | 用户表模型 |
| backend/app/models/sys_captcha.py | 验证码表模型 |
| backend/app/schemas/auth.py | 认证数据模型 |
| backend/app/schemas/response.py | 统一响应格式 |
| backend/app/crud/auth.py | 用户认证CRUD |
| backend/app/services/auth.py | 登录业务逻辑 |
| backend/app/api/auth.py | 认证接口 |
| backend/app/main.py | 应用入口 |
| backend/tests/test_auth.py | 测试用例 |
| backend/requirements.txt | 依赖 |

### 新增数据库表

| 表名 | 说明 |
|------|------|
| sys_user | 用户表 |
| sys_captcha | 验证码表 |


## API And Behavior

### 1. GET /api/auth/captcha

**说明**：获取图形验证码

**响应**：
- captcha_id: 验证码ID
- captcha_image: Base64编码的图片

### 2. POST /api/auth/login

**参数**：username, password, captcha_id, captcha_code

**响应**：access_token, refresh_token, user信息

**业务规则**：
- 验证码错误返回 400
- 用户名/密码错误返回 401
- 连续输错5次锁定30分钟

### 3. POST /api/auth/logout

**说明**：登出，销毁Token

### 4. POST /api/auth/refresh

**参数**：refresh_token

**说明**：刷新Token，返回新的access_token和refresh_token

### 5. GET /api/auth/me

**说明**：获取当前登录用户信息


## Data Model

### sys_user 用户表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键，自增 |
| username | String(50) | 用户名，唯一 |
| password | String(255) | 密码（bcrypt加密） |
| nickname | String(50) | 昵称 |
| role_id | Integer | 角色ID |
| status | Integer | 状态：0-禁用，1-启用 |
| error_count | Integer | 连续错误次数 |
| locked_until | DateTime | 锁定截止时间 |
| login_time | DateTime | 最后登录时间 |
| login_ip | String(50) | 最后登录IP |
| create_time | DateTime | 创建时间 |
| update_time | DateTime | 更新时间 |

### sys_captcha 验证码表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键，自增 |
| captcha_id | String(50) | 验证码ID，唯一 |
| captcha_code | String(10) | 验证码答案 |
| expired_at | DateTime | 过期时间 |
| create_time | DateTime | 创建时间 |


## Test Plan

| 用例编号 | 测试内容 |
|----------|----------|
| TC01 | 获取验证码接口正常返回 |
| TC02 | 验证码过期后无法使用 |
| TC10 | 正常登录成功 |
| TC11 | 用户名不存在返回401 |
| TC12 | 密码错误返回401 |
| TC13 | 验证码错误返回400 |
| TC14 | 验证码过期返回400 |
| TC15 | 禁用账号登录返回403 |
| TC16 | 锁定账号登录返回403 |
| TC17 | 锁定结束后可正常登录 |
| TC18 | 登录成功后错误次数重置 |
| TC20 | 有效Token登出成功 |
| TC21 | 无效Token登出返回401 |
| TC30 | 有效RefreshToken刷新成功 |
| TC31 | 已使用的RefreshToken返回401 |
| TC32 | 过期的RefreshToken返回401 |
| TC40 | 有效Token获取用户信息成功 |
| TC41 | 无效Token获取用户信息返回401 |

## Assumptions

1. 使用 captcha 库生成图形验证码
2. 使用 bcrypt 进行密码加密
3. 使用 python-jose 处理 JWT
4. Refresh Token 黑名单存储在 Redis（若无Redis则用数据库表代替）
5. 系统初始化时自动创建默认管理员账号（admin / admin123）
6. 统一响应格式：{"code": 200, "message": "success", "data": null}
7. 使用 SQLAlchemy 2.0 语法
8. 数据库使用 MySQL 8.0
9. Access Token 有效期 2 小时
10. Refresh Token 有效期 7 天
11. 验证码有效期 5 分钟
12. 最大登录错误次数 5 次
13. 锁定时长 30 分钟
