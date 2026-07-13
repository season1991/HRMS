# 组织架构模块规格

## Summary

实现 HRMS 的组织架构模块，包含公司、部门（树形）、岗位三类实体的管理。组织树采用 `parent_id` 自引用 + MySQL 递归 CTE 实现；本模块不涉及员工主档（`sys_user` 保持不变），但为后续员工模块预留 `dept.leader_id` 字段。

## Key Changes

### 新增文件

| 文件路径 | 说明 |
|----------|------|
| `backend/app/models/sys_company.py` | 公司表模型 |
| `backend/app/models/sys_dept.py` | 部门表模型（自引用树） |
| `backend/app/models/sys_position.py` | 岗位表模型 |
| `backend/app/schemas/org.py` | 组织架构数据模型（Company / Dept / Position 全部 In/Out） |
| `backend/app/crud/org.py` | 组织架构 CRUD（含树查询、循环引用检测） |
| `backend/app/services/org.py` | 组织架构业务编排 + 业务异常 |
| `backend/app/api/org.py` | 组织架构接口路由（`/api/org/companies`、`/api/org/depts`、`/api/org/positions`） |
| `backend/tests/test_org.py` | 测试用例（按 TC 编号） |
| `backend/.todo/org.md` | 组织架构模块开发 Todo List |

### 修改文件

| 文件路径 | 修改说明 |
|----------|----------|
| `backend/app/models/__init__.py` | 导出 `SysCompany` / `SysDept` / `SysPosition`，使 `Base.metadata.create_all` 能建表 |
| `backend/app/main.py` | `create_app()` 中 `app.include_router(org_router)` |

### 新增数据库表

| 表名 | 说明 |
|------|------|
| `sys_company` | 公司表 |
| `sys_dept` | 部门表（`parent_id` 自引用，整棵树可递归展开） |
| `sys_position` | 岗位表，隶属部门 |

> **不**新建 `sys_employee` 表；`sys_dept.leader_id` 存为 `INT NULL`，**不**建外键约束，留给后续人事模块决定是否补 FK。

## Configuration

本模块**无新增配置项**（无需在 `backend/config/{env}.yaml` 追加字段）。如未来要调分页默认页大小，可在 `Settings` 中补 `ORG_DEFAULT_PAGE_SIZE` 等。

## API And Behavior

> 所有接口统一响应格式 `{"code": 200, "message": "success", "data": ...}`，鉴权沿用现有 Bearer Token（除显式标注"公开"外均需登录）。
> 分页参数：`page`（默认 1）、`page_size`（默认 20，最大 100）。分页响应 `data` 形如 `{items: [...], total: N, page: 1, page_size: 20}`。
> 业务异常由 `services/org.py` 抛出 `OrgError(code, message)`，API 层捕获后用 `json_fail` 返回；状态码与业务码保持一致。

### 一、公司（`/api/org/companies`）

#### 1. GET `/api/org/companies`
公司列表（分页 + 关键字模糊搜索）。
**Query**：`keyword`（公司名/编码模糊）、`status`、`page`、`page_size`
**业务规则**：按 `sort_order ASC, id ASC` 排序。

#### 2. GET `/api/org/companies/all`
公司全量（不分页，供前端下拉用）。
**响应**：`{code, message, data: [Company, ...]}`，仅返回 `status=1` 的启用项。

#### 3. GET `/api/org/companies/{id}`
公司详情。
**异常**：404（公司不存在）

#### 4. POST `/api/org/companies`
新增公司。
**Body**：`{code, name, short_name?, status?, sort_order?, remark?}`
**业务规则**：
- `code` 公司内唯一 → 重复返回 400。
- `status` 默认 1（启用）。

#### 5. PUT `/api/org/companies/{id}`
修改公司。
**Body**：字段同上（`code` 可改但仍需唯一）。

#### 6. DELETE `/api/org/companies/{id}`
删除公司。
**业务规则**：
- 公司下存在部门 → 400 "请先删除该公司下部门"。
- 公司下存在岗位 → 400 "请先删除该公司下岗位"。

### 二、部门（`/api/org/depts`）

#### 1. GET `/api/org/depts/tree`
部门树。
**Query**：`company_id`（必填）
**实现**：MySQL 8 递归 CTE（`WITH RECURSIVE cte AS (...)`），前端一次拿到整棵子树。
**响应**：`data: [DeptTreeNode, ...]`，节点形如：
```json
{ "id": 1, "parent_id": 0, "name": "技术部", "code": "TECH", "leader_id": null, "status": 1, "sort_order": 0, "children": [ ... ] }
```

#### 2. GET `/api/org/depts`
部门平铺列表（分页 + 过滤）。
**Query**：`company_id`、`parent_id`、`keyword`（名称/编码）、`status`、`page`、`page_size`
**业务规则**：按 `sort_order ASC, id ASC`。

#### 3. GET `/api/org/depts/{id}`
部门详情。

