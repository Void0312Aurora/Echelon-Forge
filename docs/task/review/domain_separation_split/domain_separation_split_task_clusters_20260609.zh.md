# 域分离大拆分任务簇

状态：`2026-06-10`，面向 [域分离大拆分](README.zh.md) 的有限任务簇计划与进展台账。

## 边界决策

本子项目直接实现域分离审计提出的大拆分，不把 Naval 示范域作为前置门槛。拆分必须保持既有行为，除非某个任务簇明确记录并验证行为变化。

迁移期允许 compatibility wrapper，但不能把 wrapper 计作最终所有权，除非验收文档明确保留。可以引入 Ground-owned shell，但如果没有可执行 system 和测试，不得暗示完整 Ground runtime 成熟度。

## 有限任务簇列表

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DS-P0-A` | main thread | n/a | 创建持久子项目、状态、队列和验收表面。 | `docs/task/review/domain_separation_split/**`, `docs/task/review/README*` | 代码拆分、验收宣称 | Markdown inspection; `git diff --check` | 必需文件存在且 parent review index 已链接。 | First; serial | 1 | pass |
| `DS-P0-B` | diagnostics worker | n/a | 在代码编辑前生成 include/type ownership inventory。 | `docs/task/review/domain_separation_split/*current_status*` only | 重写审计基线 | `rg` inventory; no code edits | inventory 列出当前 generic 文件与目标 owner。 | After DS-P0-A; implementation 前可执行 | 1 | pass |
| `DS-C1-A` | implementation worker | n/a | 拆分 common combat damage struct/helper 与 Air/Naval/Ground-specific damage ownership。 | `src/components/combat/damage.h`, `src/components/combat/common/**`, `src/components/combat/air/**`, `src/components/combat/naval/**`, `src/components/combat/ground/**` | damage model 校准、新杀伤声明 | C++ build; architecture include guard | generic damage header 只含 common 或 compatibility include。 | After DS-P0-B; serial with DS-S1-A | 3 | pass |
| `DS-C1-B` | implementation worker | n/a | 拆分 combat weapon component ownership。 | `src/components/combat/weapon.h`, `src/components/combat/common/**`, `src/components/combat/air/**`, `src/components/combat/naval/**`, `src/components/combat/ground/**`, direct include users | weapon 行为重平衡、超出搬迁类型的 ammo schema 扩展 | C++ build; `rg` for naval types in generic header | Naval/Air/Ground weapon-only 类型位于 domain header 或声明 wrapper。 | After DS-P0-B; 不重叠时可与 DS-C1-A 并行 | 3 | pass |
| `DS-S1-A` | implementation worker | n/a | 将 combat damage ECS system 拆成 common routing 与 air/naval/ground update path。 | `src/systems/combat/damage_system.h`, `src/systems/combat/*damage*`, `src/core/engine/simulation_kernel_systems.cpp`, focused tests | 新 damage 机制、effects 大重写 | `cmake --build build-workshop --target ef_py -j2`; focused damage/runtime tests | common system 不再直接拥有 air/naval-only update logic。 | After DS-C1-A; serial | 4 | pass |
| `DS-S1-B` | implementation worker | n/a | 完成 Air runtime ownership migration 与 wrapper policy。 | `src/systems/air/**`, `src/components/air/**`, old `src/systems/physics/*` wrappers, old `src/components/physics/*` wrappers, source/manual README indexes | 过早删除 compatibility wrapper | C++ build; include-path `rg`; compatibility guard pytest | air-only system/tuning 的 canonical owner 为 `air`，旧路径仅为 wrapper。 | 已有 partial candidate；After DS-P0-A | 2 | pass |
| `DS-S1-C` | implementation worker | n/a | 从 generic platform systems 中抽出 naval underway resupply 等 naval-only 逻辑。 | `src/systems/systems/logistics_system.h`, `src/systems/naval/**`, registration entry points, focused naval runtime tests | naval survivability 扩展、补给真实性校准 | C++ build; focused naval tests; architecture guard | generic logistics 不再拥有 naval-only ECS system body。 | After DS-P0-B; 避免与 DS-S1-A registration edit 重叠 | 3 | pass |
| `DS-M1-A` | implementation worker | `gpt-5.4` / high | 为 weapon effects 增加 model-layer domain routing。 | `src/models/weapons/default_effects_model.cpp`, `src/models/weapons/detail/**`, `src/models/air/**`, `src/models/naval/**`, `src/models/ground/**`, effects interfaces if needed | lethality 校准、新公开 Pk 声明 | C++ build; focused effects/damage tests | effects model 通过 common/air/naval/ground path 路由，不把 air-only detail 藏在 generic 文件。 | After DS-C1-A and DS-S1-A | 4 | pass |
| `DS-M1-B` | implementation worker | `gpt-5.4` / high | 通过 domain adapter/router 移除 generic sensor model 对 ship-specific 状态的直接依赖。 | `src/models/systems/default_sensor_model.cpp`, `src/models/naval/**`, sensor interfaces/helpers, focused sensor tests | sensor fidelity 扩展、acoustic rewrite | C++ build; naval sensor tests; `rg` guard for `ShipPlatform` in generic sensor | generic sensor model 不再直接拥有 ship-only state access。 | After DS-P0-B; 避免与 model interface edits 重叠 | 3 | pass |
| `DS-T1-A` | test/architecture worker | n/a | 增加 domain-only 类型回流 generic 文件的 architecture guard。 | `tests/architecture/**`, `tests/runtime/**` focused collectors if needed | full test-suite 重组 | `python -m pytest -q <new guards>`; build smoke | guards 能捕捉本子项目命名的回归。 | implementation surface 稳定后执行 | 3 | partial |
| `DS-D1-A` | integration worker | n/a | 同步 docs/manual index 和 acceptance evidence。 | `docs/manual/**` affected entries, `src/**/README*`, this subproject docs, parent review README | 归档无关 review、宣称完整域成熟度 | Link/path inspection; `git diff --check` | 状态和证据与实现相符且不夸大。 | Last; serial | 2 | partial |

## 派发规则

- 不为本子项目创建新的 Codex 会话或线程。
- 每个 worker packet 必须精确映射到上表一个任务簇。
- 两个 worker 不得并行编辑同一个 public header、registration file、规范状态表或 acceptance line。
- component split 先于依赖其 public type 的 system/model split。
- acceptance 和 closure 簇串行执行。
- 任一簇超过 round cap 时，先停下重新划分范围，不直接追加开放 wave。
- 若使用本线程内 subagent 风格派发，遵循 [Subagent 使用规范](../../../standards/governance/subagent_usage_policy.zh.md)。

## Worker Packet 要求

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

## 验证计划

```bash
cmake --build build-workshop --target ef_py -j2
python -m pytest -q tests/architecture/compatibility_quarantine/test_guard_enforcement.py
python -m pytest -q tests/architecture/structural_boundaries
rg -n '#include "systems/physics/(aero_state_system|aerodynamics_system|control_system|propulsion_system)' src tests
rg -n '#include "components/physics/flight_dynamics_tuning' src tests
rg -n 'NavalWeapon(Type|MountDefinition|System)' src/components/combat/weapon.h
rg -n 'AircraftDamageState|AircraftVulnerability' src/components/combat/damage.h
git diff --check -- src tests docs/task/review/domain_separation_split docs/task/review/README.md docs/task/review/README.zh.md docs/manual
```

## 验收标准

- acceptance 文档要求的实现簇均为 `pass`，或明确转入 held residual。
- 聚焦 build 和 architecture gate 通过。
- 剩余 compatibility wrapper 均列出保留/弃用理由。
- 不因目录迁移或 ownership shell 宣称完整 Air/Naval/Ground 成熟度。

## 残余地图

Immediate:

- generic physics/logistics 对 Air propulsion helper 的依赖需要 named adapter 或明确 retained-dependency 决定。
- 更宽 architecture gate 仍因无关 direct-sim allowlist、binding-count assertion 和 Windows snippet link surface 失败。
- Naval/Ground effects path 仅为 ownership placeholder，不应被理解为完整 damage-fidelity implementation。

Follow-on:

- direct include cleanup 与 compatibility wrapper 的弃用/保留决定。
- Ground movement/sensing/fires/damage runtime 实现包。
- ownership split 稳定后的校准与真实性升级。
- compatibility wrapper deprecation cleanup。

Deferred:

- 完整域成熟度的公开能力声明。
- 非保持拆分兼容所必需的训练行为变化。
