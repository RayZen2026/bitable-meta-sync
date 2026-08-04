# 存储表 22 列 schema 详细

存储表是**源表 schema 的"可编辑镜像"**, 每行 = 源表的一个字段。

## 列清单 (20 列 + 1 控制行)

| 列名 | 飞书 type | 写入方 | 作用 |
|---|---|---|---|
| `__row_id__` | text (隐藏) | SKILL | 内部唯一 ID, `fld_<field_id>` 或 `__control__` |
| `original_field_id` | text | SKILL | 源表 fldXXX |
| `original_field_name` | text | SKILL | 源表当前字段名 |
| `original_field_type` | text | SKILL | 飞书 type (text/select/number/...) |
| `original_field_description` | text | SKILL | 源表当前描述 |
| `original_required` | checkbox | SKILL | 源表当前必填 (预留) |
| `original_options_json` | text | SKILL | select options JSON |
| `original_property_json` | text | SKILL | 完整字段 JSON (style/multiple/options 等) |
| `target_field_name` | text | **用户** | 目标字段名 (空=不变) |
| `target_field_type` | text | **用户** | 目标 type (空=不变, 必须同 type) |
| `target_field_description` | text | **用户** | 目标描述 (空=不变) |
| `target_required` | checkbox | **用户** | 目标必填 (空=不变, 预留) |
| `target_options_json` | text | **用户** | 目标 options JSON (空=不变) |
| `target_property_json` | text | **用户** | 目标 property JSON (空=不变) |
| `sync_status` | select | SKILL | __control__/未同步/待更新/已同步/失败/跳过/已删除 |
| `last_sync_at` | datetime | SKILL | 上次 apply 时间 |
| `diff_summary` | text | SKILL | 人类可读 diff 摘要 |
| `notes` | text | **用户** | 失败原因 / 备注 / 用户标记 |
| `created_at` | datetime | SKILL | 该行首次写入时间 |
| `created_by` | user | 飞书自动 | 创建人 |

## sync_status 选项

- `__control__`: 控制行专用
- `未同步`: 新建, 未编辑
- `待更新`: 用户已改 target, 待 apply
- `已同步`: apply 成功
- `失败`: apply 失败, notes 写原因
- `跳过`: 系统字段 (formula/auto_number), apply 不动
- `已删除`: 源表字段被删除, 标"已删除"

## 控制行 (__row_id__ = __control__)

第 1 行, 记录**表级元信息**:
- `original_field_name`: 源表名
- `diff_summary`: `source_url=...`
- `notes`: 同步策略 (all/specified)
