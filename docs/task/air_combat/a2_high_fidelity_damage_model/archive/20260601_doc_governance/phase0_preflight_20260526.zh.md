# A2 Phase 0 预检审计 - 高真实度空战毁伤模型 - 2026-05-26

状态：`phase0 accepted / phase1 minimal patch started`。

结论：本轮已完成 Phase 0 的主要代码证据审计，并补齐 `A2-P0.6 PN miss-distance baseline`。`A2-P0.1` 到 `A2-P0.6` 可作为 Phase 1 设计输入，允许开展最小 HP-first bypass 反转和事件闭环实现。deterministic fuze 仍不放行。

## 执行边界

Phase 0 关闭后，允许 Phase 1 最小行为补丁，但仍禁止把生成式 hitbox、标量 `damage` 或 RNG hit roll 宣称为完整高真实度毁伤模型。

保持 held/deferred 的内容：

- 不改 `PlatformLossState` 枚举值；
- 不改 `NavalDamageStateUpdate` 的 `ShipPlatform` filter；
- 不实现 deterministic fuze；
- 不展开正式训练。

已允许且已开始的 Phase 1 最小补丁：

- structured aircraft / C2Node 跳过 legacy HP-first kill branch；
- live missile proximity fuze 记录 `EffectsEvent` 与 `DamageReport`；
- aircraft damage update 只同步 Aircraft/C2Node 的 damage-state flags 与 `Lost` 析构；
- legacy 非结构化目标保持 HP path。

Phase 2 最小补丁也已启动：用于证明不同 aircraft hitbox 能产生不同子系统后果。E-3 C2Node 以及 F-16、Su-35、MQ-9、MH-60R 已补 authored structured damage model；但这些仍是工程校准 hitbox，不等价于战斗部、引信、脆弱性/Pk 全高保真闭环。

## 审计命令

```bash
rg -n "PlatformLossState|loss_state|static_cast<.*PlatformLossState|static_cast<int>\([^\n]*(loss|Loss)|\blossState\b" src python gym_envs tests -S
rg -n "get_unit_health|is_unit_active|health\s*[<>=!]=|current_hp|mission_kill|mobility_kill|sensor_kill" gym_envs python tests/runtime tests/world_batch src/core/engine src/core/mission -S
rg -n "ShipPlatform|has_ship_platform|ship_platform" src/components src/models src/systems src/core src/content tests -S
rg -n "damage_model|hitboxes|protected_systems|armor_mm|airframe|length_m|wingspan_m|height_m" src/content examples/config/database/aircraft examples/config/database/weapons -S
rg -n "total_reward|kills_confirmed|hits_landed|Score\b|score->" src/models src/core src/systems src/components tests/runtime/air_combat tests/runtime/engagement -S
rg -n "proximity_min_dist_m|proximity_last_dist_m|fuse_distance|min_dist|miss_distance|guidance_max_lateral_g|terminal_seeker|seeker_has_valid_track" src tests/runtime/air_combat tests/runtime/engagement -S
```

## P0.1 PlatformLossState 审计

状态：`closed_for_design`。

关键证据：

- `src/components/combat/damage.h:33` 到 `src/components/combat/damage.h:39` 定义 `enum class PlatformLossState : int`，当前值为 `CombatCapable=0`、`MissionKill=1`、`MobilityKill=2`、`SensorKill=3`、`Lost=4`。
- `src/models/weapons/default_effects_model.cpp:116` 到 `src/models/weapons/default_effects_model.cpp:126`、`src/systems/combat/damage_system.h:163` 到 `src/systems/combat/damage_system.h:173` 使用 typed enum 赋值。
- `src/core/engine/simulation_kernel_damage_debug_api.cpp:23` 到 `src/core/engine/simulation_kernel_damage_debug_api.cpp:36` 将 loss state 转为字符串；`DamageReport` 对外暴露的是字符串字段。
- 定向 grep 未发现针对 `Lost=4` 的 raw integer 比较或 `static_cast<int>` 判定。

判定：

