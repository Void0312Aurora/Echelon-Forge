# 域分离大拆分当前状态

状态：`2026-06-10`，DS-S1-C / DS-M1 / DS-T1-A 分发后的集成状态；子项目 active，尚未 accepted。

父级：[域分离大拆分](README.zh.md)

## 摘要

审计已经提升为可执行子项目。直接大拆分是当前规划框架：拆分 Air/Naval/Ground 混合热点前，不要求先完成 Naval 示范域。

2026-06-09 派发表中命名的主要 combat/model ownership hotspot 已有实现证据：
component ownership、combat damage system、naval logistics extraction、effects
routing 和 sensor routing 均已落地并通过聚焦验证。子项目仍未 accepted，因为更宽的
architecture gate 仍在既有/无关表面失败，且 Air propulsion helper dependency 仍需在最终
G2/G4 收口前转成命名 adapter 或显式保留决定。

DS-P0-B 已产出当前热点的只读 ownership inventory。该清单只是诊断事实收集，不是实现验收，也不会单独改变任何任务簇状态。

## 当前证据表

| Surface | 当前 owner state | 证据 | 状态 | 下一门槛 |
| --- | --- | --- | --- | --- |
| 子项目文档 | owner surface 已创建 | `docs/task/review/domain_separation_split/**` | pass | DS-C1-A / DS-C1-B 分发 |
| 父级 review index | 已链接 | `docs/task/review/README*` | pass | DS-D1-A 期间保持同步 |
| Air runtime systems | canonical Air owner 加 compatibility wrappers | `src/systems/air/**`, `src/components/air/**`，旧 physics/tuning wrappers | pass | Air propulsion helper dependency 仍需最终 adapter/保留决定 |
| Combat damage data | domain-owned header 加 compatibility umbrella | `src/components/combat/{common,air,naval,ground}/damage_*.h`；`src/components/combat/damage.h` | pass | DS-S1-A system split |
| Combat damage ECS | domain-owned system headers 加 compatibility umbrella | `src/systems/combat/damage_system_{common,air,naval,ground}.h`；`src/systems/combat/damage_system.h` | pass | 继续跟踪 compatibility umbrella 保留理由 |
| Weapon data | domain-owned header 加 compatibility umbrella | `src/components/combat/{common,air,naval,ground}/weapon_*.h`；`src/components/combat/weapon.h` | pass | 后续簇迁移 direct include |
| Naval logistics | Naval underway resupply 由 `systems/naval` 拥有 | `src/systems/naval/naval_logistics_system.h`；`src/systems/systems/logistics_system.h`；`src/core/engine/simulation_kernel_systems.cpp` | pass | 更宽的 Air propulsion helper residual 另行处理 |
| Effects model | generic router 加 Air/Naval/Ground owner path | `src/models/weapons/detail/default_effects_domain_routing_detail.inc`；`src/models/air/default_effects_air_domain.h`；`src/models/naval/default_effects_naval_domain.h`；`src/models/ground/default_effects_ground_domain.h` | pass | Naval/Ground 路径仅为 placeholder |
| Sensor model | generic sensor 通过 Naval adapter 路由 ship-specific 读取 | `src/models/systems/default_sensor_model.cpp`；`src/models/naval/naval_sensor_maritime_adapter.h` | pass | Acoustic model 的 `ShipPlatform` 访问不属于 DS-M1-B |
| Architecture guards | 已新增聚焦 domain split guard | `tests/architecture/structural_boundaries/test_structural_guardrails.py` | partial | 聚焦 selector 通过；更宽既有 architecture selector 仍失败 |

## DS-P0-B 清单

本节记录 2026-06-09 工作树中通过只读 `rg` / 文件检查得到的热点事实。它只指出可能的 target owner 与下一任务簇，不证明任何拆分已经实现或验收。

