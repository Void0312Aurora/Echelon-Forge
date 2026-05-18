# 武器/制导真实化 P1 实施包

状态：`2026-05-17` P1 起草版；已按当前代码/测试状态做一次进度核对。

关联文档：

- [武器系统与制导回路现实性分析](weapon_guidance_realism_analysis_20260516.zh.md)
- [武器系统与制导回路真实化核实与落地方案](weapon_guidance_realism_verification_and_plan_20260516.zh.md)
- [武器/制导真实化 P0 实施包](weapon_guidance_realism_p0_implementation_package_20260516.zh.md)
- [真实化任务总表](../program/realism_program_taskboard_20260516.zh.md)

关联代码：

- [Missile 组件](../../../../src/components/combat/weapon.h)
- [SimulationKernel 配置接口](../../../../src/core/engine/simulation_kernel.h)
- [SimulationKernel 发射实现](../../../../src/core/engine/simulation_kernel_weapon_api.cpp)
- [默认制导模型](../../../../src/models/weapons/default_guidance_model.cpp)
- [默认传感器模型](../../../../src/models/systems/default_sensor_model.cpp)
- [默认命中效果模型](../../../../src/models/weapons/default_effects_model.cpp)
- [DamageSystem / ProximityFuze](../../../../src/systems/combat/damage_system.h)
- [DataLinkSystem](../../../../src/systems/systems/data_link_system.h)
- [TrackManagerSystem](../../../../src/systems/systems/track_manager_system.h)
- [Python bindings](../../../../src/interfaces/python/bindings_core.cpp)

文档目的：

- 在 `P0` 已经跑通 seeker-only guidance、最小 3DoF 趋势和守门测试之后，
  把武器/制导方向收敛成一个可继续开工的 `P1` 包。
- 明确 `P1` 先做哪些共享收尾，哪些深化真实化应纳入本阶段，哪些继续后推到 `P2`。
- 把本次验收里实际暴露出来的共享集成问题写进任务包，而不是只写理想模型。

---

## 0. P0 验收快照

当前 `P0` 已达成的最小结果：

1. guidance 已切断对 target truth `Transform/Velocity` 的直接依赖。
2. 导弹已有最小 `boost/coast + drag + mass depletion` 趋势。
3. PN 主回路已切到“加速度指令 + 一阶 autopilot surrogate + 横向过载约束”。
4. 守门测试 [test_weapon_guidance_realism_guards.py](../../../../tests/runtime/test_weapon_guidance_realism_guards.py) 当前通过。
5. 既有武器链回归 [test_air_combat_1v1_fire_missile.py](../../../../tests/runtime/test_air_combat_1v1_fire_missile.py) 的关键命中用例已恢复通过。
6. `MissileTuning` shared 字段、Python round-trip、launch runtime 初始化、导弹 runtime debug 观测面已经落地。
7. 武器定义中的 `missile_tuning` 已可经 loader/weapon station 进入发射链路，并可被全局 tuning overlay 覆盖。

但 `P0` 仍保留了几类明显的临时做法，这些正是 `P1` 的入口：

1. `MissileTuning` 已正式扩展到 P0/P1 第一批共享字段，但仍有一部分默认回退常量保留在 guidance 私有默认值中，尚未完成更细型号化标定。
2. 发射阶段已经初始化导弹干重/推进剂质量与 `MassProperties`，但 guidance 里仍保留兼容旧发射路径的 lazy fallback。
3. Python / debug 已暴露主要 missile runtime state，但 observation/facade 口径仍偏 debug 风格，离正式稳定观测面还有一步。
5. missile 姿态/航迹参考系仍有 shared 语义缺口：
   - `MissileGuidance` 运行于平移积分之前；
   - 当前平移主路径使用 `LeapfrogIntegrate`，而旧 `UpdatePosition` 已停用；
   - missile `Transform.heading` 不一定与当前速度航迹严格同步。
6. seeker / missile / launch 参数已经部分进入数据库与 loader 链路，但 midcourse / datalink / countermeasure / fuze-damage layering 还没有形成完整型号化配置面。
7. 全量工程构建当前仍可能被并行中的共享改动阻塞，因此 `P1` 需要把 shared API 对齐和并行集成风险一起考虑。

