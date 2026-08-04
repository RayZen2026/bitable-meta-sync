"""
业务 bitable 访问层

封装 lark-cli base 子命令:
  - list_tables(app_token)
  - find_table_by_name(app_token, name)
  - create_table(app_token, name, fields)
  - list_fields(app_token, table_id)
  - list_records(app_token, table_id)
  - batch_create_records(app_token, table_id, records)

调用方式: subprocess 调 lark-cli base +<verb> (默认 user 身份, 不用 --as bot)
"""
import json
import logging
from typing import Any, Dict, List, Optional

from scripts.common import run_lark_cli

logger = logging.getLogger("bitable-meta-sync")


def create_base(name: str, folder_token: Optional[str] = None) -> str:
    """创建新 bitable app, 返回 base_token

    canonical 格式 (lark-cli 1.0.81+):
      lark-cli base +base-create --name <name> [--folder-token <token>]
      (不指定 folder_token = 我的空间 root)
    """
    args = ["base", "+base-create", "--name", name]
    if folder_token:
        args += ["--folder-token", folder_token]
    r = run_lark_cli(args)
    if not r["ok"]:
        raise RuntimeError(f"base-create 失败: {r.get('error', {}).get('message')}")
    data = r["data"]
    # 响应: {"base": {"token": "XXX", "name": "YYY"}}
    base = data.get("base") or data
    token = base.get("token") or base.get("base_token")
    if not token:
        raise RuntimeError(f"base-create 响应缺 token: {data}")
    logger.info("new base created: %s (token=%s)", name, token[:8] + "...")
    return token


def list_tables(app_token: str) -> List[Dict[str, Any]]:
    """列出 bitable 下所有表

    实际返回 (lark-cli 1.0.81+):
      {"ok": true, "data": {"tables": [{"id": "tblXXX", "name": "..."}]}}
    """
    r = run_lark_cli(["base", "+table-list", "--base-token", app_token])
    if not r["ok"]:
        raise RuntimeError(f"table-list 失败: {r.get('error', {}).get('message')}")
    data = r["data"]
    return data.get("tables") or data.get("items") or []


def find_table_by_name(app_token: str, name: str) -> Optional[Dict[str, Any]]:
    """按表名查找表 (大小写不敏感)"""
    for t in list_tables(app_token):
        t_name = t.get("name", "").strip()
        t_id = t.get("id") or t.get("table_id")
        if t_name == name.strip():
            return {**t, "table_id": t_id}
    return None


def create_table(app_token: str, name: str, fields: List[Dict[str, Any]]) -> Dict[str, Any]:
    """创建表

    canonical 格式 (lark-cli 1.0.81+):
      lark-cli base +table-create --base-token X --name T --fields 'JSON array'
    """
    r = run_lark_cli(
        [
            "base", "+table-create",
            "--base-token", app_token,
            "--name", name,
            "--fields", json.dumps(fields, ensure_ascii=False),
        ],
    )
    if not r["ok"]:
        raise RuntimeError(f"table-create 失败: {r.get('error', {}).get('message')}")
    return r["data"]


def list_fields(app_token: str, table_id: str) -> List[Dict[str, Any]]:
    """列出表所有字段

    实际返回 (lark-cli 1.0.81+):
      {"ok": true, "data": {"fields": [{"id": "fldXXX", "name": "...", "type": "text", ...}]}}
    """
    r = run_lark_cli(
        [
            "base", "+field-list",
            "--base-token", app_token,
            "--table-id", table_id,
        ],
    )
    if not r["ok"]:
        raise RuntimeError(f"field-list 失败: {r.get('error', {}).get('message')}")
    data = r["data"]
    return data.get("fields") or data.get("items") or []


def list_records(app_token: str, table_id: str, page_size: int = 500) -> List[Dict[str, Any]]:
    """拉表所有 record (单页足够, 飞书 record-list 单页上限 500)"""
    r = run_lark_cli(
        [
            "base", "+record-list",
            "--base-token", app_token,
            "--table-id", table_id,
            "--limit", str(page_size),
        ],
    )
    if not r["ok"]:
        raise RuntimeError(f"record-list 失败: {r.get('error', {}).get('message')}")
    data = r["data"]
    items = data.get("items") or data.get("records") or []
    return items


def batch_create_records(
    app_token: str,
    table_id: str,
    records: List[Dict[str, Any]],
) -> List[str]:
    """批量创建 record

    records: [{"fields": {...}}, ...]  (从 extract 传入的格式, 内部 unwrap)
    canonical 格式 (lark-cli 1.0.81+):
      lark-cli base +record-batch-create --base-token X --table-id Y \
        --json '{"create_records":[{"Name":"x"}, ...]}'

    关键:
      - 顶层 key 是 create_records (不是 records)
      - 每条 record 是直接 field map {"Name": "x"} 不是 {"fields": {...}}
      - max 200 records/call

    返回: {"ok": true, "data": {"record_ids": ["recXXX", ...]}}
    """
    if not records:
        return []

    # unwrap {"fields": {...}} → {...}
    flat_records = []
    for r in records:
        if "fields" in r:
            flat_records.append(r["fields"])
        else:
            flat_records.append(r)

    payload = {"create_records": flat_records}

    r = run_lark_cli(
        [
            "base", "+record-batch-create",
            "--base-token", app_token,
            "--table-id", table_id,
            "--json", json.dumps(payload, ensure_ascii=False),
        ],
    )
    if not r["ok"]:
        raise RuntimeError(f"record-batch-create 失败: {r.get('error', {}).get('message')}")
    data = r["data"]
    return data.get("record_id_list") or data.get("record_ids") or data.get("record_ids_list") or []
