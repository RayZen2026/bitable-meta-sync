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

## v0.2.4 增量改进 (2026-08-04)

v0.2.3 真实使用后, 任锐反馈存储表 20 列全是英文 (original_field_name / target_* / sync_status), 对非技术用户不友好。**全部改为中文列名**:

| 旧 (英文) | 新 (中文) |
|---|---|
| original_field_id | 原始字段ID |
| original_field_name | 原始字段名 |
| original_field_type | 原始类型 |
| original_field_description | 原始描述 |
| original_required | 原始必填 |
| original_options_json | 原始选项JSON |
| original_property_json | 原始属性JSON |
| target_field_name | 目标字段名 |
| target_field_type | 目标类型 |
| target_field_description | 目标描述 |
| target_required | 目标必填 |
| target_options_json | 目标选项JSON |
| target_property_json | 目标属性JSON |
| sync_status | 同步状态 |
| last_sync_at | 最后同步时间 |
| diff_summary | 差异摘要 |
| notes | 备注 |
| created_at | 创建时间 |
| created_by | 创建人 |
| __row_id__ | __row_id__ (内部 hidden, 不动) |

**额外修复**: storage_url host 之前写的是 placeholder `https://xxx.feishu.cn/`, 改为真实 `https://bggc.feishu.cn/`.

**真实使用 1 次**: 44 字段表 9 秒成功, 飞书 API 返回的字段名都是中文.

## v0.2.3 增量改进 (2026-08-04)

### 触发关键词扩宽 (LRN-20260804-048)
任锐提出 SKILL 不能从自然语言自动触发。原 trigger 只覆盖 "字段元数据 / schema / 字段配置 / 字段改名" 4 个专业词。任锐用的是 "提取 meta 信息" 等口语化表达 → 加 5 个口语化 trigger:

- 提取多维表格
- 复制表结构
- meta 抽取
- 字段表反向同步
- 多维表格备份

### 新增 --new-base 模式 (LRN-20260804-047)
任锐提出 "新的多维表格" 歧义问题: 实际指 **新 base**, 不是新 table (我之前默认成新 table 是错的, LRN-20260804-042 要作废)。新加 3 个 flag:

| flag | 作用 | 缺省 |
|---|---|---|
| --new-base | 创建新 bitable app 作为 storage | False |
| --new-base-name | 新 base 名称 | source-table + _SCHEMA |
| --folder-token | 新 base 所在 folder | 我的空间 (root) |

--storage-url 与 --new-base 互斥 (同时传报错)。

### 实现要点
- scripts/bitable.py: 加 create_base(name, folder_token=None) → 调 lark-cli base +base-create
- scripts/extract.py: extract() 加 new_base / new_base_name / folder_token 参数; storage_url 改 Optional
- scripts/main.py: extract argparse 加 3 个新 flag; preflight 用 source_url 兜底 (new_base 模式下 storage_url 还没创建)

### 真实使用 2 次
- new_base 模式 44 字段: 9 秒成功, 新 base YTWqb4VzJaTphvsjuMyc5DPSnkg (已清理)
- old mode 18 字段回归: 5 秒成功 (无回归)

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
