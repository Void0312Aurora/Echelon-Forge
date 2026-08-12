# MLF-7 二次后果耦合 — 任务簇

状态：`2026-06-18`，面向 [README.zh.md](README.zh.md) 的有限任务簇计划。
工程代理 MLF-7 验收切片的 P0-P7 均已完成；MLF-8/9/10 仍是显式后续。

## 边界决策

本子项目只推进 MLF-7：把 MLF-6 的断裂事实耦合到维护中的飞机后果表面。它可以消费
`StructuralBreakupState` 和 `StructuralBreakupEvent`；只能写入 P2 批准的后果表面。

它不得：

- 创建残骸/碎片实体或分离 ECS 实体；这是 MLF-8。
- 实现 Pk / 统计趋势；这是 MLF-9。
- 声明真实武器、AIM-120C、MQ-9、F-16C、海军或地面杀伤真值。
- 重开已封存的 MLF-1 到 MLF-5 归档包。
- 在维护中的平台损伤/失能逻辑之外新增直接 kill 或直接 `e.destruct()` 路径。
- 把已归档的 MLF-6 验收证据当成 MLF-7 实现证据。

## 有限任务簇列表

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `MLF-7A Boundary And Index` | main thread | n/a | 创建 MLF-7 子项目入口：README、任务簇、当前状态、派发队列、验收记录、archive 占位和父级导航。 | `docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_secondary_consequence_coupling/**`、父 README | runtime edits、实现声明 | `git diff --check -- docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_secondary_consequence_coupling docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/README*.md docs/domains/air/README*.md` | 后续 Agent 不依赖聊天历史即可恢复 MLF-7；P0 范围和非目标明确 | first, serial | 1 | complete |
| `MLF-7B Consequence Inventory` | main thread | n/a | 盘点 MLF-7 输入、候选写入面、执行顺序和禁止直接写入路径。 | `missile_lethality_secondary_consequence_coupling_consequence_inventory_20260618.md` | runtime edits | 引用路径存在；inventory 覆盖 `StructuralBreakupState`、`StructuralBreakupEvent`、`AircraftDamageState`、下游消费者、`PlatformDamageState`、`Health` 和禁止写入面 | inventory 完成；P2 可以决定批准的耦合 | after 7A; serial | 1 | complete |
| `MLF-7C Coupling Contract` | main thread | n/a | 定义 `wing_loss`、`tail_loss`、`engine_detach`、`fuselage_rupture` 和 `multi_axis` 到后果的映射；决定节拍和失能阈值。 | `missile_lethality_secondary_consequence_coupling_contract_20260618.md` | runtime edits、校准声明 | 文档审查；每个模式都有明确有边界效果和 no-breakup 守卫；记录注册顺序选择 | code 前先验收契约 | after 7B; serial | 2 | complete |
| `MLF-7D Runtime Bridge` | main thread | n/a | 实现从 `StructuralBreakupState` 到批准飞机后果状态的有边界 bridge。 | `src/systems/combat/structural_consequence_system.h`、`src/core/engine/simulation_kernel_systems.cpp`、聚焦测试 | debris entities、Pk、stock lethality、直接删除 | no-breakup、wing loss、multi-axis、幂等、same-tick bridge 的聚焦 C++ 测试；build 通过 | 只按 P2 契约更新批准表面；无误报 | after 7C; serial | 3 | complete / focused-pass |
| `MLF-7E Loss-State And Consequence Diagnostics` | main thread | n/a | 让后果 delta 和失能状态转移以稳定链路可见。 | event-store interface/store、`StructuralBreakupState`、聚焦 C++ 测试 | 训练奖励改动、Pk 投影 | 测试显示从 MLF-6 事实到后果诊断的 `chain_id` 连续性 | 诊断能回答发生了什么后果以及原因，不依赖 last-event 猜测 | after 7D | 2 | complete / event-pass |
| `MLF-7F Focused Validation` | main thread | n/a | 增加命名聚焦 lane，覆盖 no-breakup、断裂后果、multi-axis、不可逆状态、失能升级和无直接实体生命周期。 | `src/tests/test_structural_failure_system.cpp`、`CMakeLists.txt` | 大范围 oracle 重写、训练改动 | `ctest --test-dir build-workshop -R 'structural_consequence|structural_failure' --output-on-failure` | 聚焦 lane 证明初始 MLF-7 行为和零误报 | after 7D | 2 | complete / focused-pass |
| `MLF-7G Regression Smoke` | main thread | n/a | 跑更广 air_combat/world_batch lane，区分 inherited residual 和 MLF-7 regression。 | test execution；只有有证据时才更新 obsolete oracle | 新功能 | `PYTHONPATH=build-workshop:. pytest -q tests/runtime/air_combat/ tests/world_batch/` -> 447 passed | 更广 lane 全绿或记录为 inherited/non-MLF-7 | after 7E+7F; serial | 2 | complete / broad-pass |
| `MLF-7H Acceptance And Archive Boundary` | main thread | n/a | 汇总证据、更新当前状态和父级导航、记录 MLF-8/9/10 残余并准备 archive 边界。 | docs/index only，除非明确要求 archive | 未授权 archive 移动、过度声明 | docs diff check；记录聚焦和更广命令 | accepted 包真实且有边界 | after 7G; serial | 1 | complete |