#### 4. POST `/api/org/depts`
新增部门。
**Body**：`{company_id, parent_id?, name, code, leader_id?, sort_order?, status?, category?}`
**业务规则**：
- `company_id` 必须存在 → 否则 400。
- `parent_id` 不传或 0 → 创建顶级部门。
- 若 `parent_id != 0` 则必须存在且 `company_id` 一致 → 否则 400。
- `code` 公司内唯一 → 重复返回 400。
- `category`（字典/枚举）默认 2（部门），可选 1=公司层级/3=班组。

#### 5. PUT `/api/org/depts/{id}`
修改部门基础字段（**不含** `parent_id`）。
**说明**：移动部门用专用接口 `/move`，便于权限拆分和循环检测。

#### 6. PUT `/api/org/depts/{id}/move`
移动部门（修改 `parent_id`）。
**Body**：`{parent_id}`（0 表示提升为顶级）
**业务规则**：
- 新父部门必须存在且同公司 → 否则 400。
- 不能将部门移动到自身或其后代下 → 否则 400 "不能将部门移动到自身或子部门下"。
  **实现**：从新 `parent_id` 沿 `parent_id` 上溯到根，若途经 `id` 则判定成环。

#### 7. DELETE `/api/org/depts/{id}`
删除部门。
**业务规则**：
- 存在子部门 → 400 "请先删除子部门"。
- 存在岗位 → 400 "请先删除该部门下岗位"。

### 三、岗位（`/api/org/positions`）

#### 1. GET `/api/org/positions`
岗位列表（分页）。
**Query**：`company_id`、`dept_id`、`keyword`（名称/编码）、`status`、`page`、`page_size`

#### 2. GET `/api/org/positions/all`
岗位全量（下拉用）。
**Query**：`dept_id`（可空；不传则返回所有启用岗位）
**响应**：仅返回 `status=1`。

#### 3. GET `/api/org/positions/{id}`
岗位详情。

#### 4. POST `/api/org/positions`
新增岗位。
**Body**：`{company_id, dept_id, name, code, level?, sort_order?, status?, remark?}`
**业务规则**：
- `dept_id` 必须存在 → 否则 400。
- `code` 公司内唯一 → 重复返回 400。

#### 5. PUT `/api/org/positions/{id}`
修改岗位。

#### 6. DELETE `/api/org/positions/{id}`
删除岗位。
**说明**：本期不引用岗位的实体（员工主档未上线），故**无引用检查**；直接删除即可。

## Data Model

### `sys_company` 公司表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键，自增 |
| code | String(50) | 公司编码，全局唯一 |
| name | String(100) | 公司名称 |
| short_name | String(50) NULL | 公司简称 |
| status | Integer | 0-禁用，1-启用，默认 1 |
| sort_order | Integer | 排序，默认 0 |
| remark | String(500) NULL | 备注 |
| create_time | DateTime | 创建时间，`func.now()` |
| update_time | DateTime | 更新时间，`onupdate=func.now()` |

**索引**：`code` UNIQUE；`(status, sort_order)` 普通索引。

### `sys_dept` 部门表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键，自增 |
| company_id | Integer | 所属公司，不为空 |
| parent_id | Integer | 父部门，0=顶级，默认 0 |
| name | String(100) | 部门名称 |
| code | String(50) | 部门编码，公司内唯一 |
| category | Integer | 类型：1=公司层 / 2=部门 / 3=班组，默认 2 |
| leader_id | Integer NULL | 部门负责人 `employee.id` 预留，**不建外键** |
| sort_order | Integer | 同级排序，默认 0 |
| status | Integer | 0-禁用，1-启用，默认 1 |
| create_time | DateTime | 创建时间 |
| update_time | DateTime | 更新时间 |

**索引**：`code` 在 `company_id` 内 UNIQUE → `UNIQUE(company_id, code)`；`(company_id, parent_id, sort_order)` 普通索引（加速树查询）；`parent_id` 普通索引（递归 CTE 关联用）。

### `sys_position` 岗位表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键，自增 |
| company_id | Integer | 所属公司，不为空 |
| dept_id | Integer | 所属部门，不为空 |
| name | String(100) | 岗位名称 |
| code | String(50) | 岗位编码，公司内唯一 |
| level | Integer NULL | 职级（如 P5、M3），可空 |
| sort_order | Integer | 排序，默认 0 |
| status | Integer | 0-禁用，1-启用，默认 1 |
| remark | String(500) NULL | 备注 |
| create_time | DateTime | 创建时间 |
| update_time | DateTime | 更新时间 |

**索引**：`UNIQUE(company_id, code)`；`(dept_id, sort_order)` 普通索引。

## Test Plan

> 用例编号规则：`TC-OR-Cxx`（公司）/ `TC-OR-Dxx`（部门）/ `TC-OR-Pxx`（岗位）。测试栈沿用 `test_auth.py` 的 `engine` / `session_factory` / `client` / `redis_client` fixture + SQLite 内存库。

