# ADR：兵力包与群组组合

语言：
- 英文规范页：[force_package_composition_adr.md](force_package_composition_adr.md)
- 中文配套页：`force_package_composition_adr.zh.md`

Document kind: `standard`
Lifecycle: `proposed`
Canonical: `docs/architecture/standards/force_package_composition_adr.md`
Owner: `architecture/joint-contracts`
Last verified: `2026-11-26`

**状态：** 待评审的资格验证设计；现有 scenario expansion 与 Joint/tasking 契约仍是权威。

定义可复用、带版本的 force-package authoring 投影，描述 unit assembly、角色、包含关系、
指挥关系和布局，并编译到现有 scenario entity 与 Joint/tasking 契约。通用编译器不成为第二套
ECS、命令或领域战术权威。

成员可引用平台蓝图组装或有限的嵌套 package，展开必须形成确定性 DAG；环、重复 scoped ID、
未解析 import 及冲突 side/role 约束在创建 entity 前拒绝。成员关系、任务权威、通信连接和动态
orders 分开处理；嵌套不会自动授予命令、无线电或信息权限。Air/Naval/Ground 的编队、舰载库存
和领域几何由各自 adapter 负责。现有 CSG compiler 通过显式 adapter 保留。

资格验证应覆盖 Air 编队、Naval 群组、Ground squad、嵌套 package 及失败样例；生产启用需经过
schema/identity、native Joint/tasking admission 和领域 owner 审查。

## 方案比较与实现检查点

方案比较以英文规范页的 Option comparison 为准。

编译结果及身份计算已保留实例作用域内的关系，校验嵌套角色能力，并保留 frame、anchor 与 provenance 引用。资格适配器要求显式提供 entity 与 assembly 映射，校验 group/entity/inventory 元数据，并只把新鲜且完整通过资格的快照交给现有 loader。named 和 mirror 两个 S0 fixture 的 native 坐标与 replay 帧保持一致；CSG 位置、geodesy 和 native materialization 仍由原 owner 负责。命令和库存迁移仍待验收；关系记录本身不会授予指挥权限。

详见[原型证据和剩余门槛](../work/issues/rfc_qualified_composition_implementation.md)。Lifecycle 仍为 proposed；此检查点不代表 owner 批准或生产准入。

## 资格快照与摘要归属（Issue #294）

适配器保留既有 `CsgForcePackageQualification` 字段与摘要编码。外层冻结的 dataclass 仅包含标量值与标量元组，而编译后的场景仍持有可变字典；冻结外层对象并不能阻止在资格验证（qualification）与发布加载（publication）之间被原地篡改。因此，发布前仍须对当前输入执行完整校验，且仅在校验全部通过后调用一次既有的 `load_compiled_scenario`。这是同步跨阶段防篡改守卫，而非对外部调用方自述证据的密码学认证或并发读写保护。

| 资格摘要 | 所属所有者与覆盖内容 | 分类与发布期校验 |
| --- | --- | --- |
| `package_identity_digest` | 通用兵力包编译器：schema、package reference、entities（含 role/side/assembly/provenance）、relationships、package instances（含 frame/anchor/provenance）与 assembly/native-type 绑定 | 公开身份证据与 TOCTOU 守卫。校验独立传入的 compiled package reference 与 identity，并通过 `CompiledForcePackage.is_fresh()` 重新计算完整 v1 身份；仅存下摘要不足以防止可变记录被替换或修改。 |
| `entity_bindings_digest` | CSG 适配器：按序排列的显式 scoped-ID / native-name 对 | 公开绑定证据与绑定表 TOCTOU 守卫。每个 qualification 重算一次，同时校验排序、基数、唯一性、投影范围与完整 CSG 实体覆盖；它本身不单独证明 role/type/member 语义正确。 |
| `scenario_digest` | Scenario 编译器 / CSG 适配器：完整合并后的场景（含实体几何、`csg_member` 身份、库存、元数据与环境） | 公开快照证据与全场景 TOCTOU 守卫。比较当前校验摘要与已资格认证值：在 `scenario.is_fresh()` 成功后直接复用等价的 `semantic_digest`，旧输出缺省时显式哈希。即便场景是新近重编译且 fresh 的，只要内容改变仍会拒绝发布。 |
| `embarked_inventory_digest` | CSG 所有者：所选群组的完整舰载库存 | 由 `scenario_digest` 已覆盖子集派生的公开领域证据。每次 qualification 重算一次以维护公共字段及下游兼容性，不是独立库存权威。 |
| `geometry_digest` | CSG 所有者：`meta.csg.geometry` 完整投影 | 由 `scenario_digest` 已覆盖子集派生的公开领域证据。在 qualification 阶段与 publication 调用阶段各计算一次、与 `evidence_refs` 复用结果并保留比对，保证篡改该字段仍被拒绝。 |
| `compiled_relationships_digest` | 适配器投影的通用 package 关系（含 package 归属） | 由 package identity 子集派生的公开关系证据。在发布校验中重算并与显式 `relationship_edges` 一同对比；关系仅作证据记录，不授予指挥控制权限。 |

`evidence_refs` 将 package、relationship、scenario 与 geometry 身份重复整理为可读索引，不是额外摘要或准入凭据；`entity_binding_projection` 与 `relationship_edges` 属于显式证据而非摘要，发布期均保留比对。

### 重复校验审计与收敛结论

- **跨阶段必须保留（共享代码但各自执行）**：`Scenario.is_fresh()`（含导入文件 mtime 与 OOB provenance）、CSG 运行时元数据与合并元数据一致性、独立传入 package 的完整 `CompiledForcePackage.is_fresh()` 校验、绑定范围/成员/原生类型校验，以及发布前群组完备性与 package 覆盖校验。
- **已收敛冗余计算**：`scenario.is_fresh()` 刚算过规范载荷时直接复用 `semantic_digest`（空值保留显式哈希）；`evidence_refs` 直接复用已算出的 `geometry_digest`；单次发布循环内合并对同一 compiled package 引用/身份/关系摘要的重复抓取与校验，同时令 `CompiledForcePackage.as_dict()` 返回深拷贝分离的记录字典，防止修改导出证据反向污染已编译记录。
- **测试覆盖**：负向固件覆盖几何与引导坐标、库存数量/类型/宿主、role/side、实体/成员/群组绑定与归属、package 图/frame/anchor/provenance/native-type 漂移、以及场景元数据/环境篡改（含原地篡改、清空 `semantic_digest` 篡改与新编译替换场景），确保全部在调用 loader 前失败；S0 named/mirror 场景（双种子）及嵌套包回归校验原生元数据与回放帧等价性。
