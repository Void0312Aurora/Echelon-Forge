# MLF-7 二次后果耦合 — 当前状态

状态：`2026-06-18` accepted / archived MLF-7 切片完成。P1 inventory、P2
coupling contract、P3 structural consequence bridge、P4 链路关联事件诊断、P5
聚焦 C++ 验证、P6 更广 Python/runtime smoke 和 P7 验收均已完成。

## 已打开范围

- MLF-7 现在作为独立 A2 follow-on 子项目存在：
  [README.zh.md](README.zh.md)。
- 阶段计划、任务簇、展开后的派发队列、inventory、contract、验收记录和父级
  archive 注册均存在。
- 父级导航会把后续 Agent 指向本包，而不是继续扩展 MLF-6。
- runtime 现在包含
  [structural_consequence_system.h](../../../../../../src/systems/combat/structural_consequence_system.h)，
  并注册在 `StructuralFailureUpdate` 之后。
- 聚焦 C++ 验证已覆盖 no-breakup、各断裂模式、multi-axis loss state、幂等、ECS
  同 tick bridge 行为和链路关联 `platform_consequence` 诊断。
- 本切片的更广 Python smoke 和相邻 engagement/facade/binding/tool lane 均已通过。

## 当前成熟度矩阵

| 区域 | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| P0 boundary/index | complete | README、任务簇、当前状态、派发队列、验收记录、父级 archive 注册、父级导航 | 导航存在 |
| P1 consequence inventory | complete | [后果盘点](missile_lethality_secondary_consequence_coupling_consequence_inventory_20260618.zh.md) | 只授权初始 bridge |
| P2 coupling contract | complete | [耦合契约](missile_lethality_secondary_consequence_coupling_contract_20260618.zh.md) | 工程代理；没有 calibration/Pk 权威 |
| Runtime bridge | complete / focused-pass | [structural_consequence_system.h](../../../../../../src/systems/combat/structural_consequence_system.h)、[simulation_kernel_systems.cpp](../../../../../../src/core/engine/simulation_kernel_systems.cpp) | 只写批准的 aircraft/platform/loss-state 表面 |
| Diagnostics / events | complete / event-pass | `StructuralBreakupEvent` 父 id 保存在 `StructuralBreakupState::last_breakup_event_id`；`PlatformConsequenceEvent` 记录 before/after consequence delta | 仅诊断事件；无 Pk、debris 或直接生命周期 |
| Focused validation | complete / focused-pass | [test_structural_failure_system.cpp](../../../../../../src/tests/test_structural_failure_system.cpp)、`structural_consequence` CTest | 覆盖 bridge、零误报和链路关联后果诊断 |
| Broad regression | complete / broad-pass | `PYTHONPATH=build-workshop:. pytest -q tests/runtime/air_combat/ tests/world_batch/` -> 447 passed | 未观察到 MLF-7 更广 runtime regression |
| 相邻 event/facade 测试 | complete / pass | `PYTHONPATH=build-workshop:. pytest -q tests/runtime/engagement/ tests/runtime/facade/ tests/runtime/bindings/ tests/tools/test_structural_breakup_export.py` -> 160 passed | 覆盖 P4 触及的 event-store/facade/binding 边界 |
| Acceptance | complete | 验收记录已更新 completed/held 项 | 仅按工程代理 MLF-7 切片验收 |

## 进入事实

- MLF-6 提供 `StructuralBreakupState` 和 `StructuralBreakupEvent` 事实，但有意不改变
  `structural_integrity`、飞行动力学或失能状态。
- A8 提供 accepted 证据，证明飞机损伤可通过维护中的动力、飞行、燃油、火灾、传感和
  触地路径传播。
- `AircraftDamageStateUpdate` 当前早于 `StructuralFailureUpdate` 运行；MLF-7 必须显式处理
  这一执行顺序约束。

## 残余登记

| ID | 描述 | 严重度 | 状态 |
| --- | --- | --- | --- |
| MLF7-R1 | 初始 bridge 的 P1 consequence inventory 已完成。 | medium | closed |
| MLF7-R2 | 初始 bridge 的 coupling contract 和批准写入面已定义。 | high | closed |
| MLF7-R3 | 执行顺序已决定：bridge 在 `StructuralFailureUpdate` 后运行；下游物理投影下一 tick 消费。 | high | closed |
| MLF7-R4 | runtime bridge 和聚焦 C++ 测试已存在且通过。 | high | closed |
| MLF7-R5 | 残骸/碎片生命周期仍后置到 MLF-8。 | medium | intentionally held |
| MLF7-R6 | Pk / 统计趋势权威仍后置到 MLF-9。 | medium | intentionally held |
| MLF7-R7 | 专门 structural-consequence event / diagnostic export 已为实质后果 delta 记录链路关联 `platform_consequence` 事件。 | medium | closed |
| MLF7-R8 | 本切片的更广 `tests/runtime/air_combat/` 和 `tests/world_batch/` smoke 已通过。 | medium | closed |

## 建议下一步

1. 保持 MLF-8 残骸/碎片生命周期、MLF-9 Pk / 统计趋势投影和 MLF-10 校准门为显式后续。
2. MLF-8/9/10 只能作为后续独立子项目打开；除非发现 regression 或权威边界修正，不继续扩展已归档的 MLF-7 包。

## 必须拒绝的声明

- [x] MLF-7 runtime 行为仅限已批准的 structural consequence bridge。
- [x] 没有直接坠毁/删除规则。
- [x] 没有残骸/碎片生命周期。
- [x] 没有 Pk 权威。
- [x] 没有真实武器、stock AIM-120C、MQ-9 或 F-16C 杀伤权威。
- [x] 没有海军或地面结构后果模型。
