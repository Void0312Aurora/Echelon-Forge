# ADR：版本化平台蓝图与能力组装

语言：
- 英文规范页：[platform_blueprint_assembly_adr.md](platform_blueprint_assembly_adr.md)
- 中文配套页：`platform_blueprint_assembly_adr.zh.md`

Document kind: `standard`
Lifecycle: `proposed`
Canonical: `docs/architecture/standards/platform_blueprint_assembly_adr.md`
Owner: `architecture/content-contracts`
Last verified: `2026-10-12`

**状态：** 待评审的资格验证设计；旧 unit JSON 和 native materialization 仍是权威。

采用可选的平台蓝图/组装 authoring 投影，并将其编译到现有 `UnitDefinition`、
`CapabilityBundle` 与 `ResolvedPlatformSpawnPlan` 契约；受限的
`platform_blueprint_adapter` 只有在绑定到未改变的 legacy `UnitDefinition` 快照时，
才能把已解析的资格计划投影为现有的 `TypedPlatformSpawnRequest` 形状。会改变模块绑定或
覆盖值的计划，必须先走既有 legacy lowering 和 loader 路径。不替换 unit database 或 `DefaultUnitFactory`。
只有 native factory 可以 materialize ECS entity。

逻辑产物分为研究/装备证据、版本化模块、带类型槽位约束的平台蓝图、显式模块选择和白名单
覆盖的组装、scenario instance，以及交给 native admission/materialization 的规范化 resolved
spawn plan。研究资料不会自动变成可生成内容。

验证必须在发布前 fail-closed：schema/version、引用种类与版本、依赖闭包、槽位基数、单位/物理
范围、能力兼容性、证据状态和 native plan。未知必需引用、重复槽位、不支持能力、非法覆盖均在
mutation 前拒绝；稳定 ID 只由逻辑 ID、版本、解析引用和类型化覆盖组成，不依赖路径或遍历顺序。

首个证明应覆盖一个 Air 和一个 Naval/Ground 平台，并保持现有 `load_database`、`spawn_unit`
与生产 profile 不变。

## 方案比较与实现检查点

方案比较以英文规范页的 Option comparison 为准。

原型记录模块参数 digest 和 native ref，校验有限数值及边界，并显式映射到现有 UnitDefinition 字段。新增质量、功耗预算和槽位安装类别检查，在发布前拒绝不兼容组装。显式 hardpoint contract 与 loadout selection 现在校验安装类别、允许的 module kind、数量、容量、物理元数据和 native identity，并将这些值纳入 canonical plan identity；legacy lowering 还要求声明 loadout 写入路径及匹配证据，避免选择的 loadout 在投影时静默丢失。typed bridge 将完整 legacy 定义 digest 纳入 ID；如果 lowering 会改变该快照则拒绝；同时使用 authored capability key 到 native capability family 的带版本资格映射，将映射摘要纳入 typed request identity，并在 DTO 发布前拒绝未知 key。它还可将共享的 source type 与已 admitted 的 native factory plan 比对，family、capability type、implementation ref 及 required/supported flags 必须一致。`WorldBatchRuntime` 还通过只读查询暴露 factory 已解析的 plan 供资格诊断使用；只有 factory 负责 materialize。F-16 与地面步兵已验证初始化及四步后的公开观察一致性；另有 F-16 证明通过现有 typed request 路径生成，并在四步后保持观察一致。更广泛的 native 单位兼容性和 owner 生产审查仍待验收。

详见[原型证据和剩余门槛](../work/issues/rfc_qualified_composition_implementation.md)。Lifecycle 仍为 proposed；此检查点不代表 owner 批准或生产准入。
