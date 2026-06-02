"""配置加载与管理。

启动时加载 config.yaml，缺失则从 config.default.yaml 复制。
提供全局 config 单例，支持点号属性访问和运行时修改。
"""
import os
import shutil
from types import SimpleNamespace
from typing import Any

import yaml

CONFIG_FILE = "config.yaml"
DEFAULT_CONFIG_FILE = "config.default.yaml"


def _dict_to_namespace(d: dict) -> SimpleNamespace:
    """递归将 dict 转为 SimpleNamespace，支持属性访问。"""
    ns = {}
    for k, v in d.items():
        if isinstance(v, dict):
            ns[k] = _dict_to_namespace(v)
        elif isinstance(v, list):
            ns[k] = [_dict_to_namespace(item) if isinstance(item, dict) else item for item in v]
        else:
            ns[k] = v
    return SimpleNamespace(**ns)


def _namespace_to_dict(ns: SimpleNamespace) -> dict:
    """递归将 SimpleNamespace 转回 dict（用于 YAML 序列化）。"""
    result = {}
    for k, v in ns.__dict__.items():
        if isinstance(v, SimpleNamespace):
            result[k] = _namespace_to_dict(v)
        elif isinstance(v, list):
            result[k] = [
                _namespace_to_dict(item) if isinstance(item, SimpleNamespace) else item
                for item in v
            ]
        else:
            result[k] = v
    return result


def _deep_merge(base: SimpleNamespace, override: dict) -> None:
    """递归将 override dict 合并到 base SimpleNamespace（原地修改）。"""
    for k, v in override.items():
        if not hasattr(base, k):
            setattr(base, k, v if not isinstance(v, dict) else _dict_to_namespace(v))
            continue
        existing = getattr(base, k)
        if isinstance(v, dict) and isinstance(existing, SimpleNamespace):
            _deep_merge(existing, v)
        else:
            setattr(base, k, v)


def _validate_required(cfg: SimpleNamespace) -> None:
    """校验必填配置项，缺失时抛出 ValueError。"""
    required = [
        ("uie_version", "model", "uie", "version"),
        ("ocr_engine", "model", "ocr", "engine"),
        ("model_dir", "path", "model_dir"),
        ("ocr_onnx", "path", "ocr_onnx"),
        ("uie_paddle", "path", "uie_paddle"),
    ]
    errors = []
    for label, *path in required:
        current = cfg
        for part in path:
            current = getattr(current, part, None)
            if current is None:
                errors.append(f"缺少必填配置项: {label} ({'->'.join(path)})")
                break
    if errors:
        raise ValueError("\n".join(errors))


def load_config(config_path: str = CONFIG_FILE) -> SimpleNamespace:
    """加载配置文件，返回 SimpleNamespace 对象。"""
    if not os.path.exists(config_path):
        if os.path.exists(DEFAULT_CONFIG_FILE):
            shutil.copy(DEFAULT_CONFIG_FILE, config_path)
        else:
            raise FileNotFoundError(
                f"配置文件 {config_path} 不存在，且找不到 {DEFAULT_CONFIG_FILE}"
            )

    with open(config_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    if raw is None:
        raise ValueError(f"配置文件 {config_path} 为空")

    cfg = _dict_to_namespace(raw)
    _validate_required(cfg)
    return cfg


def save_config(cfg: SimpleNamespace, config_path: str = CONFIG_FILE) -> None:
    """将当前配置持久化到 config.yaml。"""
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(_namespace_to_dict(cfg), f, allow_unicode=True, default_flow_style=False, sort_keys=False)


# 全局配置单例 — 在 main.py 启动时初始化
config: SimpleNamespace = None  # type: ignore


def init_config() -> SimpleNamespace:
    """初始化全局配置单例。"""
    global config
    config = load_config()
    return config


def load_default_config() -> SimpleNamespace:
    """加载出厂默认配置（不从 config.yaml 读取，直接读 config.default.yaml）。"""
    if not os.path.exists(DEFAULT_CONFIG_FILE):
        raise FileNotFoundError(f"默认配置文件 {DEFAULT_CONFIG_FILE} 不存在")
    with open(DEFAULT_CONFIG_FILE, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return _dict_to_namespace(raw)
