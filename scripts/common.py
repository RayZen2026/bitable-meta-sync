"""
共享工具

  - parse_bitable_url(url)  - 提取 app_token (base) from URL
  - parse_table_url(url)    - 提取 table_id from URL (含 ?table=)
  - run_lark_cli(args)      - subprocess 调 lark-cli + JSON 解析
  - setup_logger()          - 统一 logger
"""
import json
import logging
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SKILL_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_ROOT))

logger = logging.getLogger("bitable-meta-sync")


def setup_logger(level: str = "INFO") -> None:
    """统一 logger 设置 (main.py 入口调)"""
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def parse_bitable_url(url: str) -> str:
    """从 bitable URL 提取 app_token (base token)

    支持: https://bggc.feishu.cn/base/<token>?table=<table_id>
          https://xxx.feishu.cn/base/<token>
    """
    m = re.search(r"/base/([A-Za-z0-9]+)", url)
    if not m:
        raise ValueError(f"bitable URL 解析失败: {url}")
    return m.group(1)


def parse_table_id_from_url(url: str) -> Optional[str]:
    """从 URL 提取 table_id (?table=<id>), 缺省返回 None"""
    m = re.search(r"[?&]table=([A-Za-z0-9]+)", url)
    return m.group(1) if m else None


def run_lark_cli(
    args: List[str],
    timeout: int = 60,
    as_user: bool = True,
) -> Dict[str, Any]:
    """subprocess 调 lark-cli + 解析 JSON 输出

    返回: {"ok": bool, "data": ..., "error": ..., "raw": ...}
    """
    cmd = ["lark-cli"]
    if as_user:
        cmd += ["--as", "user"]
    cmd += args

    logger.debug("lark-cli cmd: %s", " ".join(cmd))

    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": {"message": f"timeout after {timeout}s"}, "raw": ""}

    if r.returncode != 0:
        return {
            "ok": False,
            "error": {
                "message": f"lark-cli rc={r.returncode}",
                "stderr": r.stderr.strip(),
            },
            "raw": r.stdout,
        }

    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError as e:
        return {
            "ok": False,
            "error": {"message": f"JSON parse failed: {e}"},
            "raw": r.stdout,
        }

    if not data.get("ok"):
        return {
            "ok": False,
            "error": data.get("error", {"message": "unknown"}),
            "raw": r.stdout,
        }

    return {"ok": True, "data": data.get("data", {}), "raw": r.stdout}


def safe_json_dumps(obj: Any) -> str:
    """JSON 序列化 (飞书 Long Text 字段用)"""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True)


def safe_json_loads(s: str) -> Any:
    """JSON 反序列化, 失败返回 None"""
    if not s:
        return None
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return None