本次核对后，建议把上面 `1/2/3/6` 视为“已部分完成但未完全收口”，不要再按“尚未开始”理解。

---

## 1. P1 总目标

`P1` 的目标不是“做完整导弹武器学”，而是把 `P0` 的局部改造从 guidance 私有 workaround
提升为可共享、可参数化、可继续深化的系统能力。

更准确地说，`P1` 要完成两层工作：

1. `P1 前置集成收尾`
   - 把 `P0` 的临时常量、lazy 初始化、debug-only 观测口径，收敛为 shared runtime / config / binding / database 的正式能力。

2. `P1 深化真实化`
   - 在 shared 基础补齐 seeker type 分化、midcourse/datalink、参数化 3DoF、fuze/damage layering、countermeasure interaction 的第一版。

---

## 2. P1 范围分层

### 2.1 P1 前置集成收尾

这一层的判断标准不是“更像真实导弹”，而是“让当前 P0 逻辑不再依赖私有补丁”。

#### A. `MissileTuning` 正式扩展与 shared API 对齐

需要纳入 `P1`。

原因：

1. 当前 `boost_time / drag / induced drag / propellant fraction / autopilot tau / track memory`
   仍写死在 guidance 私有 header 中。
2. 只要这些量不进入 shared tuning，后续 seeker type、数据库参数、型号差异都无法落地。

建议文件范围：

- [simulation_kernel.h](../../../../src/core/engine/simulation_kernel.h)
- [simulation_kernel_weapon_api.cpp](../../../../src/core/engine/simulation_kernel_weapon_api.cpp)
- [bindings_core.cpp](../../../../src/interfaces/python/bindings_core.cpp)

建议最小字段集：

```cpp
int seeker_type;
double seeker_activation_range_m;
double seeker_gimbal_limit_deg;
double seeker_ifov_deg;
double bearing_filter_tau_s;
double elevation_filter_tau_s;
double range_filter_tau_s;
double track_break_time_s;

double boost_time_s;
double sustain_time_s;
double boost_thrust_n;
double sustain_thrust_n;
double reference_area_m2;
double cd0_subsonic;
double cd0_supersonic;
double induced_drag_k;
double propellant_mass_kg;

double max_lateral_g;
double autopilot_tau_s;
double max_accel_response_g_per_s;

double min_launch_range_m;
double max_launch_off_boresight_deg;
bool lobl_required;
bool midcourse_datalink_supported;
```

验收口径：

1. Python 可以 round-trip 设置并读取这些字段。
2. shared launch path 能把 tuning 真正传到 missile entity，而不是 guidance 再回退到默认常量。
3. 旧测试不因字段扩展而被 aggregate init 破坏。

#### B. 发射初始化与质量语义收尾

需要纳入 `P1`。

原因：

1. 当前导弹 `Mass{80,0,0}` 的初始化仍是不真实的占位值。
2. `P0` 在 guidance 内做的 propellant split 只是过渡手段，不应长期保留。

建议文件范围：

- [simulation_kernel_weapon_api.cpp](../../../../src/core/engine/simulation_kernel_weapon_api.cpp)
- [dynamics.h](../../../../src/components/physics/dynamics.h)
- [weapon.h](../../../../src/components/combat/weapon.h)

需要收掉的 P0 workaround：

1. guidance 内 lazy `fuel_mass_kg` 补写
2. guidance 内 lazy `MassProperties` 创建
3. guidance 内 runtime 初始值兜底

期望 shared 语义：

1. `fire_missile()` 直接生成：
   - `Mass{empty_mass_kg, fuel_mass_kg, stores_mass_kg=0}`
   - `MassProperties`
   - `Missile` runtime 初值
2. launch 时就写明：
   - `burnout_time_s`
   - `current_speed_mps`
   - seeker 初始模式

验收口径：

1. `debug_get_mass_state()` 在导弹刚发射后即显示合理的 dry/fuel split。
2. 去掉 guidance lazy split 后，现有 P0 guard tests 仍通过。
3. 发射实现不再依赖“P0 guidance 首帧补丁”才能运行。

#### C. Python / binding / observation / debug 暴露收尾

