# DocScanX — 文档敏感信息扫描系统

> **以人为本的个人信息保护合规工具**  
> 纯离线、CPU 推理、内网部署，零数据外传风险

---

## 目录

- [概述](#概述)
- [核心功能](#核心功能)
- [架构](#架构)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [打包部署](#打包部署)
- [输出报告](#输出报告)
- [项目路线图](#项目路线图)
- [技术栈](#技术栈)
- [许可](#许可)

---

## 概述

**DocScanX** 是一个面向企业的文档敏感信息扫描系统，帮助组织履行《个人信息保护法》合规义务。系统批量扫描本地目录（或远程文件服务器）下的办公文档，自动识别并提取 10+ 类个人敏感信息，跨文件关联同人数据，生成结构化脱敏报告。

### 适用场景

- 企业内部文档合规自查
- 个人信息盘点与风险排查
- 数据出境前的敏感信息检查
- 存量文件中的个人隐私识别与脱敏

---

## 核心功能

| 功能 | 说明 |
|------|------|
| 📁 **批量扫描** | 支持千级文件批量处理，覆盖 Word、Excel、PPT、PDF、TXT、图片等常见格式 |
| 🔍 **敏感信息提取** | 基于 UIE 信息抽取模型 + 正则规则引擎，精准提取身份证号、手机号、银行卡号、地址等 12+ 类敏感字段 |
| 👤 **跨文件关联** | 同一自然人在不同文档中自动识别并关联聚合，形成「数据主体」画像 |
| 🛡️ **合规脱敏** | 输出前对敏感字段自动脱敏（掩码模式），支持自定义脱敏规则 |
| ⚖️ **风险评分** | 基于敏感信息数量与类型的综合风险评分，快速定位高风险文件/人员 |
| 📊 **多格式报告** | 支持 HTML（可视化）、JSON（程序化）、Excel（统计）、CSV（明细）四种报告格式 |
| 🌐 **远程扫描** （二期） | 支持 FTP / SFTP / SMB / WebDAV 远程文件服务器扫描 |
| 🔌 **纯离线运行** | 一期完全离线，CPU 推理，无 GPU 依赖，无数据外传风险 |

### 支持的敏感信息类型

身份证号、手机号、银行卡号、护照号、驾驶证号、车牌号、电子邮件、IP 地址、姓名、地址、日期、金额、组织机构等 —— 均可通过配置文件启用/禁用并自定义正则规则。

---

## 架构

```
main.py            — FastAPI 应用入口（Web 服务）
│
├── app/
│   ├── api/       — REST API 路由（扫描、配置、报告、日志、数据主体）
│   ├── engine/    — 核心引擎
│   │   ├── file_parser.py   — 文件解析（DOCX/XLSX/PPTX/PDF/TXT/图片）
│   │   ├── ocr.py           — OCR 文字识别（RapidOCR ONNX）
│   │   ├── uie_engine.py    — UIE 信息抽取（Paddle/PyTorch）
│   │   ├── masking.py       — 脱敏处理
│   │   ├── risk.py          — 风险评分
│   │   ├── scanner.py       — 扫描任务编排
│   │   ├── pipeline.py      — 处理管道
│   │   ├── report.py        — 报告生成
│   │   └── validator.py     — 数据验证
│   ├── core/      — 配置管理与日志
│   ├── services/  — 业务服务层
│   ├── utils/     — 工具函数
│   └── web/       — 前端 SPA（静态页面 + Jinja2 模板）
│
├── models/        — 离线 AI 模型
│   ├── ocr/       — RapidOCR ONNX（文字检测/识别/分类）
│   └── uie/       — UIE 信息抽取（PaddlePaddle / PyTorch 两种格式）
│
├── config.yaml    — 运行时配置
├── output/        — 扫描结果输出目录
└── build_exe.py   — 单文件打包脚本
```

### 处理流程

```
文件 → 格式解析 → OCR（图片/扫描件） → UIE 信息抽取 → 规则补充 → 跨文件关联
  → 脱敏 → 风险评分 → 多格式报告输出
```

---

## 快速开始

### 环境要求

- **操作系统**：Windows 10/11 x64 或 Linux（Ubuntu 20.04+ / CentOS 7+）
- **Python**：3.10+
- **硬件**：CPU 推理（无需 GPU），建议 8GB+ 内存

### 安装

```bash
# 1. 克隆仓库
git clone https://github.com/Kokxi/DocScanX.git
cd docscanx

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate    # Linux
venv\Scripts\activate       # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. （可选）安装信息抽取模型依赖
# PaddlePaddle 方案（推荐）
pip install paddlenlp>=2.8 paddlepaddle>=3.0

# 或 PyTorch 方案（备选）
pip install torch transformers
```

### 模型准备

> ⚠️ 模型文件默认不纳入 Git 管理，克隆后 `models/` 目录为空，需要手动下载。

模型清单如下（参见 `models/README.md` 获取下载脚本和链接）：

| 模型 | 路径 | 大小 | 说明 |
|------|------|------|------|
| OCR 文字检测 | `models/ocr/ch_PP-OCRv3_det_infer.onnx` | 2.4 MB | 基于 RapidOCR ONNX |
| OCR 文字识别 | `models/ocr/ch_PP-OCRv3_rec_infer.onnx` | 10.7 MB | |
| OCR 方向分类 | `models/ocr/ch_ppocr_mobile_v2.0_cls_infer.onnx` | 0.6 MB | |
| UIE-tiny（推荐） | `models/uie/paddle/uie-tiny/` | 288 MB | 中等精度，生产推荐 |
| UIE-mini | `models/uie/paddle/uie-mini/` | 103 MB | 轻量版 |
| UIE-base | `models/uie/paddle/uie-base/` | 450 MB | 最高精度 |
| UIE PyTorch | `models/uie/pytorch/` | 391 MB | 回退方案 |

下载完成后，使用以下命令验证模型就绪：

```bash
# 检查 OCR 模型
ls models/ocr/*.onnx
# 检查 UIE 模型（以 uie-tiny 为例）
ls models/uie/paddle/uie-tiny/
```

### 启动

```bash
# 启动 Web 服务（默认 http://localhost:8090）
python main.py

# 或指定端口
python main.py --port 8080
```

### 使用

1. 浏览器打开 `http://localhost:8090`
2. 在「扫描任务」页面选择本地目录或上传文件
3. 点击「开始扫描」等待处理完成
4. 在「扫描报告」页面查看/导出扫描结果
5. 在「数据主体」页面查看跨文件关联的人员信息

---

## 配置说明

`config.yaml` 是运行时配置文件，主要配置项：

| 配置项 | 说明 |
|--------|------|
| `scan.directories` | 默认扫描目录列表 |
| `scan.extensions` | 支持的文件扩展名 |
| `sensitive_types` | 敏感信息类型定义（启用/禁用 + 正则规则） |
| `masking.rules` | 脱敏规则配置 |
| `risk_scoring` | 风险评分规则 |
| `ocr.enabled` | OCR 开关 |
| `uie.model` | UIE 模型选择（tiny/mini/base） |
| `server.host` / `server.port` | 服务监听地址 |
| `server.open_browser` | 启动时是否自动打开浏览器 |

> **提示**：UI 中进入「系统配置」页面可在线编辑敏感类型与风险评分规则。

---

## 打包部署

支持通过 PyInstaller 打包为单文件绿色部署：

```bash
python build_exe.py
```

打包后的可执行文件在 `dist/` 目录下，模型目录 `models/` 保持外置，方便离线分发和更新。

---

## 输出报告

扫描结果输出到 `output/` 目录下，每次扫描生成一个时间戳子目录：

```
output/
└── 20260602_123036/
    ├── meta.json      — 扫描元信息
    ├── report.html    — 可视化报告（浏览器打开）
    ├── report.json    — 结构化数据
    ├── report.xlsx    — Excel 表格
    └── report.csv     — CSV 明细
```

---

## 项目路线图

### 一期 ✅（已完成）

- [x] 平台骨架搭建（FastAPI + 前端 SPA）
- [x] 本地文件批量扫描
- [x] 多格式文件解析（DOCX/XLSX/PPTX/PDF/TXT/图片）
- [x] OCR 文字识别（RapidOCR ONNX）
- [x] UIE 信息抽取
- [x] 正则规则引擎（12 种敏感类型，可配置）
- [x] 跨文件关联聚合
- [x] 自动脱敏
- [x] 风险评分
- [x] 多格式报告输出
- [x] 远程 FTP 扫描
- [x] 敏感类型/规则在线配置
- [x] 单文件 exe 打包

### 二期 🔜（规划中）

- [ ] 大模型对接（非文本文件深度识别）
- [ ] 扩展远程协议（SFTP / SMB / WebDAV）
- [ ] 增量扫描
- [ ] SQLite 持久化
- [ ] 数据加密存储（AES-256-GCM）

---

## 技术栈

| 类别 | 技术 |
|------|------|
| 后端框架 | Python 3.10+ / FastAPI / Uvicorn |
| 前端 | HTML + CSS + JavaScript（SPA 单页应用） |
| OCR | RapidOCR ONNX（PaddleOCR 模型） |
| 信息抽取 | UIE（PaddleNLP / PyTorch） |
| 文件解析 | python-docx / openpyxl / python-pptx / pdfplumber / PyMuPDF |
| 配置管理 | YAML |
| 打包 | PyInstaller |

---

## 许可

本项目仅供内部合规使用。模型文件（OCR / UIE）遵循其各自的开源许可协议。
