"""远程文件源扫描。支持 FTP 协议，下载→本地管线处理→清理。"""
import os
import ftplib
import logging
import shutil
import tempfile
from dataclasses import dataclass
from typing import Optional

from app.engine.pipeline import process_directory, PipelineResult

logger = logging.getLogger("system")


@dataclass
class RemoteSource:
    name: str
    protocol: str
    host: str
    port: int = 21
    username: str = ""
    password: str = ""
    base_path: str = "/"
    max_file_size_mb: float = 500
    connect_timeout: int = 30


class _FtpSession:
    """上下文管理器：连接/断开 FTP。"""

    def __init__(self, source: RemoteSource):
        self.source = source
        self.ftp = ftplib.FTP()

    def __enter__(self):
        self.ftp.connect(self.source.host, self.source.port,
                         timeout=self.source.connect_timeout)
        self.ftp.login(self.source.username or "anonymous",
                       self.source.password or "")
        return self.ftp

    def __exit__(self, *args):
        try:
            self.ftp.quit()
        except Exception:
            try:
                self.ftp.close()
            except Exception:
                pass


def connect_ftp(source: RemoteSource) -> _FtpSession:
    """返回 FTP 连接的上下文管理器。"""
    return _FtpSession(source)


def list_ftp_files(ftp, base_path: str) -> list:
    """递归列出 FTP 目录下所有文件。MLSD 优先，回退 NLST。"""
    files = []

    def _list_dir(path):
        items = []
        try:
            ftp.retrlines(f"MLSD {path}", items.append)
        except Exception:
            # 回退：仅列出文件名，无法获取大小
            for name in ftp.nlst(path):
                items.append(f"type=file;size=0; {name}")

        for item in items:
            parts = item.split("; ")
            name = parts[-1].strip()
            if name in (".", ".."):
                continue

            item_type = "file"
            size = 0
            for p in parts[:-1]:
                kv = p.split("=", 1)
                if len(kv) != 2:
                    continue
                k, v = kv[0].strip(), kv[1].strip()
                if k == "type":
                    item_type = v
                elif k == "size" or k == "sizd":
                    try:
                        size = int(v)
                    except ValueError:
                        pass

            full = f"{path.rstrip('/')}/{name}"
            if item_type == "dir":
                _list_dir(full)
            else:
                files.append({"path": full, "size": size})

    _list_dir(base_path)
    return files


def download_ftp_file(ftp, remote_path: str, local_dir: str) -> str:
    """下载单个文件到本地目录，返回本地路径。冲突时追加序号。"""
    name = os.path.basename(remote_path)
    dest = os.path.join(local_dir, name)

    base, ext = os.path.splitext(name)
    n = 1
    while os.path.exists(dest):
        dest = os.path.join(local_dir, f"{base}_{n}{ext}")
        n += 1

    with open(dest, "wb") as f:
        ftp.retrbinary(f"RETR {remote_path}", f.write)

    return dest


def scan_remote_source(source: RemoteSource,
                       ext_groups: Optional[dict] = None,
                       mask_enabled: bool = True) -> PipelineResult:
    """扫描远程 FTP 源：连接→查文件→下载→管线处理→清理临时目录。"""
    work_dir = tempfile.mkdtemp(prefix="docscanx_remote_")
    logger.info(f"远程扫描工作目录: {work_dir}")

    try:
        with connect_ftp(source) as ftp:
            all_files = list_ftp_files(ftp, source.base_path)
            logger.info(f"远程发现 {len(all_files)} 个文件")

            # 筛选扩展名
            from app.core import config as config_module
            cfg = config_module.config
            ext_map = getattr(cfg.scan, "file_extensions", {}) if cfg else {}
            supported = set()
            if ext_groups and ext_map:
                for grp, enabled in ext_groups.items():
                    if enabled and grp in ext_map:
                        supported.update(ext_map[grp])

            downloaded = 0
            for fi in all_files:
                ext = os.path.splitext(fi["path"])[1].lower()
                if supported and ext not in supported:
                    continue
                size_mb = fi["size"] / (1024 * 1024)
                if size_mb > source.max_file_size_mb:
                    logger.warning(f"跳过大文件: {fi['path']} ({size_mb:.1f}MB)")
                    continue
                try:
                    download_ftp_file(ftp, fi["path"], work_dir)
                    downloaded += 1
                except Exception as e:
                    logger.error(f"下载失败 [{fi['path']}]: {e}")

            logger.info(f"下载完成: {downloaded}/{len(all_files)} 文件")

        if downloaded == 0:
            return PipelineResult()

        return process_directory(
            dir_path=work_dir,
            include_subdir=True,
            extract_archive=False,
            ext_groups=ext_groups,
            mask_enabled=mask_enabled,
        )

    finally:
        try:
            shutil.rmtree(work_dir)
            logger.info(f"已清理临时目录: {work_dir}")
        except Exception as e:
            logger.warning(f"清理临时目录失败: {e}")
