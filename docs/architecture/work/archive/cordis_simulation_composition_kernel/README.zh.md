# Cordis 仿真组合内核

状态：`2026-08-23` 已闭合的有界默认 CPU-exact 计划；P0 权威/文档门禁、P1-A composition census、
P1-B manifest/resolution contract、P2-A 原生 lifecycle baseline 已通过。P2-B 默认
provider 迁移、P2-C0 projection/catalog-lock、P2-C1 默认 profile Cordis/native、P3-A
默认 system-contribution migration、P3-B 默认 profile projection、P4-A 默认
backend-provider migration、P5-A 默认 CPU-exact composition-evidence 与 P6-A 默认
profile Cordis package maturation、P7-A 默认 CPU-exact host/batch parity 与 P8-A
migration closure 均已接受。稳定规则现由
[runtime composition 基线](../../../standards/runtime_composition_baseline.zh.md)维护。
更广 profile/provider、Node、CUDA parity、外部 plugin distribution 与完整 replay 是本闭合
范围之外的 held 残余。

语言：

- 英文规范页：[README.md](README.md)
- 中文配套页：`README.zh.md`

Document kind: `task`
Lifecycle: `archived`
Canonical: `docs/architecture/work/archive/cordis_simulation_composition_kernel/README.md`
Owner: `architecture/runtime-composition`
Last verified: `2026-08-23`

相关权威：

- [架构 owner](../../../README.zh.md)
- [Runtime composition 基线](../../../standards/runtime_composition_baseline.zh.md)
- [仿真系统架构设计](../../../standards/simulation_system_architecture_design.zh.md)
- [Runtime workflow 与 contract 基线](../../../standards/runtime_workflow_and_contract_baseline.zh.md)
- [系统模块化 issue](../../issues/modularization_plan.zh.md)
- [Runtime facade contract issue](../../issues/runtime_facade_contract_plan.zh.md)
- [子项目创建标准](../../../../engineering/automation/rules/subproject_creation_standard.zh.md)
- [当前 kernel 构造](../../../../../src/core/engine/simulation_kernel.cpp)
- [当前系统注册](../../../../../src/core/engine/simulation_kernel_systems.cpp)
- [后端语义接口](../../../../../src/runtime/facade/internal/world_batch_backend.h)

## 目的

本子项目把 Cordis 作为仿真 runtime 的长期声明式组合控制面引入，同时保持
Experiment Face 对实验意图的权威，以及 C++ 对确定性解析、实例化和执行的权威。
它建立从实验意图到 runtime composition 的显式投影、版本化低层组合契约、按 owner
分类的准入、原生生命周期内核、证据身份和可选 Node 宿主，但不把 JavaScript、异步
plugin 派发或跨语言 service lookup 放入逐 step 路径。

本项目不是为了短期重构便利或未经证明的性能收益。它面向多模型族、领域扩展、后端
实现、实验 profile、binding 和未来外部插件包的长期演进，并要求这些扩展不能创建
额外 truth path。

## 当前状态

