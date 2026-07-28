# DocScanX 离线模型

> ⚠️ **模型文件默认不纳入 Git 管理**（`.gitignore` 排除了 `models/*`），  
> 克隆仓库后需要手动下载模型才能运行。

---

## 模型清单

### OCR 引擎（RapidOCR ONNX）

| 文件 | 大小 | 用途 |
|------|------|------|
| `ocr/ch_PP-OCRv3_det_infer.onnx` | 2.4 MB | 文字检测 |
| `ocr/ch_PP-OCRv3_rec_infer.onnx` | 10.7 MB | 文字识别 |
| `ocr/ch_ppocr_mobile_v2.0_cls_infer.onnx` | 0.6 MB | 文字方向分类 |
| `ocr/rapidocr_config.yaml` | 1 KB | RapidOCR 配置参考 |

### UIE 信息抽取（PaddlePaddle 格式）

| 模型 | 大小 | 说明 |
|------|------|------|
| `uie/paddle/uie-tiny/` | ~288 MB | 中等精度，推荐生产使用 |
| `uie/paddle/uie-mini/` | ~103 MB | 轻量版，适合低资源环境 |
| `uie/paddle/uie-base/` | ~450 MB | 最高精度 |

### UIE 信息抽取（PyTorch 格式，备选）

| 模型 | 大小 | 说明 |
|------|------|------|
| `uie/pytorch/` | ~391 MB | 通过 `transformers` 加载，PaddlePaddle 不可用时的回退方案 |

---

## 下载方法

### 方法一：一键下载脚本（推荐）

项目提供了一键下载脚本，会自动下载所有模型并放置到正确位置。

#### Windows（`download_models.bat`）

将以下内容保存为 `download_models.bat` 并双击运行：

```batch
@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo === DocScanX 模型下载脚本 ===
echo.

:: ---------- Python 检查 ----------
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

:: ---------- 1. OCR 模型 ----------
echo [1/3] 下载 OCR 模型（RapidOCR ONNX）...
pip install rapidocr-onnxruntime -q
python -c "
import rapidocr_onnxruntime, os, shutil
src = os.path.join(os.path.dirname(rapidocr_onnxruntime.__file__), 'models')
dst = 'models/ocr'
os.makedirs(dst, exist_ok=True)
for f in os.listdir(src):
    shutil.copy2(os.path.join(src, f), os.path.join(dst, f))
print('OCR models copied to', dst)
"
if %errorlevel% neq 0 (
    echo [错误] OCR 模型下载失败
    pause
    exit /b 1
)
echo OK
echo.

:: ---------- 2. UIE Paddle 模型 ----------
echo [2/3] 下载 UIE 模型（PaddlePaddle 格式，约 800MB）...
pip install paddlenlp>=2.8 paddlepaddle>=3.0 -q
python -c "
from paddlenlp import Taskflow
import os, shutil

models = ['uie-tiny', 'uie-mini', 'uie-base']
cache_root = os.path.expanduser('~/.paddlenlp/taskflow/information_extraction')
dst_root = 'models/uie/paddle'

for m in models:
    print(f'  下载 {m}...')
    uie = Taskflow('information_extraction', model=m, schema=['姓名'])
    del uie
    # 复制到目标目录
    src = os.path.join(cache_root, m)
    dst = os.path.join(dst_root, m)
    if os.path.exists(src):
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        print(f'  已复制到 {dst}')
"
if %errorlevel% neq 0 (
    echo [警告] UIE Paddle 模型下载失败，请检查网络或改用 PyTorch 方案
)
echo OK
echo.

:: ---------- 3. UIE PyTorch 模型 ----------
echo [3/3] 下载 UIE 模型（PyTorch 格式，约 400MB）...
pip install modelscope -q
python -c "
from modelscope.hub.snapshot_download import snapshot_download
import os, shutil

model_dir = snapshot_download('iic/nlp_structbert_siamese-uie_chinese-base', cache_dir='models/uie/pytorch')
print(f'PyTorch 模型已下载到 {model_dir}')
"
if %errorlevel% neq 0 (
    echo [警告] PyTorch 模型下载失败
)
echo OK
echo.

echo === 全部完成！===
echo 现在可以运行 python main.py 启动 DocScanX 了
pause
```

#### Linux / macOS（`download_models.sh`）

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "=== DocScanX 模型下载脚本 ==="

# 1. OCR 模型
echo "[1/3] 下载 OCR 模型（RapidOCR ONNX）..."
pip install rapidocr-onnxruntime -q
python3 -c "
import rapidocr_onnxruntime, os, shutil
src = os.path.join(os.path.dirname(rapidocr_onnxruntime.__file__), 'models')
dst = 'models/ocr'
os.makedirs(dst, exist_ok=True)
for f in os.listdir(src):
    shutil.copy2(os.path.join(src, f), os.path.join(dst, f))
