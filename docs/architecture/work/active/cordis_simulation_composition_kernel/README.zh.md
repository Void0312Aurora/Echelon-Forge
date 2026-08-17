# Cordis 仿真组合内核

状态：`2026-08-17` active design；P0 权威/文档门禁、P1-A composition census 与
P1-B manifest/resolution contract、P2-A 原生 lifecycle baseline 已通过。下一步是
P2-B 默认 provider 迁移。

语言：

- 英文规范页：[README.md](README.md)
- 中文配套页：`README.zh.md`

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/cordis_simulation_composition_kernel/README.md`
Owner: `architecture/runtime-composition`
Last verified: `2026-08-17`

相关权威：

- [架构 owner](../../../README.zh.md)
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
| 模型组合 | 耦合 | `SimulationKernel` 构造默认 environment、effects、sensor、acoustic、control、guidance 和 unit factory 实现 | 既有接口允许替换，但没有一致的 composition owner |
| Service 生命周期 | 不一致 | 模型指针通过 Flecs ref 发布，而 `GroundContactSystem` 在注册时捕获 environment model 指针 | provider 替换不是完整生命周期迁移 |
| 系统组合 | 静态 | 单一注册函数以固定序列安装 shared、air、naval 和 ground 系统集 | 注册顺序不是插件依赖图或 profile 契约 |
| 后端选择 | 部分抽象 | `IWorldBatchBackend` 已存在，但 `RuntimeFacade` 直接构造 `FlecsCpuBackend` | 后端能力合同存在，但缺少通用 provider-selection root |
| Stage 语义 | 已有基础 | 维护中的 stage-node manifest 描述 semantic stage、read/write shard、clock、latency、sync 和 barrier | registry 还不是系统组合的唯一输入 |
| Composition contract | P1-B pass | 已有版本化 requested/resolved manifest、稳定 service key/scope/error code、canonical hash、默认兼容 fixture 与 fail-closed resolution test | 这是无资源的 contract baseline；不会构造 provider 或拥有 runtime resource |
| 原生 lifecycle kernel | P2-A pass | 隔离的 `ef_composition` library、closed native JSON ingestion、catalog/factory metadata validation、scoped transactional realization、typed generation handle、rollback、rebuild 与逆序 disposal test | 尚未把默认 model、service、system、backend、binding 或 Cordis producer 迁入该 library |
| Cordis 集成 | 不存在 | 仓库中没有维护中的 Cordis、Node-API 或 Node package 表面 | 这是新的跨 runtime 边界，不是普通依赖升级 |

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
- 只在原生组合合同稳定后增加 Node-API host adapter；
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
3. Cordis 是必需的长期声明式组合控制面。它把已准入 profile/plugin/service/configuration
   展开为 canonical 低层 request。原生与 Python compatibility producer 可为离线和
   embedded 运行生成同一 contract，但不能取代本计划引入 Cordis 的目标。
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
| `P2-B Default Provider Migration` | 把默认 model/service 构造迁到准入原生 provider 后，并输出首份 production composition identity。 | P2-A accepted | 默认 behavior/replay parity 保持，raw provider capture 被移除，resolved plan 带有 evidence | ready |
| `P2-C Cordis Default-Profile Vertical Slice` | 引入首条仓库自有 Cordis profile/plugin 路径，把默认 runtime request 投影到 canonical P1-B contract。 | P2-B production path stable | Cordis 与原生 compatibility producer 输出字节等价的默认 request，并由原生侧重新校验和实例化 | planned |
| `P3-A System Package Composition` | 把仓库准入的 system package 编译进冻结的原生 stage graph。 | P2-B 与 owner admission rule accepted | 默认图 parity 保持，且没有 package 拥有私有 pipeline | planned |
| `P3-B Capability And Profile Projection` | 把 capability/policy request 与 compatibility profile 名称下沉为 owner 准入的 contribution bundle。 | P3-A declaration boundary stable | domain label 只作为 compatibility bundle，而不是永久 composition ontology | planned |
| `P4 Backend Composition` | 通过准入 provider 选择 CPU、CUDA-resident、diagnostics 和未来 backend。 | P2-B 和 backend contract 可用 | `RuntimeFacade` 不再点名具体 backend，准入继续由 capability 驱动 | planned |
| `P5 Evidence And Replay Expansion` | 将 P2-B/P2-C identity baseline 扩展到 graph、backend、host、replay 与 comparison evidence。 | production composition exists | 无法解释的 composition mismatch 被拒绝 | planned |
| `P6 Cordis Package Maturation` | 完成仓库自有 Cordis profile、configuration overlay、diagnostics、provenance 与 plugin ergonomics。 | P2-C accepted 且 owner contract 可用 | 维护中的 Cordis composition 覆盖准入 production profile，但不成为 hot-path executor | planned |
| `P7 Conditional Node Host` | 仅为获批用例增加 Node-API hosting，不改变原生/Python 可用性或 step 语义。 | Cordis producer accepted 且 host decision approved | Node-hosted 运行使用同一原生 owner 与 parity gate | conditional |
| `P8 Migration And Closure` | 删除被取代的 truth path、提升稳定规则并关闭或路由残余。 | 必需 native、Cordis、system、backend、evidence 与 parity gate accepted | Cordis 计划具备准入 producer/native 纵向路径；可选 Node/外部生态残余有具名 owner | planned |

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
3 个 kernel-owned service/event object、7 个发布到 Flecs 的 singleton ref、82 个中央
component-registration call、34 个 active system-registration call、30 个 exact-stage
descriptor、5 个 maintained stage-node manifest entry，以及 3 个 Python 可见 runtime
ownership tier。完整证据与限制见 composition census。

P1-B 随后冻结 host-neutral requested/resolved contract 与默认兼容 fixture。P2-A 现已
提供独立的原生 realization library 与聚焦生命周期证据：普通 MSVC build 中 14 个 C++
test case、430 个 assertion 全部通过，并在 MSVC AddressSanitizer 下再次通过；composition
architecture suite 为 20 passed、1 个环境 skip。这些证据只证明隔离的 lifecycle 边界，
不证明已经接入当前仿真 constructor 或完成行为 parity。

## 验收门

只有满足以下条件，本子项目才能标记为 accepted：

- 默认原生 composition 与迁移前已接受基线在行为和 replay 上等价；
- composition resolution 确定且具有稳定身份；
- 影响 truth 的 provider 和 stage contribution 在获准重配置 barrier 之间不可变；
- 生命周期 failure injection 证明完整 rollback 且无悬垂 service reference；
- `SimulationKernel` 和 `RuntimeFacade` 不再直接构造具体默认 model/backend；
- stage 顺序继续由维护中的 stage contract 管理，而不是 Cordis plugin 顺序；
- 实验意图通过显式 runtime-composition projection 到达 Cordis，且 resolved catalog lock
  中可见按 owner 分类的准入；
- 至少一条仓库自有 Cordis 默认 profile 路径输出 canonical request，并由原生 composition
  compiler 消费和重新校验；
- Python 和 standalone C++ 运行不要求 Node；
- 启用 Node/Cordis host 时，它不进入逐 step call graph；
- CPU/CUDA parity 和代表性 world-batch 性能保持在另行冻结的容差内；
- composition provenance 通过维护中的 diagnostics/replay evidence 导出；
- 父索引、standard、reference 和 archive 路由同步且不扩大能力声明。

## 残余与下一步

立即工作是 P2-B 默认 provider 迁移。它必须把现有默认 model、factory、event store、
damage bridge 与 weapon-release service 构造移到获准的原生 provider 后，保持已接受
的默认行为/replay 基线，并输出首份 production composition identity。随后执行 P2-C
首个 Cordis 纵向切片：仓库自有 Cordis 默认 profile 必须输出由原生侧重新校验和实例化
的同一 canonical request。system family、backend 与 binding 迁移继续作为独立后续切片；
Node hosting 保持 conditional，不作为 Cordis producer/native 路径的闭合前置条件。

长期残余包括插件真实性与分发政策、多进程宿主、远程 composition catalog、第三方
兼容和开发态 live reload。它们属于受治理 follow-on，不能削弱确定性、provenance
或离线运行。

## 归档

只有当前权威、验收和残余路由得到保留后，历史或被取代的任务包才迁入
[archive](archive/README.zh.md)。本 active package 关闭前，稳定架构规则必须提升到
architecture standards 或 reference 表面。