## 派发规则

- 每个 worker packet 必须对应上方唯一任务簇。
- `MLF-7B` 和 `MLF-7C` 是 runtime 写入前的强制前置。
- 不允许两个 worker 同时编辑同一个耦合表、事件契约或失能状态规则。
- `MLF-7D` 在契约之后串行执行。只有写集保持独立时，`MLF-7E` 和 `MLF-7F`
  才可并行。
- `MLF-7G` 和 `MLF-7H` 已针对本验收切片关闭。
- 如果某个簇超过 round cap，停止并重新划分范围，不要直接追加新 wave。
- 遵循 [Subagent 使用规范](../../../../../../engineering/automation/standards/subagent_usage_policy.zh.md)。

## Worker Packet 要求

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

runtime 簇还必须包括：

- 每个被读取的 `StructuralBreakupState` 或 `StructuralBreakupEvent` 字段。
- 每个被写入的 `AircraftDamageState`、`PlatformDamageState`、`Health`、
  `FlightModel` 或 `Propulsion` 字段，以及授权它的 P2 契约行。
- 执行顺序/节拍决策及测试证据。
- 确认未添加残骸实体生命周期、Pk 投影或直接删除规则。

## 验证计划

初始验证命令：

```bash
# Docs-only P0
git diff --check -- \
  docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_secondary_consequence_coupling \
  docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/README*.md \
  docs/domains/air/README*.md

# Runtime 实现阶段加入后
cmake --build build-workshop -j 2
ctest --test-dir build-workshop -R structural --output-on-failure
PYTHONPATH=build-workshop:. pytest -q tests/runtime/air_combat/ tests/world_batch/
```

## 验收标准

- [x] `MLF-7A`：子项目入口和父级导航存在。
- [x] `MLF-7B`：后果 inventory 完成。
- [x] `MLF-7C`：code 前先验收 coupling contract。
- [x] `MLF-7D`：runtime bridge 消费 MLF-6 事实并只写批准的后果表面。
- [x] `MLF-7E`：诊断显示链路关联的后果 delta。
- [x] `MLF-7F`：聚焦 lane 覆盖初始 bridge、no-breakup 守卫和无直接实体生命周期。
- [x] `MLF-7G`：更广 smoke 全绿或 residual 被分离。
- [x] `MLF-7H`：残余和 archive 边界同步。

## 残余地图

后续：

- MLF-8：残骸/碎片实体生命周期。
- MLF-9：Pk / 统计趋势投影。
- MLF-10：特定武器/平台校准门。

后置：

- 海军和地面结构后果。
- 真实世界杀伤权威。
