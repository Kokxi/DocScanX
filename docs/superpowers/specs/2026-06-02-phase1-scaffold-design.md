# DocScanX Phase 1 — 平台骨架设计

> 日期：2026-06-02 | 状态：已确认

## 目标

搭建项目脚手架、配置系统、日志系统、FastAPI 骨架，为 Phase 2 三条并行开发线提供基础。

## 产出清单

1. 完整目录结构（含空文件和占位模块）
2. `config.yaml` + `config.default.yaml` + 配置加载/验证/热更新模块
3. 结构化日志系统（system / task / audit 三类，滚動文件）
4. FastAPI Web 服务（3 个端点：health / config get / config put）
5. `requirements.txt`（仅 Phase 1 依赖）

## 目录结构

```
DocScanX/
├── main.py
├── config.yaml
├── config.default.yaml
├── requirements.txt
│
├── app/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── logging_config.py
│   ├── engine/
│   │   └── __init__.py
│   │   (其余 engine 模块 Phase 2 填充)
│   ├── scheduler/
│   │   └── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── config_api.py
│   │   ├── task_api.py        (Phase 2)
│   │   ├── result_api.py      (Phase 2)
│   │   └── log_api.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── model_checker.py   (Phase 2)
│   │   ├── resource_monitor.py (Phase 2)
│   │   └── log_service.py
│   └── utils/
│       ├── __init__.py
│       ├── file_utils.py
│       └── text_utils.py
│
├── frontend/
│   ├── index.html             (Phase 2 填充)
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── app.js
│       ├── api.js
│       ├── dashboard.js
│       ├── scan.js
│       ├── persons.js
│       ├── reports.js
│       ├── settings.js
│       └── logs.js
│
├── models/                    (空目录 + .gitkeep)
├── output/                    (空目录 + .gitkeep)
├── logs/                      (空目录 + .gitkeep)
├── temp/                      (空目录 + .gitkeep)
└── tests/                     (空目录 + .gitkeep)
```

## 配置系统

**文件**：`config.yaml` 按技术设计方案 §3.1 完整写入，二期段注释。`config.default.yaml` 为出厂值副本。

**`app/core/config.py`**：
- 启动加载 `config.yaml`，缺失则从 `config.default.yaml` 复制
- 必填项缺失 → 拒绝启动，打印错误
- 用 `SimpleNamespace` 递归构建嵌套属性访问
- PUT 接口修改内存副本，不持久化（除非明确调用"保存为默认"）
- 全局单例：`from app.core.config import config`

## 日志系统

**`app/core/logging_config.py`**：用标准库 `logging` + `RotatingFileHandler`：
- system 日志：`logs/system.log`，最大 10MB，保留 5 个备份
- task 日志：`logs/task.log`（Phase 2 由 task_manager 写入）
- audit 日志：`logs/audit.log`，单独 logger

**`app/services/log_service.py`**：提供日志查询接口（读取文件 + 解析 + 分页 + 过滤）。

## FastAPI 骨架

**`main.py`**：加载配置 → 初始化日志 → 检查模型目录（仅警告）→ uvicorn 启动 `0.0.0.0:8080`。

**端点**（Phase 1 实现）：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/health` | `{"status": "ok", "timestamp": "..."}` |
| GET | `/api/v1/config` | 返回当前完整配置 |
| PUT | `/api/v1/config` | 更新配置（内存），body 为部分或全部配置项 |
| GET | `/api/v1/config/defaults` | 返回默认配置 |

**API 契约**：所有响应格式 `{"code": 0, "data": ..., "message": "ok"}`，错误码约定 `0=成功, 400=参数错误, 500=内部错误`。

**静态文件**：`/` 指向 `frontend/index.html`（Phase 1 时 index.html 为占位空白页）。

## Phase 1 依赖

```
fastapi>=0.100.0
uvicorn[standard]>=0.22.0
pyyaml>=6.0
```

不含 PaddlePaddle、PaddleOCR、PaddleNLP 等 —— 这些是 Phase 2 的依赖。

## 不在 Scope

- 任何 ML 模型加载
- 文件扫描/解析
- 前端页面内容（仅占位）
- 数据库/持久化存储
- 二期大模型/远程文件功能

## 验证标准

1. `python main.py` 启动成功，访问 `http://localhost:8080` 看到空白页
2. `GET /api/v1/health` 返回 200
3. `GET /api/v1/config` 返回完整配置 JSON
4. `PUT /api/v1/config` 修改置信度阈值，再次 GET 验证已生效
5. 重启后配置恢复为文件值
6. `logs/` 目录下生成 system.log
