# HRMS 人力资源管理系统

一个前后端分离的人力资源管理系统，当前已实现登录认证模块（图形验证码、账号密码登录、JWT Token 签发与登出）。

## 技术栈

**后端**（`backend/`）

- Python 3.11 + FastAPI + Uvicorn
- SQLAlchemy 2.0 + PyMySQL（MySQL）
- Redis（验证码、Token 黑名单）
- JWT（python-jose）+ bcrypt 密码哈希
- pydantic-settings + YAML 多环境配置（`dev` / `uat` / `prod`）
- pytest + httpx 测试栈

**前端**（`frontend/`）

- Vue 3 + Vite + TypeScript
- Element Plus、Pinia、Vue Router、Axios

## 目录结构

```
HRMS/
├── backend/                # FastAPI 后端
│   ├── app/                # 应用代码（api / core / crud / models / schemas / services）
│   ├── config/             # 多环境配置（dev.yaml / uat.yaml / prod.yaml）
│   ├── tests/              # pytest 测试用例
│   └── requirements.txt
├── frontend/               # Vue 3 前端
│   ├── src/
│   │   ├── api/            # 后端接口封装
│   │   ├── router/         # 路由
│   │   ├── stores/         # Pinia 状态
│   │   ├── views/          # 页面（Login / Profile / Health）
│   │   └── layout/         # 布局组件
│   └── package.json
└── AGENTS.md               # 项目级开发规范（必读）
```

## 环境准备

- **Python**：使用 conda 管理，环境名固定为 `dev_env`（Python 3.11）。如果该环境不存在或损坏，先联系维护者，不要自行重建。
- **MySQL 8.x** 与 **Redis 6.x+**：本地默认连接信息见 `backend/config/dev.yaml`，需要时可自行覆盖。
- **Node.js**：建议 18.x 或 20.x LTS。

> 首次克隆后，请先完整阅读根目录的 [`AGENTS.md`](./AGENTS.md)，里面记录了若干必须遵守的硬性约定（包括 conda 环境的正确激活方式）。

## 启动后端

> ⚠️ PowerShell 单行写法 `conda activate dev_env; uvicorn ...` 不会真正切换环境——必须分两步，或直接用绝对路径调用 `dev_env` 的 Python。

**方式 A：分两步（推荐）**

```powershell
conda activate dev_env
cd backend
uvicorn app.main:app --reload
```

**方式 B：直接调用 dev_env 的 Python**

```powershell
cd D:\Workspace\HRMS\backend
& "D:\anaconda3\envs\dev_env\python.exe" -m uvicorn app.main:app --reload
```

首次启动时会自动建表（开发环境）。可通过 `APP_ENV` 切换配置：

```powershell
$env:APP_ENV = "uat"   # 加载 backend/config/uat.yaml
```

**安装依赖**（首次或升级后）：

```powershell
& "D:\anaconda3\envs\dev_env\python.exe" -m pip install -r backend/requirements.txt
```

启动成功后访问：

- 健康检查：<http://localhost:8000/health>
- 接口文档（Swagger UI）：<http://localhost:8000/docs>

## 启动前端

```powershell
cd frontend
npm install        # 首次或依赖变更后执行
npm run dev        # 开发模式，默认 http://localhost:5173
```

其他常用脚本：

```powershell
npm run build      # 类型检查 + 生产构建，产物在 frontend/dist/
npm run preview    # 本地预览构建产物
```

## 运行测试

后端使用 pytest。**必须**在 `dev_env` 下执行，否则 `bcrypt` 版本可能与 `passlib` 不兼容：

```powershell
conda activate dev_env
cd backend
pytest -v
```

## 默认账号

启动后端后，可在数据库 `sys_user` 表中自行插入测试账号；登录接口要求：

- `username` / `password`（bcrypt 哈希存储）
- `captcha_id` / `captcha_code`（先调用 `/api/auth/captcha` 获取图形验证码）
