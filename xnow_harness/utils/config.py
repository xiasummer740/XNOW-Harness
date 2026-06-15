"""XNOW Harness 配置管理"""

import os
import yaml
from pathlib import Path
from typing import Any, Optional

DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "config.default.yaml"
PROJECT_CONFIG_NAME = ".xnow.yaml"


def _deep_merge(base: dict, override: dict) -> dict:
    """深度合并字典"""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(path: Optional[Path] = None) -> dict:
    """加载配置（默认配置 + 项目配置 + 环境变量覆盖）"""
    # 1. 加载默认配置
    with open(DEFAULT_CONFIG_PATH, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # 2. 加载项目级配置
    if path and path.exists():
        with open(path, encoding="utf-8") as f:
            project_config = yaml.safe_load(f)
        if project_config:
            config = _deep_merge(config, project_config)

    # 3. 自动发现项目 .xnow.yaml
    cwd = Path.cwd()
    xnow_config = cwd / PROJECT_CONFIG_NAME
    if xnow_config.exists():
        with open(xnow_config, encoding="utf-8") as f:
            local_config = yaml.safe_load(f)
        if local_config:
            config = _deep_merge(config, local_config)

    # 4. 环境变量覆盖 API Key
    _resolve_api_keys(config)

    return config


def _resolve_api_keys(config: dict):
    """从环境变量读取 API Key"""
    for model_key in ["primary", "fast"]:
        model = config.get("model", {}).get(model_key, {})
        env_var = model.get("api_key_env", "")
        if env_var and env_var in os.environ:
            model["api_key"] = os.environ[env_var]
        else:
            model["api_key"] = os.environ.get("DEEPSEEK_API_KEY", "")


def save_project_config(config: dict):
    """保存项目级配置到 .xnow.yaml"""
    path = Path.cwd() / PROJECT_CONFIG_NAME
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, indent=2)
    return path
