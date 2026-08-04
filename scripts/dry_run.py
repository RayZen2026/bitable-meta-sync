"""
dry-run 流程 (阶段 2 stub)

阶段 1 仅实现占位, 阶段 2 实现:
  - diff 算法 (同主类型 property diff)
  - 人类可读 diff 报告
"""
import logging
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_ROOT))

logger = logging.getLogger("bitable-meta-sync")


def dry_run(source_url: str, source_table_name: str, storage_url: str) -> dict:
    """dry-run 主流程 (阶段 2 stub)"""
    return {
        "ok": False,
        "error": {
            "code": "E_NOT_IMPLEMENTED",
            "message": "dry-run 阶段 2 待实现, 当前版本仅支持 extract",
        },
    }
