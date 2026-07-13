# 组织架构模块 (org) 开发 Todo List

> 规格来源：`backend/spec/org_spec.md`
> 状态标记：`[ ]` 未开始　`[~]` 进行中　`[✔]` 已完成　`[✘]` 已取消
> 测试栈沿用 `test_auth.py` 的 `engine` / `session_factory` / `client` / `redis_client` fixture
> 注：dev 单元测试用 SQLite + fakeredis；递归 CTE 在 Service 层用 Python 兼容封装

## Phase 1 · 测试驱动 —— 全红

- [ ] 写 `backend/tests/test_org.py` 全部 42 个 TC（先写，预期全 RED）
  - [ ] 公司 12 个：TC-OR-C01~C12
  - [ ] 部门 20 个：TC-OR-D01~D20
  - [ ] 岗位 10 个：TC-OR-P01~P10
- [ ] `pytest backend/tests/test_org.py -v` 确认 42 用例全 **RED**

## Phase 2 · 骨架：路由可达 + 表创建

- [ ] `app/models/sys_company.py`：`SysCompany` 模型（11 字段 + 索引）
- [ ] `app/models/sys_dept.py`：`SysDept` 模型（含 `parent_id` 自引用 + 索引）
- [ ] `app/models/sys_position.py`：`SysPosition` 模型
- [ ] `app/models/__init__.py`：导出三个新模型
- [ ] `app/api/org.py` 创空 router
- [ ] `app/main.py`：`app.include_router(org_router)`
- [ ] 启动 uvicorn 验证表自动创建

## Phase 3 · 公司 CRUD（TC-OR-C01~C12 全 GREEN）

- [ ] `app/schemas/org.py`：`CompanyIn` / `CompanyUpdate` / `CompanyOut` / `CompanyListOut`
- [ ] `app/crud/org.py`：`create_company` / `get_company_by_id` / `get_company_by_code` / `list_companies` / `list_companies_all` / `update_company` / `delete_company`
- [ ] `app/services/org.py`：`OrgError` / `Company*Error` + `create/update/delete/list` 业务编排（含唯一性校验、引用检查）
- [ ] `app/api/org.py`：`/api/org/companies` 6 个接口
- [ ] TC-OR-C01~C12 全 GREEN

## Phase 4 · 部门 CRUD（TC-OR-D01~D20 全 GREEN）

- [ ] `app/schemas/org.py`：`DeptIn` / `DeptUpdate` / `DeptMoveIn` / `DeptOut` / `DeptTreeNode` / `DeptListOut`
- [ ] `app/crud/org.py`：`create_dept` / `get_dept_by_id` / `get_dept_by_code` / `list_depts` / `update_dept` / `move_dept`（含 `would_create_cycle` 检测）/ `delete_dept`（含子部门/岗位检查）
- [ ] `app/services/org.py`：`Dept*Error` + 业务编排；`get_dept_tree(company_id)` 走 Service 层 Python 递归（生产可用 CTE 优化，但接口契约统一）
- [ ] `app/api/org.py`：`/api/org/depts` 7 个接口（含 `/tree` 和 `/{id}/move`）
- [ ] TC-OR-D01~D20 全 GREEN

## Phase 5 · 岗位 CRUD（TC-OR-P01~P10 全 GREEN）

- [ ] `app/schemas/org.py`：`PositionIn` / `PositionUpdate` / `PositionOut` / `PositionListOut`
- [ ] `app/crud/org.py`：`create_position` / `get_position_by_id` / `get_position_by_code` / `list_positions` / `list_positions_all` / `update_position` / `delete_position`
- [ ] `app/services/org.py`：`Position*Error` + 业务编排
- [ ] `app/api/org.py`：`/api/org/positions` 6 个接口
- [ ] TC-OR-P01~P10 全 GREEN

## Phase 6 · 全量回归 & 契约输出

- [ ] 跑 `pytest backend/tests -v`，确认 18（auth）+ 42（org）= 60/60 全通过
- [ ] 启动服务验证 `/docs` Swagger UI 正常
- [ ] 导出 `backend/openapi/openapi_org.json` 供前端消费

## Phase 7 · 前端开发（frontend/）

- [ ] `frontend/src/api/org.ts`：companies / depts / positions 全部 TS 接口封装（含类型 `Company` / `Dept` / `DeptTreeNode` / `Position` / `Paged<T>`）
- [ ] `frontend/src/router/index.ts`：注册 `/org/companies`、`/org/depts`、`/org/positions` 三个受保护路由
- [ ] `frontend/src/views/org/CompanyList.vue`：表格 + 新增/编辑对话框 + 删除确认
- [ ] `frontend/src/views/org/DeptTree.vue`：左侧树（Element Plus `el-tree`）+ 右侧详情/编辑面板 + 拖拽 / 移动父部门
- [ ] `frontend/src/views/org/PositionList.vue`：表格 + 部门下拉筛选 + 新增/编辑/删除
- [ ] `frontend/src/layout/AppSidebar.vue`（如尚未建）：在侧边栏加 "组织架构" 菜单组
- [ ] 本地启动联调：vite proxy 调通，42 个接口在浏览器可走通主流程