- `ForcedLanding` 不能插入到现有枚举中间导致 `Lost` 变号。
- 后续如需要 `ForcedLanding`，采用 append-only enum 值或 aircraft-only overlay state。
- Phase 1 不应改枚举；只允许消费现有 `MissionKill`、`MobilityKill`、`SensorKill`、`Lost`。

剩余风险：

- 文本 grep 不能证明外部存档或下游脚本没有依赖 raw int。若将来要序列化 enum int，必须新增契约测试。

## P0.2 health observer 审计

状态：`closed_for_design_with_compatibility_guard`。

关键证据：

- `src/core/engine/simulation_kernel_observation_api.cpp:161` 到 `src/core/engine/simulation_kernel_observation_api.cpp:163` 的 `is_unit_active()` 只返回实体是否有效。
- `src/core/engine/simulation_kernel_observation_api.cpp:242` 到 `src/core/engine/simulation_kernel_observation_api.cpp:249` 的 `get_unit_health()` 直接返回 `Health.current_hp/max_hp`，实体不存在时返回 `[0.0, 0.0]`。
- `src/core/mission/runtime/termination_runtime.cpp:28` 仍以 `inputs.health <= 0.0` 触发 crash health 终止。
- `gym_envs/scenario_loader/reward_runtime/objectives.py` 同时读取 `is_unit_active()` 与 `get_unit_health()` 作为 objective/reward 观测。
- `gym_envs/scenario_loader/execution_runtime/mainline.py`、`python/rl/runtime/world_batch/adapter.py`、`python/rl/tasking/bridge.py` 都把 active 状态作为运行时决策输入。
- 空战、engagement、world-batch 测试中存在大量对 `[100.0, 100.0]`、`[0.0, 0.0]`、`is_unit_active()` 的断言。

判定：

- Phase 1 不能简单删除或弱化 `Health`。
- 对 structured aircraft，`Health.current_hp` 应改为派生兼容读数，但迁移必须保持 `is_unit_active()` 与终止逻辑可解释。
- 如果平台只是 `MissionKill` 或 `SensorKill`，实体仍可 active；只有 `Lost` 或实体析构应使 `is_unit_active()` 为 false。
- 训练 reward 不应再依赖“每次命中连续扣 HP”作为真实毁伤信号，应改读 `DamageReport`、loss state 或 subsystem capability。

剩余风险：

- 旧训练曲线可能把 HP 当连续 shaping。Phase 1 需要明确 legacy HP path 与 structured aircraft path 的分流测试。

## P0.3 ShipPlatform filter 审计

状态：`closed_for_design`。

关键证据：

- `src/systems/combat/damage_system.h:130` 注册 `ecs.system<Health, PlatformDamageState, const ShipPlatform>("NavalDamageStateUpdate")`，飞机即使挂载 `PlatformDamageState` 也不会进入这个持续更新系统。
- `src/systems/naval/ship_motion_system.h`、`src/models/systems/default_acoustic_model.cpp`、`src/models/systems/default_sensor_model.cpp`、`src/systems/systems/data_link_system.h` 都有合法的 `ShipPlatform` 消费。
- `src/models/core/default_unit_factory.h:1223` 到 `src/models/core/default_unit_factory.h:1224` 只在 `def.has_ship_platform` 时挂载 `ShipPlatform`。

判定：

- 不应为了让飞机 damage tick 而移除 `NavalDamageStateUpdate` 的 `ShipPlatform` filter。
- Phase 1 推荐新增 aircraft-specific damage update，或抽出 shared helper 后分别注册 ship/aircraft 系统。
- 舰船推进缩放逻辑使用 `ship.max_speed_mps` 推导推力上限，不适合直接套给飞机。

剩余风险：

- `PlatformDamageState` 当前含有 `flooding_severity`、`ongoing_hull_breach` 等舰船语义字段。飞机可先复用核心 capability 字段，但 aircraft overlay state 会更清晰。

## P0.4 Aircraft content inventory

状态：`evidence_closed / content_gap_open`。

关键证据：

