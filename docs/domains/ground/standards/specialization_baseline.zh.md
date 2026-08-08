# Ground 特化基线

语言：[英文规范页](specialization_baseline.md)；本页为中文配套。

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/domains/ground/standards/specialization_baseline.md`
Owner: `domains/ground`
Last verified: `2026-08-08`

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
- `src/models/domains/ground/` 拥有显式 effects placeholder route，用于保留旧有的
  finalize-only 行为；它不是已释放的 Ground effects model。
- 原生与 compatibility-shell Ground 场景使用共享 loader 和 tasking bridge，
  不建立私有 Ground runtime 路径。

当前不存在已接受的 `src/systems/domains/ground/` owner。该目录不存在表示 Ground
runtime-system ownership 仍保持 held，并不把 Ground 执行语义授权给其他领域。

## 内容与 Capability 规则

- 新的维护中 Ground unit definition 必须使用原生 Ground 身份，不得使用
  `Aircraft` 替代物。
- `Ground_Platoon_MVP` 可以作为原生 schema 加载、静态身份、health/state inspection
  和静态 task/status 链的证据。
- 生成 `Aircraft` 的 compatibility-shell 场景可以继续作为 regression fixture，
  但必须声明该边界，也不得被引用为原生 Ground 平台证据。
- 当前 `ground_mobility_flat_deferred` 声明和
  `static_or_caller_initial_velocity_only` 行为不得被描述为 route movement 或
  terrain mobility。
- 后续 Ground system、model 或场景必须扩展共享 runtime stage 与合同，不得引入
  Ground 私有 scheduler、packet family 或 command/status pipeline。

## Held 边界

当前维护面尚未建立：

- route following、movement dynamics、terrain traversal、passability、cover、
  concealment、obstacle 或 breach behavior；
- Ground sensing、line-of-sight 计算、track fusion、data-link behavior 或
  observation export；
- direct fire、indirect fire、effects、damage、suppression 或 attrition；
- logistics、sustainment、recovery 或 learned Ground policy；
- 正式 Ground `CommandPacket`、`ObservationPacket` 或 `TrackPacket` 特化。

这些领域必须先具备独立标准与验收证据，任务或场景才能把它们声明为维护中能力。

## 验证

当前证据锚点：

- [Ground component 边界](../../../../src/components/domains/ground/README.zh.md)
- [Ground tasking component 边界](../../../../src/components/domains/ground/tasking/README.zh.md)
- [Ground model placeholder 边界](../../../../src/models/domains/ground/README.zh.md)
- [Ground 原生平台 schema 测试](../../../../tests/runtime/ground/test_ground_native_platform_schema.py)
- [Ground 原生静态场景测试](../../../../tests/runtime/ground/test_ground_native_static_scenario.py)
- [Ground realism-gradient 护栏](../../../../tests/architecture/ground/test_realism_gradient_guardrails.py)

## 非目标

本标准不授权工作、不定义 Army 条令，也不把当前静态 MVP 提升为完整 land-warfare
模型。Active work 与成熟度裁决属于 [Ground 任务区](../../../task/ground/archive/owner_migration_20260808/README.zh.md)。
