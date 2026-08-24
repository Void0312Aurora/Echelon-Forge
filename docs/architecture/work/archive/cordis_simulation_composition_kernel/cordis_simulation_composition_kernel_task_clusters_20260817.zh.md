# Cordis 仿真组合内核任务簇

状态：`2026-08-23`，[Cordis 仿真组合内核](README.zh.md)的有限交付计划；P0、P1-A 与
P1-B 已通过，P2-A 已作为原生 lifecycle baseline 通过。P2-B 与 P2-C0 已在 evidence
和独立审阅绿色后作为有界切片接受。P2-C1 默认 profile、P3-A 默认图、P3-B 默认 profile
projection、P4-A 默认 backend-provider、P5-A 默认 CPU-exact composition-evidence、
P6-A 默认 profile Cordis package-maturation、P7-A 默认 CPU-exact host/batch parity 与
P8-A migration closure 也已接受。有限计划已闭合并归档；更广扩展继续由分别具名 owner
治理。

语言：

- 英文规范页：[cordis_simulation_composition_kernel_task_clusters_20260817.md](cordis_simulation_composition_kernel_task_clusters_20260817.md)
- 中文配套页：`cordis_simulation_composition_kernel_task_clusters_20260817.zh.md`

Document kind: `task`
Lifecycle: `archived`
Canonical: `docs/architecture/work/archive/cordis_simulation_composition_kernel/cordis_simulation_composition_kernel_task_clusters_20260817.md`
Owner: `architecture/runtime-composition`
Last verified: `2026-08-23`

## 边界决策

本计划把 Cordis 作为长期声明式 composition control plane 引入，并以原生组合内核、
版本化低层 manifest、按 owner 分类的 admission lock、provider/lifecycle 基础设施、
受治理 system contribution 与 composition evidence 为支撑。Experiment Face 继续拥有
实验意图；Cordis 拥有声明式 profile/plugin/service 组合；相应 domain/runtime owner
准入实现；原生 C++ 拥有确定性实例化和执行。Node host 保持 conditional。计划必须
保持单一 runtime truth path、backend capability admission、replay identity 与离线
C++/Python 运行。

下列任务标签只用于本计划派发，不得进入 public API、runtime string、schema field 或
production type name。

## 有限任务簇

