# 飞书字段 type 映射表

> 来源: lark-cli 1.0.81+ canonical format
> 参考: lark-base-shortcut-field-properties.md (lark-base skill)

## 字符串 type (本机 1.0.81 实际返回)

| type 字符串 | 中文 | 主类型 | 可编辑 | 备注 |
|---|---|---|---|---|
| `text` | 文本 | text | ✅ | style.type: plain/phone/url/email/barcode |
| `number` | 数字 | number | ✅ | style.type: plain/currency/progress/rating |
| `select` | 选择 | select | ✅ | multiple 控制单/多选 + options[] |
| `datetime` | 日期 | date | ✅ | style.format: yyyy/MM/dd 等 9 种 |
| `checkbox` | 复选框 | checkbox | ✅ | 无 property |
| `user` | 人员 | person | ✅ | multiple |
| `group_chat` | 群组 | group | ✅ | multiple |
| `attachment` | 附件 | attachment | ✅ | 无 property |
| `location` | 地理位置 | location | ✅ | location.input_type |
| `auto_number` | 自动编号 | auto_number | ❌ | 只读, style.rules 控制格式 |
| `formula` | 公式 | formula | ❌ | 只读, expression 不可改 |
| `link` | 关联 | link | ⚠️ | name/description 可改, link_table 不可改 |
| `lookup` | 引用 | lookup | ❌ | 只读, from/select/where |
| `created_at` | 创建时间 | date | ❌ | 系统只读 |
| `updated_at` | 最后修改时间 | date | ❌ | 系统只读 |
| `created_by` | 创建人 | person | ❌ | 系统只读 |
| `updated_by` | 最后修改人 | person | ❌ | 系统只读 |

## 数字 type (老 API 规范, 已弃用)

⚠️ 本机 lark-cli 1.0.81+ 实际返回字符串 type, 不再返回数字 1/2/3 等。
本 SKILL 统一使用字符串映射。

## 实际观察 (2026-08-04, 升级售后判责规则表)

```json
{"id": "fldlNUZIyz", "name": "规则ID", "type": "auto_number", "style": {"rules": [...]}}
{"id": "fldHsJr6kG", "name": "是否生效", "type": "formula", "expression": "IF(...)"}
{"id": "fld5YOKao4", "name": "调整动作类型", "type": "select", "multiple": false, "options": [...]}
{"id": "fldFqOz2qh", "name": "生效截止日期", "type": "datetime", "style": {"format": "yyyy/MM/dd"}}
{"id": "fldfumk6A3", "name": "比例系数", "type": "number", "style": {"type": "plain", "precision": 2, "percentage": true}}
{"id": "fldVTOkDJp", "name": "规则来源", "type": "select", "multiple": false, "options": [...]}
```

## select options 颜色规范

```json
{
  "name": "选项名",
  "hue": "Red|Orange|Yellow|Lime|Green|Turquoise|Wathet|Blue|Carmine|Purple|Gray",
  "lightness": "Lighter|Light|Standard|Dark|Darker"
}
```

缺省: hue=Blue, lightness=Lighter

## datetime format 允许值 (飞书 API 限制)

- yyyy/MM/dd
- yyyy/MM/dd HH:mm
- yyyy/MM/dd HH:mm Z
- yyyy-MM-dd
- yyyy-MM-dd HH:mm
- yyyy-MM-dd HH:mm Z
- MM-dd
- MM/dd/yyyy
- dd/MM/yyyy

⚠️ 飞书**不允许** `yyyy-MM-dd HH:mm:ss`（精确到秒）
