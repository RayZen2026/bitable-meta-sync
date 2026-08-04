---
name: bitable-meta-sync
description: |
  飞书多维表格字段元数据双向同步 SKILL — 把源表的字段 schema（字段名/类型/必填/选项/描述）
  抽取到一张可编辑的"存储表"，让用户在飞书 UI 里改字段配置，再把变更同步回源表。
  
  解决：跨表 schema 不一致、字段改名漏改、字段类型改错无法审计等问题。
  
  Trigger: 字段元数据同步 / 飞书 schema 双向同步 / bitable meta sync /
  bitable 字段配置同步 / 字段改名批量同步.
  
  严格不修改源表数据记录、不跨主类型转换字段类型、不做视图/仪表盘同步。

license: Proprietary (internal use only)
compatibility: |
  Requires lark-cli ≥ 1.0.79, Python 3.9+, 飞书源表 + 存储表读写权限,
  lark-cli 已 auth login (任一可读源/目标 bitable 的 user 身份).

metadata:
  openclaw:
    emoji: 🔄
    id: bitable-meta-sync
    version: 0.2.1
    primaryEnv: BITABLE_META_SYNC_PROFILE
    requires:
      bins: [lark-cli, python3]
      env:
        - BITABLE_META_SYNC_PROFILE
      config: [config.yaml]
    install:
      - "pip install pyyaml"
    user-invocable: true
    disable-model-invocation: false
    trigger:
      intent:
        - 字段元数据同步
        - 飞书 schema 双向同步
        - bitable meta sync
        - bitable 字段配置同步
        - 字段改名批量同步
---

# bitable-meta-sync SKILL

> **定位**：把源表的字段 schema 抽到一张可编辑"存储表"，让用户在飞书 UI 改字段配置，再把变更同步回源表。
> **不**修改源表数据记录、**不**跨主类型转换字段类型、**不**做视图/仪表盘同步。

## When to use

适合以下场景：

- 跨多张表批量改字段名 / 描述 / 必填（飞书 UI 单表改无法批量）
- 业务表和字段说明表 schema 不一致需要核对（"字段说明表 4 步 SOP"自动化）
- 字段类型 / 选项调整后，需要审计"改了什么 / 何时改的 / 改前是什么"
- 把字段配置当作"可编辑数据"在团队里流转（产品改字段名 → 飞书 UI 改存储表 → 自动 apply）

不适合：

- ❌ 改字段类型（Text → Number）—— 飞书 API 不支持，必须手动"建新 + 迁移 + 删旧"
- ❌ 跨 bitable app 复制 schema —— 留待 v2
- ❌ 历史版本管理 (git-style commits/log) —— 留待 v2

## Subcommands（路径 A 单 slash command + argparse）

```bash
bitable-meta-sync <extract|apply|dry-run> [options]
```

### extract

抽取源表字段 schema 到存储表（首次或重建）。

```bash
bitable-meta-sync extract \
  --source-url <bitable_url> \
  --source-table <table_name> \
  --storage-url <bitable_url>
```

- `--source-url`：源 bitable URL (https://xxx.feishu.cn/base/<token>)
- `--source-table`：源表名（如"升级售后判责规则表"）
- `--storage-url`：目标 bitable URL（存储表建在这）
- `--storage-table`：存储表名（缺省 = source-table）

**返回**：JSON 报告（含 editable / readonly 字段分类）

### dry-run

计算 diff 并输出报告，不写入任何表。

```bash
bitable-meta-sync dry-run \
  --source-url <bitable_url> \
  --source-table <table_name> \
  --storage-url <bitable_url>
```

**返回**：diff 报告（每字段的 from → to 变更摘要）

### apply

把存储表 target 列的变更写回源表。**默认需要二次确认**。

```bash
bitable-meta-sync apply \
  --source-url <bitable_url> \
  --source-table <table_name> \
  --storage-url <bitable_url> \
  [--conflict abort|skip|force]   # 缺省 abort
  [--scope all|specified]         # 缺省 all
  [--confirm]                     # 跳过 TTY 二次确认 (cron 用)
```

**二次确认机制**：
- 交互场景：apply 触发后，TTY 等待用户输入"确认"才执行
- 自动化场景：`--confirm` flag 跳过等待

## 存储表设计

存储表是源表 schema 的"可编辑镜像"，**每行 = 源表的一个字段**。

| 列组 | 列数 | 写入方 | 作用 |
|---|---|---|---|
| 主键 | 1 (`__row_id__`) | SKILL | `fld_<field_id>` 或 `__control__` |
| 原始 | 7 (`original_*`) | SKILL | 源表当前 schema 快照 |
| 目标 | 7 (`target_*`) | **用户** | 想改成的 schema |
| 状态 | 4 | SKILL | 同步进度跟踪 |
| 审计 | 3 | SKILL/飞书 | 时间戳 + 修改人 |

详细 schema 见 [`references/storage-table-schema.md`](references/storage-table-schema.md)。

## 主类型分类

飞书 27 种 type 字段归到 10 个主类型 + 1 个 system readonly 类别：

| 主类型 | 飞书 type | 可编辑 property |
|---|---|---|
| text | text/phone/url | 无 |
| number | number | formatter/currency_code/min/max |
| select | select | options[] (单/多选) |
| date | datetime | date_formatter |
| checkbox | checkbox | 无 |
| person | user | multiple |
| attachment | attachment | 无 |
| link | link | ❌ table_id 只读 |
| location | location | input_type |
| group | group_chat | multiple |
| **system (只读)** | formula/auto_number/lookup/created_at/updated_at/created_by/updated_by | ❌ |

详细映射见 [`references/field-type-mapping.md`](references/field-type-mapping.md)。

## 安全机制

| 机制 | 实现 |
|---|---|
| **dry-run 模式** | 独立子命令，不写任何表 |
| **二次确认** | TTY stdin "确认" / `--confirm` flag |
| **失败隔离** | 单字段 try/except，不影响其他 |
| **同步前备份** | apply 第一步 refresh `original_*` 为当前源表 |
| **跨主类型拒绝** | diff 时检测，标"失败"不写 |
| **系统字段跳过** | extract 时标"跳过" |
| **同名表冲突** | extract 时检测，abort 不覆盖 |
| **可重入** | `sync_status=已同步` 字段跳过 |

## References

| 文档 | 内容 |
|---|---|
| [implementation-plan.md](references/implementation-plan.md) | 4 阶段实施进度 + 决策记录 |
| [storage-table-schema.md](references/storage-table-schema.md) | 存储表 20 列详细 |
| [field-type-mapping.md](references/field-type-mapping.md) | 飞书 27 type → 主类型 |
| [sync-rules.md](references/sync-rules.md) | 同步规则（允许/禁止 + diff 算法） |
| [cli-examples.md](references/cli-examples.md) | 3 子命令完整示例 |
| [lark-cli-quirks.md](references/lark-cli-quirks.md) | 13 条 lark-cli 1.0.81+ 已知坑 |

设计文档：飞书 docx `FQhtdvtUOopg53xfGP0ccUHdnTf`（PublicAssistant 目录）
