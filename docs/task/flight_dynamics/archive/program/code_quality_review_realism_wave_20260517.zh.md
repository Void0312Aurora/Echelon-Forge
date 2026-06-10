# 真实化推进代码质量审查

状态：`2026-05-17` 审查冻结版。

审查范围：`P0 + P1` 真实化推进的全部 170 文件未提交变更（+5,022 / -759 行），
涵盖 `src/` 下 56 个修改文件与 10 个全新 C++ 文件。

关联文档：

- [真实化任务总表](realism_program_taskboard_20260516.zh.md)
- [真实化 P1 任务总表](realism_program_p1_taskboard_20260517.zh.md)
- [真实化主线当前状态](realism_program_current_status_20260517.zh.md)
- [飞行动力学分析](../flight/flight_dynamics_realism_analysis_20260516.zh.md)
- [传感器分析](../sensor_situation/sensor_situation_realism_analysis_20260516.zh.md)
- [武器分析](../weapon_guidance/weapon_guidance_realism_analysis_20260516.zh.md)
- [海军分析](../naval/naval_realism_analysis_20260516.zh.md)
- [C2 分析](../c2_command_chain/c2_command_chain_realism_analysis_20260517.zh.md)

文档定位：

- 本文档不重复各领域的物理真实性分析，仅审查本次代码变更的结构质量。
- 重点评估越界耦合、上帝对象倾向、重复代码、以及架构退化风险。

---

## 一、总体判断

本轮真实化推进在物理功能上的收益是实质性的——五域全部到达 P0 可用。
但代码结构上出现了若干需要关注的问题：**上帝工厂膨胀、内容层跨域污染、
重复定义、Kernel API 线性增长，以及 Python 编排层的边界回渗与高耦合热点**。

好消息是这些问题还处于"刚冒头"阶段，纠正成本较低。但如果不干预，
按同样节奏再推进两三轮，它们会固化为架构债务。

---

## 二、需要立即关注的问题

### 2.1 default_unit_factory.h：God Factory 在形成

**现状：** 845 行，27 个 `#include`，包含链路覆盖全部域：

```
command → combat → physics → sensors → naval → content → core
```

`make_factory_default_sensor()`（94 行内联函数）制造飞机、导弹、舰船、
设施、C2 节点的传感器——所有域的默认值集中在一个函数中。

问题：

- **域知识泄漏。** 工厂不应同时知道"F-16 的雷达参数""DDG-51 的传感器包"
  "潜艇的安静速度"。这是不同问题域的对象，分别属于不同工厂。
  正确划分应为 `DefaultAirUnitFactory` / `DefaultSurfaceUnitFactory` /
  `DefaultSubsurfaceUnitFactory`，每类只持有自己域的参数。
- **万能默认反模式。** 工厂的 5 个内置默认类型都调用同一个
  `make_factory_default_sensor()` 只修改末尾 2 个参数。除了传感器类型枚举，
  它们把 `max_range=30000m, fov_deg=120°` 作为所有平台的万能默认——
  这在物理上是错的（AN/SPS-67 的探测距离应该是雷达地平线约束的 46.3km，
  而不是与机载雷达相同的万能 30km）。
- **头文件过重。** 845 行全部在 `.h` 中，每一次 `#include` 变更都触发
  大范围重新编译。

**具体代码位置：**

- `make_factory_default_sensor()`：第 49-94 行（46 行内联默认值初始化）
- `class DefaultUnitFactory`：第 97-845 行（745 行方法体）
- 对飞机/导弹/舰船/设施/C2 五种类型的传感器使用同一函数但只改 sensor_type

### 2.2 unit_definition.h：内容层域污染

**现状：** 164 行。原本是纯数据定义（跨域共用 DTO），本轮新增了运行时组件依赖：

```cpp
#include "components/systems/sonar.h"
#include "components/naval/embarked_air_ops.h"
#include "components/naval/ship_platform.h"
#include "components/naval/submarine_platform.h"
#include "components/physics/flight_dynamics_tuning.h"
```