| 区域 | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| 模型组合 | 原生 provider root | P2-B 将默认 environment、effects、sensor、acoustic、control、guidance、event-store、release-service 和 unit-factory ownership 通过准入 native catalog 路由 | system family 与更广 provider-package 扩展仍属后续切片 |
| Service 生命周期 | generation-governed / fail-closed raw-world quarantine | provider handle 在 wrapper/kernel lifecycle lock 下原子刷新；system consumer 在执行时解析 generation-aware Flecs ref；剩余 raw Flecs access 使用 operation-lock-backed RAII lease，且会永久关闭 provider rebuild | 长期 raw dependency reference、typed replacement lease 与更广 handover evidence 仍是残余 |
| 系统组合 | P3-A 默认图有界切片已接受 | owner-derived component/system contribution registry 校验自身 count、identity、dependency edge 与 stage order；native conformance 在 realization 前另行校验冻结 artifact | profile-specific omission、完整 semantic-stage/read-write join 与更广 package admission 属于后续 gate |
| Capability/profile projection | P3-B 默认 profile 有界切片已接受 | 版本化 projection 将 capability/policy、owner catalog、83 个 component contribution 与 34 个 native system order join；Cordis 与 native conformance 校验同一 join | 更多 profile、semantic-stage/read-write metadata 与外部 package admission 仍属后续 gate |
| 后端选择 | P4-A 默认 provider 有界切片已接受 | `RuntimeFacade` 通过 native provider catalog 实例化 generated 默认 CPU-exact request；profile、provider、implementation-version、capability、metadata 与 construction failure 均在 ownership 外逸前 fail closed；独立审阅返回 P0/P1/P2 = 0/0/0 | 更广 maintained provider、CUDA parity 与 evidence expansion |
| Stage 语义 | 已有基础 | stage-node manifest 仍是 semantic authority；P3-A registry 提供 executable 默认 stage order，P3-B projection 携带 native system order，不另造 stage ontology | 完整 semantic-stage/read-write join 仍属后续 gate |
| Composition contract | P1-B pass | 已有版本化 requested/resolved manifest、稳定 service key/scope/error code、canonical hash、默认兼容 fixture 与 fail-closed resolution test | 这是无资源的 contract baseline；不会构造 provider 或拥有 runtime resource |
| 原生 lifecycle kernel | P2-A 历史基线；P2-B 原生 realization 已实现 | 隔离的 `ef_composition` library、closed native JSON ingestion、catalog/factory metadata validation、scoped transactional realization、typed generation handle、rollback、rebuild、逆序 disposal test，以及 P2-B 默认 provider realization seam | system family、backend、binding 迁移仍属后续切片；Cordis producer 集成现为有界 P2-C1 切片 |
| Projection 与 catalog lock | P2-C0 accepted bounded slice | 已生成 producer-neutral request 与 owner-derived lock schema、canonical fixture、identity 重算、负向 admission matrix，并已在 `ef_composition` 接入 native revalidation，且未 lower 到 P1-B | P2-C1/P3-B 默认 profile join 已作为有界切片接受；更广 profile/package admission 仍为 residual |
| Cordis 集成 | P2-C1/P3-B/P6-A 默认 profile package 有界切片已接受 | `packages/cordis-runtime` 使用 Cordis lifecycle primitive、严格仓库 package/overlay SDK、确定性四节点依赖解析、原始字节 pin、canonical provenance 与无本机路径 diagnostics；native conformance 校验不变的 request/lock/projection/manifest；独立审阅返回 P0/P1/P2 = 0/0/0 | truth-changing 或更广 profile 需 owner 另行准入；Node host、外部签名/plugin、CUDA 与 parity 属于后续 gate |

## 范围

纳入：

- 定义稳定的 `SimulationCompositionManifest` 和规范化序列化；
- 建立具有 application、backend、batch、world、episode 显式 scope 的原生 C++
  composition root；
- 把 model、service、system package 和 backend 构造移出 `SimulationKernel` 与
  `RuntimeFacade` 构造函数；
- 将插件贡献绑定到既有 capability、stage、clock、barrier、replay 和 evidence
  contract；
- 保证 composition resolution 确定、可验证、可散列，并在维护中的仿真执行前冻结；
- 增加 Cordis package，解析准入插件并生成原生 runtime 消费的同一版本化 manifest；
- 只有在原生组合合同稳定后、P6-B 又经独立 host decision 获准时，才增加 Node-API
  host adapter；
- 保持 Python/nanobind 和 standalone C++ 部署不依赖 Node runtime；
- 通过受治理 extension point 支持未来 domain、model、backend、diagnostics 和
  experiment plugin。

不纳入：

- 替换 Flecs ECS 和状态查询引擎；
- 用 Cordis event 或 JavaScript callback 替换确定性的 C++ stage scheduler；
- 逐 step Node、JavaScript、IPC 或动态 service lookup；
- 在 episode 内任意热替换影响 truth 的插件；
- 让插件发现绕开 stage、content、backend、evidence 或 domain 准入；
- 在签名、兼容性、provenance 和 sandbox 政策验收前建设公开插件市场；
- 没有代表性 batch benchmark 就声明性能提升。

## 架构决策

目标采用分层组合架构：

1. Experiment Face 拥有跨 simulation、policy 与 evaluation 维度的用户可见实验意图。
2. typed runtime projection 把该意图转换为 capability、policy、profile 与配置要求。
   已冻结的 P1-B requested manifest 继续作为 canonical 低层交换 contract，而不是未来
   唯一 authoring abstraction。