- `src/content/unit_definition.h:124` 到 `src/content/unit_definition.h:136` 定义 `Airframe`，包含 `length_m`、`wingspan_m`、`height_m`、`configuration`。
- `src/content/unit_definition.h:208` 已在 `UnitDefinition` 中持有 `HitboxConfig damage_model`。
- `src/content/unit_definition_loader.cpp:498` 到 `src/content/unit_definition_loader.cpp:508` 读取 airframe 几何。
- `src/content/unit_definition_loader.cpp:711` 到 `src/content/unit_definition_loader.cpp:739` 已能读取 authored `damage_model.hitboxes`。
- `src/models/core/default_unit_factory.h:1298` 到 `src/models/core/default_unit_factory.h:1308` 优先挂载 authored hitbox。
- `src/models/core/default_unit_factory.h:1309` 到 `src/models/core/default_unit_factory.h:1321` 在 `def.airframe.length_m > 0.0` 时生成默认 hitbox，并挂载 `SystemHealth` 与 `PlatformDamageState`。
- `src/models/core/default_unit_factory.h:1424` 到 `src/models/core/default_unit_factory.h:1465` 生成 Conventional / Flanker 两类默认 hitbox。

飞机内容清单：

| 文件 | 类型 | airframe | authored damage_model | 当前结构化路径 |
|----|----|----|----|----|
| `examples/config/database/aircraft/units/f16c_block50.json` | `Aircraft` | 有 | 有 | authored structured hitbox |
| `examples/config/database/aircraft/units/su35s_flanker_e.json` | `Aircraft` | 有 | 有 | authored structured hitbox |
| `examples/config/database/aircraft/units/mq9_reaper.json` | `Aircraft` | 有 | 有 | authored structured hitbox |
| `examples/config/database/aircraft/units/mh60r_mvp.json` | `Aircraft` | 有 | 有 | authored structured hitbox，直升机仍需 rotor/flight-control 更细建模 |
| `examples/config/database/aircraft/units/e3_sentry.json` | `C2Node` | 有 | 有 | authored structured hitbox |

修正结论：

- 早先 forward 文档中“飞机没有 hitbox”的判断需要修正。当前代码已经为多数带 airframe 的飞机生成基础 hitbox。
- 但是这只是 procedural fallback，不等价于高真实度 authored aircraft vulnerability。
- 更严重的问题仍是 `default_effects_model.cpp:143` 到 `src/models/weapons/default_effects_model.cpp:159` 的 HP-first bypass：lethal HP 命中会在几何逻辑前摧毁目标并 `return`。

判定：

- Phase 1 可以以 generated fallback 作为最小结构化入口；Phase 2 已补首批 authored aircraft hitbox，但文档和测试必须标明它仍不是全量高真实度 vulnerability evidence。
- `E-3_Sentry_AWACS`、`F-16C_Block50`、`Su-35S_Flanker-E`、`MQ-9_Reaper`、`MH-60R_MVP` 已补 airframe 与 authored damage model，不再是 HP-only。
- 后续 authored 内容优先级应转为：飞控/液压细节、结构 g-limit 与 flutter 边界、座舱/飞行员 overlay、战斗部 profile 和脆弱性/Pk 校准。

## P0.5 Score write-point 审计

状态：`closed_for_design_with_decoupling_required`。

关键证据：

- `src/models/weapons/default_effects_model.cpp:137` 到 `src/models/weapons/default_effects_model.cpp:140` 从 attacker 获取 `Score`。
- `src/models/weapons/default_effects_model.cpp:146` 到 `src/models/weapons/default_effects_model.cpp:155` 在 physical effects path 内直接写 `total_reward`、`hits_landed`、`kills_confirmed`。
- `src/core/engine/simulation_kernel_weapon_api.cpp:531` 在 launch path 写 `score->missiles_fired`。
- `src/core/engine/simulation_kernel_weapon_api.cpp:947` 到 `src/core/engine/simulation_kernel_weapon_api.cpp:948` 在 naval CIWS 命中分支写 `hits_landed` 与 `kills_confirmed`。
- `src/core/engine/simulation_kernel_observation_api.cpp:622` 到 `src/core/engine/simulation_kernel_observation_api.cpp:623` 将 `Score.total_reward` 暴露到 observation。
- `src/components/combat/scoring.h` 明确把 `Score.total_reward` 标为 RL accumulated reward。

