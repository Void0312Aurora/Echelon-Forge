# Ground 特化基线

语言：[英文规范页](specialization_baseline.md)；本页为中文配套。

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/domains/ground/standards/specialization_baseline.md`
Owner: `domains/ground`
Last verified: `2026-09-24`

## 范围

本标准定义稳定的 Ground 特化边界，以及当前仓库证据实际支持的声明。它规范
Ground 身份、内容与 component 所有权，并区分已接受的静态基础设施和仍保持
held 的执行行为。

它不拥有 Joint command relationship、Army 军种组织或跨域 runtime 架构。

## 规范身份与路由

- 维护中的特化名必须是 `ground`。
- 文本 alias `army`、`ground`、`land` 以及 `ServiceProfile.Army` 必须路由到
  维护中的 `ground` tasking profile。
- `Army` 必须保持为 service profile，`land` 必须保持为 alias。二者都不得建立
  额外 runtime 栈或文档 owner。
- 未知的显式 tasking profile 或 service-profile hint 必须 fail closed，不得静默
  回退到 Ground。
- Joint/common-core 命名和授权关系必须继续归
  [Joint 标准](../../joint/standards/command_and_modeling_baseline.zh.md)所有。
  Army 专属组织和军种解释仍归
  [Army service profile](../../joint/service_profiles/standards/army_profile.zh.md)。

## 已接受实现基线

以下表面已经实现并有测试支撑：

- Python binding 已暴露 `UnitType::Ground`。
- `Ground_Platoon_MVP` 是 runtime 可加载的原生内容定义，包含
  `specialization=ground`、`service_profile=Army`、
  `tasking_profile=ground`、`echelon=platoon`、
  `platform_family=dismounted_unit` 和 `doctrine_family=land_tactics`。
- `src/components/domains/ground/` 拥有 Ground component slice。当前 command/tasking
  slice 仅是静态 G0/G1 元数据，不是执行动力学。
- 原生与 compatibility-shell Ground 场景使用共享 loader 和 tasking bridge，
  不建立私有 Ground runtime 路径。
- `Ground_Infantry_Soldier_MVP` 是原生的单兵 fixture，其 `MoveStatic` 命令由受限的
  `GroundInfantryMovement` 系统消费。该系统应用地表与坡度速度代价并推进一个水平
  运动学步；它不建立 route following 或完整的单兵动力学模型。

## 已注册且可达，但不构成能力

`src/models/domains/ground/` 拥有结构化的 ground effects 路由。只有在 ground 自有的
`GroundPlatformDamageState` 与共享的 hitbox、system-health、platform-damage 界面同时
存在时它才选中目标；它把战斗部机制负载写进 ground state，把该 state 投影到共享
capability 字段，然后调用共享 finalize。组件 id 在组合路径里按 world 解析一次并传给该
路由——effects 侧不再靠解析组件类型去找它——因此该路由会选中，机制会运行。`2026-09-22`
实测：一次结构命中后共享 capability 向量为 `[0.8167, 1.0000, 0.9010, 0.8680]`，而不是
placeholder 兜底的"全零并被摧毁"；在多 world 进程里每个 world 都给出同一后果。修复与
测量记录见
[Ground Damage Effects Route Repair](../../../domains/ground/work/active/ground_damage_effects_route_repair/README.md)。

机制可达仍不等于能力。这不是已释放的 Ground effects model：任何 Ground 任务、场景或
observation 声明都不得以它为依据。目前任何弹头类型的 Ground 命中都不会降低 mobility：effects
model 只对结构化空中目标估算弹头机理载荷，因此 Ground 路径永远到不了底盘的 mobility 和履带
分支。`2026-09-28` 撤回了"命中应降低 mobility"这一期望，没有用未校准的物理去满足它；现行契约
由一个运行时测试钉住，按部件推导机动损失的后续议题及其进入条件记录在 route-repair 包中。
定位该缺陷的**修复前**测量见
[DM-G1 可达性诊断](../../../systems/combat/reviews/ground_damage_reachability_20260921.md)。

`src/systems/domains/ground/` 拥有 Ground 的 per-tick systems 面。地面损伤响应由
`src/systems/domains/ground/damage_system_ground.h` 注册为默认组合 stage 30 的
`builtin.system.ground_damage`，另由
`src/systems/domains/ground/movement_system.h` 注册
`builtin.system.ground_infantry_movement` 为 stage 34。后者只是单兵 fixture 的受限
单步消费者，不释放 route movement、passability、sensing、fires、logistics 或
observation export。准入记录见
[Ground Infantry Movement v1](../work/active/ground_infantry_movement_v1/README.zh.md)。

## 内容与 Capability 规则

- 新的维护中 Ground unit definition 必须使用原生 Ground 身份，不得使用
  `Aircraft` 替代物。
- `Ground_Platoon_MVP` 可以作为原生 schema 加载、静态身份、health/state inspection
  和静态 task/status 链的证据。
- 生成 `Aircraft` 的 compatibility-shell 场景可以继续作为 regression fixture，
  但必须声明该边界，也不得被引用为原生 Ground 平台证据。
- platoon 的 `ground_mobility_flat_deferred` 声明和
  `static_or_caller_initial_velocity_only` 行为不得被描述为 route movement 或
  terrain mobility。单兵声明只能引用上面准入的受限 `MoveStatic` 地表/坡度步。
- 后续 Ground system、model 或场景必须扩展共享 runtime stage 与合同，不得引入
  Ground 私有 scheduler、packet family 或 command/status pipeline。

## Held 边界

当前维护面尚未建立：

- route following、加速度/疲劳/队形 dynamics、terrain traversal、passability、cover、
  concealment、obstacle 或 breach behavior；
- Ground sensing、line-of-sight 计算、track fusion、data-link behavior 或
  observation export；
- direct fire、indirect fire、effects、damage、suppression、attrition 或 combat runtime；
- logistics、sustainment、recovery 或 learned Ground policy；
- 正式 Ground `CommandPacket`、`ObservationPacket` 或 `TrackPacket` 特化。

这些领域必须先具备独立标准与验收证据，任务或场景才能把它们声明为维护中能力。机制可达
不是这种证据：ground damage 机制现在会运行，并对运行时套件所测的那一次命中给出上面的
实测后果，但这仍不使 effects、damage、suppression 或 attrition 成为 Ground 能力、场景
声明或本域可以依赖的模型。

## 验证

当前证据锚点：

- [Ground component 边界](../../../../src/components/domains/ground/README.zh.md)
- [Ground tasking component 边界](../../../../src/components/domains/ground/tasking/README.zh.md)
- [Ground model 边界](../../../../src/models/domains/ground/README.zh.md)
- [Ground 原生平台 schema 测试](../../../../tests/runtime/ground/test_ground_native_platform_schema.py)
- [Ground 原生静态场景测试](../../../../tests/runtime/ground/test_ground_native_static_scenario.py)
- [Ground 原生单兵移动测试](../../../../tests/runtime/ground/test_ground_infantry_native_unit.py)
- [Ground 损伤响应测试](../../../../tests/runtime/ground/test_ground_damage_response.py)
- [Ground realism-gradient 护栏](../../../../tests/architecture/ground/test_realism_gradient_guardrails.py)

## 非目标

本标准不授权工作、不定义 Army 条令，也不把当前静态 MVP 提升为完整 land-warfare
模型。Active work 与成熟度裁决属于 [Ground 所有者入口](../../../domains/ground/README.zh.md)。
