"""
extract 流程

  1. preflight (lark-cli 可用, 源/存储 bitable 可读写)
  2. 解析 source_url → app_token, 查 source_table_id by name
  3. 解析 storage_url → app_token
  4. 检查 storage app 内是否已有同名表, 有则 abort
  5. 拉源表 fields, 分类 editable / readonly
  6. 创建存储表 (22 列 schema)
  7. 写控制行 + 字段行 (batch_create)
  8. 返回: {storage_table_id, total/editable/readonly count, readonly list}
"""
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 允许从 SKILL 根目录 import scripts.*
SKILL_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from scripts.common import run_lark_cli, safe_json_dumps  # noqa: E402
from scripts import bitable  # noqa: E402
from scripts import schema as schema_mod  # noqa: E402

logger = logging.getLogger("bitable-meta-sync")


def _now_str() -> str:
    """飞书 DateTime 字段接受 'YYYY-MM-DD HH:mm:ss' 字符串"""
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def _build_storage_field_defs() -> List[Dict[str, Any]]:
    """从 schema.STORAGE_TABLE_COLUMNS 构建 lark-cli +table-create 的 fields 格式

    canonical 格式 (lark-cli 1.0.81+):
      {
        "name": "...",
        "type": "text" | "select" | "number" | "datetime" | "user" | "checkbox",
        "description": "...",
        "options": [...]   # 仅 select
        "style": {...}     # 仅 number/datetime
        "multiple": false  # 仅 select/user
      }
    """
    defs = []
    for col in schema_mod.STORAGE_TABLE_COLUMNS:
        d: Dict[str, Any] = {
            "name": col["name"],
            "type": col["type"],
        }
        if col.get("description"):
            d["description"] = col["description"]
        if col.get("options"):
            d["options"] = col["options"]
        if col.get("style"):
            d["style"] = col["style"]
        if col["type"] == schema_mod.T_SELECT:
            d["multiple"] = False
        if col["type"] == schema_mod.T_USER:
            d["multiple"] = False
        defs.append(d)
    return defs


def _extract_relevant_fields(field: Dict[str, Any]) -> Dict[str, Any]:
    """从源表 field JSON 提取可序列化部分 (options, style, multiple 等)"""
    result = {}
    for key in ("style", "options", "multiple", "default_value", "description",
                "expression", "link_table", "auto_serial"):
        if key in field:
            result[key] = field[key]
    return result


def _field_to_storage_row(
    field: Dict[str, Any],
) -> Dict[str, Any]:
    """源表 field → 存储表 record fields"""
    field_id = field.get("id", field.get("field_id", ""))
    field_name = field.get("name", field.get("field_name", ""))
    field_type = field.get("type", "")
    description = field.get("description", "") or ""
    # ⚠️ 飞书 v3 API 不返回 is_required (默认全 false), 留空
    # required = bool(field.get("is_required", False))

    readonly = schema_mod.is_readonly(field_type)
    sync_status = "跳过" if readonly else "未同步"

    # 提取 options (select 字段)
    options = field.get("options") or []
    options_json = safe_json_dumps(options) if options else ""

    # 提取 property (style + multiple + 其他)
    property_json = safe_json_dumps(_extract_relevant_fields(field)) if field else ""

    row_id = schema_mod.build_storage_field_id(field_id)
    display = schema_mod.display_type(field_type)

    return {
        "fields": {
            "__row_id__": row_id,
            "original_field_id": field_id,
            "original_field_name": field_name,
            "original_field_type": display,
            "original_field_description": description,
            "original_options_json": options_json,
            "original_property_json": property_json,
            # target 列全空
            "sync_status": sync_status,
            "created_at": _now_str(),
        }
    }


