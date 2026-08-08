# 部件响应 owner 边界清理切片

日期：`2026-06-21`

状态：P5 response owner 已迁移完成。`ComponentMechanismLoadRow` 只承载载荷/机制事实；
概率、sample、failure mode、integrity 和阈值响应均由 `ComponentResponseRow` 承载。

## 当前分类

load row 当前保留：

- `direct_hit`
- `distance_m`
- `effect_scale`
- fragment / blast / rod / penetration mechanism fields
- component dependency fields

response row 当前承载：

- `threshold_scale`
- `failure_probability`
- `failure_sample`
- `failure_mode`
- `failure_severity`
- `integrity_before`
- `integrity_after`
- redundancy availability before/after

`effect_scale` 是当前 load 侧聚合量；它需要继续拆解为 named factors 时，走 P4/P6 后续校准和消费者迁移，不再被标注为兼容层。

## 当前基线

刷新后的 review packet 显示：

- `rows_with_response_fields_on_load_row = 0`
- `component_response_row_count = 33`
- `response_owner_violation_field_counts = {}`
- `aggregate_coupled_load_field_names_present = ["effect_scale"]`

## 验证

已覆盖的关键测试：

- `tests/runtime/engagement/test_engagement_contract_shape.py`
- `tests/runtime/bindings/test_bindings_engagement_surface.py`
- `tests/runtime/air_combat/test_warhead_component_event_surface.py`
- `tests/tools/test_kill_chain_decoupling_probe.py`

后续要处理的是工程代理数据校准和聚合 load scalar 的消费者迁移，不是保留旧 response 兼容层。
