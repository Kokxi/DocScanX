# DocScanX 离线模型目录

用于打包发布的预下载模型文件。模型在构建/安装时会被复制到运行时位置。

## 模型清单

### OCR 引擎（RapidOCR ONNX）

| 文件 | 大小 | 用途 |
|------|------|------|
| `ocr/ch_PP-OCRv3_det_infer.onnx` | 2.4 MB | 文字检测 |
| `ocr/ch_PP-OCRv3_rec_infer.onnx` | 10.7 MB | 文字识别 |
| `ocr/ch_ppocr_mobile_v2.0_cls_infer.onnx` | 0.6 MB | 文字方向分类 |
| `ocr/rapidocr_config.yaml` | 1 KB | RapidOCR 配置参考 |

依赖: `rapidocr-onnxruntime` (无需 PaddlePaddle)

### UIE 信息抽取（PaddlePaddle 格式）

| 模型 | 大小 | 说明 |
|------|------|------|
| `uie/paddle/uie-tiny/` | 288 MB | 中等精度，推荐生产使用 |
| `uie/paddle/uie-mini/` | 103 MB | 轻量版，适合低资源环境 |
| `uie/paddle/uie-base/` | 450 MB | 最高精度 |

依赖: `paddlenlp>=2.8`, `paddlepaddle>=3.0`

### UIE 信息抽取（PyTorch 格式，备选）

| 模型 | 大小 | 说明 |
|------|------|------|
| `uie/pytorch/` | 391 MB | 通过 `transformers` 加载，PaddlePaddle 不可用时的回退方案 |

依赖: `transformers`, `torch`

## 重新下载

如果模型文件缺失或损坏，运行：

```bash
# OCR 模型（RapidOCR 自动下载到 site-packages，复制到此处）
pip install rapidocr-onnxruntime
cp -r $(python -c "import rapidocr_onnxruntime; import os; print(os.path.join(os.path.dirname(rapidocr_onnxruntime.__file__), 'models'))")/* models/ocr/

# UIE PaddlePaddle 模型
python -c "
from paddlenlp import Taskflow
for m in ['uie-tiny', 'uie-mini', 'uie-base']:
    uie = Taskflow('information_extraction', model=m, schema=['姓名'])
    del uie
"
# 然后从 ~/.paddlenlp/taskflow/information_extraction/ 复制到 models/uie/paddle/

# UIE PyTorch 模型
pip install modelscope
python -c "
from modelscope.hub.snapshot_download import snapshot_download
snapshot_download('iic/nlp_structbert_siamese-uie_chinese-base', cache_dir='models/uie/pytorch')
"
```
