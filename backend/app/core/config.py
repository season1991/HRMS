"""应用配置（pydantic-settings + YAML 多环境）

加载顺序（高 → 低）：
1. .env 文件
2. backend/config/{APP_ENV}.yaml   ← 按 APP_ENV 选择 dev / uat / prod
3. 环境变量（os.environ）
4. file secrets
5. 类默认值

⚠️ 初始化参数（Settings(DEBUG=True)）不会生效——避免代码中硬编码覆盖配置。

启动行为：
- 默认 APP_ENV=dev，加载 config/dev.yaml（dev 也是测试环境，单元测试直接使用）
- 设置 APP_ENV=uat 加载 config/uat.yaml
- 设置 APP_ENV=prod 加载 config/prod.yaml（生产密钥通过环境变量注入）
- 设置 APP_ENV 为其他值（未指定环境）或对应文件缺失 → 回退到 dev.yaml
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Tuple

import yaml
from pydantic.fields import FieldInfo
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)


# backend/config/ 目录（backend/app/core/config.py → 向上两级 → backend/）
CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"


class YamlConfigSource(PydanticBaseSettingsSource):
    """从 backend/config/{APP_ENV}.yaml 读取配置（优先级低于 env vars）

    加载策略：
    - APP_ENV 未设置 → 默认 dev，加载 dev.yaml
    - APP_ENV 指定为 dev / uat / prod → 加载对应 yaml
    - APP_ENV 为其他值（未指定环境）或对应文件缺失 → 回退到 dev.yaml
    """

    def __init__(self, settings_cls: type[BaseSettings]) -> None:
        super().__init__(settings_cls)
        env = os.getenv("APP_ENV", "dev")
        path = CONFIG_DIR / f"{env}.yaml"
        if not path.exists():
            # 非指定环境或文件缺失，统一回退到 dev.yaml（dev 即测试环境）
            path = CONFIG_DIR / "dev.yaml"
        self._env = env
        self._path = path
        self._data: dict[str, Any] = {}
        if path.exists():
            with open(path, encoding="utf-8") as f:
                loaded = yaml.safe_load(f) or {}
            if not isinstance(loaded, dict):
                raise ValueError(
                    f"{path} 必须是键值对 YAML（dict），实际为 {type(loaded).__name__}"
                )
            self._data = loaded

    def get_field_value(
        self, field: FieldInfo, field_name: str
    ) -> Tuple[Any, str, bool]:
        value = self._data.get(field_name)
        return value, field_name, False

    def prepare_field_value(
        self, field_name: str, field: FieldInfo, value: Any, value_is_complex: bool
    ) -> Any:
        return value

    def __call__(self) -> dict[str, Any]:
        return dict(self._data)


class Settings(BaseSettings):
    """全局配置"""

    # 应用基础
    APP_NAME: str
    APP_ENV: str
    DEBUG: bool

    # 数据库
    DATABASE_URL: str
    DB_ECHO: bool

    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_MINUTES: int

    # 登录安全策略
    MAX_LOGIN_ERROR_COUNT: int
    LOCK_MINUTES: int
    CAPTCHA_EXPIRE_MINUTES: int

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,  # pydantic-settings 强制签名；故意不返回，禁用 init kwargs 覆盖
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # 优先级从左到右递减
        return (
            dotenv_settings,
            YamlConfigSource(settings_cls),
            env_settings,
            file_secret_settings,
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """单例获取配置对象"""
    return Settings()


settings = get_settings()