3. Cordis 是必需的长期声明式组合控制面。它通过 Cordis primitives 加仓库自有的
   DeepSeek-Harness-style profile/bundle layer，独占维护中高层 runtime request 到
   canonical 低层 request 的 lowering。原生与 Python 离线路径只能消费 canonical
   低层 manifest 或生成的 frozen profile，不独立解析任意高层 request。
4. model、system、backend、domain、evidence 与 security owner 分别把自己的实现类别
   准入 `AdmittedCatalogLock`；共享 lifecycle registry 本身不授予语义准入。
5. 原生 C++ composition compiler/root 重新校验、解析、实例化并冻结精确 runtime plan，
   拥有资源，并执行确定性销毁与 rollback。
6. Flecs、原生 scheduler、backend 与 episode/runtime owner 保留可执行语义。Cordis
   lifecycle event 仅是管理事件；维护中的 step 路径不含 Cordis 或 binding 调用。

完整设计见
[Cordis 仿真组合架构](cordis_simulation_composition_kernel_architecture.zh.md)。

## 阶段计划

| 阶段 | 目标 | 入口条件 | 退出条件 | 状态 |
| --- | --- | --- | --- | --- |
| `P0 Authority and Boundary` | 建立 owner、目标架构、非目标、任务簇和验收模型。 | 用户授权和已检查的仓库基线 | 双语子项目文档和父架构链接通过文档门禁 | pass |
| `P1 Composition Contract` | 冻结 manifest schema、service key、plugin descriptor、scope、兼容规则和确定性解析。 | P0 accepted | schema fixture、校验规则、canonical encoding 和 contract test 存在 | pass |
| `P2-A Native Lifecycle Kernel` | 实现隔离的 C++ catalog、scoped transaction、replacement、rollback、freeze 和确定性 disposal substrate。 | P1 contract frozen | 聚焦原生与架构门禁通过 | pass |
| `P2-B Default Provider Migration` | 把默认 model/service 构造迁到准入原生 provider 后，并输出首份 production composition identity。 | P2-A accepted | 默认 behavior/replay parity 保持，raw provider capture 被移除，resolved plan 带有 evidence | accepted bounded slice |
| `P2-C0 Projection And Catalog-Lock Contract` | 冻结 producer-neutral `RuntimeCompositionRequest` DTO 与 owner-derived `AdmittedCatalogLock` artifact、identity 和 admission rule。 | P2-B production path/identity stable | Cordis 获得唯一 typed 高层输入与版本化 owner-approved catalog lock；离线路径被限制为 canonical 低层 artifact | accepted bounded slice |
| `P2-C1 Cordis Default-Profile Vertical Slice` | 使用 Cordis primitives 加仓库 profile/bundle layer lower 默认 request，并通过 production native path 实例化。 | P2-C0 accepted | Experiment fixture -> request -> Cordis -> manifest/catalog lock -> native realization 的正负 admission case 通过 | accepted bounded default-profile slice；更广扩展 residual |
| `P3-A System Contribution Migration` | 把仓库准入的 system package 编译进冻结的原生 stage graph。 | P2-C1 accepted；除非另有显式 independent-stream amendment | 默认图 parity 保持，且没有 package 拥有私有 pipeline | accepted bounded default-graph slice；更广 package/profile admission residual |
| `P3-B Capability And Profile Projection` | 把 capability/policy request 与 compatibility profile 名称下沉为 owner 准入的 contribution bundle。 | P2-C0 与 P3-A declaration boundary stable | domain label 只作为 compatibility bundle，而不是永久 composition ontology | accepted bounded default-profile slice；更广 profile residual |
| `P4-A Backend Provider Migration` | 通过准入 provider 选择 CPU、CUDA-resident、diagnostics 和未来 backend。 | P2-C1 与 backend contract 可用 | `RuntimeFacade` 不再点名具体 backend，准入继续由 capability 驱动 | 默认 provider 有界切片已接受；更广 provider residual |
| `P5-A Composition Evidence Expansion` | 将 P2-B/P2-C0/P2-C1 identity baseline 扩展到 graph、backend、原生执行 owner、replay 与 comparison evidence。 | production Cordis/native composition exists，且 P4-A 默认 provider 已接受 | 无法解释的 composition/catalog-lock mismatch 被拒绝 | 默认 CPU-exact 有界切片已接受；更广 profile/backend 与调用语言证明为 residual |
| `P6-A Cordis Package Maturation` | 在 Cordis primitives 之上完成仓库自有 configuration overlay、profile/bundle package、diagnostics、provenance 与 plugin ergonomics。 | P2-C1 与有界 P5-A 已接受，且 owner contract 可用 | 维护中的 Cordis composition 覆盖准入 production bundle，但不成为 hot-path executor | 默认 profile package 有界切片已接受；更广/外部 package residual |
| `P6-B Node Host Adapter` | 仅为获批用例增加 Node-API hosting，不改变原生/Python 可用性或 step 语义。 | P6-A accepted 且 host decision approved | Node-hosted 运行使用同一原生 owner 与 parity gate | conditional / held pending host decision |
| `P7-A Host And Batch Parity` | 证明 native、Python 与 Cordis-produced parity；仅在 P6-B 获准时加入 Node 行。 | P4-A/P5-A/P6-A accepted | 准入 profile 通过正确性和批准的 batch budget | 默认 CPU-exact 有界切片已接受；Node 行 held |
| `P8-A Migration Closure` | 删除被取代的 truth path、提升稳定规则并关闭或路由残余。 | 必需 native、Cordis、system、backend、evidence 与 parity gate accepted | Cordis 计划具备准入 producer/native 纵向路径；可选 Node/外部生态残余有具名 owner | accepted bounded closure |