问题：

- `UnitDefinition` 语义上是"JSON 加载后的中间数据容器"，应只依赖基本类型和
  自身域内容。引入 `sonar.h`（运行时传感器逻辑）、`ship_platform.h`
  （运行时物理组件）、`submarine_platform.h`（运行时物理组件）、
  `flight_dynamics_tuning.h`（模型层调谐参数）将内容层污染为对运行时
  组件图的编译依赖。
- 新增的 `NavalStoresDefinition` / `NavalLogisticsDefinition` 放在
  `content/unit_definition.h` 下。它们的自然归属应该是
  `components/naval/ship_logistics.h`——它们是舰船域的数据结构，
  不是跨域内容定义。

### 2.3 Vec3 重复定义

`missile_guidance_math.h`（新建文件）定义了：

```cpp
namespace missile_guidance { struct Vec3 { double x, y, z; }; }
// operator+, operator-, operator*, operator/, dot, cross, norm, normalize...
```

但项目已有的等效类型在 `components/basic/common.h`：

```cpp
namespace Math { struct Vector3 { double x, y, z; }; }
```

相同的数据结构，两套命名，独立的运算符实现。`default_guidance_model.cpp`
的制导逻辑每次需要在 `Vec3` 和 `Math::Vector3` 之间做字段级搬运。

正确做法：`missile_guidance_math.h` 直接使用 `Math::Vector3`，
仅将 `Vec3` 保留为 `using Vec3 = Math::Vector3` 的命名空间别名。

### 2.4 传感器工厂函数重复

同一个 Sensor 默认值被初始化了两次：

- `default_unit_factory.h:60-94` — `make_factory_default_sensor()`
- `unit_definition_loader.cpp:13` — `make_default_sensor_definition()`

二者的初始化完全一致：`reference_snr_db=13.0`、`pfa=1e-6`、
`confirm_hits_m=2`、`alpha_beta_alpha=0.65`、`alpha_beta_beta=0.12` 等。
抽取一个 `sensor_factory_defaults.h` 或 `kDefaultSensor` 常量即可消除。

### 2.5 RuntimeFacade 逃逸口已收窄到 adapter / compat view

项目文档明确把 `RuntimeFacade::runtime()` 定义为兼容/诊断逃逸口，并要求
"维护中的 Python 前端必须把访问集中在一个显式 adapter 中"。当前主线
已经完成一轮回收：raw runtime 访问不再散落在 `WorldBatchVecEnv` /
`leader_world_batch_runtime.py` 业务流程中，而是集中到
`python/rl/runtime/world_batch/adapter.py` 与 `RuntimeCompatibilityView`
这类迁移期兼容面。

- `src/interfaces/python/bindings_runtime.cpp:301`
  仍直接把 `RuntimeFacade.runtime()` 暴露给 Python，作为 compatibility /
  diagnostics 逃逸口。
- `python/rl/runtime/world_batch/adapter.py`
  在 `RuntimeFacadeAdapter` 中缓存 `self.facade.runtime()` 返回的 raw
  `WorldBatchRuntime`。
- `python/rl/runtime/world_batch_vec_env.py`
  仍公开 `batch_runtime` / `runtime_facade` 属性，但 `batch_runtime` 当前是
  `RuntimeCompatibilityView`，用于兼容仍期望旧 `vec_env.batch_runtime`
  访问面的测试和迁移代码。
- `python/rl/runtime/leader_world_batch_runtime.py`
  当前通过 `WorldBatchVecEnvAccess` 访问 `WorldBatchVecEnv` 的受控方法，
  不再直接穿透 `batch_runtime.world()` 驱动业务流程。

问题：

- **收口尚未冻结。** 兼容适配器已经隔离了旧 API，但公开属性仍容易被
  新调用方误认为维护接口。
- **边界语义被稀释。** 调用方已经不再区分"长期 facade contract"和
  "迁移期 raw runtime"，未来想真正切断 `WorldBatchRuntime` 会波及
  `leader_world_batch_runtime.py`、测试和协同执行 runtime。