| Cluster | Owner | Capability tier / model ID / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `P0-A Authority Scaffold` | main thread | n/a | 创建双语 active 子项目、架构、状态、队列、验收、archive 和父路由。 | `docs/architecture/work/archive/cordis_simulation_composition_kernel/**`、`docs/architecture/README*`、选定双语注册表条目 | runtime code、能力声明 | 文档元数据、本地链接、双语配对、`git diff --check` | 必需文件齐全且架构 owner 路由本项目 | 首个串行任务簇 | 1 + 1 repair | pass |
| `P1-A Composition Census` | main thread | n/a | 盘点全部 constructor、setter、raw capture、service ref、system registration、backend selection、reset boundary、stage registry、binding entry 和相关测试。 | 本项目 current-status/evidence 文件，可选生成式 inventory | runtime 修改、在 inventory 中隐藏设计变更 | 可复现 `rg` inventory、直接 ownership trace 和文件行证据 | 每条 composition edge 都有 owner、scope、replacement rule 和 migration disposition | P0-A 后 | 1 + 1 repair | pass |
| `P1-B Manifest And Resolution Contract` | main thread | n/a | 冻结 host-neutral manifest schema、plugin/provider descriptor、service key、scope、conflict rule、canonical encoding、versioning 和 resolution order。 | `src/runtime/contracts/**`、schema producer input、`tests/architecture/composition/**`、本设计更新 | provider 实现、Node host、动态下载 | schema freshness、canonical fixture、invalid-manifest matrix、确定性 permutation test | native 与未来 Cordis producer 可面向一个无歧义 contract | P1-A 后 | 2 + 1 repair | pass |
| `P2-A Native Lifecycle Kernel` | main thread | n/a | 实现 catalog、resolver、validator、scope、transaction、freeze、typed handle、effect、rollback 和确定性 disposal。 | 获批的新 `src/runtime/composition/**`、聚焦 CMake target、`src/tests/test_composition_lifecycle.cpp`、architecture guard | 同一切片迁移默认 provider、system、backend、binding 或 Cordis | 聚焦 C++、MSVC AddressSanitizer、failure injection、architecture contract suite | scope 隔离、失败原子性、确定性解析和 teardown 通过 | P1-A/P1-B 后；共享 contract 与 P2-B 串行 | 3 + 1 repair | pass |
| `P2-B Default Provider Migration` | engine owner | n/a | 把默认 model、factory、event store、bridge、release service 构造迁入 native provider/kernel builder，并发布首份 production resolved-plan identity。 | `src/core/engine/**`、`src/models/**` composition 入口、准入 provider 文件、聚焦测试、有界 evidence DTO join | system-family 拆分、Cordis package、Node host | 一条受控默认 behavior/replay 对比、一个 provider failure/teardown 路径、重复 create/destroy、无悬垂 provider capture、identity roundtrip/mismatch test | compatibility profile 在 `SimulationKernel` 不构造具体 model 的情况下构造当前 kernel，且 run 导出稳定 requested/resolved identity | P2-A 后；与 P2-C0 在 production identity/contract seam 上串行 | 3 + 1 repair | accepted bounded slice |
| `P2-C0 Projection And Catalog-Lock Contract` | composition-contract owner，需 category-owner sign-off | n/a | 冻结 producer-neutral `RuntimeCompositionRequest` DTO 与确定生成的 owner-derived `AdmittedCatalogLock` artifact，包括 version、canonical bytes、hash、category authority、provenance 与正负 admission rule。 | 获批 `src/runtime/contracts/**` 下新的有界高层 request/catalog-lock input、generator、fixture、architecture test、本项目文档 | 修改 P1-B 低层字段、Cordis package 实现、Node host、system migration | schema/header freshness、deterministic lock generation、stable identity、category-owner matrix、unknown/unadmitted/version/provenance rejection、offline low-level-only guard | Cordis 有唯一 typed 高层 request 与可核验 owner-approved lock；原生/Python 离线路径不能 lower 任意高层 request | P2-B production identity 稳定后 | 2 + 1 repair | accepted bounded slice |
| `P2-C1 Cordis Default-Profile Vertical Slice` | future Cordis integration owner | n/a | 使用 Cordis plugin/context/service/injection/event/effect primitives 加仓库 profile/bundle layer，lower production 默认 request 并通过原生路径实例化。 | 有界 `packages/cordis-runtime/**`、package manifest/lockfile、P2-C0 adapter/artifact、canonical fixture、端到端 conformance test、本项目文档 | Node-API host、system-family 拆分、外部 plugin、完整 SDK ergonomics、hot-path service | Experiment fixture -> request -> Cordis -> manifest/catalog lock -> native realization；canonical bytes/hash；真实 provider identity；负向 admission；offline-native regression | 真实默认路径证明完整 Experiment projection/Cordis/owner-lock/native 权威链，且不存在私有 Cordis catalog | P2-C0 后；除非另行授权，否则在任何后续 implementation cluster 前 | 2 + 1 repair | accepted bounded default-profile slice；broader expansion residual |
| `P3-A System Contribution Migration` | future scheduler owner | n/a | 用准入的 component/system/stage contribution 替换中央全域注册清单，并编译到既有 scheduler contract。 | `src/systems/**` 注册接缝、`simulation_kernel_systems.cpp`、runtime contract、composition test | 替换 Flecs、改变语义生命周期、私有 domain pipeline | 精确默认 stage-order parity、manifest validation、graph conflict test | compatibility profile 在无私有 package pipeline 前提下复现已接受默认图；profile-specific omission 属于后续扩展 | P2-C1 后；更早 independent-stream 派发要求 architecture owner 显式 amendment，证明无共享 contract/write-set dependency | 4 + 1 repair | accepted bounded default-graph slice；更广 package/profile admission residual |
| `P3-B Capability And Profile Projection` | future cross-domain integration owner | n/a | 把 typed capability/policy request 与 compatibility profile 名称下沉为 owner 准入的 model/component/system/stage bundle。 | owner 批准的 projection/profile contract、domain integration test、composition fixture | 把 air/naval/ground label 设为永久 ontology、提升领域成熟度、实现缺失行为 | projection validation、forbidden dependency guard、owner contract suite | capability requirement 为主；具名 domain profile 是不能绕开 owner standard 的显式 compatibility bundle | P2-C0 与 P3-A 声明后；写集不重叠时各 owner 可并行 | 每个 bundle family 2 + 1 repair | accepted bounded default-profile projection；更广 profile residual |
| `P4-A Backend Provider Migration` | 主线程 + 独立 reviewer | `gpt-5.6-sol` / `max`：P0/P1/P2 = 0/0/0 | 把 CPU、CUDA-resident、diagnostics 和未来 backend 选择迁入 provider admission，不改变 facade 语义。 | `src/runtime/facade/**`、`src/runtime/providers/**`、backend contract/test、CMake/CI、有界文档 | 新 backend 语义、放宽 GPU parity | facade contract、backend admission matrix、聚焦 native/provider failure test | `RuntimeFacade` 不再构造具体 backend，拒绝的 profile 在运行前失败 | P2-C1 后 | 3 + repair | 默认 provider 有界切片已接受；更广 provider residual |
| `P5-A Composition Evidence Expansion` | 主线程 + 独立 reviewer | `gpt-5.6-sol` / `max`：P0/P1/P2 = 0/0/0 | 把已接受默认 request/manifest/lock/profile/provider/backend/graph realization 绑定到逐 world scope evidence 与 maintained replay/comparison admission。 | evidence/replay contract、facade diagnostics、schema generator、聚焦测试、CMake/CI、有界文档 | 对不支持的 backend/state 宣称完整 replay，或声明调用语言证明 | DTO/schema/header freshness、ASCII/signed-int64 totality、zero-world failure、11-provider 与 83+2+34 graph join、全部 world/五类 scope evidence、resize/configure ABA rejection、commit sealing、mismatch rejection | 维护中的默认 CPU-exact run 可识别 realized composition/catalog lock，replay/comparison 拒绝无法解释的 mismatch | P2-C1 与相关 P3/P4 join 后 | 3 + repair | 默认 CPU-exact 有界切片已接受；更广 profile/backend、调用语言证明与完整 state replay 为 residual |
| `P6-A Cordis Package Maturation` | main thread + independent reviewer | `gpt-5.6-sol` / `max`：P0/P1/P2 = 0/0/0 | 在已接受 P2-C1 producer 上，以 Cordis primitives 扩展仓库自有 profile/bundle package、configuration overlay、diagnostics、provenance、dependency resolution 与 plugin SDK ergonomics。 | 获批的 `packages/cordis-runtime/**`、workspace manifest/lockfile、fixture、文档 | JavaScript 仿真步进、任意外部 native plugin、替代 owner admission | package test、projection/schema conformance、LF 稳定原始 pin、canonical native parity、封存 provenance/diagnostics test | 维护中的 Cordis bundle 只输出 owner 准入且被 native validator 同样接受的 request | P2-C1 与相应 P3/P4/P5 owner contract 后 | 3 + repair | 默认 profile package 有界切片已接受；更广/外部 package residual |
| `P6-B Node Host Adapter` | future bindings owner | n/a | 仅在存在获批 host 用例时，在粗粒度 `RuntimeFacade` 用例和原生 composition 上增加 Node-API adapter。 | 获批的 `src/interfaces/node/**`、CMake/package wiring、binding test | raw ECS 暴露、逐 stage callback、替换 nanobind | 若获准：configure/load/reset/setup/inject/advance/evaluate/export/diagnostics 与 leak/teardown test | 若获准，Node-hosted run 使用同一原生 runtime，stage execution 无 binding call | P6-A 与显式 host decision 后 | 3 + 1 repair | conditional / held pending host decision |
| `P7-A Host And Batch Parity` | future integration owner | `gpt-5.6-sol` / `max`：P0/P1/P2 = 0/0/0 | 证明 native、Python 与 Cordis-produced composition 保持确定行为和 batch budget；仅在 P6-B 获批时纳入 Node。 | integration test、benchmark/probe、evidence package、有界修复 | 通过调参掩盖语义 mismatch、无关优化 | producer/host parity matrix、冻结 action/state/event/reward/termination/replay comparison、32-world 内存/cold-warm/吞吐/reset/teardown 测量 | 冻结 profile 通过正确性和另行批准的回归预算 | P4-A/P5-A/P6-A 后；Node 行还要求 P6-B | 2 + 1 repair | 默认 CPU-exact 有界切片已接受；Node 行 held |
| `P8-A Migration Closure` | main integration owner | closure record `9c3dbeb6e37c6f2b672d2f5186c646acb9df8e2f40359c86992b6a4271c3f449` | 删除被取代的 setter/构造真值，提升稳定规则，记录 accepted scope，拆分残余并同步 index/archive。 | 受影响 composition code、architecture standard/reference、本项目 acceptance/archive、owner index | 删除历史证据、静默扩大插件准入、把 Cordis 当作可选完成证据 | 全验收矩阵、Cordis/native vertical conformance、link/bilingual audit、caller inventory、compatibility proof | 不再存在双 composition path；维护一条准入 Cordis producer/native 路径；可选 Node/外部生态残余有具名 owner | 最终串行任务簇 | 2 + 1 repair | accepted bounded closure |

