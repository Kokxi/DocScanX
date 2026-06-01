# DocScanX Phase 1 平台骨架 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 搭建 DocScanX 项目脚手架：目录结构、配置系统、日志系统、FastAPI 骨架（3 个端点）。

**Architecture:** Python 3.8+，FastAPI + uvicorn 内嵌 Web 服务，YAML 配置文件通过 SimpleNamespace 提供嵌套属性访问，标准库 logging + RotatingFileHandler 实现三类结构化日志。

**Tech Stack:** Python 3.8+, FastAPI 0.100+, uvicorn 0.22+, PyYAML 6.0+, 标准库 logging

---

### Task 1: 创建目录结构和 .gitkeep 文件

**Files:**
- Create: `config.yaml` (empty placeholder, content in Task 2)
- Create: `config.default.yaml` (content in Task 2)
- Create: `requirements.txt` (content in Task 3)
- Create: `app/__init__.py`
- Create: `app/core/__init__.py`
- Create: `app/engine/__init__.py`
- Create: `app/scheduler/__init__.py`
- Create: `app/api/__init__.py`
- Create: `app/services/__init__.py`
- Create: `app/utils/__init__.py`
- Create: `frontend/index.html`
- Create: `frontend/css/style.css`
- Create: `frontend/js/app.js`
- Create: `frontend/js/api.js`
- Create: `frontend/js/dashboard.js`
- Create: `frontend/js/scan.js`
- Create: `frontend/js/persons.js`
- Create: `frontend/js/reports.js`
- Create: `frontend/js/settings.js`
- Create: `frontend/js/logs.js`
- Create: `models/.gitkeep`
- Create: `output/.gitkeep`
- Create: `logs/.gitkeep`
- Create: `temp/.gitkeep`
- Create: `tests/.gitkeep`

All `__init__.py` files are empty. All `frontend/js/*.js` files are empty. `frontend/css/style.css` is empty. `.gitkeep` files are empty.

- [ ] **Step 1: Create all directories**

```bash
mkdir -p E:/DocScanX/app/core
mkdir -p E:/DocScanX/app/engine
mkdir -p E:/DocScanX/app/scheduler
mkdir -p E:/DocScanX/app/api
mkdir -p E:/DocScanX/app/services
mkdir -p E:/DocScanX/app/utils
mkdir -p E:/DocScanX/frontend/css
mkdir -p E:/DocScanX/frontend/js
mkdir -p E:/DocScanX/models
mkdir -p E:/DocScanX/output
mkdir -p E:/DocScanX/logs
mkdir -p E:/DocScanX/temp
mkdir -p E:/DocScanX/tests
```

- [ ] **Step 2: Create all empty files**

```bash
touch E:/DocScanX/config.yaml
touch E:/DocScanX/config.default.yaml
touch E:/DocScanX/requirements.txt
touch E:/DocScanX/app/__init__.py
touch E:/DocScanX/app/core/__init__.py
touch E:/DocScanX/app/engine/__init__.py
touch E:/DocScanX/app/scheduler/__init__.py
touch E:/DocScanX/app/api/__init__.py
touch E:/DocScanX/app/services/__init__.py
touch E:/DocScanX/app/utils/__init__.py
touch E:/DocScanX/frontend/index.html
touch E:/DocScanX/frontend/css/style.css
touch E:/DocScanX/frontend/js/app.js
touch E:/DocScanX/frontend/js/api.js
touch E:/DocScanX/frontend/js/dashboard.js
touch E:/DocScanX/frontend/js/scan.js
touch E:/DocScanX/frontend/js/persons.js
touch E:/DocScanX/frontend/js/reports.js
touch E:/DocScanX/frontend/js/settings.js
touch E:/DocScanX/frontend/js/logs.js
touch E:/DocScanX/models/.gitkeep
touch E:/DocScanX/output/.gitkeep
touch E:/DocScanX/logs/.gitkeep
touch E:/DocScanX/temp/.gitkeep
touch E:/DocScanX/tests/.gitkeep
```

- [ ] **Step 3: Verify directory structure**

```bash
find E:/DocScanX -type f -o -type d | sort
```

Expected: All 30+ paths listed above exist.

---

### Task 2: 写配置文件 config.default.yaml 和 config.yaml