- **测试仍需标注兼容语义。** `tests/world_batch/test_world_batch_vec_env.py`
  仍会断言 `vec_env.batch_runtime` / `vec_env.runtime_facade` 可用，并读取
  controller state；这些断言应继续明确为 compatibility view，而不是新
  业务代码的推荐入口。

这类问题当前不是"主线散落穿透"，而是**兼容层仍有被误用为主线接口的风险**。

补充说明：

- 本轮主线程已经开始回收这条泄漏：
  `world_batch_vec_env.py` 与 `leader_world_batch_runtime.py` 的部分 world/time-step
  访问已先收回显式 adapter，且 `tests/architecture/runtime_facade`
  已补守卫。
- 但风险并未消失。当前状态更准确的表述是：
  **“raw runtime 逃逸口已从散落业务调用收窄到兼容接口残留，尚未完成最终冻结。”**

### 2.6 ScenarioLoader 正在形成 Python 侧 God Object

`gym_envs/scenario_loader/core.py` 当前 1163 行，定义 122 个实例方法。
虽然目录上已经把 `loading/`、`reward_runtime/`、`behavior_runtime/`
等子域拆开，但 `ScenarioLoader` 仍是所有子域的唯一 owner 和总路由：

- 持有场景数据、entity roster、waypoint/mission state、reward cache、
  compiled metadata、scripted opponent state、leader/tasking bridge 等多类状态。
- 通过大量 `_foo_impl(self)` 形式把子模块逻辑重新挂回同一个类方法空间。
- 直接依赖 `examples.agents.RedScriptedAgent`
  （`gym_envs/scenario_loader/core.py:6` 与 `:1099`），形成
  `gym_envs -> examples` 的反向层依赖。

问题：

- **职责过宽。** 场景装载、行为更新、奖励结算、导航几何、脚本对手、
  运行时状态同步都需要改同一个 owner。
- **跨边界依赖。** `examples/` 本应是示例与实验入口，但当前被主线 loader
  直接 import，说明"上层目录反哺下层运行时"已经发生。
- **拆包未真正拆权。** 子模块虽然下沉了文件，但控制权和状态所有权仍集中在
  `ScenarioLoader`，后续继续加功能时仍然会回流到 `core.py`。

这已经是典型的"文件分包了，但对象边界没有分开"。

补充说明：

- 本轮主线程已经先做了 `ScenarioLoader` 状态壳抽离，并把 execution episode state
  的 mission/route/reward/runtime cache 同步逻辑集中到 `runtime_state.py`。
- 此外，`scripted-opponent` 与 `command-chain` 的第一阶段 owner 抽离已经落地：
  `build/reset/step` 生命周期与 `_leader_phase_manager`、`_naval_screen_*`
  运行态缓存已分别下沉到 `behavior_runtime/scripted_opponents.py` 与
  `behavior_runtime/command_chain_owner.py`。
- 同时，`post_waypoint_transition / mission_phase_name / _approach_prev_*`
  这组 behavior-phase 状态也已下沉到 `behavior_runtime/behavior_phase_owner.py`，
  并通过 `runtime_state.py` 的统一镜像视图保持 execution episode state 合同不变。
- 因此当前最突出的剩余问题，已经从“所有状态都挤在一个 owner”收窄为：
  **compat facade 与更深协作者切面仍滞留在 `core.py`，对象边界仍未彻底拆权。**

### 2.7 simulation_kernel_weapon_api.cpp 正在形成 Weapon 侧集成热点

当前 `simulation_kernel_weapon_api.cpp` 不再只是“发射一个导弹”的薄 API，
而是开始同时承担：

1. mission/track 选择
2. station-based launch definition 解析
3. definition tuning -> runtime tuning 转换
4. global tuning overlay
5. launch envelope 判定
6. munition / ammo / cooldown / VLS 消耗
7. missile runtime state assembly

本轮新增的 `launch envelope` 前置拒射本身是正确的，
而且行为回归当前为绿；问题在于它是叠加在一个已经持续膨胀的集成点上。