| Hotspot | Target owner | Current coupling | Direct evidence | Recommended next cluster |
| --- | --- | --- | --- | --- |
| `src/components/combat/damage.h` | Common damage primitive，加 Air/Naval/Ground component-owned header。 | `DamageComponent`、`Hitbox`、`ComponentDamageState`、`SystemHealth`、`PlatformDamageState` 与 Air-specific vulnerability/state/baseline 类型仍在同一 generic header。Naval flooding 被嵌入 `PlatformDamageState`；Ground damage 在此无 owner 类型。 | `rg` 显示 `AircraftVulnerabilityEvidenceRow` 在第 118 行，`AircraftVulnerabilityProfile` 第 170 行，`SystemHealth` 第 230 行，`ComponentDamageState` 第 236 行，`PlatformDamageState` 第 270 行，`flooding_severity` 第 275 行，`ongoing_hull_breach` 第 277 行，`AircraftDamageState` 第 284 行，`AircraftDamageBaseline` 第 704 行，`clamp_aircraft_damage_state` 第 727 行，`apply_aircraft_damage_state_to_platform` 第 794 行。该 header 中未出现 `GroundDamage` 或 ground-owned damage 类型。 | 先执行 `DS-C1-A`；下游 consumer 等待拆分后的公开 surface。 |
| `src/systems/combat/damage_system.h` | Common fuze / event routing，加 Air/Naval/Ground domain-owned update system 或 adapter。 | 单个 header 同时 include `components/combat/damage.h`、`components/combat/weapon.h`、`components/naval/ship_platform.h`、physics、logistics、sensor、EW 和 effects interface。单个 `register_damage_system` 同时拥有 common `ProximityFuze`、Air `AircraftDamageStateUpdate` 和 Naval `NavalDamageStateUpdate`；没有 Ground update path。 | `rg` 显示 naval include 在第 19 行，`register_damage_system` 第 1171 行，`ProximityFuze` 第 1172 行，`AircraftDamageStateUpdate` 第 1690 行并由 `UnitType::Aircraft` / `UnitType::C2Node` gate，`NavalDamageStateUpdate` 第 1840 行并绑定 `ShipPlatform`。Air helper block 包含 structural envelope、sensor、fuel leak、cascade 与 component dependency consumer，范围约第 758-1124 行。 | `DS-S1-A`，但要等 `DS-C1-A` 稳定公开 component surface。 |
| `src/components/combat/weapon.h` | Common weapon profile/runtime、Air release state、Naval weapon system state，以及未来 Ground weapon owner shell。 | `WarheadProfile`、`FuzeProfile`、`Missile` 名义上是 generic，但 seeker/guidance/fuze runtime 仍偏 air-shaped。`PilotWeaponReleaseState` 与 naval weapon 类型在同一个 generic 文件；Ground weapon ownership 缺失。 | `rg` 显示 `WarheadProfile` 第 14 行，`FuzeProfile` 第 24 行，`Missile` 第 71 行，`MissileSharedLaunchRuntimeState` 第 164 行，`PilotWeaponReleaseState` 第 296 行，`NavalWeaponType` 第 306 行，`NavalWeaponMountDefinition` 第 313 行，`NavalWeaponSystem` 第 332 行。该 header 中未出现 `GroundWeapon` 或 ground-owned weapon 类型。 | `DS-C1-B`。 |
| `src/systems/systems/logistics_system.h` | Common/base logistics，加 Air fuel-consumption ownership 或 adapter，并把 Naval underway resupply 放入 `systems/naval`。 | `FuelConsumption` 仍在 generic platform-system 文件里，但 include `systems/air/propulsion_system.h`，并调用 `flight_dynamics::propulsion_fuel_flow_kg_per_s`。`ResupplyLogic` 是 common/base loop，但注释和条件含 plane/ground 假设，且 `ResupplyState` 已带 naval 字段。`NavalUnderwayResupply` 是 naval ECS body，却仍在 generic 文件。 | `rg` 显示 Air include 第 16 行，`FuelConsumption` 第 20 行，`MassUpdate` 第 64 行，`LogisticsAction` 第 90 行，`ResupplyLogic` 第 111 行，`NavalUnderwayResupply` 第 189 行。`components/systems/logistics.h` 在第 57-88 行定义 `NavalStores`、`ResupplyKind::NavalUnderway` 与 `NavalResupplyStage`。 | `DS-S1-C` 负责 naval extraction；`DS-S1-B` 需验证 Air fuel-flow dependency / wrapper policy。 |
| `src/models/weapons/default_effects_model.cpp` 与 `detail/*.inc` | Common effects router，加 Air/Naval/Ground model-owned detail implementation。 | 主模型 include `components/combat/damage.h`，并只通过 `is_structured_damage_air_target` 进入 structured damage；非 structured target 走 legacy health/randomized fallback。detail 文件由 common geometry/warhead helper 与 Air platform resolution 组成；没有 Naval/Ground detail path。 | `rg --files` 列出 10 个 detail fragment。主文件在第 62 行 include `default_effects_air_platform_resolution_detail.inc`。`is_structured_damage_air_target` 第 32-42 行要求 `UnitType::Aircraft` / `UnitType::C2Node`、`HitboxConfig`、`SystemHealth`、`PlatformDamageState`。对主文件和 detail fragment 运行 `rg 'Naval|Ground|Ship|ship|naval|ground'` 无匹配。Air 证据集中在 `default_effects_state_detail.inc` 的 `processed_air_systems` / Air hit flags，以及 `default_effects_air_platform_resolution_detail.inc` 的 `AircraftDamageState`、`AircraftVulnerabilityProfile` 与 platform consequence blocks。 | `DS-M1-A`，等 `DS-C1-A` 与 `DS-S1-A` 稳定 shared damage/effects surface 后推进。 |
| `src/models/systems/default_sensor_model.cpp` | Common sensor model，加 Naval maritime adapter/router 处理 ship-specific state。 | generic sensor model 直接 include `components/naval/ship_platform.h`，读取 `ShipPlatform` 生成 maritime state，用 `UnitType::Ship` 触发 sea clutter，并读取目标舰艇高度做 radar horizon。 | `rg` 显示 naval include 第 5 行，`maritime_state_for` 中 `entity.get<ShipPlatform>()` 第 143 行，ship sea-state 字段第 149-151 行，`target_is_ship` / `UnitType::Ship` 第 173-174 行，目标 `ShipPlatform` 高度使用第 359-360 行。 | `DS-M1-B`。 |
| Air partial candidate：`src/systems/air`、`src/components/air`、旧 wrapper | `systems/air` / `components/air` 作为 canonical Air runtime/tuning owner；旧 physics 路径只保留 compatibility wrapper。 | Air owner 目录存在，并已被 `simulation_kernel_systems.cpp`、`content/unit_definition.h`、Python bindings 和 model factory 直接使用。旧 `systems/physics/{aero_state,aerodynamics,control,propulsion}_system.h` 与 `components/physics/flight_dynamics_tuning.h` 是 include-only wrapper。但该候选仍是 partial：Air systems 仍通过 `components/combat/damage.h` 获取 `AircraftDamageState`，且 generic physics/logistics 文件仍 include `systems/air/propulsion_system.h`。 | `rg --files` 列出 `src/systems/air/{aero_state_system.h,aerodynamics_system.h,control_system.h,propulsion_system.h}` 与 `src/components/air/flight_dynamics_tuning.h`。wrapper 检查显示旧 air physics header 只 include 新 Air header。include 使用显示 `simulation_kernel_systems.cpp` 第 36-44 行直接 include Air headers，并在第 182-187 行注册 Air systems；`systems/air/aerodynamics_system.h` 与 `propulsion_system.h` 仍 include `components/combat/damage.h`。 | 现在验证 `DS-S1-B`；与 `DS-C1-A` 协调 Air damage type include dependency。 |

## 已知工作树风险

上方 DS-P0-B inventory 是实现簇落地前的 `2026-06-09` 历史快照。它不应被重新理解为 DS-S1-C / DS-M1 之后的当前代码状态。后续追踪应按 pathspec 验证 domain-split 路径，并继续把无关 review/test archive 变动排除在验收判断之外。

## 立即下一步

1. 决定 generic physics/logistics 中剩余 Air propulsion helper dependency 是转成命名 adapter，还是作为显式 retained compatibility dependency 保留。
2. 将更宽 architecture 失败作为 held residual 处理，直到既有 direct-sim allowlist 和 Windows snippet link failure 在本拆分之外解决。
3. Naval/Ground effects 路径只作为 placeholder ownership shell 记录，不宣称完整 domain damage fidelity。
4. 上述 residual 关闭或被后续包显式接受后，再重跑完整 acceptance。

## 状态说明

- `active`：执行表面存在且正在准备。
- `planned`：有限任务簇存在但未开始。
- `partial`：已有实现候选，但尚未 accepted。
- `held`：已知热点，尚无验收拆分。
- `pass`：任务簇满足 closure gate。
- `accepted`：子项目级验收门槛满足。
