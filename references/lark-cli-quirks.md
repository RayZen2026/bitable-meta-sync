# 已知 lark-cli 坑 (本机 1.0.81 实测)

## 1. flag 是 `--base-token` 不是 `--app-token`

```bash
# ❌
lark-cli base +field-list --app-token X --table-id Y
# ✅
lark-cli base +field-list --base-token X --table-id Y
```

## 2. field 的 `id` 不是 `field_id`, `name` 不是 `field_name`

```json
// ❌ 假设
{"field_id": "fldXXX", "field_name": "..."}
// ✅ 实际
{"id": "fldXXX", "name": "..."}
```

## 3. field 的 `type` 是**字符串** ("text") 不是数字 (1)

```json
// ❌ 老 API 规范
{"type": 1}
// ✅ lark-cli 1.0.81+ canonical
{"type": "text"}
```

## 4. field 的 select options 在顶层, 不在 `property.options`

```json
// ❌ 假设
{"type": "select", "property": {"options": [...]}}
// ✅ 实际
{"type": "select", "options": [...]}
```

## 5. field 的 number/datetime 用 `style` 不是 `property`

```json
// ❌
{"type": "number", "property": {"precision": 2}}
// ✅
{"type": "number", "style": {"type": "plain", "precision": 2}}
```

## 6. table-list 的 data key 是 `tables` 不是 `items`

```json
// ❌ 假设
{"data": {"items": [...]}}
// ✅ 实际
{"data": {"tables": [...]}}
```

## 7. record-batch-create 的 JSON 结构是 `create_records` (单数 + list)

```bash
# ❌
--json '{"records": [{"fields": {...}}]}'
# ✅
--json '{"create_records": [{...}]}'  # 直接 field map, 不要 {"fields": ...} 包装
```

## 8. record-batch-create 的响应 key 是 `record_id_list`

```json
// ❌ 假设
{"record_ids": [...]}
// ✅ 实际
{"record_id_list": [...]}
```

## 9. record-batch-create max 200 records/call (不是 1000)

```python
BATCH = 200  # 飞书硬限
```

## 10. datetime style.format 飞书不允许 `yyyy-MM-dd HH:mm:ss`

允许值:
- yyyy/MM/dd
- yyyy/MM/dd HH:mm
- yyyy/MM/dd HH:mm Z
- yyyy-MM-dd
- yyyy-MM-dd HH:mm
- yyyy-MM-dd HH:mm Z
- MM-dd
- MM/dd/yyyy
- dd/MM/yyyy

❌ yyyy-MM-dd HH:mm:ss (精确到秒不被允许)
✅ yyyy-MM-dd HH:mm (改用这个)

## 11. select field 写入时 value 必须在预定义 options 内

```json
// ❌ "未同步" 不在 sync_status options → 800030005 not_found
{"sync_status": "未同步"}
// ✅ 加 options 后:
{"options": [{"name": "未同步", "hue": "Gray", "lightness": "Lighter"}], ...}
```

## 12. select field 读取时 value 是 array 形式

```json
// API 读取返回
{"sync_status": ["未同步"]}  // 注意是数组
```

## 13. dynamic_options_source vs static options

select 字段两种 options 模式:
- static: 传 `options: [{name, hue, lightness}]`
- dynamic: 传 `dynamic_options_source: ...`

两者**二选一, 不能同时传**。
