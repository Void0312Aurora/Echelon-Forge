# MLF-7 二次后果耦合 — 验收记录

状态：`2026-06-18`，工程代理 MLF-7 切片 accepted。P1/P2/P3、P4 诊断、
P5 聚焦验证、P6 更广 smoke 和 P7 状态同步均已满足。

## 验收范围

本记录将有边界 MLF-7 切片标记为 accepted。`[x]` = 已满足；`[~]` =
有意保留在 MLF-7 外。

## MLF-7A：边界和索引

- [x] README、任务簇、当前状态、派发队列、验收记录和 archive 占位存在。
- [x] A2 父 README 将 MLF-7 链接为已有事件和 smoke 证据的 accepted 工程代理 bridge。
- [x] Air-combat README 将 MLF-7 路由为 MLF-6 验收后的 follow-on，并记录剩余
  MLF-8/9/10 residual 边界。
- [x] 禁止声明已列出并继续拒绝。

## MLF-7B：后果盘点

- [x] Inventory 列出 MLF-7 可能读取的每个 `StructuralBreakupState` 字段。
- [x] Inventory 列出 MLF-7 可能用于诊断或链路关联的每个 `StructuralBreakupEvent`
  字段。
- [x] Inventory 列出每个候选写入面和 owner：`AircraftDamageState`、
  `PlatformDamageState`、`Health`、`FlightModel`、`Propulsion`、diagnostics 和 tests。
- [x] Inventory 记录 `AircraftDamageStateUpdate`、`StructuralFailureUpdate` 和
  MLF-7 bridge 之间的执行顺序。
- [x] Inventory 将直接删除、残骸生命周期和 Pk 投影标记为禁止项。

## MLF-7C：耦合契约

- [x] 每个断裂模式都有明确有边界的后果映射。
- [x] no-breakup / intact 状态有零效果守卫。
- [x] multi-axis 和 `full_breakup` 行为明确且可测试。
- [x] 失能状态升级阈值明确，并且不绕开维护中的 damage/loss-state helper。
- [x] 契约说明 aircraft-damage/loss-state 字段在 `StructuralFailureUpdate` 后更新；
  flight/propulsion/sensor 下游投影下一 tick 消费。

## MLF-7D：Runtime Bridge

- [x] Runtime bridge 读取 `StructuralBreakupState` 或批准的事件事实。
- [x] Runtime bridge 只写入 P2 批准的后果表面。
- [x] 没有新增直接 `e.destruct()` 路径。
- [x] 没有创建残骸/碎片实体。
- [x] 没有新增 Pk 或训练奖励投影。

## MLF-7E：诊断

- [x] 后果 delta 可在聚焦 C++ 状态测试中按目标实体查看。
- [x] 当上游 `chain_id` 存在时，从结构事实到后果诊断的链路关联保持连续。
- [x] 诊断通过 `generic_research_structural_consequence_projection`、diagnostics-only
  可见性和继续拒绝 calibration/Pk 声明，将工程代理值和校准真值分开。

## MLF-7F：聚焦验证

- [x] no-breakup case 产生零 MLF-7 后果 delta。
- [x] `wing_loss`、`tail_loss`、`engine_detach` 和 `fuselage_rupture` 分别产生预期
  有边界后果。
- [x] `multi_axis` / `full_breakup` 产生预期失能状态行为。
- [x] 不可逆 MLF-6 状态不会造成重复 runaway delta。
- [x] 聚焦测试证明没有直接残骸生命周期或直接删除路径。

## MLF-7G：回归 Smoke

- [x] C++ 聚焦 lane 通过。
- [x] 相关 Python diagnostic/runtime 测试通过：
  `PYTHONPATH=build-workshop:. pytest -q tests/runtime/engagement/ tests/runtime/facade/ tests/runtime/bindings/ tests/tools/test_structural_breakup_export.py`
  -> 160 passed。
- [x] 完整 `tests/runtime/air_combat/` 和 `tests/world_batch/` lane 通过：
  `PYTHONPATH=build-workshop:. pytest -q tests/runtime/air_combat/ tests/world_batch/`
  -> 447 passed。

## MLF-7H：验收和归档

- [x] 当前状态总结实现证据和 residual。
- [x] A2 父 README 和 air-combat README 状态同步。
- [x] 已按显式归档请求移动到父级 A2 本地归档。
- [x] MLF-8/9/10 residual 保持具名。

## 必须拒绝的声明

- [x] 没有真实世界 Pk 权威。
- [x] 没有确定性击杀权威。
- [x] 没有 stock AIM-120C/MQ-9/F-16C 杀伤权威。
- [x] 没有残骸/碎片生命周期权威。
- [x] 没有海军或地面结构后果权威。
- [x] 没有维护中平台损伤路径之外的直接坠毁/删除规则。
