# ADR：版本化平台蓝图与能力组装

语言：
- 英文规范页：[platform_blueprint_assembly_adr.md](platform_blueprint_assembly_adr.md)
- 中文配套页：`platform_blueprint_assembly_adr.zh.md`

Document kind: `standard`
Lifecycle: `proposed`
Canonical: `docs/architecture/standards/platform_blueprint_assembly_adr.md`
Owner: `architecture/content-contracts`
Last verified: `2026-10-10`

**状态：** 待评审的资格验证设计；旧 unit JSON 和 native materialization 仍是权威。

采用可选的平台蓝图/组装 authoring 投影，并将其编译到现有 `UnitDefinition`、
`CapabilityBundle` 与 `ResolvedPlatformSpawnPlan` 契约；不替换 unit database 或
`DefaultUnitFactory`。只有 native factory 可以 materialize ECS entity。

逻辑产物分为研究/装备证据、版本化模块、带类型槽位约束的平台蓝图、显式模块选择和白名单
覆盖的组装、scenario instance，以及交给 native admission/materialization 的规范化 resolved
spawn plan。研究资料不会自动变成可生成内容。

验证必须在发布前 fail-closed：schema/version、引用种类与版本、依赖闭包、槽位基数、单位/物理
范围、能力兼容性、证据状态和 native plan。未知必需引用、重复槽位、不支持能力、非法覆盖均在
mutation 前拒绝；稳定 ID 只由逻辑 ID、版本、解析引用和类型化覆盖组成，不依赖路径或遍历顺序。

首个证明应覆盖一个 Air 和一个 Naval/Ground 平台，并保持现有 `load_database`、`spawn_unit`
与生产 profile 不变。