**Files:**
- Write: `config.default.yaml`
- Write: `config.yaml`

- [ ] **Step 1: Write config.default.yaml**

Write to `E:/DocScanX/config.default.yaml`:

```yaml
# DocScanX 默认配置
# 用户可修改 config.yaml 覆盖以下值

scan:
  default_path: ""
  include_subdir: true
  extract_archive: true
  file_extensions:
    archive: [.zip, .rar, .7z]
    office_new: [.docx, .xlsx, .pptx]
    office_old: [.doc, .xls, .ppt]
    pdf: [.pdf]
    image: [.jpg, .jpeg, .png, .bmp, .tiff]
    text: [.txt, .csv, .md, .log]
    structured: [.json, .xml]
    dev: [.py, .java, .js, .html, .sql, .css, .cpp]
  extension_groups_default:
    archive: true
    office_new: true
    office_old: false
    pdf: true
    image: true
    text: true
    structured: false
    dev: false

model:
  uie:
    version: small
    path: ./models/uie-small
    schema: [name, id_card, phone, bank_card, address, email, wechat, birthday, job_no, plate_no, passport, gender]
  ocr:
    engine: rapidocr
    rapidocr_path: ./models/ocr_rapidocr
    paddleocr_path: ./models/ocr_paddle_v4_light

inference:
  confidence_threshold: 0.65
  text_chunk_size: 512
  text_chunk_overlap: 64

pdf:
  text_threshold: 20

task:
  file_timeout: 300
  max_retry: 3
  log_detail: true

memory:
  max_memory_mb: 2048
  gc_watermark: 0.8
  temp_clean_after_task: true

concurrency:
  file_parse_workers: 2
  ocr_workers: 1
  uie_workers: 1

# --- 二期扩展：大模型配置 ---
# llm:
#   enable: false
#   api_base: ""
#   api_key: ""
#   model: ""
#   timeout: 30
#   max_retries: 3
#   cross_validation: false
#   confidence_boost: 0.8

# --- 二期扩展：远程文件源 ---
# remote_sources:
#   - name: "Example-Server"
#     protocol: ftp
#     host: ""
#     port: 21
#     username: ""
#     password: ""
#     base_path: "/"
#     max_file_size_mb: 500
#     connect_timeout: 30

log:
  level: INFO
  max_days: 7
  max_size_mb: 10
  path: ./logs

path:
  output_dir: ./output
  temp_dir: ./temp
  model_dir: ./models
  log_dir: ./logs
```

- [ ] **Step 2: Copy default config as initial config.yaml**

```bash
cp E:/DocScanX/config.default.yaml E:/DocScanX/config.yaml
```

---

### Task 3: 写 requirements.txt

**Files:**
- Write: `requirements.txt`

- [ ] **Step 1: Write requirements.txt**

Write to `E:/DocScanX/requirements.txt`:

```
fastapi>=0.100.0
uvicorn[standard]>=0.22.0
pyyaml>=6.0
```

- [ ] **Step 2: Install dependencies**

```bash
cd E:/DocScanX && pip install -r requirements.txt
```

Expected: All 3 packages installed successfully.

---

### Task 4: 写 app/utils/file_utils.py 和 app/utils/text_utils.py

**Files:**
- Write: `app/utils/file_utils.py`
- Write: `app/utils/text_utils.py`

- [ ] **Step 1: Write file_utils.py**

Write to `E:/DocScanX/app/utils/file_utils.py`:

```python
"""文件系统工具函数。"""
import os


def ensure_dir(dir_path: str) -> str:
    """确保目录存在，不存在则创建。返回目录路径。"""
    os.makedirs(dir_path, exist_ok=True)
    return dir_path


def get_file_size_mb(file_path: str) -> float:
    """获取文件大小（MB）。"""
    return os.path.getsize(file_path) / (1024 * 1024)


def is_file_accessible(file_path: str) -> bool:
    """检查文件是否存在且可读。"""
    return os.path.isfile(file_path) and os.access(file_path, os.R_OK)
```

- [ ] **Step 2: Write text_utils.py**

Write to `E:/DocScanX/app/utils/text_utils.py`:

```python
"""文本处理工具函数。"""


def truncate(text: str, max_len: int = 100) -> str:
    """截断文本到指定长度，超出加省略号。"""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


def safe_str(obj) -> str:
    """安全转换为字符串，避免 None / 编码异常。"""
    if obj is None:
        return ""
    return str(obj)
```

---

### Task 5: 写 app/core/config.py

**Files:**
- Write: `app/core/config.py`

- [ ] **Step 1: Write config.py**

Write to `E:/DocScanX/app/core/config.py`:

```python
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
    required_paths = [
        ("uie", "model", "uie", "path"),
        ("uie", "model", "uie", "version"),
        ("ocr", "model", "ocr", "engine"),
    ]
    errors = []
    for label, *path in required_paths:
        current = cfg
        for part in path:
            current = getattr(current, part, None)
            if current is None:
                errors.append(f"缺少必填配置项: {'->'.join([label, *path])}")
                break
    if errors:
        raise ValueError("\n".join(errors))


def load_config(config_path: str = CONFIG_FILE) -> SimpleNamespace:
    """加载配置文件，返回 SimpleNamespace 对象。"""
    # 如果 config.yaml 不存在，从默认配置复制
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
```

- [ ] **Step 2: Verify config module imports**

```bash
cd E:/DocScanX && python -c "from app.core.config import load_config, load_default_config, _dict_to_namespace, _namespace_to_dict, _deep_merge; print('OK')"
```

Expected: `OK` (no import errors)

---

### Task 6: 写 app/core/logging_config.py

**Files:**
- Write: `app/core/logging_config.py`

- [ ] **Step 1: Write logging_config.py**

Write to `E:/DocScanX/app/core/logging_config.py`:

```python
"""日志系统初始化。

提供三种日志通道：
- system: 系统事件（启动/停止/配置变更），输出到控制台 + logs/system.log
- task: 任务处理记录，输出到 logs/task.log
- audit: 操作审计，输出到 logs/audit.log
"""
import logging
import os
from logging.handlers import RotatingFileHandler

from app.utils.file_utils import ensure_dir

_loggers_initialized = False

LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def _create_rotating_handler(
    filepath: str, max_bytes: int, backup_count: int = 5
) -> RotatingFileHandler:
    """创建滚動文件 handler。"""
    ensure_dir(os.path.dirname(filepath))
    handler = RotatingFileHandler(
        filepath, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    return handler


def setup_logging(log_dir: str = "./logs", max_size_mb: int = 10, level: str = "INFO") -> None:
    """初始化全局日志系统。"""
    global _loggers_initialized
    if _loggers_initialized:
        return

    max_bytes = max_size_mb * 1024 * 1024
    log_level = getattr(logging, level.upper(), logging.INFO)

    # System logger — 控制台 + 文件
    system_logger = logging.getLogger("system")
    system_logger.setLevel(log_level)
    system_logger.propagate = False

    # 控制台 handler
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    console.setLevel(log_level)
    system_logger.addHandler(console)

    # 文件 handler
    system_logger.addHandler(_create_rotating_handler(
        os.path.join(log_dir, "system.log"), max_bytes
    ))

    # Task logger — 仅文件
    task_logger = logging.getLogger("task")
    task_logger.setLevel(log_level)
    task_logger.propagate = False
    task_logger.addHandler(_create_rotating_handler(
        os.path.join(log_dir, "task.log"), max_bytes
    ))

    # Audit logger — 仅文件
    audit_logger = logging.getLogger("audit")
    audit_logger.setLevel(logging.INFO)
    audit_logger.propagate = False
    audit_logger.addHandler(_create_rotating_handler(
        os.path.join(log_dir, "audit.log"), max_bytes
    ))

    _loggers_initialized = True
    system_logger.info("日志系统初始化完成")


def get_system_logger() -> logging.Logger:
    return logging.getLogger("system")


def get_task_logger() -> logging.Logger:
    return logging.getLogger("task")


def get_audit_logger() -> logging.Logger:
    return logging.getLogger("audit")
```

- [ ] **Step 2: Verify logging module imports**

```bash
cd E:/DocScanX && python -c "from app.core.logging_config import setup_logging, get_system_logger; print('OK')"
```

Expected: `OK`

---

### Task 7: 写 app/services/log_service.py

**Files:**
- Write: `app/services/log_service.py`

- [ ] **Step 1: Write log_service.py**