需要纳入 `P1`。

原因：

1. 目前 P0 的主要验收是黑盒趋势测试，shared API 对导弹内部状态暴露不足。
2. 后续 seeker / midcourse / fuze / damage 测试会需要更稳定的观测面。

建议文件范围：

- [bindings_core.cpp](../../../../src/interfaces/python/bindings_core.cpp)
- [simulation_kernel_observation_api.cpp](../../../../src/core/engine/simulation_kernel_observation_api.cpp)
- [observation.h](../../../../src/core/interfaces/observation.h)

建议新增或补强的导出内容：

1. missile tuning 全字段
2. missile runtime debug/state view
   - seeker mode
   - has_valid_track
   - filtered bearing/elevation/range
   - commanded / achieved lateral accel
   - current speed
   - burnout time
3. 必要时新增一个明确的 debug API，而不是继续隐式复用其他接口

验收口径：

1. 测试不再需要靠实现细节猜测导弹状态。
2. seeker memory、activation、autopilot lag 可通过 Python 验证。

#### D. shared 参考系与阶段语义对齐

必须纳入 `P1`。

这是本次验收暴露出的最关键 shared 问题之一。

问题描述：

1. `MissileGuidance` 当前运行在平移积分之前。
2. 主平移路径使用 `LeapfrogIntegrate`，旧 `UpdatePosition` 不再是主路径。
3. missile `Transform.heading` 对 guidance / seeker / debug 的语义并不稳定。

这带来的后果是：

1. seeker 相对方位角的解释容易依赖过时姿态。
2. guidance 内部只能继续保留“以当前速度航迹为主”的工程近似。
3. 后续若要做 seeker gimbal、look angle、datalink midcourse，必须先统一 shared 口径。

建议文件范围：

- [simulation_kernel_systems.cpp](../../../../src/core/engine/simulation_kernel_systems.cpp)
- [guidance_system.h](../../../../src/systems/combat/guidance_system.h)
- [common.h](../../../../src/components/basic/common.h)
- [movement_system.h](../../../../src/systems/physics/movement_system.h)
- [leapfrog_system.h](../../../../src/systems/physics/leapfrog_system.h)

`P1` 推荐目标：

1. 明确 missile guidance 使用的是：
   - `body attitude reference`
   - 还是 `velocity track reference`
2. 保证 shared runtime 至少有一条一致的“导弹当前航迹/姿态”语义可用。
3. 把 seeker relative angle 的解释写进代码与测试，而不是继续留在隐式约定里。

验收口径：

1. missile `heading` / `ground track` / seeker relative bearing 的关系可用单测说明。
2. 相同输入下，不会因为系统顺序或姿态缓存不同而导致 guidance 发散。

#### E. 数据库 / loader / 默认参数链路

需要纳入 `P1`。

原因：

1. 当前 missile 参数仍主要停留在 `fire_missile()` 默认值和少量 Python tuning。
2. 不进入数据库，后续 seeker type 差异、型号差异、参数来源审查都无法稳定推进。

建议文件范围：

- [unit_definition.h](../../../../src/content/unit_definition.h)
- [unit_definition_loader.cpp](../../../../src/content/unit_definition_loader.cpp)
- [default_unit_factory.h](../../../../src/models/core/default_unit_factory.h)
- `examples/config/database/**`

`P1` 目标不是做完整武器库，而是先跑通：

1. `数据库 -> UnitDefinition -> SimulationKernel -> MissileTuning -> fire_missile()`
2. 至少支持 1-2 类代表性空空导弹参数模板

验收口径：

1. 不改代码常量也能通过数据库切换 seeker / mass / thrust / drag 基础参数。
2. 新老场景在缺省配置下保持兼容。

### 2.2 P1 深化真实化

这一层以“有了 shared 能力后，补第一版更像样的武器学行为”为目标。

#### A. seeker type 分化

应纳入 `P1`。

理由：

1. 当前导引头虽然走 `Sensor -> ContactList`，但本质上还是统一 seeker。
2. `ARH / IR / SARH` 至少需要不同的工作模式、激活条件和抗干扰口径。

`P1` 最小分化目标：

1. `ARH`
   - 支持激活距离
   - 支持 midcourse 到 terminal 切换