这些阶段描述依赖顺序，不是截止日期，也不是降低长期目标的理由。阶段可以拆成有界
实现切片，但改变以上架构决策必须有显式替代决定。

## 任务簇

- [基于源码的 composition census](cordis_simulation_composition_census_20260817.zh.md)
- [P1-B manifest 与 resolution contract](cordis_simulation_composition_contract_20260817.zh.md)
- [有限任务簇计划](cordis_simulation_composition_kernel_task_clusters_20260817.zh.md)
- [当前状态与残余登记](cordis_simulation_composition_kernel_current_status_20260817.zh.md)
- [派发队列](cordis_simulation_composition_kernel_dispatch_queue_20260817.zh.md)
- [验收合同](cordis_simulation_composition_kernel_acceptance_20260817.zh.md)
- [独立计划架构审阅](../../../reviews/cordis_simulation_composition_program_review_20260817.zh.md)
- [active owner 对计划架构审阅的回复](../../../reviews/cordis_simulation_composition_program_review_response_20260817.zh.md)

## 输出与证据

预期维护输出包括：

- 版本化 composition schema 和 canonical fixture；
- 带聚焦测试的原生 lifecycle/provider library；
- 默认以及 domain/backend composition profile；
- 生成或校验后的 stage graph 与 composition hash；
- 使用同一低层 contract 的 Cordis package，以及在另行获批时提供的 Node host adapter；
- Python、C++ 与 Cordis producer parity 证据；若 Node adapter 获准，再加入 Node host parity；
- lifecycle、replay、failure injection、batch scale 和性能报告；
- 阻止逐 step 跨语言调用和双重组合真值的架构 guard。

仅创建本子项目文档只证明计划和门禁已经建立，不证明 runtime composition 能力。

`2026-08-17` 的 P0 验证记录为：维护面链接问题 `0`；全树审计中由本子项目产生或指向
本子项目的链接问题 `0`；严格双语注册表 `74/74` 同步；文档治理测试 `21` 项通过；
文档 diff check 通过。

P1-A 随后记录当前 construction/migration 基线：7 个可替换 model/factory provider、
3 个 kernel-owned service/event object、7 个发布到 Flecs 的 singleton ref、83 个中央
component-registration call、34 个 active system-registration call、30 个 exact-stage
descriptor、5 个 maintained stage-node manifest entry，以及 3 个 Python 可见 runtime
ownership tier。完整证据与限制见 composition census。