## 派发规则

- 每个实现 packet 必须精确映射一个任务簇和一个有界 write set。
- P0、contract freeze、共享 runtime ownership、acceptance 和 closure 保持串行。
- P2-B、P2-C0 与 P2-C1 是独立有界切片，但共享 production identity、projection、
  catalog-lock 与默认 profile contract，因此保持串行。P2-C1 是整体计划关闭的必需条件；
  P2-B 可以保留独立的有界原生验收。
- P2-C0 后，任何 implementation cluster 在 P2-C1 前都不得 release，除非 architecture
  owner 显式 amendment 授权 independent stream，并证明不会创建或修改竞争的
  lowering/catalog authority。
- 只读 census 可与 schema design 并行，但 P2 构造前必须整合其 finding。
- 两个 worker 不得同时修改 composition contract、同一 provider family、中央 stage
  registry、facade ownership 或状态权威。
- domain profile 只有在 common service/stage contract 冻结且写集不重叠时才能并行。
- 任务簇到达 round cap 后停止并重新划分范围，不能自动增加无限 repair wave。
- runtime 修改必须进行相称的 build、test、parity、lifecycle 和 evidence 校验；docs-only
  检查不能关闭 runtime 任务簇。
- 每个 material implementation/repair cluster 在提交稳定后必须进行独立只读审阅。默认矩阵
  覆盖 lifecycle/ownership、contract/canonicalization、integration/CI/docs，并使用
  `gpt-5.6-sol`、`max` reasoning；除非后续显式决策改变配置。未解决 P1 会阻断下一 cluster。