2. `IR`
   - 不依赖 range 才能继续 terminal track
   - 支持更短 track memory 和更窄 IFOV
3. `SARH`
   - 第一版只要求“需要外部照射/数据链授权”这一层逻辑

建议文件范围：

- [simulation_kernel.h](../../../../src/core/engine/simulation_kernel.h)
- [simulation_kernel_weapon_api.cpp](../../../../src/core/engine/simulation_kernel_weapon_api.cpp)
- [default_guidance_model.cpp](../../../../src/models/weapons/default_guidance_model.cpp)
- [default_sensor_model.cpp](../../../../src/models/systems/default_sensor_model.cpp)

#### B. midcourse / datalink / activation range

应纳入 `P1`。

这是 `P0` 到“BVR 空战可用”之间最值钱的一步。

`P1` 最小目标：

1. 导弹在 terminal seeker 激活前，允许使用：
   - 惯性保持
   - 或 datalink/track cueing 的简化中制导
2. 支持 `seeker_activation_range_m`
3. 支持 `midcourse_datalink_supported`
4. 支持 terminal 切换失败后的 memory / ballistic 退化

建议文件范围：

- [default_guidance_model.cpp](../../../../src/models/weapons/default_guidance_model.cpp)
- [data_link_system.h](../../../../src/systems/systems/data_link_system.h)
- [track_manager_system.h](../../../../src/systems/systems/track_manager_system.h)

验收重点：

1. ARH 导弹不会一出筒就按 terminal seeker 模式打满全程。
2. datalink 丢失时会退化，而不是继续享受 truth 风格中制导。

#### C. 更真实的 3DoF 参数化

应纳入 `P1`，但只做到“参数化 + 分 seeker/型号可区分”，不追求 `P2` 级型号复刻。

`P1` 目标：

1. 从 guidance 私有常量切到 tuning/database 参数。
2. 支持不同导弹的：
   - propellant mass
   - boost/sustain duration
   - thrust
   - reference area
   - `Cd0_subsonic / Cd0_supersonic`
   - induced drag
   - max lateral g
3. 保持当前 `3DoF + accel surrogate` 路线，不进入 `6DoF`

建议文件范围：

- [default_guidance_model.cpp](../../../../src/models/weapons/default_guidance_model.cpp)
- [simulation_kernel.h](../../../../src/core/engine/simulation_kernel.h)
- `examples/config/database/**`

#### D. fuze / hit / damage layering

应纳入 `P1`，但只做第一层分离。

本阶段的目标不是完整破片方向性，而是把“截获、起爆、毁伤”三层从混合状态中拆开。

`P1` 最小目标：

1. `intercept / miss geometry`
2. `fuze decision`
3. `warhead / damage application`

推荐第一版：

1. 近炸仍可保留简化，但加入：
   - arm time
   - impact / proximity 区分
   - 更明确的最近点 / range-rate 条件
2. 毁伤层至少做到：
   - HP 路径
   - subsystem damage 路径
   - 两者关系不再互相打架

建议文件范围：

- [damage_system.h](../../../../src/systems/combat/damage_system.h)
- [default_effects_model.cpp](../../../../src/models/weapons/default_effects_model.cpp)

#### E. countermeasure interaction

应纳入 `P1`，但只做简化版。

`P1` 最小目标：

1. flare / chaff 不再只是“最强信号替换器”
2. 引入最小的：
   - seduction hysteresis
   - track memory interaction
   - kinematic rejection 或角分离门限
3. 不做完整 DRFM / RGPO / VGPO / HOJ

建议文件范围：

- [default_sensor_model.cpp](../../../../src/models/systems/default_sensor_model.cpp)
- [default_guidance_model.cpp](../../../../src/models/weapons/default_guidance_model.cpp)
- [ew_system.h](../../../../src/systems/systems/ew_system.h)

---

## 3. 明确不纳入 P1、后推到 P2 的内容

以下内容建议继续后推到 `P2`：

