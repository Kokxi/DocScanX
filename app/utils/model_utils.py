"""模型路径解析工具。

将配置中的相对路径解析为绝对路径，提供统一的模型文件定位接口。
"""
import os
from typing import Optional


def resolve_path(base_dir: str, rel_path: str) -> str:
    """将相对路径解析为绝对路径。已是绝对路径则直接返回。"""
    if os.path.isabs(rel_path):
        return os.path.normpath(rel_path)
    return os.path.normpath(os.path.join(base_dir, rel_path))


def get_ocr_model_dir(config) -> str:
    """获取 OCR ONNX 模型目录的绝对路径。"""
    from app.core import config as config_module
    c = config if config is not None else config_module.config
    base = os.getcwd()
    return resolve_path(base, c.path.ocr_onnx)


def get_uie_paddle_dir(config, version: Optional[str] = None) -> str:
    """获取 UIE PaddlePaddle 模型目录的绝对路径。

    Args:
        config: 配置对象，None 则使用全局配置
        version: 模型版本 (tiny/mini/base)，默认使用配置中的 version
    """
    from app.core import config as config_module
    c = config if config is not None else config_module.config
    if c is None:
        raise RuntimeError("配置未初始化")
    base = os.getcwd()
    ver = version or c.model.uie.version
    base_dir = resolve_path(base, c.path.uie_paddle)
    return os.path.join(base_dir, f"uie-{ver}")


def get_uie_torch_dir(config) -> str:
    """获取 UIE PyTorch 模型目录的绝对路径。"""
    from app.core import config as config_module
    c = config if config is not None else config_module.config
    base = os.getcwd()
    return resolve_path(base, c.path.uie_torch)


def verify_ocr_models(config=None) -> bool:
    """验证 OCR ONNX 模型文件是否完整。"""
    ocr_dir = get_ocr_model_dir(config)
    required = [
        "ch_PP-OCRv3_det_infer.onnx",
        "ch_PP-OCRv3_rec_infer.onnx",
        "ch_ppocr_mobile_v2.0_cls_infer.onnx",
    ]
    return all(os.path.exists(os.path.join(ocr_dir, f)) for f in required)


def verify_uie_models(config=None) -> dict:
    """验证各版本 UIE PaddlePaddle 模型是否存在。

    Returns:
        dict: {version: bool} 各版本是否完整
    """
    result = {}
    required = ["model_state.pdparams", "config.json", "vocab.txt", "tokenizer_config.json"]
    for ver in ["tiny", "mini", "base"]:
        ver_dir = get_uie_paddle_dir(config, ver)
        result[ver] = all(os.path.exists(os.path.join(ver_dir, f)) for f in required)
    return result
