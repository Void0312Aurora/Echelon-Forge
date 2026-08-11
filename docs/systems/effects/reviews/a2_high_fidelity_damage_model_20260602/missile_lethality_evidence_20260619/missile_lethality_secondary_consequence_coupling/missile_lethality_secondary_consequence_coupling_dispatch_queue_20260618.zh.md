# MLF-7 二次后果耦合 — 派发队列

状态：`2026-06-18` 派发队列已更新。`MLF-7A-X1` 到 `MLF-7H-C1`
均已针对 accepted 工程代理 MLF-7 切片关闭。

父任务簇：
[missile_lethality_secondary_consequence_coupling_task_clusters_20260618.zh.md](missile_lethality_secondary_consequence_coupling_task_clusters_20260618.zh.md)

当前状态：
[missile_lethality_secondary_consequence_coupling_current_status_20260618.zh.md](missile_lethality_secondary_consequence_coupling_current_status_20260618.zh.md)

## 队列摘要

| Packet | Cluster | Suggested owner | 派发状态 | 允许写入面 | 验证 / 返回门 |
| --- | --- | --- | --- | --- | --- |
| `MLF-7A-X1` | `MLF-7A Boundary And Index` | main thread | complete | 子项目文档和父 README 链接 | P0 文档存在，父级导航链接 MLF-7 |
| `MLF-7B-X1` | `MLF-7B Consequence Inventory` | main thread | complete | `missile_lethality_secondary_consequence_coupling_consequence_inventory_20260618.md` | Inventory 列出事实输入、候选写入、执行顺序、诊断、测试和禁止直接写入面 |
| `MLF-7C-X1` | `MLF-7C Coupling Contract` | main thread | complete | `missile_lethality_secondary_consequence_coupling_contract_20260618.md` | Contract 将每个断裂模式映射到有边界后果写入和 cadence |
| `MLF-7D-W1` | `MLF-7D Runtime Bridge` | main thread | complete / focused-pass | `src/systems/combat/structural_consequence_system.h`、注册文件、聚焦 C++ 测试 | runtime 写入引用 P2 contract 行，并通过 no-false-positive 聚焦测试 |
| `MLF-7E-W1` | `MLF-7E Loss-State And Consequence Diagnostics` | main thread | complete / event-pass | event-store interface/store、`StructuralBreakupState`、聚焦 C++ 测试 | 诊断显示链路关联的后果 delta 和失能状态转移 |
| `MLF-7F-T1` | `MLF-7F Focused Validation` | main thread | complete / focused-pass | `src/tests/test_structural_failure_system.cpp`、`CMakeLists.txt` | 命名 lane 覆盖各断裂模式、no-breakup、幂等和直接生命周期拒绝 |
| `MLF-7G-C1` | `MLF-7G Regression Smoke` | main thread | complete / broad-pass | 测试执行记录；无需 oracle update | 更广 lane green：447 passed |
| `MLF-7H-C1` | `MLF-7H Acceptance And Archive Boundary` | main thread | complete / archived | docs/index 和父级 archive 注册表 | 验收包同步状态、残余、父级导航和 archive 边界 |

## 派发规则

- `MLF-7A-X1` 到 `MLF-7H-C1` 已针对本 accepted 切片关闭。
- 后续工作应打开 MLF-8/9/10 packet；除非发现 MLF-7 regression，不继续扩展 MLF-7。
- 遵循 [Subagent 使用规范](../../../../../../engineering/automation/standards/subagent_usage_policy.zh.md)。

## Packet Briefs

### `MLF-7B-X1` — 后果盘点

派发状态：complete。

目标：产出 docs-only inventory，让 P2 能决定 MLF-7 到底读什么、写什么、什么绝对不能碰。

Worker prompt：

```text
你在 /home/void0312/Workshop/CMO 处理 MLF-7B Consequence Inventory。
不要修改 runtime code。不要创建 debris/wreck、Pk、weapon-specific、training-reward
或 direct-delete 行为。先阅读 MLF-7 README、current status、task clusters 和 dispatch
queue。然后写入 missile_lethality_secondary_consequence_coupling_consequence_inventory_20260618.md。

盘点：
- MLF-6 事实输入：
  src/components/combat/structural_failure.h
  src/runtime/contracts/engagement_contracts.h
  src/core/engine/engagement_event_types.h
  src/runtime/facade/runtime_facade_types.h
  tools/diagnostics/structural_breakup_export.py
- 候选 maintained 后果表面：
  src/components/domains/air/combat/damage_air.h
  src/components/combat/common/damage_common.h
  src/components/physics/performance.h
  src/components/physics/dynamics.h
  src/systems/combat/damage_system_air.h
  src/systems/combat/damage_system_common.h
  src/core/engine/simulation_kernel_systems.cpp
- 必须保留的既有证据：
  docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_structural_failure/README.zh.md
  docs/systems/effects/reviews/damage_effect_chain_20260608/README.zh.md

Inventory 必须包含：
- MLF-7 可能读取的每个 StructuralBreakupState 字段和 helper；
- MLF-7 可能用于链路关联或诊断的每个 StructuralBreakupEvent 字段；
- MLF-7 可能写入的每个候选 AircraftDamageState、PlatformDamageState、Health、
  FlightModel、Propulsion、Mass、Sensor 或 event/probe 表面；
- AircraftDamageStateUpdate 和 StructuralFailureUpdate 的当前执行顺序；
- 禁止直接写入面，包括实体删除、debris/wreck 生命周期、Pk、stock weapon truth
  和 training reward change。

返回必须包含 status、touched files、commands/outcomes、remaining paths、
behavior risks 和 integration notes。
```