1. 完整 `6DoF` 导弹刚体、舵面、角速度和姿态闭环
2. 完整 seeker estimator 重构为 Kalman / IMM 等更高阶滤波
3. 完整 SARH / HOJ / DRFM / RGPO / VGPO 行为细节
4. 完整破片方向性、破片锥、warhead effectiveness 几何模型
5. 完整动态发射包线：
   - no-escape zone
   - loft profile
   - dynamic LAR
6. 型号级高精度参数复刻与性能标定
7. 多脉冲、多段火箭、冲压等更复杂推进模型

`P1` 的边界应始终保持：

- “能共享、能参数化、能稳定测试、能解释趋势”
- 而不是“先把高级模型挂进去，再回头补接口”

---

## 4. 建议文件范围

### 4.1 `P1 前置集成收尾`

建议主文件：

- [simulation_kernel.h](../../../../src/core/engine/simulation_kernel.h)
- [simulation_kernel_weapon_api.cpp](../../../../src/core/engine/simulation_kernel_weapon_api.cpp)
- [weapon.h](../../../../src/components/combat/weapon.h)
- [dynamics.h](../../../../src/components/physics/dynamics.h)
- [simulation_kernel_observation_api.cpp](../../../../src/core/engine/simulation_kernel_observation_api.cpp)
- [bindings_core.cpp](../../../../src/interfaces/python/bindings_core.cpp)
- [simulation_kernel_systems.cpp](../../../../src/core/engine/simulation_kernel_systems.cpp)
- [guidance_system.h](../../../../src/systems/combat/guidance_system.h)
- [unit_definition.h](../../../../src/content/unit_definition.h)
- [unit_definition_loader.cpp](../../../../src/content/unit_definition_loader.cpp)
- [default_unit_factory.h](../../../../src/models/core/default_unit_factory.h)

### 4.2 `P1 深化真实化`

建议主文件：

- [default_guidance_model.cpp](../../../../src/models/weapons/default_guidance_model.cpp)
- [default_sensor_model.cpp](../../../../src/models/systems/default_sensor_model.cpp)
- [data_link_system.h](../../../../src/systems/systems/data_link_system.h)
- [track_manager_system.h](../../../../src/systems/systems/track_manager_system.h)
- [default_effects_model.cpp](../../../../src/models/weapons/default_effects_model.cpp)
- [damage_system.h](../../../../src/systems/combat/damage_system.h)
- [ew_system.h](../../../../src/systems/systems/ew_system.h)

---

## 5. 最小测试清单

### 5.1 `P1 前置集成收尾`

建议最小测试：

1. `test_missile_tuning_roundtrip_python_to_launch`
   - Python 设置 tuning 后，发射实体能拿到相同参数。
2. `test_missile_mass_is_initialized_at_spawn`
   - 发射后立即可见合理 dry/fuel mass，而不是 guidance 首帧后才补齐。
3. `test_missile_runtime_state_initialized_at_spawn`
   - `burnout_time/current_speed/seeker_mode` 在 launch 即存在。
4. `test_missile_heading_or_track_reference_semantics`
   - 明确验证 seeker bearing 相对于哪条 shared 参考系解释。
5. `test_missile_runtime_debug_surface_exposed`
   - Python 可读取 seeker memory、accel command、energy state。

### 5.2 `P1 深化真实化`

建议最小测试：

1. `test_arh_midcourse_then_terminal_activation`
2. `test_ir_seeker_operates_without_range_measurement_dependency`
3. `test_sarh_requires_external_support_or_degrades`
4. `test_datalink_loss_degrades_midcourse_guidance`
5. `test_parameterized_boost_sustain_profiles_diverge_by_tuning`
6. `test_proximity_vs_impact_fuze_paths_are_distinct`
7. `test_countermeasure_seduction_requires_persistence_or_separation`
8. `test_weapon_p0_guards_still_pass`
9. `test_air_combat_1v1_fire_missile_regression_still_pass`

验收时至少应跑：

```bash
CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/test_weapon_guidance_realism_guards.py
CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/test_air_combat_1v1_fire_missile.py
```

建议新增：

- `tests/runtime/test_weapon_guidance_tuning_plumbing.py`
- `tests/runtime/test_weapon_guidance_midcourse_datalink.py`
- `tests/runtime/test_weapon_fuze_damage_layering.py`

---

## 6. 数据源落地方式