这意味着：

- 短期内它是高收益切口，因为能最快把 weapon realism 参数变成真实行为。
- 中期如果继续把 seeker activation、midcourse datalink、damage layering、
  launch authorization 等都继续塞进这里，`simulation_kernel_weapon_api.cpp`
  会演化成 Weapon 线的 God API。

因此这里的建议不是回退本轮行为改动，而是尽快把后续工作拆成：

1. launch definition resolution
2. tuning resolution / overlay
3. launch authorization / envelope policy
4. runtime state assembly

四个较清晰的协作者或 helper 层。

---

## 三、结构性问题（现在可控但会随时间恶化）

### 3.1 Kernel API 持续膨胀

`simulation_kernel.h` 在 249 行内承载 32+ 公共 API 方法名。本轮新增：

| 新增 API | 本质 | 问题 |
|----------|------|------|
| `get_unit_velocity()` | 直接读 `Velocity` 组件 | 通用 ECS 查询不适合内核公共接口 |
| `set_unit_ammo()` | 直接写 `Ammo` 组件 | 同上 |
| `set_weapon_cooldown()` | 直接写 `WeaponCooldown` 组件 | 同上 |
| `acoustic_model_` | 声学模型引用 | 内核知道一个新域的模型接口 |

模式越来越像"SimulationKernel = 所有 ECS 组件的 CRUD 门面"。
内核的公共 API 和系统中的组件数量成线性增长——每加一个新组件，
内核就需要新的 getter/setter 供 Python bindings 调用。

`RuntimeFacade` 的注释提到"逃逸口收口"——但如果 Kernel 本身
变成了逃逸口，收口就是徒劳的。正确的方向是 facde 提供类型安全的
请求/响应管道，内核不再做"通用 CRUD"。

### 3.2 系统注册的手动 Phase 链

`simulation_kernel_systems.cpp` 末尾约 50 行是顺序函数调用链：

```cpp
register_ship_motion_system(ecs);        // Phase 5.2: simple surface-ship kinematics
register_submarine_motion_system(ecs);   // Phase 5.25: simple submarine kinematics
register_sensor_system(ecs);             // Phase 6: Sensor
register_sonar_system(ecs);              // Phase 6.1: Sonar / acoustic contacts
register_embarked_air_ops_system(ecs);   // Phase 6.57: Embarked helo ...
```

内核不应该知道"潜艇"和"舰载直升机"。这些系统注册应该由
域模块通过注册接口自主完成，内核只提供注册入口。

当前设计意味着每次添加新系统（哪怕只是概念验证级别的），
都必须修改核心内核文件。在 5-10 个域的并行开发中，
`simulation_kernel_systems.cpp` 会成为合并冲突热点。

### 3.3 default_guidance_model.cpp 缺少函数级模块化

从 291 行增长到 587 行（+102%）。`update()` 方法现在混合了：

- seeker track filter（一阶低通）
- 3DoF 推进/阻力积分
- PN 加速度指令
- autopilot surrogate（一阶滞后）
- 质量消耗/燃尽检测
- track memory / reacquisition

这些都是独立可测试的制导子功能。正确的提取方向是：

```
update() →
  seeker_track(contacts, dt) → {bearing, range, closing_speed}
  propulsion_step(mass, dt)  → {thrust, mass_consumed}
  drag_force(speed, alpha)   → {drag_vector}
  pn_accel_cmd(los, closing) → {accel_cmd}
  autopilot_response(accel_cmd, dt) → {achieved_accel}
```

当前全部内联在 `update()` 的一个巨型 lambda/分支块中。

### 3.4 facade contract 还没有真正脱离 mission/episode 内部类型

`runtime/contracts` 和 `runtime/facade` 的文档都强调自己是上层 contract，
但当前 public types 仍然直接依赖 mission episode controller 的内部数据：

- `src/runtime/contracts/world_batch_contracts.h:12`
  include 了 `core/mission/episode/execution_episode_batch_prepare.h`