Write to `E:/DocScanX/app/services/log_service.py`:

```python
"""日志查询服务。

从日志文件中读取、解析、过滤、分页返回日志条目。
"""
import os
import re
from typing import Optional

LOG_PATTERN = re.compile(
    r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] \[(\w+)\] \[([^\]]+)\] (.+)"
)


def _parse_log_line(line: str) -> Optional[dict]:
    """解析单行日志，返回 dict 或 None（非标准格式行）。"""
    m = LOG_PATTERN.match(line.strip())
    if not m:
        return None
    return {
        "time": m.group(1),
        "level": m.group(2),
        "name": m.group(3),
        "message": m.group(4),
    }


def query_logs(
    filename: str,
    log_dir: str = "./logs",
    page: int = 1,
    page_size: int = 20,
    level: Optional[str] = None,
    name: Optional[str] = None,
    search: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
) -> dict:
    """分页查询日志文件。

    Args:
        filename: 日志文件名（不含路径），如 "system.log"
        log_dir: 日志目录
        page: 页码（从 1 开始）
        page_size: 每页条数
        level: 级别过滤（DEBUG/INFO/WARNING/ERROR）
        name: 日志名称过滤（如 "system", "task", "audit"）
        search: 关键词搜索
        start_time: 起始时间（字符串比较）
        end_time: 结束时间（字符串比较）

    Returns:
        {"items": [...], "total": int, "page": int, "page_size": int}
    """
    filepath = os.path.join(log_dir, filename)
    if not os.path.isfile(filepath):
        return {"items": [], "total": 0, "page": page, "page_size": page_size}

    # 读取全部行并解析（日志文件通常不大，全量读入内存）
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    entries = []
    for line in lines:
        entry = _parse_log_line(line)
        if entry is None:
            continue
        # 过滤
        if level and entry["level"].upper() != level.upper():
            continue
        if name and entry["name"] != name:
            continue
        if start_time and entry["time"] < start_time:
            continue
        if end_time and entry["time"] > end_time:
            continue
        if search and search.lower() not in entry["message"].lower():
            continue
        entries.append(entry)

    # 倒序（最新在前）
    entries.reverse()

    total = len(entries)
    start = (page - 1) * page_size
    end = start + page_size
    items = entries[start:end]

    return {"items": items, "total": total, "page": page, "page_size": page_size}


def get_available_logs(log_dir: str = "./logs") -> list:
    """返回日志目录下可查询的日志文件列表。"""
    if not os.path.isdir(log_dir):
        return []
    return sorted([f for f in os.listdir(log_dir) if f.endswith(".log")])
```

---

### Task 8: 写 app/api/router.py

**Files:**
- Write: `app/api/router.py`

- [ ] **Step 1: Write router.py**

Write to `E:/DocScanX/app/api/router.py`:

```python
"""API 路由注册。"""
from fastapi import APIRouter

from app.api.config_api import router as config_router
from app.api.log_api import router as log_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(config_router, tags=["config"])
api_router.include_router(log_router, tags=["logs"])
```

---

### Task 9: 写 app/api/config_api.py

**Files:**
- Write: `app/api/config_api.py`

- [ ] **Step 1: Write config_api.py**

Write to `E:/DocScanX/app/api/config_api.py`:

```python
"""配置相关 API 端点。"""
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request

from app.core.config import (
    _namespace_to_dict,
    _deep_merge,
    config,
    load_default_config,
    save_config,
)
from app.core.logging_config import get_audit_logger, get_system_logger

router = APIRouter()


@router.get("/health")
async def health():
    """健康检查。"""
    return {
        "code": 0,
        "data": {"status": "ok", "timestamp": datetime.now().isoformat()},
        "message": "ok",
    }


@router.get("/config")
async def get_config():
    """获取当前完整配置。"""
    return {
        "code": 0,
        "data": _namespace_to_dict(config) if config else {},
        "message": "ok",
    }


@router.put("/config")
async def update_config(request: Request):
    """更新配置（内存，不持久化）。"""
    body = await request.json()
    if not body or not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="请求体必须为 JSON 对象")

    try:
        _deep_merge(config, body)
        get_audit_logger().info(f"配置变更: {list(body.keys())}")
        return {"code": 0, "data": _namespace_to_dict(config), "message": "配置已更新（内存）"}
    except Exception as e:
        get_system_logger().error(f"配置更新失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/config/defaults")
async def get_default_config():
    """获取出厂默认配置。"""
    try:
        defaults = load_default_config()
        return {"code": 0, "data": _namespace_to_dict(defaults), "message": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

### Task 10: 写 app/api/log_api.py

**Files:**
- Write: `app/api/log_api.py`

- [ ] **Step 1: Write log_api.py**

Write to `E:/DocScanX/app/api/log_api.py`:

```python
"""日志查询 API 端点。"""
from fastapi import APIRouter, Query

