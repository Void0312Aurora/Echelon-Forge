# ADR：版本化平台蓝图与能力组装

语言：
- 英文规范页：[platform_blueprint_assembly_adr.md](platform_blueprint_assembly_adr.md)
- 中文配套页：`platform_blueprint_assembly_adr.zh.md`

Document kind: `standard`
Lifecycle: `proposed`
Canonical: `docs/architecture/standards/platform_blueprint_assembly_adr.md`
Owner: `architecture/content-contracts`
Last verified: `2026-11-26`

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

原型记录模块参数 digest 和 native ref，校验有限数值及边界，并显式映射到现有 UnitDefinition 字段。新增质量、功耗预算和槽位安装类别检查，在发布前拒绝不兼容组装。显式 hardpoint contract 与 loadout selection 现在校验安装类别、允许的 module kind、数量、容量、物理元数据和 native identity，并将这些值纳入 canonical plan identity；legacy lowering 仍要求声明 loadout 写入路径及匹配证据，避免选择的 loadout 在投影时静默丢失。`UnitDefinition::default_loadout` 保留旧版单字符串格式，并接受有序字符串数组表达同一 station 的多个载荷。原生 factory 在发布前校验引用、导弹类型、非空数组、有效挂点容量、载荷质量和挂点累计质量；生成时按 station 和数组顺序创建稳定命名的载荷实体，释放时按序号还原对应 weapon 定义。F-16 的两枚 AIM-120C-7 改放在 300 kg 的 2、8 号挂点，两枚 AIM-9X 留在 150 kg 翼尖挂点。现有内容审计发现 Su-35 的两处 R-73 引用无法解析，且 190 kg 的 R-77-1 超过 150 kg 翼尖挂点容量，因此维持未准入，待内容记录和挂点分配修复。typed bridge 在 native projection 与请求身份中保留数量，并将完整 legacy 定义 digest 纳入 ID；若 lowering 改变快照则拒绝。它同时使用 authored capability key 到 native capability family 的带版本资格映射，把映射摘要纳入 typed request identity，并在 DTO 发布前拒绝未知 key。source type/capability 语义仍须与原生 factory plan 一致。`WorldBatchRuntime` 通过只读查询暴露 factory 解析计划；只有 factory 负责实例化。F-16 与地面步兵已验证初始化及四步后的公开观察一致性。owner 批准的 mapping、回滚行为、更广泛的 native 单位兼容性和生产审查仍待验收。

详见[原型证据和剩余门槛](../work/issues/rfc_qualified_composition_implementation.md)。Lifecycle 仍为 proposed；此检查点不代表 owner 批准或生产准入。

## Issue #293：消费者、所有权与冗余桥接收敛

F-16 与地面单位共享同一条所有权链路：
1. 原始 `PlatformBlueprint`、模块记录、选择与覆盖经 `platform_blueprint.resolve_platform_assembly` 校验结构、能力、物理与覆盖契约，并生成带私有解析密封摘要（resolver seal）的规范化 `ResolvedPlatformSpawnPlan`；
2. `LegacyUnitProjection` 将显式路径绑定至递归冻结的不可变源快照；`lower_to_legacy_unit_definition` 保留为修改后组装导出及旧版 JSON 导入的兼容路径，`UnitDefinitionLoader` 仍是加载入口；
3. `platform_blueprint_adapter.to_expanded_typed_platform_request` 绑定计划、快照与能力词汇表并生成 `ExpandedTypedPlatformRequest`；
4. `capability_bundles.bindings_adapter` 构造原生 DTO，`RuntimeFacade.apply_world_setup` 与既有的 `DefaultUnitFactory` 仍是唯一的实例化与准入权威。

### 冗余收敛与边界保留

- **已消除冗余**：对于携带有效 resolver seal 的规范化计划，桥接层改为基于当前蓝图/所选模块重算印章一致性校验，不再二次调用 `resolve_platform_assembly`；对于未变的冻结 `LegacyUnitProjection` 快照，通过共享映射字段检查及构建期规范 JSON 摘要确认等价性，不再重复生成、解冻并序列化整份 `UnitDefinition` 副本。外部直接构造或 `dataclasses.replace` 生成的无印章计划仍回退走完整重解析与全量公开字段比对，确保安全边界不退化。
- **保留边界**：外部输入约束、单挂点 `quantity == 1` 限制（拒绝非 1 与布尔值）、模块证据/物理/原生身份校验、工厂 `validate_factory_resolved_capability_plan` 对等校验，以及旧版 JSON（单字符串与有序载荷数组）导入兼容性全部完整保留。
- **测试覆盖**：以 `f16c_block50.json` 与 `ground_infantry_soldier_mvp.json` 验证规范桥接不触发重复解析/降级/解冻、与完整重校验副本完全等价，并在具备本地 `ef_py` 构建的环境中验证初始化及连续 4 步后的 `AgentObservation` / `InstrumentState` 及 F-16 `default_loadout` 与传统生成路径一致；负向样例覆盖陈旧蓝图、模块物理/证据/能力漂移、直接修改计划与外部无印章计划错误。无本地 `ef_py` 构建时仅运行纯内容测试不能单独证明原生执行等价性。