- `src/runtime/facade/runtime_facade_types.h:11`
  include 了 `core/mission/episode/execution_episode_controller.h`
- `src/runtime/facade/runtime_facade.h:58-73`
  公开方法直接收发 `ExecutionEpisodeState`、
  `ExecutionEpisodeRuntimeProducts`、`ExecutionBatchStepResult`

这说明 facade 现在更像"对 lower-level runtime 的薄包装"，而不是一个已经完成
抽象收口的应用层契约。

风险：

- mission/episode 内部类型一旦调整，facade header、Python bindings、
  contract tests 都会联动修改。
- facade 未来很难拆成独立 target，因为 contract header 仍然拖着
  `core/mission/episode` 的编译依赖。

### 3.5 env 入口文件承担了 bootstrap 与公共工具箱职责

`gym_envs/universal_env.py` 和 `gym_envs/leader_env.py` 在 import 阶段都自行扫描
`build-workshop/build-gpu/build` 并改写 `sys.path`，目的是优先加载仓库内的
`ef_py` 扩展。这和已有的 `python/testing/runtime.py` 中的路径引导逻辑
高度重复。

同时，`universal_env.py` 已经成为多个模块反向 import 的公共 helper 集合：

- `build_pilot_action`
- `build_universal_observation`
- `build_step_info`
- `normalize_action`
- `half_to_unit`

这些 helper 被 `python/rl/runtime/*`、`gym_envs/leader_env_parts/*`、
`examples/viz/*`、`tests/runtime/*` 共同依赖。

问题：

- **入口文件难以下沉。** 一旦 `UniversalEnv` 想继续瘦身，就会连带影响大量
  与环境类本身无关的 helper 依赖。
- **导入副作用过强。** 环境模块不只是定义 env，还在承担仓库构建目录选择与
  Python 导入治理，导致运行时逻辑和开发机目录布局发生耦合。

---

## 四、当前可接受的权衡

### 4.1 舰船/潜艇运动系统是对称设计

`ship_motion_system.h` 和 `submarine_motion_system.h` 是同一目录下
同一模式（命令驱动的响应受限运动学）的并行实现。对称设计是合理的——
潜艇的 `target_depth_m` + 3D vs 舰船的 `z=0` 是自然的领域差异，
不应强制合并为同一个系统。

### 4.2 数据链 TrackReport 去重语义正确

新增的 track 去重逻辑（position delta > 500m、velocity delta > 2m/s、
上次数据链更新 > 5s）语义上属于 `DataLinkFusionSystem` 的正确职责——
"谁该发、发什么、多久发一次"应该在数据链系统内部，不应外漏到 TrackManager。
当前实现是正确的。

### 4.3 分级毁伤枚举位置正确

`PlatformDamageState` 在 `components/combat/damage.h` 中，
`Health.mission_kill/mobility_kill/sensor_kill` 在
`components/combat/health.h` 中——这两者都属于 combat 组件束，
位置正确，没有跨域污染。

### 4.4 missile_guidance_types.h 隔离得当

`MissileGuidanceDefaults` 被抽取为独立的 `constexpr` 常量集合，
与 `default_guidance_model.cpp` 的实现逻辑分离。这允许调谐参数
在编译时确定而不污染制导逻辑。

---

## 五、关键指标

| 指标 | 真实化推进前 | 审查时 | 风险 |
|------|------------|--------|------|
| `default_unit_factory.h` 行数 | ~563 | 845 | **高** |
| `default_unit_factory.h` 跨域包含数 | ~18 | 27 | **高** |
| `unit_definition.h` 运行时组件依赖 | 0 | 5 | **中** |
| `default_guidance_model.cpp` 行数 | 291 | 587 | **中** |
| `simulation_kernel.h` 公共 API | ~25 | ~32 | **中** |
| `simulation_kernel_weapon_api.cpp` 行数 | ~225 | ~689 | **中** |
| 重复定义（Vec3 / sensor factory） | 0 | 2 | **低** |
| Kernel 知道的领域（ship/sub/sonar/helo） | 1 (ship) | 4 | **中** |
| `gym_envs/scenario_loader/core.py` 行数 / 方法数 | - | 1163 / 122 | **高** |
| `python/rl/runtime/world_batch_vec_env.py` 行数 | - | 2018 | **高** |
| facade 逃逸口公开路径 | 0 | `RuntimeFacade.runtime()` + `vec_env.batch_runtime` | **高** |
| env 自行 `sys.path` bootstrap 入口 | 0 | 2 (`universal_env.py`, `leader_env.py`) | **中** |

