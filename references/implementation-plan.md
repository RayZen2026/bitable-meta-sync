# 实施阶段

> 本文档记录 SKILL 的分阶段实施计划。**SKILL.md 不写实施进度**（那是项目元信息，不是 LLM 上下文）。
> 设计文档以飞书 docx `FQhtdvtUOopg53xfGP0ccUHdnTf` 为准。

## 阶段 0：骨架 ✅ (2026-08-04 完成)

- 路径 A 单 slash command + argparse
- preflight 4 项：lark-cli 可用 + version ≥ 1.0.79 / bitable read / bitable write / 磁盘 ≥ 100MB
- 共享工具：common.py (run_lark_cli 包装) / schema.py (主类型映射)
- 端到端骨架跑通

## 阶段 1：extract ✅ (2026-08-04 完成, 真实使用验证)

- 源表 fields 拉取（lark-cli 1.0.81+ canonical format）
- 主类型分类（10 大主类型 + system readonly）
- 存储表 22 列 schema（20 列实际 + 飞书自动审计列）
- 控制行（__row_id__ = __control__）写入
- 同名表冲突检测
- 端到端验证：
  - **测试 1**（开发期）：升级售后判责规则表（18 字段）→ 19 records 写入
  - **测试 2**（真实使用，2026-08-04 19:40-19:41 UTC）：升级售后商家审核任务表（44 字段）→ 45 records 写入, 19 秒, 无 bug fix
- readonly 字段处理：5 项（4 formula + 1 updated_at）全部正确分类
- **DEC-20260804-008 已解决**：飞书系统字段 type 是字符串（`created_at` / `updated_at` / `created_by` / `updated_by`），不是 1003/1004 数字枚举

**关键技术发现**（详见 [lark-cli-quirks.md](lark-cli-quirks.md)）：
1. type 是字符串（不是数字）
2. field key 是 `id`/`name`（不是 `field_id`/`field_name`）
3. select options 在顶层（不是 `property.options`）
4. number/datetime 用 `style`（不是 `property`）
5. record-batch-create 用 `--json '{"create_records":[...]}'
6. 响应 key 是 `record_id_list`
7. record-batch-create max 200/call
8. datetime style.format 不允许 `yyyy-MM-dd HH:mm:ss`
9. select 写入时 value 必须在预定义 options 内
10. select 读取时 value 是 array

## v0.2.2 增量改进 (2026-08-04)

阶段 1 真实使用后发现 2 个 SKILL bug, 修复后端到端 6-8 秒:

| LRN | 问题 | 修复 |
|---|---|---|
| LRN-20260804-039 | parse_bitable_url 只支持 /base/&lt;token&gt; | 调 lark-cli wiki +node-get 解析 wiki URL → base_token; preflight.py 同步复用 |
| LRN-20260804-040 | storage_table_name 默认是源表名 (冲突) | 默认改为 源表名_SCHEMA 后缀 |

**真实使用 2 次** (wiki URL + base URL 回归), 0 bug fix.

## 阶段 2：dry-run + diff 算法 ⬜ (待启动)

- 拉存储表所有 records
- 对每行计算 original_* vs target_* diff
- 按主类型走各自的 diff 函数（number/select/date/link/location 等）
- 跨主类型 → 标"失败"
- 系统字段 → 跳过
- 输出 diff 报告（人类可读 + JSON）

**关键算法**：
- `_diff_text(fld)` → 比较 name/description
- `_diff_select(fld)` → options 增/改/重排/换色
- `_diff_number(fld)` → formatter/precision/percentage/currency_code
- `_diff_date(fld)` → date_formatter
- `_diff_user(fld)` → multiple
- `_diff_location(fld)` → input_type

## 阶段 3：apply + 安全机制 ⬜ (待启动)

- **二次确认**：TTY stdin "确认" / `--confirm` flag
- **apply 前 backup**：refresh `original_*` 为当前源表
- **单字段 try/except**：失败隔离
- **重入安全**：`sync_status=已同步` 跳过
- **conflict 策略**：abort/skip/force
- **scope 策略**：all/specified
- **系统字段跳过**：永不 apply
- **跨主类型拒绝**：apply 时再校验一次

## 阶段 4：测试 + 完整文档 ⬜ (待启动)

- 单元测试：property diff 各种 case
- 集成测试：端到端 extract → dry-run → apply
- 飞书 type 全部 27 type 覆盖测试
- 完整 README + CHANGELOG
- 第一个吃螃蟹的表：升级售后判责规则表 v0.2

## 决策记录（待任锐拍板）

详见飞书 design doc `FQhtdvtUOopg53xfGP0ccUHdnTf` 第 12 节：

- DEC-20260804-001 路径 A 单 slash command
- DEC-20260804-002 同名存储表拒绝
- DEC-20260804-003 跨主类型拒绝
- DEC-20260804-004 二次确认双模式
- DEC-20260804-005 存储表位置任选
- DEC-20260804-006 失败隔离
- DEC-20260804-007 scope=specified 用 notes 标记
- DEC-20260804-008 系统字段 type 编号 ✅ 已解决（type 是字符串, schema.py READONLY_TYPES 已包含）
