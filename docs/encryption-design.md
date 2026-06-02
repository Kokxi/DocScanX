# DocScanX 数据加密方案设计

## 架构总览

```
首次启动                        后续启动
────────                        ────────
检测 data/.key_hash 不存在      检测 data/.key_hash 存在
        │                              │
        ▼                              ▼
前端 → 初始化密码页              前端 → 解锁页
        │                              │
        ▼                              ▼
POST /api/auth/setup           POST /api/auth/unlock
  {password}                     {password}
        │                              │
        ▼                              ▼
PBKDF2-SHA256                 PBKDF2-SHA256
  → key (32 bytes)              → key (32 bytes)
  → key_hash (SHA256)           → SHA256(key) vs key_hash
  → 写入 data/.key_hash          → 匹配: key 驻留 app.state
        │                         → 不匹配: 403 "密码错误"
        ▼
key 驻留 app.state
```

**核心原则：** 密钥只在进程内存中，不入库、不落盘、不写日志。进程重启必须重新解锁。

---

## 密码学方案

| 环节 | 算法 | 说明 |
|------|------|------|
| 密钥派生 | PBKDF2-SHA256, 600K 迭代 | 主密码 → 32-byte key |
| 密钥验证 | SHA256(key) | 存 hash，不存 key |
| 数据加密 | AES-256-GCM | 每条记录独立 IV + auth tag |
| 依赖 | `cryptography` | pip install cryptography |

### 加密文件格式

```
[16 bytes IV] [ciphertext + auth tag (GCM)]
```

每个 report.json 写入时生成随机 IV，密文 = AES-GCM(明文, key, IV)，输出 IV + 密文拼接。

---

## 数据存储

### 新增文件

```
data/
  .key_hash       ← 64 char hex: SHA256(derived_key)
  .hint           ← 可选，密码提示（明文）
output/
  <report_id>/
    report.json.enc   ← 加密后的 JSON（替代原 report.json）
    report.csv.enc
    report.xlsx.enc
    meta.json.enc
```

### 不改动

- `config.yaml` — 不加密，不含敏感数据
- `logs/` — 日志本身不含敏感数据（脱敏后写入）

---

## API 设计

### GET /api/auth/status

返回当前加密状态，前端据此决定显示哪一页。

```json
// 未初始化
{"code": 0, "data": {"initialized": false, "unlocked": false, "has_hint": false}}

// 已初始化，已锁定
{"code": 0, "data": {"initialized": true, "unlocked": false, "has_hint": true, "hint": "公司开机密码"}}

// 已初始化，已解锁
{"code": 0, "data": {"initialized": true, "unlocked": true}}
```

### POST /api/auth/setup

首次设置主密码。

```
Request:  {"password": "myp@ssw0rd", "hint": "公司开机密码"}
Response: {"code": 0, "data": {"message": "设置成功"}}
Error:    {"code": 1, "message": "密码不能少于8位"}
          {"code": 1, "message": "密码已设置，如需修改请使用修改密码功能"}
```

### POST /api/auth/unlock

每次启动后解锁。

```
Request:  {"password": "myp@ssw0rd"}
Response: {"code": 0, "data": {"message": "解锁成功"}}
Error:    {"code": 1, "message": "密码错误"}
```

### POST /api/auth/change-password

修改主密码（需先解锁）。

```
Request:  {"old_password": "myp@ssw0rd", "new_password": "newp@ssw0rd", "new_hint": "新提示"}
Response: {"code": 0, "data": {"message": "密码修改成功"}}
Error:    {"code": 1, "message": "原密码错误"}
```

### POST /api/auth/check-key

后端中间件或前端定时检查密钥是否仍有效。

```
Response: {"code": 0, "data": {"ok": true}}
```

---

## 中间件设计

`app/api/auth_middleware.py` — 对所有 `/api/v1/*` 请求（除 `/api/auth/*` 外）检查 `app.state.encryption_key is not None`，未解锁返回：

