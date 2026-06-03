# A2 guidance / miss-distance / evasion 证据路线 - 2026-05-28

状态：`evidence_route_only / deterministic_fuze_deferred / pk_authority_deferred`。

本文档定义 A2 高真实度毁伤模型中 guidance、miss distance 与 evasion 的证据路线。它面向后续实现与验收，不修改运行时代码；结论必须继续服从当前 A2 主线边界：evasion 不能通过黑盒 `hit probability` 直接定义杀伤权威，必须先改变导弹飞行、最近距、引信触发、战斗部 footprint 和目标局部脆弱性输入，再由 `EffectsEvent` / `DamageReport` / 平台状态消费。

## 1. 当前 baseline 与 evasion 边界

### 1.1 当前 PN / guidance baseline

当前导弹 guidance 不是纯粹的脚本命中，也不是单一 Pk 判定。现有 `DefaultGuidanceModel` 具有以下可审计行为：

| 证据面 | 当前行为 | 关键源 |
|----|----|----|
| seeker state | `Track / Memory / Ballistic` 三态；有 local detection 或 datalink 时更新 track，失去 track 后在 timeout 内记忆外推 | `src/models/weapons/default_guidance_model.cpp`、`src/models/weapons/missile_guidance_types.h` |
| FOV / lock range | contact 需满足 `seeker_lock_range` 与 `seeker_fov_deg`，terminal seeker 激活后还要求 local sensor hit | `DefaultGuidanceModel::update` contact filter |
| PN 与 capture | 横向加速度由 capture 项加 PN 项组成；PN 项消费 bearing/elevation rate、closing speed 和 `nav_gain` | `DefaultGuidanceModel::update` commanded acceleration |
| 能量状态 | boost/sustain thrust、propellant mass、reference area、Cd、induced drag、max lateral g、autopilot tau 会改变速度、转弯代价和响应滞后 | `resolve_tuning()`、`update_mass_and_drag_state()` |
| 最近距记录 | `proximity_min_dist_m`、`proximity_last_dist_m`、`proximity_engaged` 保存在 missile runtime，可通过 debug state 和 effects event 观测 | `src/components/combat/weapon.h`、`src/systems/combat/damage_system.h` |

现有 P0 baseline 矩阵已经固定四类几何差异：

| 几何 | 当前基线判读 |
|----|----|
| head-on | `proximity_min_dist_m < 50 m`，可进入近炸窗口 |
| tail-chase | `proximity_min_dist_m > 5000 m`，追尾能量不足明确 |
| beam | `250 m < proximity_min_dist_m < 1000 m`，横穿 LOS rate 下最近距显著放大 |
| high-off-boresight | `proximity_min_dist_m < 5 m`，可形成稳定结构命中回归 |

该 baseline 的意义是：几何和能量已经能改变 miss distance，因此 Phase 4 deterministic fuze 不能只靠“进入某个半径就必杀”放行。

### 1.2 当前 evasion 相关边界

当前代码中仍存在一个 compatibility 层 evasion 输入：proximity fuze 的 `hit_prob` 使用 `base_hit * fuze_effective_reliability * (1.0 - 0.3 * evasion)`。这只能被视为历史兼容残留，不能作为高真实度 evasion 权威。

当前已经具备更好的传递面：

| 传递面 | 已有基础 | 仍缺口 |
|----|----|----|
| 目标机动到最近距 | PN baseline 能区分迎头、追尾、beam、high-off-boresight | 缺持续机动脚本、目标 g/energy 限制、pilot/autopilot 约束矩阵 |
| seeker/FOV/track memory | FOV、lock range、terminal local hit、midcourse datalink、track memory timeout 已有行为测试 | 缺 look-down/clutter、notch、遮挡、multi-target/decoy、机动导致 track quality 下降 |
| missile energy | boost/sustain、drag、turn induced drag、max g、autopilot tau 已有测试 | 缺 altitude/Mach envelope、loft、motor profile 与真实 AIM/R 系参数校准 |
| fuze / warhead | `EffectsEvent` 已暴露 miss distance、local detonation point、closure、missile axis、fuze type/signature、warhead footprint 证据 | 当前 proximity fuze 仍有 RNG hit roll，signature 是代理；deterministic fuze authority 未放行 |
| vulnerability | profile/evidence descriptor gate 已能按 weapon/aspect/closure/miss-distance 行匹配 | 当前真实外部校准数据缺失；synthetic scaffold 不能授予 Pk 或 deterministic fuze authority |

