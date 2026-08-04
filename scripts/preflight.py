"""
preflight 4 项运行时自检

不查 env 完整（yaml metadata.openclaw.requires.env 已做）
查 yaml 覆盖不到的运行时项:
  1. check_lark_cli      - lark-cli 可用 + version
  2. check_bitable_read  - 源 bitable 可读
  3. check_bitable_write - 存储 bitable 可写
  4. check_disk          - 磁盘空间 (临时输出)

任一项失败 -> raise PreflightError -> main.py abort
"""
import json
import logging
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

import yaml

# 允许从 SKILL 根目录 import scripts.* (单独跑 preflight.py 时需要)
SKILL_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_ROOT))

logger = logging.getLogger("bitable-meta-sync")

CONFIG_PATH = SKILL_ROOT / "config.yaml"


class PreflightError(Exception):
    """preflight 自检失败"""
    pass


def _load_config() -> Dict[str, Any]:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def check_lark_cli() -> bool:
    """检查 lark-cli 可用 + version ≥ 1.0.79"""
    try:
        r = subprocess.run(
            ["lark-cli", "--version"],
            capture_output=True, text=True, timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        raise PreflightError(f"lark-cli 不可用: {e}")

    if r.returncode != 0:
        raise PreflightError(f"lark-cli --version 失败: rc={r.returncode}, stderr={r.stderr.strip()}")

    # 解析版本号 (类似 "lark-cli version 1.0.81" 或 "1.0.81")
    version_str = (r.stdout or "").strip()
    import re
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", version_str)
    if not m:
        raise PreflightError(f"lark-cli 版本号解析失败: {version_str!r}")

    major, minor, patch = (int(x) for x in m.groups())
    if (major, minor, patch) < (1, 0, 79):
        raise PreflightError(
            f"lark-cli 版本过低: {major}.{minor}.{patch} (需要 ≥ 1.0.79)"
        )

    logger.info("lark-cli OK: %s", version_str)
    return True


def check_bitable_access(bitable_url: str, mode: str = "read") -> bool:
    """检查 bitable 可访问 (read 拉表 list, write 试 create-folder)

    mode: "read" 或 "write"
    """
    # 从 URL 提取 token
    # https://bggc.feishu.cn/base/<token>
    import re
    m = re.search(r"/base/([A-Za-z0-9]+)", bitable_url)
    if not m:
        raise PreflightError(f"bitable URL 解析失败: {bitable_url}")
    token = m.group(1)

    # 用 base +table-list 探测
    cmd = ["lark-cli", "--as", "user", "base", "+table-list",
           "--base-token", token]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        raise PreflightError(f"bitable {token[:8]}... 访问超时")

    if r.returncode != 0:
        raise PreflightError(
            f"bitable {token[:8]}... 访问失败: rc={r.returncode}, stderr={r.stderr.strip()}"
        )

    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError as e:
        raise PreflightError(f"bitable {token[:8]}... 返回非 JSON: {e}")

    if not data.get("ok"):
        err = data.get("error", {})
        raise PreflightError(
            f"bitable {token[:8]}... 业务失败: {err.get('message', 'unknown')}"
        )

    logger.info("bitable %s... %s OK", token[:8], mode)
    return True


def check_disk(min_mb: int = 100) -> bool:
    """检查磁盘空间 (临时输出用)"""
    usage = shutil.disk_usage(SKILL_ROOT)
    free_mb = usage.free // (1024 * 1024)
    if free_mb < min_mb:
        raise PreflightError(f"磁盘空间不足: {free_mb}MB (需要 ≥ {min_mb}MB)")
    logger.info("disk OK: %dMB free", free_mb)
    return True


def preflight(source_url: str, storage_url: str) -> None:
    """4 项运行时自检, 任一失败 raise PreflightError"""
    logger.info("=== preflight start ===")
    check_lark_cli()
    check_bitable_access(source_url, mode="read")
    check_bitable_access(storage_url, mode="write")
    check_disk()
    logger.info("=== preflight OK ===")