### 公司（12 个）

| 用例编号 | 测试内容 |
|----------|----------|
| TC-OR-C01 | 新增公司正常返回 200，字段回显 |
| TC-OR-C02 | 编码重复返回 400 |
| TC-OR-C03 | 公司列表分页：page=1 / page_size=10 正常返回 total + items |
| TC-OR-C04 | 公司列表 keyword 模糊搜索 name |
| TC-OR-C05 | 公司全量仅返回 status=1 |
| TC-OR-C06 | 详情接口 200 返回完整字段 |
| TC-OR-C07 | 详情接口不存在公司返回 404 |
| TC-OR-C08 | 修改公司正常返回 200 |
| TC-OR-C09 | 修改公司编码重复返回 400 |
| TC-OR-C10 | 删除无部门/岗位的公司返回 200 |
| TC-OR-C11 | 删除有部门的公司返回 400 |
| TC-OR-C12 | 删除有岗位的公司返回 400 |

### 部门（20 个）

| 用例编号 | 测试内容 |
|----------|----------|
| TC-OR-D01 | 新增顶级部门（parent_id=0）正常 |
| TC-OR-D02 | 新增子部门（指定 parent_id）正常 |
| TC-OR-D03 | 新增部门 company_id 不存在返回 400 |
| TC-OR-D04 | 新增部门 parent_id 与 company_id 不一致返回 400 |
| TC-OR-D05 | 同公司内 code 重复返回 400 |
| TC-OR-D06 | 部门树接口按 company_id 递归返回嵌套 children |
| TC-OR-D07 | 部门树接口空公司返回 `[]` |
| TC-OR-D08 | 部门平铺列表按 parent_id / keyword 过滤 |
| TC-OR-D09 | 部门详情 200 / 404 不存在 |
| TC-OR-D10 | 修改部门基础字段成功（不含 parent_id） |
| TC-OR-D11 | 移动部门到另一个父部门成功 |
| TC-OR-D12 | 移动部门到自身返回 400 |
| TC-OR-D13 | 移动部门到其后代下返回 400 |
| TC-OR-D14 | 移动部门到跨公司父部门返回 400 |
| TC-OR-D15 | 移动部门到顶级（parent_id=0）成功 |
| TC-OR-D16 | 删除无子部门/岗位的部门成功 |
| TC-OR-D17 | 删除存在子部门的部门返回 400 |
| TC-OR-D18 | 删除存在岗位的部门返回 400 |
| TC-OR-D19 | 部门列表按 sort_order 升序 |
| TC-OR-D20 | 修改部门编码重复返回 400 |

### 岗位（10 个）

| 用例编号 | 测试内容 |
|----------|----------|
| TC-OR-P01 | 新增岗位正常 |
| TC-OR-P02 | 新增岗位 dept_id 不存在返回 400 |
| TC-OR-P03 | 新增岗位 code 重复返回 400 |
| TC-OR-P04 | 岗位列表按 dept_id 过滤 |
| TC-OR-P05 | 岗位全量仅返回 status=1 |
| TC-OR-P06 | 岗位详情 200 / 404 不存在 |
| TC-OR-P07 | 修改岗位成功 |
| TC-OR-P08 | 删除岗位成功 |
| TC-OR-P09 | 岗位列表按 sort_order 升序 |
| TC-OR-P10 | 跨公司同 code 的两个岗位可同时存在 |

## Assumptions

1. 数据库为 MySQL 8.0（递归 CTE 依赖 `WITH RECURSIVE`，SQLite 测试用 mock / 退化方案：`tree` 接口在测试中改为递归 Python 查库，或仅跑集成测试）。
2. **递归 CTE 的测试策略**：单元测试用 SQLite 时改用 Python 端循环展开（`get_dept_tree` 服务函数封装掉数据库方言差异），保持 42 个 TC 在 SQLite 下全 GREEN。
3. 不做软删除，统一用 `status` 字段表达启用/停用；删除是物理删除。
4. 不做操作日志、审批流、版本号字段。
5. `leader_id` 字段本期不暴露于 Pydantic 写模型（Schema 不带 `leader_id` 入参），但模型保留该列；如需支持指定负责人，待员工模块上线后再补。
6. 不做国际化（i18n）字典；分类 `category` 直接存整数。
7. 树深度不设硬上限，由业务自行约束；移动部门时只防环，不防"过深"。
8. 接口全部需登录鉴权（沿用现有 Bearer Token），本模块不引入新的权限模型（不做按钮级权限）。
9. 分页统一参数 `page` / `page_size`，与未来其他模块对齐。
10. 排序统一 `sort_order ASC, id ASC`。
11. 错误响应统一由 `core/response.py` 现有 `json_fail` 输出。
12. 单元测试沿用 `test_auth.py` 的 `fakeredis` + SQLite 内存方案，无需真实 MySQL/Redis。