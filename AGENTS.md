# HRMS 项目级 Codex 规则

## Python 环境

- 使用 conda 管理 Python 环境，环境名固定为 `dev_env`。
- 任何 Python 操作（安装依赖、运行后端、跑 pytest、执行脚本）之前，必须先激活该环境：

  ```bash
  conda activate dev_env
  ```

- 不要在未激活 `dev_env` 的情况下执行 `pip install`、`python`、`uvicorn`、`pytest` 等命令。
- 依赖统一写到 `backend/requirements.txt`，不要在 `dev_env` 之外另起虚拟环境。
- 如果 `dev_env` 不存在或损坏，先停下来告诉用户，不要自行重建环境。