print('OCR models copied to', dst)
"
echo "OK"

# 2. UIE Paddle 模型
echo "[2/3] 下载 UIE 模型（PaddlePaddle 格式）..."
pip install paddlenlp>=2.8 paddlepaddle>=3.0 -q
python3 -c "
from paddlenlp import Taskflow
import os, shutil

models = ['uie-tiny', 'uie-mini', 'uie-base']
cache_root = os.path.expanduser('~/.paddlenlp/taskflow/information_extraction')
dst_root = 'models/uie/paddle'

for m in models:
    print(f'  下载 {m}...')
    uie = Taskflow('information_extraction', model=m, schema=['姓名'])
    del uie
    src = os.path.join(cache_root, m)
    dst = os.path.join(dst_root, m)
    if os.path.exists(src):
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        print(f'  已复制到 {dst}')
"
echo "OK"

# 3. UIE PyTorch 模型
echo "[3/3] 下载 UIE 模型（PyTorch 格式）..."
pip install modelscope -q
python3 -c "
from modelscope.hub.snapshot_download import snapshot_download
snapshot_download('iic/nlp_structbert_siamese-uie_chinese-base', cache_dir='models/uie/pytorch')
print('PyTorch 模型下载完成')
"
echo "OK"

echo "=== 全部完成！==="
```

---

### 方法二：逐一下载（只需必要模型）

#### OCR 模型

**方式 A：从 pip 包获取（推荐）**

```bash
pip install rapidocr-onnxruntime
# 找到模型文件位置
python -c "import rapidocr_onnxruntime; import os; print(os.path.join(os.path.dirname(rapidocr_onnxruntime.__file__), 'models'))"
# 将目录下的文件复制到 models/ocr/
```

**方式 B：直接下载 ONNX 文件**

| 文件 | 下载地址 |
|------|---------|
| 检测模型 | https://github.com/RapidAI/RapidOCR/releases/download/v1.0.0/ch_PP-OCRv3_det_infer.onnx |
| 识别模型 | https://github.com/RapidAI/RapidOCR/releases/download/v1.0.0/ch_PP-OCRv3_rec_infer.onnx |
| 分类模型 | https://github.com/RapidAI/RapidOCR/releases/download/v1.0.0/ch_ppocr_mobile_v2.0_cls_infer.onnx |
| 配置文件 | https://github.com/RapidAI/RapidOCR/raw/main/python/rapidocr_onnxruntime/config.yaml |

#### UIE 模型 — PaddlePaddle 格式

```bash
pip install paddlenlp>=2.8 paddlepaddle>=3.0

# 触发下载（以 uie-tiny 为例）
python -c "
from paddlenlp import Taskflow
uie = Taskflow('information_extraction', model='uie-tiny', schema=['姓名'])
del uie
"

# 模型缓存位置：~/.paddlenlp/taskflow/information_extraction/uie-tiny/
# 复制到 models/uie/paddle/uie-tiny/
```

包含 `uie-tiny`（288 MB）、`uie-mini`（103 MB）、`uie-base`（450 MB）三种规格，按需下载。

#### UIE 模型 — PyTorch 格式（备选）

来源：[ModelScope — nlp_structbert_siamese-uie_chinese-base](https://www.modelscope.cn/models/iic/nlp_structbert_siamese-uie_chinese-base)

```bash
pip install modelscope
python -c "
from modelscope.hub.snapshot_download import snapshot_download
snapshot_download('iic/nlp_structbert_siamese-uie_chinese-base', cache_dir='models/uie/pytorch')
"
```

---

## 模型目录结构（下载后）

```
models/
├── ocr/
│   ├── ch_PP-OCRv3_det_infer.onnx
│   ├── ch_PP-OCRv3_rec_infer.onnx
│   ├── ch_ppocr_mobile_v2.0_cls_infer.onnx
│   └── rapidocr_config.yaml
├── uie/
│   ├── paddle/
│   │   ├── uie-tiny/
│   │   │   ├── config.json
│   │   │   ├── model_state.pdparams
│   │   │   ├── special_tokens_map.json
│   │   │   ├── tokenizer_config.json
│   │   │   └── vocab.txt
│   │   ├── uie-mini/   (同上结构)
│   │   └── uie-base/   (同上结构)
│   └── pytorch/
│       ├── config.json
│       ├── pytorch_model.bin
│       └── vocab.txt
├── .gitkeep
└── README.md
```

---

## 注意事项

- **磁盘空间**：全量下载约需 1.5 GB 空间
- **网络要求**：下载过程需要联网，模型下载后可离线使用
- **最低依赖**：仅需 OCR + 任一 UIE 模型即可运行
  - 推荐组合：OCR（3 个 ONNX）+ UIE-tiny（Paddle）
- **模型文件已排除 Git**：若需自行分发模型，请通过其他渠道（网盘、内部共享等）