- 委派时遵循
  [Subagent 使用规范](../../../../engineering/automation/standards/subagent_usage_policy.zh.md)。

## Worker Packet 要求

```text
cluster:
status: pass | partial | blocked | failed
baseline revision and configuration:
touched files:
commands and outcomes:
composition/lifecycle claims proven:
determinism or replay impact:
performance evidence:
remaining paths:
behavior risks:
integration notes:
```

每个 packet 还必须说明是否引入或移除了 composition truth source、cross-language call、
provider replacement path、compatibility wrapper 或 runtime dependency。

## 验证计划

文档边界：

```powershell
git diff --check -- docs/architecture
python tools/maintenance/translate_docs_batch.py audit --root docs --registry docs/engineering/documentation/reference/bilingual_document_clusters.json
python tools/maintenance/translate_docs_batch.py clusters --root docs --registry docs/engineering/documentation/reference/bilingual_document_clusters.json
```

P1 及后续任务簇必须在目标确定后补充精确命令。最低 runtime 矩阵包括：

- 聚焦 C++ lifecycle/composition test；
- architecture ownership 与 forbidden-dependency test；
- manifest schema/canonical-hash fixture；
- 默认 CPU 行为与 replay comparison；
- 适用时的 backend admission 和 CPU/CUDA parity；
- Python binding 回归；
- P2-C1 起的 Cordis producer lifecycle/conformance test；
- 仅在 P6-B 显式获准时运行 Node host test；
- 代表性 multi-world 启动、内存和 step-throughput probe。

## 验收标准

- native 与 Cordis producer 共享一个版本化 composition contract。
- Experiment intent、Cordis 声明式组合、按 owner 分类的准入与原生实例化是相互分离的
  显式权威。
- 原生解析与实例化确定、事务化、有 scope 且携带 evidence。
- Flecs 和原生 stage scheduler 继续拥有仿真执行权威。
- 具体默认 model/backend 构造离开 kernel/facade constructor。
- 可替换 provider 不会在已注册系统中留下旧引用。
- system/domain contribution 通过既有 stage/capability admission。
- Cordis/Node 不进入维护中的逐 step call graph。
- native/Python 运行不依赖 Node 安装。
- host/backend parity 失败不能被 compatibility fallback 隐藏。
- 已接受 runtime 行为、文档、index、evidence 与 archive 状态一致。

## 残余地图

立即：

- 将已接受的 P1-A census、P1-B contract 与 P2-A lifecycle kernel 作为不可变输入；
- 实现 P2-B，同一切片不启动 system family、backend、Cordis package 或 binding 迁移，
  但要发布首份 production composition identity；
- 保持既有默认 behavior/replay baseline，并在声明 provider replacement 安全前移除
  environment-model raw capture；
- 以一条固定短 trace 完成迁移前后对比，不建立新的通用 replay framework；
- P2-B 后派发 P2-C0 冻结 request/catalog-lock authority，再派发 P2-C1，用真实默认
  provider path 而不是仅凭 fixture 证明 Cordis primitives 加仓库 profile/bundle layer。

后续：超出已接受 native-direct/本地 `ef_py` P7-A 切片的更广 host 行（Node 行取决于
P6-B）、超出已接受默认值的更广 provider/system/profile admission、超出
CPU-exact 有界切片的 backend evidence parity 与 CPU/CUDA parity、另行批准的 Node host，
以及超出仓库自有 SDK 的外部 plugin 签名/分发与开发工具。

另行验收后再做：公开插件市场、远程 package registry/自动下载、不可信 native plugin
sandbox、分布式多进程仿真 ownership、影响 truth 的 live reload，以及整体替换现有
binding/ECS。
