"""DocScanX 打包脚本。

将项目打包为单文件 EXE，模型目录保持外置以便离线分发。
用法: python build_exe.py
"""
import os
import sys
import shutil
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(PROJECT_ROOT, "dist")
BUILD_DIR = os.path.join(PROJECT_ROOT, "build_tmp")


def check_pyinstaller():
    try:
        import PyInstaller
        return True
    except ImportError:
        return False


def install_pyinstaller():
    print("[INFO] 安装 PyInstaller...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller>=6.0"])


def clean():
    for d in [BUILD_DIR]:
        if os.path.isdir(d):
            shutil.rmtree(d, ignore_errors=True)
    for f in glob_files(PROJECT_ROOT, "*.spec"):
        path = os.path.join(PROJECT_ROOT, f)
        if "DocScanX" in f:
            os.remove(path)


def glob_files(root, pattern):
    import glob
    return [os.path.relpath(p, root) for p in glob.glob(os.path.join(root, pattern))]


def build():
    print("[INFO] 开始构建 DocScanX...")

    # 确保输出目录
    os.makedirs(DIST_DIR, exist_ok=True)

    # 收集数据目录
    datas = []
    # 模板文件
    templates_dir = os.path.join(PROJECT_ROOT, "app", "web", "templates")
    datas.append((templates_dir, "app/web/templates"))
    # 静态文件
    static_dir = os.path.join(PROJECT_ROOT, "app", "web", "static")
    datas.append((static_dir, "app/web/static"))
    # 默认配置
    default_config = os.path.join(PROJECT_ROOT, "config.default.yaml")
    datas.append((default_config, "."))

    # 构建 datas 参数
    datas_args = []
    for src, dst in datas:
        datas_args.extend(["--add-data", f"{src}{os.pathsep}{dst}"])

    # 隐藏导入
    hidden_imports = [
        "jinja2", "jinja2.ext",
        "uvicorn.logging", "uvicorn.loops", "uvicorn.loops.auto",
        "uvicorn.protocols", "uvicorn.protocols.http", "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets", "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan", "uvicorn.lifespan.on",
        "starlette.templating",
        "openpyxl", "openpyxl.cell", "openpyxl.styles",
        "docx", "pptx", "pdfplumber",
        "chardet", "yaml",
    ]

    hi_args = []
    for hi in hidden_imports:
        hi_args.extend(["--hidden-import", hi])

    # 排除不需要的模块
    excludes = ["tkinter", "matplotlib", "numpy", "scipy", "pandas",
                "PIL", "cv2", "torch", "paddle", "paddlenlp"]
    exclude_args = []
    for e in excludes:
        exclude_args.extend(["--exclude-module", e])

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--console",
        "--name", "DocScanX",
        "--distpath", DIST_DIR,
        "--workpath", BUILD_DIR,
        "--specpath", PROJECT_ROOT,
        *datas_args,
        *hi_args,
        *exclude_args,
        "--clean",
        os.path.join(PROJECT_ROOT, "main.py"),
    ]

    print(f"[INFO] 执行: {' '.join(cmd)}")
    subprocess.check_call(cmd, cwd=PROJECT_ROOT)

    exe_path = os.path.join(DIST_DIR, "DocScanX.exe")
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print(f"[OK] 构建成功: {exe_path} ({size_mb:.1f} MB)")
    else:
        print("[ERROR] 构建失败，未找到输出文件")
        sys.exit(1)


def create_dist_package():
    """创建完整的分发包（EXE + models + config + 说明）。"""
    pkg_dir = os.path.join(DIST_DIR, "DocScanX")
    os.makedirs(pkg_dir, exist_ok=True)

    # 复制 EXE
    exe_src = os.path.join(DIST_DIR, "DocScanX.exe")
    if os.path.exists(exe_src):
        shutil.copy2(exe_src, pkg_dir)

    # 复制模型
    models_dir = os.path.join(PROJECT_ROOT, "models")
    models_dst = os.path.join(pkg_dir, "models")
    if os.path.isdir(models_dir):
        if os.path.isdir(models_dst):
            shutil.rmtree(models_dst, ignore_errors=True)
        shutil.copytree(models_dir, models_dst, ignore=shutil.ignore_patterns("*.pyc", "__pycache__"))

    # 复制默认配置
    shutil.copy2(os.path.join(PROJECT_ROOT, "config.default.yaml"),
                 os.path.join(pkg_dir, "config.default.yaml"))

    # 创建使用说明
    readme = """DocScanX — 文档敏感信息扫描系统

## 使用方法

1. 双击 DocScanX.exe 启动服务
2. 浏览器访问 http://localhost:8080
3. 在"设置"页面配置扫描路径和模型参数
4. 在"扫描任务"页面输入目标目录开始扫描
5. 在"报告"页面下载扫描报告

## 目录说明

- DocScanX.exe    主程序
- models/         离线模型文件（OCR + UIE）
- config.default.yaml  默认配置
- output/         扫描报告输出目录
- logs/           日志文件目录

## 注意事项

- 首次启动会自动从 config.default.yaml 生成 config.yaml
- 模型目录 (models/) 必须与 EXE 在同一目录
- 支持的文档格式: docx, xlsx, pptx, pdf, txt, csv, json, xml
- 扫描件 PDF 需要 OCR 模型支持
"""
    with open(os.path.join(pkg_dir, "README.txt"), "w", encoding="utf-8") as f:
        f.write(readme)

    # 打包 ZIP
    zip_path = os.path.join(DIST_DIR, "DocScanX")
    shutil.make_archive(zip_path, "zip", DIST_DIR, "DocScanX")
    print(f"[OK] 分发包: {zip_path}.zip")


if __name__ == "__main__":
    if not check_pyinstaller():
        install_pyinstaller()

    clean()
    build()
    create_dist_package()
    print("[DONE] DocScanX 打包完成")
