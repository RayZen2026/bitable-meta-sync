# CLI 使用示例

## extract (阶段 1 已实现)

```bash
python3 scripts/main.py extract \
  --source-url "https://bggc.feishu.cn/base/HGDzb2h7MaydFxsqlyAcCpALnB1" \
  --source-table "升级售后判责规则" \
  --storage-url "https://bggc.feishu.cn/base/Ltj9boOl8aO3iYsc642cj0SCn8f" \
  --storage-table "升级售后判责规则_SCHEMA"
```

输出:
```json
{
  "ok": true,
  "source_table_id": "tblty9QJT2g7caeg",
  "storage_table_id": "tblT2kj3fKjsHSs7",
  "total_fields": 18,
  "editable_fields": 16,
  "readonly_fields": 2,
  "readonly_list": [...]
}
```

跳过 preflight (调试):
```bash
python3 scripts/main.py extract ... --skip-preflight
```

## dry-run (阶段 2 stub)

```bash
python3 scripts/main.py dry-run \
  --source-url "..." --source-table "..." --storage-url "..."
```

## apply (阶段 3 stub)

```bash
python3 scripts/main.py apply \
  --source-url "..." --source-table "..." --storage-url "..." \
  --conflict abort --scope all --confirm
```
