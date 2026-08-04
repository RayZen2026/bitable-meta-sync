# 同步规则 (apply 阶段 3 待实现)

## 允许的变更

| 变更类型 | 数据安全 |
|---|---|
| 字段名 (name) | ✅ 不丢 |
| 字段描述 (description) | ✅ 不丢 |
| select options 增/改/重排/换色 | ✅ 不丢 |
| select options 删除 | ⚠️ 已有数据该值为空 |
| number style (precision/percentage/thousands_separator) | ✅ 不丢 |
| number currency_code | ✅ 不丢 |
| number progress color | ✅ 不丢 |
| number rating min/max/icon | ⚠️ 现有数据若超出新范围被裁剪 |
| datetime style.format | ✅ 不丢 |
| user multiple | ⚠️ true → false 多人单元格被截断 |
| group_chat multiple | ⚠️ 同上 |
| checkbox (无 property) | N/A |
| attachment/location style | ✅ 不丢 |

## 禁止的变更 (apply 时拒绝)

- ❌ 跨 type 转换 (text → select 等)
- ❌ auto_number / formula / lookup 任何改动
- ❌ link 的 link_table 改动
- ❌ system 字段 (created_at 等) 改动

## 实施细节 (阶段 3)

1. **diff 算法**: 对每个 storage 行, 比较 original_* vs target_*
2. **跨 type 检测**: `is_cross_type()` 返回 True → 标"失败"
3. **select options 处理**:
   - 保留已有 options 的 name/hue/lightness
   - 新增 options 用 name + hue + lightness
   - 飞书 PUT 不支持删除单个 option, 只能全量替换
4. **失败隔离**: 单字段 try/except, 不影响其他
5. **可重入**: `sync_status=已同步` 跳过