判定：

- structured aircraft 的 physical effects model 不应继续直接写 RL reward。
- Phase 1 最小实现可以保留 legacy HP path 的历史行为，但 structured aircraft path 必须把 hit/kill 事实交给 `EffectsEvent` / `DamageReport` 或独立 scorer 消费。
- `missiles_fired` 属于 launch telemetry，可以先保留；kill reward 和 damage reward 必须从 effects authority 中迁出。

剩余风险：

- 完全移除 `Score` 写入会影响观测和旧测试。Phase 1 需要先做事件消费层或 compatibility scorer。

## P0.6 PN miss-distance baseline

状态：`closed_with_baseline`。

关键证据：

- `src/components/combat/weapon.h:35` 到 `src/components/combat/weapon.h:38` 已保存 `proximity_min_dist_m`、`proximity_last_dist_m`、`proximity_engaged`。
- `src/systems/combat/damage_system.h:69` 到 `src/systems/combat/damage_system.h:76` 更新最近距离。
- `src/systems/combat/damage_system.h:96` 到 `src/systems/combat/damage_system.h:123` 用 `min_dist/fuse_distance` 计算 `quality`、RNG `hit_prob` 与 effective damage。
- `src/interfaces/python/bindings_core.cpp` 的 `debug_get_missile_runtime_state` 已只读暴露 `proximity_min_dist_m`、`proximity_last_dist_m`、`proximity_engaged`。
- `tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase0_pn_miss_distance_baseline_matrix_tracks_engagement_geometries` 固定 head-on / tail-chase / beam / high-off-boresight 基线。

基线矩阵：

| 几何 | `truth_min_dist_m` | `proximity_min_dist_m` | `time_s` | 判读 |
|----|----:|----:|----:|----|
| head-on | 10.36 | 10.36 | 33.43 | 近炸可达，但结构交点依赖 hitbox/impact 几何 |
| tail-chase | 7446.37 | 7446.37 | 45.02 | 追尾不可达，能量不足明确 |
| beam | 501.30 | 501.30 | 43.53 | 横穿几何产生显著 miss distance |
| high-off-boresight | 0.02 | 0.02 | 33.67 | 可控结构命中，适合作为 Phase 1 live missile regression |

判定：

- deterministic fuze 继续 held/deferred。当前几何差异足够明显，说明不能在缺少 warhead/fuze/脆弱性校准时简单移除 RNG hit roll。
- Phase 1 最小行为代码已放行：仅限 HP-first bypass 反转、structured aircraft damage path、live missile event report、aircraft damage-state 同步。

建议 benchmark 矩阵：

| 几何 | 目标动作 | 观测 | 用途 |
|----|----|----|----|
| head-on | 直飞 / 轻机动 | min distance、hit outcome、time to detonation | 基础迎头可达性 |
| tail-chase | 直飞 / 加速 | min distance、energy state | 追尾能量不足和逃逸 |
| beam | 水平横穿 | min distance、LOS rate、achieved lateral accel | PN 横向机动压力 |
| high-off-boresight | 高初始夹角 | seeker lock、terminal track、min distance | 末端视场/制导边界 |

建议先补观测面：

- 在 `debug_get_missile_runtime_state` 暴露 `proximity_min_dist_m`、`proximity_last_dist_m`、`proximity_engaged`；
- 或新增只读 benchmark harness，在导弹析构前记录 min distance；
- 输出稳定 JSON/CSV，供 Phase 4 决策引用。

## Phase 0 总判定

