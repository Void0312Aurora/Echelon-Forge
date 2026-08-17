# Cordis 仿真组合内核任务簇

状态：`2026-08-17`，[Cordis 仿真组合内核](README.zh.md)的有限交付计划；P0、P1-A 与
P1-B 已通过，P2-A 已作为隔离的原生 lifecycle baseline 通过，下一步是 P2-B。

语言：

- 英文规范页：[cordis_simulation_composition_kernel_task_clusters_20260817.md](cordis_simulation_composition_kernel_task_clusters_20260817.md)
- 中文配套页：`cordis_simulation_composition_kernel_task_clusters_20260817.zh.md`

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/cordis_simulation_composition_kernel/cordis_simulation_composition_kernel_task_clusters_20260817.md`
Owner: `architecture/runtime-composition`
Last verified: `2026-08-17`

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
| `P0-A Authority Scaffold` | main thread | n/a | 创建双语 active 子项目、架构、状态、队列、验收、archive 和父路由。 | `docs/architecture/work/active/cordis_simulation_composition_kernel/**`、`docs/architecture/README*`、选定双语注册表条目 | runtime code、能力声明 | 文档元数据、本地链接、双语配对、`git diff --check` | 必需文件齐全且架构 owner 路由本项目 | 首个串行任务簇 | 1 + 1 repair | pass |
| `P1-A Composition Census` | main thread | n/a | 盘点全部 constructor、setter、raw capture、service ref、system registration、backend selection、reset boundary、stage registry、binding entry 和相关测试。 | 本项目 current-status/evidence 文件，可选生成式 inventory | runtime 修改、在 inventory 中隐藏设计变更 | 可复现 `rg` inventory、直接 ownership trace 和文件行证据 | 每条 composition edge 都有 owner、scope、replacement rule 和 migration disposition | P0-A 后 | 1 + 1 repair | pass |
| `P1-B Manifest And Resolution Contract` | main thread | n/a | 冻结 host-neutral manifest schema、plugin/provider descriptor、service key、scope、conflict rule、canonical encoding、versioning 和 resolution order。 | `src/runtime/contracts/**`、schema producer input、`tests/architecture/composition/**`、本设计更新 | provider 实现、Node host、动态下载 | schema freshness、canonical fixture、invalid-manifest matrix、确定性 permutation test | native 与未来 Cordis producer 可面向一个无歧义 contract | P1-A 后 | 2 + 1 repair | pass |
| `P2-A Native Lifecycle Kernel` | main thread | n/a | 实现 catalog、resolver、validator、scope、transaction、freeze、typed handle、effect、rollback 和确定性 disposal。 | 获批的新 `src/runtime/composition/**`、聚焦 CMake target、`src/tests/test_composition_lifecycle.cpp`、architecture guard | 同一切片迁移默认 provider、system、backend、binding 或 Cordis | 聚焦 C++、MSVC AddressSanitizer、failure injection、architecture contract suite | scope 隔离、失败原子性、确定性解析和 teardown 通过 | P1-A/P1-B 后；共享 contract 与 P2-B 串行 | 3 + 1 repair | pass |
| `P2-B Default Provider Migration` | future engine owner | n/a | 把默认 model、factory、event store、bridge、release service 构造迁入 native provider/kernel builder，并发布首份 production resolved-plan identity。 | `src/core/engine/**`、`src/models/**` composition 入口、准入 provider 文件、聚焦测试、有界 evidence DTO join | system-family 拆分、Cordis package、Node host | 默认行为/replay 基线、lifecycle test、无悬垂 provider capture、identity roundtrip/mismatch test | compatibility profile 在 `SimulationKernel` 不构造具体 model 的情况下构造当前 kernel，且 run 导出稳定 requested/resolved identity | P2-A 后；与 P3-A 共享 engine registration 文件时串行 | 3 + 1 repair | ready |
| `P2-C Cordis Default-Profile Vertical Slice` | future Cordis integration owner | n/a | 增加最小仓库自有 Cordis package/profile，消费 typed runtime projection，并输出 canonical 默认 P1-B request，交由原生侧重新校验和实例化。 | 有界 `packages/cordis-runtime/**`、package manifest/lockfile、canonical fixture、conformance test、本项目文档 | Node-API host、system-family 拆分、外部 plugin、完整 SDK ergonomics、hot-path service | Cordis package test、schema validation、canonical-byte/hash parity、native rejection parity、offline-native regression | Cordis 与原生 compatibility producer 输出字节等价默认 request；同一原生 compiler/root 实例化两者 | P2-B production identity 稳定后、广义 profile/ecosystem 工作前 | 2 + 1 repair | planned |
| `P3-A System Contribution Migration` | future scheduler owner | n/a | 用准入的 component/system/stage contribution 替换中央全域注册清单，并编译到既有 scheduler contract。 | `src/systems/**` 注册接缝、`simulation_kernel_systems.cpp`、runtime contract、composition test | 替换 Flecs、改变语义生命周期、私有 domain pipeline | 精确默认 stage-order parity、manifest validation、graph conflict test | compatibility profile 复现已接受默认图，profile 可省略无关系统族 | P2-B/P1-B 后 | 4 + 1 repair | planned |
| `P3-B Capability And Profile Projection` | future cross-domain integration owner | n/a | 把 typed capability/policy request 与 compatibility profile 名称下沉为 owner 准入的 model/component/system/stage bundle。 | owner 批准的 projection/profile contract、domain integration test、composition fixture | 把 air/naval/ground label 设为永久 ontology、提升领域成熟度、实现缺失行为 | projection validation、forbidden dependency guard、owner contract suite | capability requirement 为主；具名 domain profile 是不能绕开 owner standard 的显式 compatibility bundle | P3-A 声明后；写集不重叠时各 owner 可并行 | 每个 bundle family 2 + 1 repair | planned |
| `P4-A Backend Provider Migration` | future backend owner | n/a | 把 CPU、CUDA-resident、diagnostics 和未来 backend 选择迁入 provider admission，不改变 facade 语义。 | `src/runtime/facade/**`、`src/runtime/providers/**`、backend contract/test、CMake | 新 backend 语义、放宽 GPU parity | facade contract、backend admission matrix、CPU/CUDA 聚焦 parity | `RuntimeFacade` 不再构造具体 backend，拒绝的 profile 在运行前失败 | P2-A/P1-B 后；contract 不重叠时可与 P3-B 并行 | 3 + 1 repair | planned |
| `P5-A Composition Evidence Expansion` | future evidence owner | n/a | 在 P2-B/P2-C requested/resolved identity baseline 上增加 provider version、graph hash、backend profile、host mode、catalog lock 与 scope generation，并接入 diagnostics/replay/comparison contract。 | evidence/replay contract、facade diagnostics、schema generator、聚焦测试 | 对不支持的 backend/state 宣称完整 replay | DTO freshness、roundtrip、mismatch rejection、deterministic hash fixture | 维护中的 run 可识别 realized composition，replay 拒绝无法解释的 mismatch | P2-B 与相关 P3/P4 join 后 | 2 + 1 repair | planned |
| `P6-A Cordis Package Maturation` | future Cordis integration owner | n/a | 在已接受 P2-C producer 上扩展仓库自有 profile、configuration overlay、diagnostics、provenance、dependency resolution 与 plugin SDK ergonomics。 | 获批的 `packages/cordis-runtime/**`、workspace manifest/lockfile、fixture、文档 | JavaScript 仿真步进、任意外部 native plugin、替代 owner admission | package test、projection/schema conformance、canonical parity、provenance/diagnostics test | 维护中的 Cordis profile 只输出 owner 准入且被 native validator 同样接受的 request | P2-C 与相应 P3/P4 owner contract 后 | 3 + 1 repair | planned |
| `P6-B Node Host Adapter` | future bindings owner | n/a | 在粗粒度 `RuntimeFacade` 用例和原生 composition 上增加 Node-API adapter。 | 获批的 `src/interfaces/node/**`、CMake/package wiring、binding test | raw ECS 暴露、逐 stage callback、替换 nanobind | configure/load/reset/setup/inject/advance/evaluate/export/diagnostics 与 leak/teardown test | Node-hosted run 使用同一原生 runtime，stage execution 无 binding call | P6-A 且 P2/P4 原生 ownership 后 | 3 + 1 repair | planned |
| `P7-A Host And Batch Parity` | future integration owner | n/a | 证明 native、Python 与 Cordis-produced composition 保持确定行为和 batch budget；仅在 P6-B 获批时纳入 Node。 | integration test、benchmark/probe、evidence package、有界修复 | 通过调参掩盖语义 mismatch、无关优化 | producer/host parity matrix、replay comparison、大 batch 内存/启动/吞吐 | 冻结 profile 通过正确性和另行批准的回归预算 | P4-A/P5-A/P6-A 后；Node 行还要求 P6-B | 2 + 1 repair | planned |
| `P8-A Migration Closure` | main integration owner | n/a | 删除被取代的 setter/构造真值，提升稳定规则，记录 accepted scope，拆分残余并同步 index/archive。 | 受影响 composition code、architecture standard/reference、本项目 acceptance/archive、owner index | 删除历史证据、静默扩大插件准入、把 Cordis 当作可选完成证据 | 全验收矩阵、Cordis/native vertical conformance、link/bilingual audit、caller inventory、compatibility proof | 不再存在双 composition path；维护一条准入 Cordis producer/native 路径；可选 Node/外部生态残余有具名 owner | 最终串行任务簇 | 2 + 1 repair | planned |

## 派发规则

- 每个实现 packet 必须精确映射一个任务簇和一个有界 write set。
- P0、contract freeze、共享 runtime ownership、acceptance 和 closure 保持串行。
- P2-B 与 P2-C 是独立有界切片，但共享默认 profile/evidence contract，因此保持串行。
  P2-C 是整体计划关闭的必需条件；P2-B 可以保留独立的有界原生验收。
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
- P6-B 后的 Node host test；
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
- P2-B 后派发 P2-C，用真实默认 provider path 而不是仅凭 fixture 证明预期的 Cordis
  context/profile/plugin 模型。

后续：provider/system migration、backend admission、composition evidence expansion、Cordis
package maturation、另行批准的 Node host、plugin SDK ergonomics 和开发工具。

另行验收后再做：公开插件市场、远程 package registry/自动下载、不可信 native plugin
sandbox、分布式多进程仿真 ownership、影响 truth 的 live reload，以及整体替换现有
binding/ECS。
