# 人力资源管理系统（HRMS）- 项目规格

## 1. 项目概述

人力资源管理系统（HRMS）是一个企业级后台管理系统，用于管理公司的人力资源相关业务。

## 2. 技术栈

### 前端技术栈
| 技术 | 说明 |
|------|------|
| Vue 3 | 前端框架 |
| Element Plus | UI 组件库 |
| Pinia | 状态管理 |
| Vue Router | 路由管理 |
| Axios | HTTP 请求库 |
| Sass | CSS 预处理器 |
| Vite | 构建工具 |

### 后端技术栈
| 技术 | 说明 |
|------|------|
| Python 3.11 | 编程语言 |
| FastAPI | Web 框架 |
| SQLAlchemy 2.0 | ORM |
| MySQL 8.0 | 数据库 |
| Redis | 缓存 |
| JWT | 认证 |
| Pydantic | 数据校验 |
| pydantic-settings | 配置管理（多源加载） |
| PyYAML | YAML 配置解析 |

## 3. 项目结构


hrms/
├── frontend/                  # 前端项目
│   └── src/
│       ├── api/             # 接口封装
│       ├── assets/          # 静态资源
│       ├── components/      # 公共组件
│       ├── directives/      # 自定义指令
│       ├── layout/         # 布局组件
│       ├── router/         # 路由配置
│       ├── stores/         # 状态管理
│       ├── utils/          # 工具函数
│       └── views/          # 页面组件
│
├── backend/                  # 后端项目
│   ├── app/                 # 应用代码
│   │   ├── api/            # 接口定义
│   │   ├── models/         # 数据库模型
│   │   ├── schemas/        # 数据模型
│   │   ├── crud/           # 数据库操作
│   │   ├── services/       # 业务逻辑
│   │   └── core/           # 核心配置（config / database / security / response）
│   ├── config/             # 多环境配置（dev.yaml / uat.yaml / prod.yaml）
│   ├── .env                # 运行时环境变量（APP_ENV 等，git ignore）
│   ├── spec/               # 规格文档
│   ├── tests/              # 测试代码
│   ├── .todo/              # 开发任务清单
│   └── requirements.txt
│
└── docs/                    # 项目文档


## 4. 开发规范

### 4.1 开发流程

开发流程分为以下阶段：

1. **先 spec 讨论再开发**：每个功能模块在开发前，必须先进行 spec 探讨并形成规格文档
2. **生成 Todo List 计划**：根据 spec 讨论结果，将开发任务分解为具体的 todo list，保存到 `.todo/` 目录（如 `.todo/模块名.md`），包含任务项和状态标记
3. **测试驱动（全红）**：先写测试用例，运行后全部失败
4. **测试驱动后端开发（全绿）**：根据测试用例驱动开发后端代码，直到测试全部通过
5. **生成 OpenAPI**：自动生成接口文档
6. **按契约生成前端页面**：根据 OpenAPI 文档生成前端接口调用代码和页面
7. **更新 Todo List**：每完成一个任务项后，标记其状态为已完成（[✔]）

| 阶段 | 产出物 | 存放位置 |
|------|--------|----------|
| 需求确认 | 规格文档 | backend/spec/ |
| 测试验证 | 测试用例 | backend/tests/ |
| 功能实现 | 代码 | backend/app/ |
| 开发计划 | Todo List | backend/.todo/ |

### 4.3 代码注释规范

代码中必须包含清晰的中文注释，以确保代码可读性和团队协作效率。

#### 注释要求

| 文件类型 | 注释要求 | 示例 |
|----------|----------|------|
| 路由文件 (api/*.py) | 每个接口必须注释功能说明、请求参数、响应格式 | # 获取图形验证码，返回Base64编码的图片 |
| Service 文件 (services/*.py) | 每个方法必须注释业务逻辑、异常情况 | # 用户登录：验证验证码->验证用户->验证密码->生成Token |
| CRUD 文件 (crud/*.py) | 每个方法必须注释数据库操作 | # 根据用户名查询用户，支持大小写不敏感 |
| Model 文件 (models/*.py) | 每个字段必须注释含义和约束 | # status: 状态 0-禁用 1-启用 |
| Schema 文件 (schemas/*.py) | 每个字段必须注释用途和校验规则 | # username: 登录用户名，长度1-50位 |
| 工具文件 (core/*.py) | 每个方法必须注释功能和使用场景 | # 生成JWT访问令牌，默认2小时有效期 |

#### 注释风格

`python
# 模块文件顶部必须包含模块说明
"""认证模块 - 提供用户登录、登出、Token管理等功能"""

# 类定义必须包含类说明
class SysUser(Base):
    """系统用户表模型"""
    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # 主键，自增
    username: Mapped[str] = mapped_column(String(50))  # 用户名，唯一索引

# 方法定义必须包含方法说明和参数说明
def login(db: Session, username: str, password: str) -> LoginResponse:
    \"\"\"
    用户登录
    
    参数:
        db: 数据库会话
        username: 用户名
        password: 密码（已加密存储）
    
    返回:
        LoginResponse: 包含Token和用户信息的响应对象
    
    异常:
        InvalidCredentialsError: 用户名或密码错误
        UserLockedError: 账号已被锁定
    \"\"\"
`

#### 注释禁止事项

- 禁止使用纯英文注释（除变量名、库函数名外）
- 禁止注释与代码功能不符的内容
- 禁止留下无意义的占位注释（如 # TODO、# xxx）
- 注释应简洁明了，避免冗长描述