def _build_control_row(source_table_name: str, source_url: str) -> Dict[str, Any]:
    """控制行 (__row_id__ = __control__)"""
    return {
        "fields": {
            "__row_id__": "__control__",
            "original_field_id": "__control__",
            "original_field_name": source_table_name,
            "original_field_type": "__control__",
            "sync_status": "__control__",
            "diff_summary": f"source_url={source_url}",
            "created_at": _now_str(),
        }
    }


def extract(
    source_url: str,
    source_table_name: str,
    storage_url: str,
    storage_table_name: Optional[str] = None,
) -> Dict[str, Any]:
    """extract 主流程"""
    storage_table_name = storage_table_name or source_table_name

    # 1. 解析 URL
    from scripts.common import parse_bitable_url
    source_app_token = parse_bitable_url(source_url)
    storage_app_token = parse_bitable_url(storage_url)
    logger.info("source app=%s..., storage app=%s...",
                source_app_token[:8], storage_app_token[:8])

    # 2. 找源表
    source_table = bitable.find_table_by_name(source_app_token, source_table_name)
    if not source_table:
        raise RuntimeError(f"源表 '{source_table_name}' 在 app {source_app_token[:8]}... 中不存在")
    source_table_id = source_table.get("table_id") or source_table.get("id")
    logger.info("source table: %s (id=%s)", source_table_name, source_table_id)

    # 3. 同名冲突检测
    existing = bitable.find_table_by_name(storage_app_token, storage_table_name)
    if existing:
        raise RuntimeError(
            f"存储表 '{storage_table_name}' 在 app {storage_app_token[:8]}... 中已存在 "
            f"(table_id={existing.get('table_id') or existing.get('id')}), "
            "请改名或先手动删除"
        )

    # 4. 拉源表 fields
    fields = bitable.list_fields(source_app_token, source_table_id)
    logger.info("source table has %d fields", len(fields))

    # 5. 分类 editable / readonly
    editable = []
    readonly = []
    for f in fields:
        ft = f.get("type", "")
        if schema_mod.is_readonly(ft):
            readonly.append(f)
        else:
            editable.append(f)

    # 6. 创建存储表
    storage_field_defs = _build_storage_field_defs()
    logger.info("creating storage table with %d columns", len(storage_field_defs))

    create_result = bitable.create_table(
        storage_app_token, storage_table_name, storage_field_defs,
    )
    storage_table_id = (
        create_result.get("table_id")
        or create_result.get("table", {}).get("table_id")
        or create_result.get("table", {}).get("id")
    )
    if not storage_table_id:
        raise RuntimeError(f"存储表创建失败: {create_result}")
    logger.info("storage table created: %s (id=%s)", storage_table_name, storage_table_id)

    # 7. 写 records (控制行 + 字段行)
    records = [_build_control_row(source_table_name, source_url)]
    records += [_field_to_storage_row(f) for f in fields]

    # 分批 (飞书 batch_create 上限 1000/批, 我们用 500 保险)
    BATCH = 500
    total_written = 0
    for i in range(0, len(records), BATCH):
        batch = records[i:i + BATCH]
        record_ids = bitable.batch_create_records(
            storage_app_token, storage_table_id, batch,
        )
        total_written += len(record_ids)
        logger.info("batch %d-%d written: %d records", i, i + len(batch), len(record_ids))

    # 8. 构造 readonly 列表
    readonly_list = [
        {
            "field_name": f.get("name", f.get("field_name", "")),
            "field_id": f.get("id", f.get("field_id", "")),
            "type": f.get("type", ""),
            "reason": "system readonly type",
        }
        for f in readonly
    ]

    return {
        "ok": True,
        "source_app_token": source_app_token,
        "source_table_id": source_table_id,
        "source_table_name": source_table_name,
        "storage_app_token": storage_app_token,
        "storage_table_id": storage_table_id,
        "storage_table_name": storage_table_name,
        "storage_url": storage_url,
        "total_fields": len(fields),
        "editable_fields": len(editable),
        "readonly_fields": len(readonly),
        "records_written": total_written,
        "readonly_list": readonly_list,
    }