from app.services.log_service import get_available_logs, query_logs

router = APIRouter()


@router.get("/logs/files")
async def list_log_files():
    """获取可用日志文件列表。"""
    files = get_available_logs()
    return {"code": 0, "data": files, "message": "ok"}


@router.get("/logs")
async def get_logs(
    file: str = Query("system.log", description="日志文件名"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    level: str = Query(None, description="级别过滤: DEBUG/INFO/WARNING/ERROR"),
    name: str = Query(None, description="日志名称过滤: system/task/audit"),
    search: str = Query(None, description="关键词搜索"),
    start_time: str = Query(None, description="起始时间"),
    end_time: str = Query(None, description="结束时间"),
):
    """分页查询日志。"""
    result = query_logs(
        filename=file,
        page=page,
        page_size=page_size,
        level=level,
        name=name,
        search=search,
        start_time=start_time,
        end_time=end_time,
    )
    return {"code": 0, "data": result, "message": "ok"}
```

---

### Task 11: 写 frontend/index.html（占位页）

**Files:**
- Write: `frontend/index.html`

- [ ] **Step 1: Write index.html placeholder**

Write to `E:/DocScanX/frontend/index.html`:

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DocScanX</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <div id="app">
        <h1>DocScanX</h1>
        <p>文档敏感信息扫描系统 — 平台骨架已就绪</p>
        <p>Phase 2 将在此构建完整前端界面</p>
    </div>
    <script src="/static/js/app.js"></script>
</body>
</html>
```

---

### Task 12: 写 frontend/css/style.css（占位样式）

**Files:**
- Write: `frontend/css/style.css`

- [ ] **Step 1: Write style.css placeholder**

Write to `E:/DocScanX/frontend/css/style.css`:

```css
/* DocScanX Styles — Phase 2 填充 */
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    margin: 0;
    padding: 40px;
    background: #f5f5f5;
    color: #333;
}
h1 { margin-bottom: 8px; }
```

---

### Task 13: 写 main.py

**Files:**
- Write: `main.py`

- [ ] **Step 1: Write main.py**

Write to `E:/DocScanX/main.py`:

```python
"""DocScanX 入口 — 启动 Web 服务。"""
import os
import sys

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import init_config
from app.core.logging_config import get_system_logger, setup_logging


def create_app() -> FastAPI:
    """创建 FastAPI 应用。"""
    app = FastAPI(title="DocScanX", version="1.0.0", docs_url=None, redoc_url=None)

    # 注册 API 路由
    app.include_router(api_router)

    # 挂载前端静态文件
    frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    async def index():
        """返回首页。"""
        from fastapi.responses import FileResponse
        return FileResponse(os.path.join(frontend_dir, "index.html"))

    return app


def main():
    """启动入口。"""
    # 1. 加载配置
    cfg = init_config()
    if cfg is None:
        print("[ERROR] 配置加载失败，无法启动")
        sys.exit(1)

    # 2. 初始化日志
    log_dir = getattr(cfg.path, "log_dir", "./logs")
    log_level = getattr(cfg.log, "level", "INFO")
    log_max_size = getattr(cfg.log, "max_size_mb", 10)

    setup_logging(log_dir=log_dir, max_size_mb=log_max_size, level=log_level)
    system_log = get_system_logger()

    # 3. 检查模型目录
    model_dir = getattr(cfg.path, "model_dir", "./models")
    if not os.path.isdir(model_dir) or not os.listdir(model_dir):
        system_log.warning(f"模型目录 {model_dir} 为空或不存在，请在 Phase 2 下载模型")

    # 4. 启动
    system_log.info(f"DocScanX 启动中... 访问 http://localhost:8080")
    uvicorn.run(create_app(), host="0.0.0.0", port=8080, log_level="info")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify app can import without errors**

```bash
cd E:/DocScanX && python -c "from main import create_app; app = create_app(); print('App created:', app.title)"
```

Expected: `App created: DocScanX`

---

### Task 14: 启动并验证

**Files:** None (verification only)

- [ ] **Step 1: Start the server in background**

```bash
cd E:/DocScanX && python main.py &
sleep 3
```

Expected: Server starts without error, logging shows "DocScanX 启动中..."

- [ ] **Step 2: Test GET /api/v1/health**

```bash
curl -s http://localhost:8080/api/v1/health | python -m json.tool
```

Expected:
```json
{
    "code": 0,
    "data": {
        "status": "ok",
        "timestamp": "..."
    },
    "message": "ok"
}
```

- [ ] **Step 3: Test GET /api/v1/config**

```bash
curl -s http://localhost:8080/api/v1/config | python -c "import sys,json; d=json.load(sys.stdin); assert d['code']==0; assert d['data']['inference']['confidence_threshold']==0.65; print('PASS')"
```

Expected: `PASS`

- [ ] **Step 4: Test PUT /api/v1/config**

```bash
curl -s -X PUT http://localhost:8080/api/v1/config -H "Content-Type: application/json" -d '{"inference": {"confidence_threshold": 0.85}}' | python -c "import sys,json; d=json.load(sys.stdin); assert d['data']['inference']['confidence_threshold']==0.85; print('PASS')"
```

Expected: `PASS`

- [ ] **Step 5: Verify runtime change not persisted**

Restart and check value reverts:
```bash
# Kill the server
kill $(lsof -t -i:8080) 2>/dev/null || true
sleep 1
# Restart
cd E:/DocScanX && python main.py &
sleep 3
# Check config — should be back to 0.65
curl -s http://localhost:8080/api/v1/config | python -c "import sys,json; d=json.load(sys.stdin); assert d['data']['inference']['confidence_threshold']==0.65; print('PASS: value reverted')"
```

Expected: `PASS: value reverted`

- [ ] **Step 6: Test GET /api/v1/config/defaults**

```bash
curl -s http://localhost:8080/api/v1/config/defaults | python -c "import sys,json; d=json.load(sys.stdin); assert d['code']==0; print('PASS')"
```

Expected: `PASS`

- [ ] **Step 7: Test GET / (index page)**

```bash
curl -s http://localhost:8080/ | head -1
```

Expected: `<!DOCTYPE html>`

- [ ] **Step 8: Verify log file created**

```bash
ls -la E:/DocScanX/logs/system.log
```

Expected: File exists with content.

- [ ] **Step 9: Test GET /api/v1/logs**

```bash
curl -s http://localhost:8080/api/v1/logs | python -c "import sys,json; d=json.load(sys.stdin); assert d['code']==0; assert d['data']['total']>0; print('PASS:', d['data']['total'], 'entries')"
```

Expected: `PASS: N entries` (N >= 1)

- [ ] **Step 10: Stop the server**

```bash
kill $(lsof -t -i:8080) 2>/dev/null || true
```

---

### Task 15: Git init and commit

- [ ] **Step 1: Initialize git repo**

```bash
cd E:/DocScanX && git init
```

- [ ] **Step 2: Create .gitignore**

```bash
cat > E:/DocScanX/.gitignore << 'EOF'
__pycache__/
*.pyc
*.pyo
.env
output/*
!output/.gitkeep
logs/*
!logs/.gitkeep
temp/*
!temp/.gitkeep
models/*
!models/.gitkeep
*.egg-info/
dist/
build/
.vscode/
.idea/
EOF
```

- [ ] **Step 3: Stage and commit**

```bash
cd E:/DocScanX && git add -A && git commit -m "$(cat <<'EOF'
feat: Phase 1 platform scaffold

- Directory structure with all module placeholders
- YAML configuration system with SimpleNamespace access
- Structured logging (system/task/audit) with rotation
- FastAPI server with config and log API endpoints
- Frontend placeholder page
EOF
)"
```

- [ ] **Step 4: Verify clean git status**

```bash
cd E:/DocScanX && git status
```

Expected: `nothing to commit, working tree clean`