`P1` 不要求把每种导弹都做成高精度数据库，但要先把“参数从哪里来、可信度如何、如何落地”建立流程。

建议分两层存放：

### 6.1 参考表层

建议新增一份配套参考表文档，记录：

1. 参数项
2. 数值/范围
3. 来源 URL
4. 来源日期
5. 可信度等级
6. 是否作为：
   - 直接数据库默认值
   - 仅 sanity range
   - 仅 P2 预研

推荐来源等级：

1. `A 级`
   - JHU APL guidance / flight control
   - NASA drag / atmosphere
   - 官方产品页
2. `B 级`
   - Designation-Systems
   - DOT&E / Air & Space Forces 等二手公开资料
3. `C 级`
   - 仿真社区、非官方数据库、论坛估值

### 6.2 数据库落地层

建议把 `P1` 参数写入：

- `examples/config/database/**`

并保持下面约定：

1. 数据库只保存“当前采用值”
2. 文档保存“来源与可信度”
3. 若数值只是工程近似，要明确标注：
   - `engineering_approx`
   - `sanity_range_based`
   - `public_source_backed`

建议优先落地的数据项：

1. dry mass / propellant mass
2. boost / sustain duration
3. boost / sustain thrust
4. reference area
5. `Cd0_subsonic / Cd0_supersonic`
6. max lateral g
7. seeker activation range
8. seeker IFOV / gimbal / memory timeout
9. fuze distance / arm time / fuze type

---

## 7. 验收口径

`P1` 的验收不应只看“能不能打中”，而要看 shared integration 是否真正闭合。

建议验收标准：

### 7.1 `P1 前置集成收尾` 验收

1. 全量 shared launch 路径能直接初始化 missile mass / runtime state，不再依赖 guidance lazy patch。
2. `MissileTuning` 能通过 Python 和数据库稳定配置。
3. shared runtime 能清晰导出 missile seeker / energy / autopilot 关键状态。
4. missile guidance 所依赖的 heading / track reference 语义在系统层被明确固定。
5. `P0` 守门测试和关键武器链回归仍通过。

### 7.2 `P1 深化真实化` 验收

1. 至少两类 seeker 工作模式出现可观察差异。
2. ARH 中制导与 terminal 激活可区分，不再全程 terminal。
3. 不同 tuning 的 3DoF 性能曲线出现稳定差异。
4. countermeasure interaction 不再退化为“最强信号立即切换”。
5. hit / fuze / damage 三层在代码与测试上可区分。

### 7.3 工程验收

1. 优先要求全量构建恢复为可用：

```bash
cmake --build build-workshop -j4
```

2. 若并行改动仍造成全量构建阻塞，需在 `P1` 任务中明确阻塞归属和临时验证路径，避免再次依赖局部重链作为长期常态。

---

## 8. 推荐实施顺序

建议 `P1` 按下面顺序推进，而不是直接从 seeker type 或 fuze 开始。

1. `MissileTuning / launch init / binding` 收尾
   - 先把参数与初始化共享化。
2. `heading / track reference / observation` 收尾
   - 先统一 seeker 角度和 guidance 参考系的 shared 语义。
3. `database / loader` 接线
   - 让参数真正脱离 guidance 私有常量。
4. `ARH midcourse + activation + datalink`
   - 把 BVR 武器链最关键的模式差异做出来。
5. `IR / SARH` 基线分化
   - 做出 seeker type 差异，而不是一套逻辑套三类武器。
6. `fuze / damage layering`
   - 补齐命中后链路。
7. `countermeasure interaction`
   - 最后补抗干扰/抗诱饵第一版。

---

## 9. P1 结束条件

满足以下条件后，可以认为武器/制导方向适合进入 `P2`：

1. `P0` workaround 已基本退出 shared 主路径。
2. missile tuning 已能通过 shared API 和数据库配置。
3. seeker type 至少完成 `ARH / IR / SARH` 第一版分化。
4. midcourse / terminal / memory / ballistic 几种模式可测试、可观察。
5. fuze / damage / countermeasure 已有第一版分层逻辑。
6. 后续更高阶工作的瓶颈开始转向“模型深度”，而不再是“shared 接口缺口”。