因此，evasion 的当前合法定位是“输入变量和压力源”，不是“杀伤概率终局”。验收应证明它沿链路改变 `miss_distance_m`、`fuze_quality`、`fuze_signature_*`、`warhead_spatial_*`、`vulnerability_*`、component failure evidence 和最终 `DamageReport`，而不是直接断言某个 `evasion=0.7` 映射成某个 kill probability。

## 2. 现代空战 / BVR 真实性梯度

建议把 guidance / miss-distance 真实性分为五级，避免一次性把未校准内容包装成“现代 BVR”。

| 梯度 | 可声明内容 | 必要证据 | 不可声明内容 |
|----|----|----|----|
| G0 结构门 | launch、guidance、miss-distance、fuze/effects 事件字段存在 | debug runtime、`EffectsEvent` 字段、P0 baseline 测试 | 真实 BVR、真实 Pk |
| G1 几何 PN | 迎头、追尾、beam、off-boresight 能产生不同最近距 | PN baseline matrix、truth min distance vs proximity min distance | 目标战术机动真实性 |
| G2 seeker/track | FOV、lock range、midcourse datalink、terminal local seeker、track memory 会影响制导 | seeker activation、no-datalink、track timeout、filter tau 测试 | ECCM / clutter / deception |
| G3 energy maneuver | motor、drag、turn cost、autopilot lag、max lateral g 改变可达性和最近距 | burn/drag/induced drag/max-g/autopilot 测试和新机动矩阵 | 真实导弹气动数据库或 loft/NZ envelope |
| G4 fuze-warhead geometry | miss distance、closure、local detonation、warhead family/footprint、signature proxy 共同影响局部毁伤 | live missile effects event、contact/timed/proximity fuze、warhead spatial evidence | 校准近炸引信、破片云、连续杆、Sachs 爆轰 |
| G5 calibrated BVR | weapon/target/aspect/closure/miss-distance 证据行可授权 effect scale 或组件失效概率 | non-synthetic descriptor、外部/validated surrogate 来源、row id/source/provenance、mechanism-load gates | 在缺少数据行时使用黑盒 hit probability |

BVR 场景至少需要 G1-G3 才能谈“逃逸影响命中几何”，至少 G4 才能谈“逃逸影响毁伤 footprint”，只有 G5 才能谈“校准过的 Pk / vulnerability 证据”。当前 A2 主线大致处于 G3/G4 的工程脚手架阶段，并具备 G5 gate 形状，但没有真实校准数据授权。

## 3. 测试矩阵

矩阵目标不是追求单个一发必杀，而是验证每个输入轴能在事件证据面留下可解释差异。

### 3.1 目标机动矩阵

| Case | 目标动作 | 观测字段 | 通过信号 |
|----|----|----|----|
| M1 straight head-on | 直飞迎头 | `truth_min_dist_m`、`proximity_min_dist_m`、`closure_mps` | 与 P0 head-on baseline 同量级 |
| M2 tail-chase escape | 追尾同向加速 | missile speed、burnout、`proximity_min_dist_m` | 最近距显著大于 fuse/warhead radius |
| M3 beam drag-out | 横穿/beam | LOS rate proxy、achieved lateral accel、miss distance | miss distance 大于迎头，导弹有显著横向加速度 |
| M4 terminal break | 末端 break turn | miss distance、fuze trigger outcome、warhead spatial scale | break timing 改变起爆点或错过触发 |
| M5 vertical split | 俯冲/爬升脱离 | elevation rate、energy、local detonation up/down | 垂直机动改变 elevation track 与局部起爆点 |
| M6 damaged evader | 飞控/发动机受损后逃逸 | target `AircraftDamageState`、miss distance、DamageReport | 受损目标机动能力降低，逃逸效果减弱 |

### 3.2 seeker / FOV / track memory 矩阵

| Case | 输入 | 观测字段 | 通过信号 |
|----|----|----|----|
| S1 FOV edge | target bearing 接近/超出 `seeker_fov_deg / 2` | `seeker_has_valid_track`、`seeker_mode`、miss distance | 超出 FOV 不应继续稳定制导 |
| S2 lock range | contact range 超出/进入 `seeker_lock_range` | track acquire time、filtered range | 超出 lock range 不应获取目标 |
| S3 midcourse datalink | `midcourse_datalink_supported` true/false，nonlocal contact | `terminal_seeker_active`、track state | 无 datalink 时 nonlocal updates 不驱动 track |
| S4 terminal local seeker | terminal active 后只给 nonlocal contact | `seeker_mode=Ballistic` 或 track break | terminal 阶段需要 local contact |
| S5 track memory | 短时丢 contact | `Memory` 状态、bearing extrapolation、timeout 后 ballistic | timeout 前外推，timeout 后清 track |
| S6 filter lag | bearing/range filter tau 快/慢 | filtered bearing、bearing rate、miss distance | filter lag 可放大高 LOS-rate 场景最近距 |

