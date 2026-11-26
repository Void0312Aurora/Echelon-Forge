# ADR：类型化机制端口与递归组合

语言：
- 英文规范页：[typed_mechanism_ports_adr.md](typed_mechanism_ports_adr.md)
- 中文配套页：`typed_mechanism_ports_adr.zh.md`

Document kind: `standard`
Lifecycle: `proposed`
Canonical: `docs/architecture/standards/typed_mechanism_ports_adr.md`
Owner: `architecture/mechanism-contracts`
Last verified: `2026-11-26`

**状态：** 待评审的资格验证设计；不启用生产路径。

## 决策

采用独立的机制图描述层，并将其编译到现有 composition 与 stage 契约。不新增第二套运行时
执行引擎，也不引入无类型的 `execute(anything)` ABI。机制适配器声明带版本的输入/输出端口、
单位、坐标系、时钟语义、可见性、所需能力、状态所有权和效果义务。

编译器必须在 provider 或 world 发布前完成图验证，生成仅用于资格验证的规范化图产物，再通过
现有 composition requested/resolved 产物和 native execution graph 接纳。native runtime 仍是
唯一执行权威。

## 约束

连接必须检查 schema 版本、单位、坐标系、新鲜度和可见性；owner 提供 schema vocabulary 时，未知
schema 必须在发布前拒绝。vocabulary 是不可变且带版本的资格产物；每个 schema 条目都标明 owner
引用，vocabulary 摘要会参与图身份；需要转换或估计时必须显式插入节点，
不得凭空制造信息。禁止同一窗口内的瞬时环；延迟反馈必须声明正的边延迟，并将源节点作为状态所有者，且其状态窗口必须覆盖该边。组合
节点导出类型化公共端口及状态/效果契约后，才能作为父图中的节点重新验证。

首个证明应放在资格验证路径，包含兼容连接、单位/坐标系或 schema 冲突、禁止环、子机制故障和
递归组合；不得改变 `builtin.default_compatibility` 或 facade/Cordis 的既有行为。

最小语义表为：端口边检查物理单位和坐标系；每秒值由有状态 owner 模型积分，每 tick 值必须显式
标记；采样/新鲜度属于端口契约；状态写入只在 owner 的 publication/commit barrier 后可见；延迟
反馈必须声明正的边延迟和源节点状态 owner。这些检查不证明数值标定或 timestep 不变性。

## 方案比较与实现检查点

方案比较以英文规范页的 Option comparison 为准。

原型已补齐递归输入闭包、能力与时钟继承、信息层、多生产者和 freshness 校验。资格适配器现在消费
owner 提供的 `StageNodeManifest` 快照，要求节点一一绑定，并在检查显式 native system
映射顺序前拒绝 adapter/diagnostic-only stage。native `WorldBatchRuntime` 还以只读副本
暴露维护中的 manifest registry 供资格诊断使用，不会安装或修改 scheduler node。不可变参数、backend 引用与 clock policy
参与图和组合身份。严格 stage admission 还要求 owner 契约字段并拒绝重复 state-shard writer；
默认资格模式仍兼容较小的证据 fixture。另有独立的静态 projection 为每个 authored node
记录 owner contract 快照，并绑定图、manifest registry 和 edge 的稳定摘要；它直接接受
native snapshot 的对象形状，若存在 realized-system 名称也只作为补充的顺序证据。该
projection 明确标记为不可执行，并拒绝无效、重复、adapter-only 和 diagnostics-only 绑定。
多个 owner vocabulary 现在可以合并为带版本的 qualification registry；只有 owner 相同的重复
schema 才会合并，owner 冲突会 fail closed。该 registry 只是显式 owner 证据的组合 seam，
不表示全仓库 canonical packet vocabulary 已经完整，也不提供可执行 dispatcher。

## 所有权与保留审计（#292）