| Gate | 状态 | 是否允许行为实现 |
|----|----|----|
| `A2-P0.1 PlatformLossState` | closed for design | 不单独放行 |
| `A2-P0.2 health observer` | closed with compatibility guard | 不单独放行 |
| `A2-P0.3 ShipPlatform filter` | closed for design | 不单独放行 |
| `A2-P0.4 aircraft content inventory` | evidence closed, content gap open | 不单独放行 |
| `A2-P0.5 Score write-point` | closed with decoupling required | 不单独放行 |
| `A2-P0.6 PN miss-distance baseline` | closed with baseline | 放行 Phase 1 最小补丁；Phase 4 继续 deferred |

当前允许推进：

- Phase 1 最小 HP-first bypass 反转；
- live missile effects/damage event 闭环；
- aircraft-specific damage-state 同步；
- 更新训练消费层，使其读取 `DamageReport`、loss state 或 subsystem capability。

当前禁止推进：

- 改 `PlatformLossState` 数值；
- 泛化 `NavalDamageStateUpdate` 并影响舰船；
- 将 generated hitbox 宣称为高真实度 authored damage model；
- 仅凭 miss-distance baseline、在缺少 warhead/fuze/脆弱性校准时移除 RNG fuze。

## Phase 1 最小补丁证据

已新增/调整的关键验证：

- `test_debug_runtime_exposes_proximity_fuze_miss_distance_state`：只读暴露 proximity fuze miss-distance state；
- `test_phase0_pn_miss_distance_baseline_matrix_tracks_engagement_geometries`：固定四类 PN/miss-distance 几何；
- `test_structured_air_target_uses_damage_state_instead_of_hp_first_kill`：debug 命中 structured F-16 时 HP 不扣减、damage state 下降、`DamageReport.hp_delta == 0`；
- `test_live_missile_hit_records_structured_air_damage_without_hp_first_kill`：真实导弹命中 structured F-16 时产生 `EffectsEvent/DamageReport`，HP 不再作为 kill authority；
- `test_phase2_aircraft_hitboxes_produce_distinct_subsystem_effects`：nose/radar、fuselage engine/fuel、wing/flight_control 三类命中产生不同后果，且 authored wing/fuel 重叠会产生燃油泄漏；
- `test_e3_sentry_c2node_uses_authored_structured_damage_model`：E-3 C2Node authored radar hitbox 进入 structured damage path，HP 不扣减但 sensor/mission capability 和 radar range 下降；
- `test_aircraft_database_units_have_authored_structured_damage_models`：F-16、Su-35、MQ-9、MH-60R、E-3 一次局部近炸进入 structured path，HP 不扣减、不直接析构，并记录 `DamageReport`；
- `test_fired_missile_does_not_retarget_friendly_and_records_engagement`：默认 1v1 发射测试改为不误锁/不误伤友方和事件目标一致，不再要求默认几何一发必杀。
- `test_loader_compute_full_step_consumes_structured_damage_report_for_combat_win`：目标 entity 仍 active 且 HP 不变时，`DamageReport.loss_state_to == mobility_kill` 会由 1v1 consumer 解释为 `combat_win`；
- `test_stage0_drone_weapon_employment_fixed_fire_smoke_reaches_weapon_release`：阶段零 fixed-fire smoke 只验证发射链路和运行稳定性；由于 Phase 4 deterministic fuze 未放行，真实导弹一次进入 fuse radius 后仍可随机未命中，不再把单发必然 `combat_win` 当作 smoke 验收。

聚焦测试：

```bash
source tools/maintenance/cmo_env.sh && cmo_python -m pytest -q \
  tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py::AirCombat1v1FireMissileTests::test_fired_missile_does_not_retarget_friendly_and_records_engagement \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_live_missile_hit_records_structured_air_damage_without_hp_first_kill \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_structured_air_target_uses_damage_state_instead_of_hp_first_kill \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase2_aircraft_hitboxes_produce_distinct_subsystem_effects \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_e3_sentry_c2node_uses_authored_structured_damage_model \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_aircraft_database_units_have_authored_structured_damage_models \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase0_pn_miss_distance_baseline_matrix_tracks_engagement_geometries
```

结果：当前空战聚焦文件为 `42 passed, 12 subtests passed`。