### 3.3 能量状态矩阵

| Case | 输入 | 观测字段 | 通过信号 |
|----|----|----|----|
| E1 boost window | boost/sustain duration 高低 | missile speed profile、time to intercept | 长 boost 或 sustain 提升中段速度 |
| E2 thrust level | boost/sustain thrust 高低 | speed、range closure、miss distance | thrust 高低改变可达性 |
| E3 drag area | reference area、Cd0 高低 | speed decay、tail chase miss distance | 高 drag 增大 miss distance 或无法追上 |
| E4 induced turn drag | induced_drag_k 高低 | turn speed loss、achieved lateral accel | 高 induced drag 降低大转弯能量 |
| E5 max lateral g | max_lateral_g 高低 | achieved lateral accel、miss distance | 低 g cap 在 beam/off-boresight 场景更差 |
| E6 autopilot response | autopilot_tau、accel response rate | acceleration buildup、miss distance | 慢响应加大末端误差 |

### 3.4 ECM / 签名输入矩阵

当前 ECM/ECCM 尚不是完整模型，矩阵应先使用可观测的 signature/track proxy，不把它写成真实电子战。

| Case | 输入 | 观测字段 | 通过信号 |
|----|----|----|----|
| X1 low RCS aspect | radar proximity + target RCS aspect | `fuze_signature_source=target_rcs_aspect`、`fuze_target_signature`、`fuze_effective_reliability` | RCS 代理影响 fuze reliability 证据 |
| X2 projected geometry | laser proximity + hitbox/projected area | `target_projected_geometry`、signature scale | 投影几何影响 laser fuze evidence |
| X3 generic proximity | generic proximity | `fuze_signature_source=generic_proximity` | 不假装有 radar/laser signature |
| X4 datalink denied | nonlocal contact + datalink false | track state、miss distance | 不能用非本机 track 维持 terminal guidance |
| X5 track quality proxy | signal strength / detection gaps | best detection、memory timeout、filter lag | quality/gap 影响 seeker continuity |
| X6 future ECM hook | jammer/deception/noise/clutter 输入 | track confidence、false target、FOV break | 仅在字段和测试落地后进入真实性声明 |

## 4. evasion 的合法传递路线

目标路线如下：

```text
目标机动 / 签名 / ECM / 诱饵 / 低空遮蔽
  -> detection / track quality / FOV / datalink / terminal seeker
  -> filtered LOS、LOS rate、closing speed、track memory
  -> PN command、autopilot lag、max-g cap、turn drag、missile energy
  -> closest approach / miss_distance_m / local detonation point / closure
  -> fuze trigger / fuze quality / signature effective reliability / delay
  -> warhead footprint / spatial sample / mechanism load / vulnerability row match
  -> component failure / subsystem damage / platform loss state
  -> DamageReport / reward consumer
```

这一路线意味着：

- `evasion` 可以作为目标机动、signature、track break 或 ECM 输入；
- `evasion` 不应直接乘在最终 kill probability 上；
- 如保留历史兼容 `hit_prob`，必须把它标为 non-authoritative，并且验收不得以它作为唯一证据；
- Pk 曲线只能校准 fuze/effects/vulnerability 的物理或半物理参数，不能跳过 `EffectsEvent`；
- deterministic fuze 的放行条件必须包含：miss-distance envelope、fuze type/signature/delay/reliability、warhead footprint、target vulnerability evidence 和 residual risk 评审。

建议后续迁移顺序：

1. 固定当前 `hit_prob` 的 non-authoritative 标签：事件里保留 `fuze_hit_probability` 作为 fuze confidence/compat evidence，不作为 kill authority。
2. 增加 evasion scenario harness：对目标机动脚本、track dropout、FOV edge、energy state 做参数化 sweeps，输出 miss-distance 和 event evidence。
3. 将 compatibility evasion 影响从 fuze hit roll 迁到 detection/track/target maneuver 输入侧。
4. 只有在 G5 evidence rows 完成后，允许 Pk-like row 校准 component failure 或 effect scale；仍不允许单行黑盒 kill。