允许写入：

- `missile_lethality_secondary_consequence_coupling_consequence_inventory_20260618.md`
- Inventory 完成后，可选只改本派发表和
  [current status](missile_lethality_secondary_consequence_coupling_current_status_20260618.zh.md)
  的状态行。

验证：

```bash
git diff --check -- docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_secondary_consequence_coupling
```

收口门：inventory 存在，所有引用路径要么可链接、要么以普通文件名记录；P2 已有足够信息决定批准写入面。

### `MLF-7C-X1` — 耦合契约

派发状态：complete。

目标：code 前定义批准的后果映射。该 packet 仍然是 docs-only。

必须决策：

- 将 `wing_loss`、`tail_loss`、`engine_detach`、`fuselage_rupture` 和
  `multi_axis` 映射到有边界 consequence delta。
- 说明 MLF-7 是否写入 `AircraftDamageState::structural_integrity`、其他飞机损伤标量、
  `PlatformDamageState` capabilities 或 loss-state 输入。
- 决定 cadence：接受经测试的一 tick 延迟，或显式调整 pipeline 顺序并配测试。
- 说明 no-breakup 行为和零误报守卫。
- 如涉及失能升级，写清 `MissionKill`、`MobilityKill`、`SensorKill`、`Lost` 规则。

允许写入：

- `missile_lethality_secondary_consequence_coupling_contract_20260618.md`
- contract review 后的状态行。

验证：

```bash
git diff --check -- docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_secondary_consequence_coupling
```

收口门：7D 计划的每个 runtime 写入都有 contract 行授权。

### `MLF-7D-W1` — Runtime Bridge

派发状态：complete / focused-pass。

目标：把已归档 MLF-6 断裂事实窄桥接到 P2 批准的 maintained consequence surface。

可能写入面，取决于 P2：

- `src/systems/combat/structural_consequence_system.h` 或批准的相邻 combat-damage 文件。
- `src/core/engine/simulation_kernel_systems.cpp`。
- 聚焦 C++ 测试，优先放在 `src/tests/test_structural_failure_system.cpp`
  或新的 MLF-7 专用测试文件。

必须返回证据：

- 从 `StructuralBreakupState` 或 `StructuralBreakupEvent` 读取的每个字段。
- 每个写入字段，以及授权它的 P2 contract 行。
- 执行顺序行为和测试证据。
- 确认没有加入 debris entity lifecycle、Pk projection 或 direct entity deletion。

### `MLF-7E-W1` — 后果诊断

派发状态：complete / event-pass。

目标：让 handoff 可见，但不创造新权威。

可能写入面，取决于 P2/P4：

- 已承载 engagement diagnostics 的 event-store/facade 表面。
- `tools/diagnostics/air_combat_weapon_employment_process_probe.py` 或窄相邻诊断 probe。
- `tests/runtime/air_combat/` 或 `tests/tools/` 下的 targeted Python tests。

收口门：诊断可显示断裂事实、后果 delta、如有的失能状态转移、`chain_id` 和因果连续性，
且不靠 last-event guessing。已由链路关联 `platform_consequence` 聚焦测试满足。

### `MLF-7F-T1` — 聚焦验证

派发状态：complete / focused-pass。

目标：增加 MLF-7 行为的命名聚焦测试。

必须覆盖：

- no-breakup 产生零 MLF-7 consequence delta；
- 每个 single mode 产生 P2 批准的有边界后果；
- multi-axis 行为符合 P2 contract；
- 上游不可逆 breakup state 不产生重复 delta，除非 P2 明确授权 cadence；
- direct entity lifecycle 仍不存在。

7D 选定 test lane 后再确定验证命令。预期形状：

```bash
cmake --build build-workshop -j 2
ctest --test-dir build-workshop -R structural --output-on-failure
```

### `MLF-7G-C1` — 回归 Smoke

派发状态：complete / broad-pass。

目标：跑更广维护中 smoke lane，并区分 inherited failure 和 MLF-7 regression。

预期命令：

```bash
PYTHONPATH=build-workshop:. pytest -q tests/runtime/air_combat/ tests/world_batch/
```

收口门：已由
`PYTHONPATH=build-workshop:. pytest -q tests/runtime/air_combat/ tests/world_batch/`
-> 447 passed 满足。

### `MLF-7H-C1` — 验收和归档边界

派发状态：complete。

目标：收口 package，但不夸大权威。

允许写入：

- MLF-7 README/status/task-cluster/dispatch/acceptance docs。
- A2 和 air-combat 父级导航文档。
- 已按用户明确请求完成 archive 移动；闭合包现在由父级注册表负责发现。

收口门：accepted/retained/deferred 边界同步，MLF-8/9/10 residual 仍显式，
且 package 不声明真实世界杀伤、Pk、weapon-specific truth 或 debris/wreck lifecycle。

## Worker Packet Checklist

每个 worker response 必须包含：

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

runtime packet 还必须引用授权每个后果写入的 P2 contract 行。