Cordis admitted catalog lock 负责 descriptor 的准入、`owner_id`、category authority、capability、
实现及版本、来源与信任决定；其 lock 身份、版本、canonical bytes 与摘要仍由现有 native
composition 契约负责。它不定义 Air 试点的细粒度端口 schema、单位、坐标系或采样语义。
`StageNodeManifest` 负责 stage 的 packet 名称、状态分片及发布策略；packet 名称也不能代替类型化
端口兼容性。完整逐字段对应关系以[英文规范页的审计表](typed_mechanism_ports_adr.md#ownership-and-retention-audit-292)为准。

| 类型与字段 | 所有权与保留决定 |
| --- | --- |
| `MechanismSchemaVocabulary.vocabulary_id`、`version`、`entries`（`schema`、`owner_ref`） | owner 提供的编译输入；保留独立命名空间、版本和 schema 所有权。`schema_names` 与 `identity_digest` 为派生视图；`owner_ref` 不表示 Cordis 已准入或信任该实现。 |
| `MechanismSchemaVocabularyRegistry.registry_id`、`version`、`vocabularies` | 编译器输入视图，**不是单独持久化的产物或 catalog lock**。`vocabulary_id` 是 `registry_id` 的接口别名。 |
| Registry 的 `entries`、`schema_names`、`identity_digest` | 从排序后的 owner vocabulary 派生，移除单独存储的 merged entries。相同 owner 的重复 schema 合并，冲突在构造时拒绝；序列化内容和摘要保持兼容。 |
| `NativeStageContractProjection.node_id`、`authored_node` | 保留 authored 节点绑定及端口、时钟、状态、实现、capability、backend、clock policy 证据；parameters 由图摘要绑定。 |
| `NativeStageContractProjection.owner_contract` | 保留与源对象分离且冻结的 native 快照，禁止由 Python authored ports 推导 native manifest。 |
| `stage_node_id`、`owner_module`、`identity_digest` | 从冻结的 owner contract 与现有绑定 payload 派生，移除独立存储；保留原有序列化别名及摘要字节。 |
| `StageManifestQualificationProjection.graph_identity_digest`、`manifest_registry_digest` | 分别保留 authored 图身份与按图节点顺序绑定的 manifest 快照摘要。后者不是完整 runtime registry 或 Cordis lock 的摘要。 |
| `node_contracts`、`edge_bindings`、`identity_digest`、`qualification_only`、`executable` | 保留 owner 绑定、含延迟窗口及状态 owner 的边、组合资格身份与显式不可执行标记。它们不授予 scheduler 准入权。 |

owner 快照保留 `node_id`、`semantic_stage`、`owner_module`、`input_packets`、`output_packets`、
`read_state_shards`、`write_state_shards`、`read_snapshot_policy`、`write_commit_policy`、
`clock_domain`、`latency_policy`、`sync_policy`、`allowed_same_window_edges`、`required_barriers`、
`event_families_emitted`、`diagnostic_trace_obligations`、`facade_visibility`、
`adapter_projection_allowed`；可选 legacy `native_system` 仅补充 realized order 证据。
验证与计算摘要使用同一份分离后的值。native validator 未经 Python binding 暴露，因此对外部 mapping
fixture 的字段形状、publish barrier、event 检查仍需保留；绑定闭包、节点身份、writer 冲突和顺序检查
属于 authored selection 的边界。端口 freshness、visibility 和数值时钟与 manifest 发布/读取、延迟、
facade 可见性各有语义，均不能相互代替。

native manifest 没有独立版本计数器，带版本的 `node_id` 和完整快照内容共同参与摘要。复用资格证据时可
提供 `expected_manifest_registry_digest`；快照不匹配会以 `mechanism.native_stage_manifest_stale`
拒绝，同一 node ID 下的策略变化也会触发。未指定预期摘要时仅验证传入快照，不声称它是当前 runtime
registry。回归测试固定既有 vocabulary、图、节点、manifest、projection 和 Air seeker composite 摘要；
native 集成测试把 Air launch-to-observation 图绑定到实际 `fire_control_launch.v1` 与
`observation_export.v1` 快照。三个 seeker helper 没有独立的 native scheduler manifest。
此次不变更 schema、实现、manifest 或 canonicalization 版本。

这仍是静态机制图契约试点。qualification/shadow 编译和生产接纳是分开的 gate；通过现有
manifest machinery 产出的 artifact 不会自动变成可执行机制。

受限 Air seeker 证明复用现有 native 视线转换、距离/世界坐标投影和有状态 CV 跟踪器，区分
窗口发布与每秒数值语义。固定测量时刻下，四种步长到达同一 4 秒终点，结果满足记录的容差。
测试路径在 tracker 更新后、外部 packet 发布前注入异常，并复用 #251 投影为未知状态；
该证据不证明回滚。当前 Air 资格路径在编译时强制六个 schema 的显式 vocabulary，这是针对三个
既有 native 实现的受限 owner 映射，且 vocabulary 摘要会绑定到图身份；它不是全仓库 packet vocabulary。snapshot 发布 seam 仅用于诊断，
不会把用户编写的图安装进 native 调度；跨域 schema 选择和 authored graph 接纳仍是独立 gate。

延迟边必须声明正的延迟窗口，并将边的源节点声明为状态拥有者，且源节点的状态窗口必须覆盖该边；组合机制保留节点/边声明的最大延迟窗口。详见[原型证据和剩余门槛](../work/issues/rfc_qualified_composition_implementation.md)。Lifecycle 仍为 proposed；此检查点不代表 owner 批准或生产准入。
