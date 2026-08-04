"""
apply 流程 (阶段 3 stub)

阶段 1 仅实现占位, 阶段 3 实现:
  - 二次确认 (TTY / --confirm)
  - 同步前备份 (refresh original_*)
  - 逐字段 PUT, 失败隔离
  - 冲突策略 (abort/skip/force)
  - scope=all/specified
"""
import logging
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_ROOT))

logger = logging.getLogger("bitable-meta-sync")


def apply(
    source_url: str,
    source_table_name: str,
    storage_url: str,
    conflict: str = "abort",
    scope: str = "all",
    confirm: bool = False,
) -> dict:
    """apply 主流程 (阶段 3 stub)"""
    return {
        "ok": False,
        "error": {
            "code": "E_NOT_IMPLEMENTED",
            "message": "apply 阶段 3 待实现, 当前版本仅支持 extract",
        },
    }
