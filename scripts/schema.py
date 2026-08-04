"""
飞书字段 type 映射 + property diff

字段类型是**字符串** (lark-cli 1.0.81+ canonical format):
  text       (style.type: plain/phone/url/email/barcode)
  number     (style.type: plain/currency/progress/rating)
  select     (multiple + options)
  datetime
  auto_number
  formula    (with expression, read-only)
  user       (with multiple)
  group_chat
  attachment
  location
  checkbox
  link       (with link_table, read-only)
  lookup     (with from/select/where, read-only)
  created_at / updated_at      (系统字段)
  created_by / updated_by      (系统字段)

EDITABLE: text, number, select, datetime, user, group_chat, attachment,
          location, checkbox
READONLY: auto_number, formula, link, lookup, created_at/updated_at,
          created_by/updated_by

文档: lark-base-shortcut-field-properties.md (lark-base skill)
"""
import json
from typing import Any, Dict, List, Optional

# ============================================================
# 主类型映射
# ============================================================

# type 字符串 → 中文显示
TYPE_DISPLAY_NAME: Dict[str, str] = {
    "text": "文本",
    "number": "数字",
    "select": "选择",
    "datetime": "日期",
    "auto_number": "自动编号",
    "formula": "公式",
    "user": "人员",
    "group_chat": "群组",
    "attachment": "附件",
    "location": "地理位置",
    "checkbox": "复选框",
    "link": "关联",
    "lookup": "引用",
    "created_at": "创建时间",
    "updated_at": "最后修改时间",
    "created_by": "创建人",
    "updated_by": "最后修改人",
}

# 不可编辑的 type (extract 时标"跳过", apply 时不动)
READONLY_TYPES = {
    "auto_number",  # 自动编号 (只读)
    "formula",      # 公式 (只读)
    "link",         # 关联 (table 只读, 其他可改)
    "lookup",       # 引用 (只读)
    "created_at",   # 系统时间
    "updated_at",   # 系统时间
    "created_by",   # 系统用户
    "updated_by",   # 系统用户
}

# 可编辑的 type
EDITABLE_TYPES = {
    "text", "number", "select", "datetime", "user", "group_chat",
    "attachment", "location", "checkbox",
}


def is_readonly(field_type: str) -> bool:
    """该 type 是否只读 (extract 跳过)"""
    return field_type in READONLY_TYPES


def is_cross_type(field_type_a: str, field_type_b: str) -> bool:
    """两个 type 是否跨主类型 (apply 时拒绝)"""
    return field_type_a != field_type_b


def build_storage_field_id(field_id: str) -> str:
    """源表 fldXXX → 存储表 __row_id__ = fld_<id>"""
    return f"fld_{field_id}"


def parse_storage_field_id(row_id: str) -> Optional[str]:
    """存储表 __row_id__ → 源表 fldXXX, 非字段行返回 None"""
    if not row_id or not row_id.startswith("fld_"):
        return None
    return row_id[4:]


def display_type(field_type: str) -> str:
    """飞书 type 字符串 → 中文显示 (如 'select / 选择')"""
    name = TYPE_DISPLAY_NAME.get(field_type, f"未知({field_type})")
    return f"{field_type} / {name}"


# ============================================================
# 存储表 schema (22 列, 飞书字段定义格式)
# ============================================================

# 字段类型字符串 (lark-cli 1.0.81+ canonical)
T_TEXT = "text"
T_NUMBER = "number"
T_SELECT = "select"
T_DATETIME = "datetime"
T_USER = "user"
T_CHECKBOX = "checkbox"
T_URL_STYLE = "url"  # text with style.type=url

# 存储表列定义: (column_name, lark_field_type, options_or_style, written_by)
STORAGE_TABLE_COLUMNS: List[Dict[str, Any]] = [
    # 主键
    {"name": "__row_id__", "type": T_TEXT, "description": "内部唯一 ID (fld_<id> 或 __control__)",
     "written_by": "SKILL", "hidden": True},

    # 原始列 (8)
    {"name": "original_field_id", "type": T_TEXT, "description": "源表 fldXXX",
     "written_by": "SKILL"},
    {"name": "original_field_name", "type": T_TEXT, "description": "源表当前字段名",
     "written_by": "SKILL"},
    {"name": "original_field_type", "type": T_TEXT, "description": "飞书 type (text/select/number/...)",
     "written_by": "SKILL"},
    {"name": "original_field_description", "type": T_TEXT, "description": "源表当前描述",
     "written_by": "SKILL"},
    {"name": "original_required", "type": T_CHECKBOX, "description": "源表当前必填 (预留)",
     "written_by": "SKILL"},
    {"name": "original_options_json", "type": T_TEXT, "description": "select options JSON",
     "written_by": "SKILL"},
    {"name": "original_property_json", "type": T_TEXT, "description": "完整字段 JSON (含 style/multiple/options)",
     "written_by": "SKILL"},

    # 目标列 (7)
    {"name": "target_field_name", "type": T_TEXT, "description": "目标字段名 (空=不变)",
     "written_by": "USER"},
    {"name": "target_field_type", "type": T_TEXT, "description": "目标 type (空=不变, 必须同 type)",
     "written_by": "USER"},
    {"name": "target_field_description", "type": T_TEXT, "description": "目标描述 (空=不变)",
     "written_by": "USER"},
    {"name": "target_required", "type": T_CHECKBOX, "description": "目标必填 (空=不变, 预留)",
     "written_by": "USER"},
    {"name": "target_options_json", "type": T_TEXT, "description": "目标 options JSON (空=不变)",
     "written_by": "USER"},
    {"name": "target_property_json", "type": T_TEXT, "description": "目标 property JSON (空=不变)",
     "written_by": "USER"},

    # 状态列 (4)
    {"name": "sync_status", "type": T_SELECT, "description": "未同步/待更新/已同步/失败/跳过/__control__",
     "written_by": "SKILL", "options": [
         {"name": "__control__", "hue": "Gray", "lightness": "Standard"},
         {"name": "未同步", "hue": "Gray", "lightness": "Lighter"},
         {"name": "待更新", "hue": "Blue", "lightness": "Lighter"},
         {"name": "已同步", "hue": "Green", "lightness": "Lighter"},
         {"name": "失败", "hue": "Red", "lightness": "Lighter"},
         {"name": "跳过", "hue": "Gray", "lightness": "Light"},
         {"name": "已删除", "hue": "Orange", "lightness": "Lighter"},
     ]},
    {"name": "last_sync_at", "type": T_DATETIME, "description": "上次 apply 时间",
     "written_by": "SKILL", "style": {"format": "yyyy-MM-dd HH:mm"}},
    {"name": "diff_summary", "type": T_TEXT, "description": "人类可读 diff 摘要",
     "written_by": "SKILL"},
    {"name": "notes", "type": T_TEXT, "description": "失败原因 / 备注 / 用户标记",
     "written_by": "USER"},

    # 审计列 (2 飞书自动 + 2 SKILL 写)
    {"name": "created_at", "type": T_DATETIME, "description": "该行首次写入时间",
     "written_by": "SKILL", "style": {"format": "yyyy-MM-dd HH:mm"}},
    {"name": "created_by", "type": T_USER, "description": "创建人 (飞书自动)",
     "written_by": "FEISHU_AUTO"},
]

SYNC_STATUS_OPTIONS = ["__control__", "未同步", "待更新", "已同步", "失败", "跳过", "已删除"]