## 5. 验收命令

只读验收命令如下，均不要求修改代码：

```bash
source tools/maintenance/cmo_env.sh && cmo_python -m pytest -q \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase0_pn_miss_distance_baseline_matrix_tracks_engagement_geometries \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_debug_runtime_exposes_proximity_fuze_miss_distance_state \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_live_missile_hit_records_structured_air_damage_without_hp_first_kill
```

```bash
source tools/maintenance/cmo_env.sh && cmo_python -m pytest -q \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_seeker_activation_range_requires_local_terminal_contact \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_without_midcourse_datalink_nonlocal_updates_do_not_drive_track \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_track_memory_timeout \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_shared_bearing_filter_tau_changes_track_response
```

```bash
source tools/maintenance/cmo_env.sh && cmo_python -m pytest -q \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_shared_burn_window_changes_guidance_speed_profile \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_shared_reference_area_changes_drag_cost \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_shared_induced_drag_changes_turn_energy_loss \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_shared_max_lateral_g_changes_guidance_cap \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_shared_autopilot_tau_changes_response_buildup
```

```bash
source tools/maintenance/cmo_env.sh && cmo_python -m pytest -q \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_global_fuze_profile_override_flows_into_runtime_and_effects_event \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_fuze_delay_schedules_detonation_after_nearest_approach \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_contact_fuze_does_not_trigger_from_near_miss_radius \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_timed_fuze_detonates_on_delay_without_proximity_gate
```

辅助审计命令：

```bash
rg -n "proximity_min_dist_m|fuze_hit_probability|resolved_compatibility_damage_evasion|miss_distance_m|vulnerability_miss_distance_scale" src tests docs/task/air_combat/archive/a2_high_fidelity_damage_model -S
rg -n "seeker_fov_deg|seeker_activation_range_m|midcourse_datalink_supported|track_memory_timeout_s|guidance_max_lateral_g|guidance_autopilot_tau_s|guidance_induced_drag_k" src tests/runtime/air_combat -S
```

## 6. Residual risks

| 风险 | 当前影响 | 建议关闭条件 |
|----|----|----|
| compatibility evasion 仍参与 fuze hit roll | 可能把 evasion 误读为黑盒命中概率权威 | 标注 non-authoritative，迁移到 sensing/track/target maneuver 输入侧 |
| proximity fuze 最近点后一帧触发 | `closure_mps` 可为 0 或偏离真实最近点 | 引入连续 closest-approach interpolation 或 substep fuze check |
| seeker/FOV 简化 | 无真实 antenna scan、gimbal、look-down、clutter、notch、ECM | 增加 track quality/confidence、scan cadence、false target/decoy 和 clutter gates |
| 目标机动脚本不足 | 当前 baseline 主要是几何与速度，不是完整 BVR tactic | 增加 terminal break、drag、crank/notch、vertical split、energy state sweeps |
| missile energy 未校准 | motor/drag/turn cost 可解释但不是真实导弹数据库 | 引入 weapon-specific authored/validated profiles 与 envelope tests |
| warhead footprint 仍是工程化脚手架 | 不能声明真实破片云/连续杆/爆轰传播 | 使用外部数据或 validated surrogate，按 mechanism-load gates 验证 |
| vulnerability evidence 形状先于数据 | G5 gate 存在，但真实授权数据缺失 | 非 synthetic descriptor、row provenance、source/validation manifest 和审计报告齐备 |
| reward consumer 可能重新引入捷径 | 训练层可能偏好 HP 或单发必杀 | reward 只消费 `DamageReport` / loss state / subsystem capability，不写回物理 authority |

## 7. 最小验收定义

一次合格的 guidance / miss-distance / evasion 证据提交至少应满足：

- baseline 矩阵仍能区分 head-on、tail-chase、beam、high-off-boresight；
- evasion 或目标机动改变的是 track / LOS / energy / miss distance / fuze / footprint 证据链，而不是只改一个最终概率；
- `EffectsEvent` 能导出 `miss_distance_m`、局部起爆点、closure、fuze type/signature、warhead footprint、vulnerability scale/source；
- `DamageReport` 由 effects/subsystem state 派生，structured aircraft 不回退 HP-first kill；
- residual risks 中涉及未校准内容的项不得被文档或测试名误称为 calibrated / authoritative。
