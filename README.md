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

## 文件结构

```
bitable-meta-sync/
├── SKILL.md                        # LLM 入口 (触发词/用法/安全)
├── README.md                       # 本文件 (项目说明 + 目录树)
├── config.yaml                     # SKILL 配置
├── .gitignore                      # Git 忽略
├── scripts/
│   ├── main.py                     # argparse 入口
│   ├── bitable.py                  # lark-cli 包装层
│   ├── schema.py                   # 主类型映射 + storage table 22 列定义
│   ├── extract.py                  # extract 流程
│   ├── apply.py                    # apply 流程 (阶段 3 stub)
│   ├── dry_run.py                  # dry-run 流程 (阶段 2 stub)
│   ├── preflight.py                # 运行时自检 (lark-cli + 凭据 + 磁盘)
│   └── common.py                   # 共享工具 (run_lark_cli 包装)
└── references/
    ├── implementation-plan.md      # 4 阶段实施进度 + 决策记录
    ├── field-type-mapping.md       # 飞书 27 type → 10 主类型映射
    ├── storage-table-schema.md     # 存储表 20 列详细
    ├── sync-rules.md               # 同步规则 (允许/禁止 + diff 算法)
    ├── cli-examples.md             # 3 子命令示例
    └── lark-cli-quirks.md          # 13 条 lark-cli 1.0.81+ 已知坑
```

## 当前状态

- ✅ 阶段 0：骨架
- ✅ 阶段 1：extract（端到端跑通 + 真实使用 4 次成功, 44/18 字段表 + --new-base 模式）
- ⬜ 阶段 2：dry-run + diff 算法
- ⬜ 阶段 3：apply + 安全机制
- ⬜ 阶段 4：测试 + 完整文档（含 CHANGELOG）

### 真实使用记录（v0.2.0）

| 日期 | 源表 | 字段数 | 耗时 | 结果 |
|---|---|---|---|---|
| 2026-08-04 19:40 UTC | 升级售后商家审核任务表 | 44 | 19 秒 | ✅ 无 bug fix |
| 2026-08-04 21:14 UTC | 升级售后商家审核任务表 (wiki URL) | 44 | 7 秒 | ✅ v0.2.2 验证: wiki URL + _SCHEMA 默认 |
| 2026-08-04 21:15 UTC | 升级售后判责规则 (回归) | 18 | 6 秒 | ✅ v0.2.2 回归测试 |
| 2026-08-04 21:31 UTC | 升级售后商家审核任务表 (--new-base) | 44 | 9 秒 | ✅ v0.2.3 --new-base 模式 |

详细进度见 [references/implementation-plan.md](references/implementation-plan.md)

## License

Proprietary (internal use only).