P1-B 随后冻结 host-neutral requested/resolved contract 与默认兼容 fixture。P2-A 提供了
隔离的原生 realization library；P2-B 现已把 production default kernel 接入该 root，输出
requested/resolved identity 与 world-scope generation，并仅允许在受监管 world 尚未 mutation、
也未暴露 raw Flecs lease 前执行 provider rebuild。active trace frame 与受监管 `SimObject`
实体同样会拒绝 rebuild。raw Flecs lease 会与 rebuild/shutdown 串行化，但当前有意采用
fail-closed 而非可重新开启的策略。当前聚焦证据见 current-status 文档；P2-C1 默认
profile Cordis producer/native 有界纵向切片已接受，更广 profile/package 扩展仍开放。

## P2-B 验收门

P2-B 在 native production seam 上满足以下有界条件后验收：

- 默认 provider profile 通过 native composition root 构造，`SimulationKernel`
  中不再存在具体默认构造或 registration-time raw capture；
- 一个受控默认 trace 与已接受的迁移前基线在行为/replay 上等价；
- 一条 production provider 构造/teardown 失败路径证明 rollback 完整且无悬垂
  service reference；
- 重复 kernel create/destroy 运行不出现生命周期漂移；
- requested/resolved composition identity 与 world generation 稳定且可观测；
- 最新实现批次通过一次独立 `gpt-5.6-sol/max` 审阅，且没有未解决的 P1/P0。

以上是 P2-B 唯一的验收阻塞项。已有 lifecycle、lease、mutation-barrier、ABI
与 architecture 测试用于支撑这些门禁；不得借此把更广的 backend、host 或性能要求
继续加入本切片。

## 全局收口门

stage/profile contribution 迁移、Cordis request/catalog-lock projection、真实 Cordis
默认 profile 纵向路径、backend 与 CPU/CUDA parity、host/batch 性能、扩展 provenance
以及 Node host 决策，属于后续切片或全局收口，不属于 native P2-B 验收阻塞项。

## 残余与下一步

P2-B、P2-C0、P2-C1、P3-A、P3-B 默认 profile projection 与 P4-A 默认 backend-provider
切片均已作为有界切片接受。受控 parity trace、production failure/teardown 路径、重复
create/destroy evidence、native revalidation、
独立审阅、registry admission 与精确默认图顺序均已记录并通过。P3-A 已把中央
component/system call 替换为 owner-derived registry，但尚未填满全部 semantic-stage/read-write
字段，也未开放 profile-specific package omission。P3-B 将具名默认 compatibility profile 绑定到
capability/policy requirement 与 owner lock/native graph；它不是通用多 profile resolver。
P4-A 仅接受维护中的默认 CPU-exact provider。P5-A 将该切片绑定到 request/manifest/lock/
profile、11 个 provider version、83+2+34 executable graph、精确 backend identity、全部
realized world 与五类 scope，以及严格 composition-comparison evidence。
host 字段记录原生执行 owner（`native_cpp/native.v1`），不声明调用语言证明；Python
caller-origin attestation 仍是 residual。P6-A 现已固定 Cordis/package-lock/profile module/
bundle/default overlay 的精确字节，解析确定性四节点依赖图，拒绝缺失、重复、成环、冲突
或改变 truth 的 package input，并在输出无本机路径 diagnostics 前把 provenance 绑定到实际
request/lock/profile projection。它不拥有 provider、backend 选择、component contribution
或 system order。更广 P2-C1 profile/provider、CUDA parity、binding 迁移、外部签名/plugin
与完整 replay 继续作为独立 held 计划。P7-A 增加严格 native-direct 与
本地 `ef_py` caller 行，将其 join 到 Cordis-produced artifact，并冻结 action/state/event/
window/composition-comparison 语义参考及保守的 32-world cold/warm/reset/RSS/teardown budget。
独立 `gpt-5.6-sol/max` 审阅返回 P0/P1/P2 = 0/0/0。P8-A 删除了隐式 empty-manifest
fallback，封存 live caller/truth-path inventory，证明退场 setter/concrete-construction surface
不存在，提升维护中 standard，并路由全部可选 residual。

长期残余包括插件真实性与分发政策、多进程宿主、远程 composition catalog、第三方
兼容和开发态 live reload。它们属于受治理 follow-on，不能削弱确定性、provenance
或离线运行。

## 归档

本 package 是已归档的实现与验收 provenance；其嵌套
[archive](archive/README.zh.md) 保留更早的 superseded local record。当前权威是维护中的
runtime composition baseline；不得把本 package 当作 active task queue。
