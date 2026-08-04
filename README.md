# bitable-meta-sync

飞书多维表格字段元数据双向同步工具。

## 用途

把源表的字段 schema（字段名/类型/必填/选项/描述）抽取到一张可编辑的"存储表"，
让用户在飞书 UI 里改字段配置，再把变更同步回源表。

详细设计见：飞书 design doc `FQhtdvtUOopg53xfGP0ccUHdnTf`

## 快速开始

```bash
# 抽取源表 schema 到存储表
python3 scripts/main.py extract \
  --source-url "https://bggc.feishu.cn/base/<source_token>" \
  --source-table "升级售后判责规则表" \
  --storage-url "https://bggc.feishu.cn/base/<storage_token>"

# 干跑：看 diff
python3 scripts/main.py dry-run \
  --source-url "..." --source-table "..." --storage-url "..."

# 同步：把存储表 target 列写回源表
python3 scripts/main.py apply \
  --source-url "..." --source-table "..." --storage-url "..." --confirm
```

## 当前状态

- ✅ 阶段 0：骨架
- ✅ 阶段 1：extract
- ⬜ 阶段 2：dry-run + diff
- ⬜ 阶段 3：apply
- ⬜ 阶段 4：测试 + 文档

## License

Proprietary (internal use only).