---

## 六、建议的最低干预

按紧迫度排列：

| # | 干预 | 目标文件 | 工作量 |
|----|------|----------|--------|
| 1 | 抽取 SharedDefaultSensor | 新建 `sensor_factory_defaults.h`，消除 `default_unit_factory.h:60-94` 与 `unit_definition_loader.cpp:13` 的重复 | 小（~30 行搬迁） |
| 2 | 拆分 default_unit_factory.h | 传感器创建逻辑 → `models/systems/sensor_factory.h`；舰船创建逻辑 → `models/naval/ship_factory.h`（新建） | 中（~200 行搬迁） |
| 3 | 消除 Vec3 重复 | `missile_guidance_math.h` 统一使用 `Math::Vector3`，通过 `using Vec3 = Math::Vector3` 提供命名空间别名 | 小（纯替换） |
| 4 | 拆分 default_guidance_model.cpp | 6 个独立子功能提取为命名空间函数 | 中（~150 行重组，无功能变更） |
| 5 | 系统注册去耦合 | 新建 `SystemRegistry` 或 `RegistrationToken` 接口，让新系统自注册而非硬编码在内核 `simulation_kernel_systems.cpp` 中 | 大（架构变更，建议 P1 后处理） |
| 6 | 收口 RuntimeFacade 逃逸口 | 不再把 `batch_runtime` 作为维护接口对外公开；为必须保留的 low-level 能力补 facade/adaptor 方法；逐步移除测试对 raw runtime 的直接断言 | 中（Python API 收敛） |
| 7 | 拆分 ScenarioLoader 的 owner 职责 | scripted opponent、behavior update、mission state、compiled metadata 分离为显式 service/state 对象；移除对 `examples.agents` 的直接依赖 | 中（结构重组，无需先改物理逻辑） |
| 8 | 抽出 env bootstrap 与共享 helper | 把 `ef_py` build 目录选择收敛到统一 bootstrap 模块；把 `universal_env.py` 中的公共 helper 提到独立 support 模块 | 中（导入路径调整） |

---

## 七、审查结论

本轮真实化推进的代码在**物理正确性方向上是成功的**——142 个新增行（单个文件峰值）
足以覆盖导弹制导的重写、推力瞬态的引入、和声纳域的从零搭建。

但在**结构维护性方向上有三个清晰的警告信号**：

1. **God Factory** 正在成型——如果不拆，下一轮海战/声纳/潜艇的完善会让
   一个文件突破 1000 行。
2. **内核 API 线性膨胀**——每新增一个组件就需要新 getter/setter 的模式
   不能持续。需要 before-next-wave 引入 facade 请求管道。
3. **头文件污染**——`unit_definition.h` 从纯数据定义污染为运行时组件依赖图。
   需要立即回溯。
4. **Python 编排层开始进入局部高熵区**——`ScenarioLoader` 总管化、
   `WorldBatchVecEnv` 重新暴露 raw runtime、`universal_env.py` 变成
   公共工具箱兼 bootstrap 入口。如果不在这一轮收口，下一轮问题会从
   "局部热点"演化成"主线接口事实失控"。

干预 #1-#4 建议在 P1 收尾前完成（预计总工时 < 半天）；干预 #6-#8
建议至少完成设计冻结或第一轮收口，否则 facade / env / loader 三者之间的
耦合会继续放大；干预 #5 建议纳入下一轮架构整理（P1 后）。

本审查冻结到下一次大规模代码变更前为止。