```json
{"code": 403, "message": "系统已锁定，请先解锁"}
```

启动时 `app.state.encryption_key = None`，解锁成功后设置。

---

## 前端页面

### 1. 初始化页

```
┌──────────────────────────────────────┐
│                                      │
│     🔒 DocScanX                      │
│     首次使用，请设置主密码              │
│                                      │
│     ┌──────────────────────────┐     │
│     │ 主密码（至少8位）          │     │
│     │ [___________________]    │     │
│     │                          │     │
│     │ 确认密码                  │     │
│     │ [___________________]    │     │
│     │                          │     │
│     │ 密码提示（可选，帮助记忆）  │     │
│     │ [___________________]    │     │
│     └──────────────────────────┘     │
│                                      │
│     ⚠️ 请务必记住此密码               │
│     密码丢失后，数据无法恢复           │
│                                      │
│     [ 确认设置 ]                      │
│                                      │
└──────────────────────────────────────┘
```

### 2. 解锁页

```
┌──────────────────────────────────────┐
│                                      │
│     🔒 DocScanX 已锁定               │
│                                      │
│     ┌──────────────────────────┐     │
│     │ 主密码 [_______________] │     │
│     │                          │     │
│     │ 💡 提示：公司开机密码      │     │  ← 如果设置了 hint
│     └──────────────────────────┘     │
│                                      │
│     [ 解锁 ]                         │
│                                      │
│     ❌ 密码错误                       │  ← 错误时显示
│                                      │
└──────────────────────────────────────┘
```

### 3. 修改密码（系统配置页内）

```
系统配置
  ━━ 基本设置
  ━━ 风险评分规则
  ━━ 安全设置  ← 新增
       │
       ├── 修改主密码
       │   原密码    [___________]
       │   新密码    [___________]
       │   确认密码  [___________]
       │   密码提示  [___________]
       │   [ 确认修改 ]
       │
       └── 当前状态: 🔒 已解锁 / 🔓 已锁定
```

---

## 启动流程变更

```python
# main.py create_app() 中新增

app.state.encryption_key = None  # 初始未解锁

# 中间件：拦截所有 /api/v1/* 请求
# 排除 /api/auth/*，检查 key 是否存在
```

```python
# main.py main() 中新增

# 2. 初始化加密系统
from app.core.encryption import init_encryption
init_encryption(cfg)
```

---

## 改造范围

| 文件 | 操作 | 说明 |
|------|------|------|
| `app/core/encryption.py` | **新建** | PBKDF2、AES-GCM 加解密、hash 验证 |
| `app/api/auth_api.py` | **新建** | 4 个认证端点 |
| `app/api/auth_middleware.py` | **新建** | 未解锁拦截中间件 |
| `app/api/router.py` | 修改 | 注册 auth_router，添加中间件 |
| `main.py` | 修改 | 初始化加密系统 |
| `app/engine/report.py` | 修改 | save_report / list_reports 加解密 |
| `app/api/subject_api.py` | 修改 | _load_all_persons 解密读取 |
| `app/web/templates/spa.html` | 修改 | 添加 3 个新页面/状态 |
| `app/web/static/js/app.js` | 修改 | 认证状态管理与 API 调用 |
| `app/web/static/css/app.css` | 修改 | 新页面样式 |
| `requirements.txt` | 修改 | 新增 `cryptography` |

## 边界情况

- **忘记密码**：无恢复机制，与用户确认后删除 `data/.key_hash` 重置（数据全部丢失）
- **暴力破解防护**：PBKDF2 600K 迭代，单次验证耗时 ~200ms，天然限速
- **备份恢复**：备份时一同备份 `data/.key_hash`，恢复时用原密码可解
- **多实例**：不推荐，同一 `data/` 目录只应一个进程访问
- **密钥泄露**：仅存内存，进程崩溃不会泄露。服务器被攻破能 dump 内存则无法防御（本地工具可接受）
