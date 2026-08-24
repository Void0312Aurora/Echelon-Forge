# Cordis 仿真组合内核验收合同 — 2026-08-17

状态：`2026-08-23` 有界验收记录；documentation/authority、composition-census、
contract/canonicalization、P2-B native production seam、P2-C0 projection/catalog-lock、
P2-C1 默认 profile Cordis/native、P3-A 默认图 system-contribution、P3-B 默认 profile
projection、P4-A 默认 backend provider、P5-A 默认 CPU-exact composition evidence、
P6-A package maturation、P7-A host/batch parity 与 P8-A migration closure 均已在各自
声明边界内接受。有界默认 CPU-exact 计划已闭合；更广 profile/provider、Node、CUDA、
外部 plugin 与完整 replay 继续作为 held 残余。

语言：

- 英文规范页：[cordis_simulation_composition_kernel_acceptance_20260817.md](cordis_simulation_composition_kernel_acceptance_20260817.md)
- 中文配套页：`cordis_simulation_composition_kernel_acceptance_20260817.zh.md`

Document kind: `task`
Lifecycle: `archived`
Canonical: `docs/architecture/work/archive/cordis_simulation_composition_kernel/cordis_simulation_composition_kernel_acceptance_20260817.md`
Owner: `architecture/runtime-composition`
Last verified: `2026-08-23`

父项目：[Cordis 仿真组合内核](README.zh.md)

## 验收边界

本合同区分有界的 native P2-B 验收与后续全局收口。P2-B 证明 production
provider seam；尚未实现的 Cordis、backend、host 或性能迁移不属于本次验收。

## 门禁矩阵

| 门禁 | 必需证据 | 拒绝条件 | 状态 |
| --- | --- | --- | --- |
| 文档与权威 | 双语 archived evidence package、维护中 standard、completed-work 父路由、有效链接、同步元数据与显式 Experiment projection/Cordis/admission/native 权威链 | orphan task、composition owner 竞争、stale active route 或 runtime 过度声明 | pass |
| Composition census | constructor、replacement、registration、backend、stage、reset、binding、test 的可复现 inventory | 迁移范围内仍有未知 owner 或未分类 replacement path | pass |
| Contract/canonicalization | versioned schema、invalid-input matrix、canonical byte fixture、permutation-stable hash | 结果依赖发现顺序、host 或歧义 provider 语义 | pass |
| 原生 lifecycle | P2-B production provider 构造、一条 failure/teardown rollback 路径，以及无悬垂 service reference | 部分 runnable state、stale handle 或 teardown 顺序歧义 | accepted bounded P2-B |
| 默认行为 parity | 一次受控的迁移前后默认 state/event/observation/replay 对比 | 通过 tolerance/fallback 隐藏无法解释的语义差异 | accepted bounded P2-B |
| Stage graph integrity | 既有 stage contract validation、精确默认图 comparison 与 owner-derived registry admission | plugin/host event order 影响 stage execution | accepted bounded P3-A default-graph slice；完整 semantic-stage/read-write projection 仍开放 |
| Domain profile admission | 默认 compatibility profile 的 capability/policy join 与 owner-derived contribution bundle；更广 minimal/common/air/naval/ground/combined profile | profile 绕开领域成熟度或创建私有 lifecycle | accepted bounded P3-B default-profile slice；更广 domain profile planned |
| Backend admission | facade 按精确 profile/provider/version/capability identity 选择准入 provider；unsupported candidate 与 construction failure 均 fail closed | 具体 backend 仍是构造真值、忽略 identity drift 或拒绝 profile 静默 fallback | P4-A 默认 provider 有界切片已接受；更广 provider admission 仍开放 |
| Projection/catalog-lock authority | versioned producer-neutral request DTO、确定性 owner-derived lock、canonical bytes/hash、category-owner matrix、正负 admission case 与 offline high-level-lowering guard | Cordis 拥有私有 catalog、存在两个高层 resolver，或原生侧无法核验 lock identity/selection | accepted bounded P2-C0 |
| Evidence/replay | 精确 request/manifest/lock/profile identity、11 个 provider version、83+2+34 graph identity、精确 backend identity、原生执行 owner、全部 world/五类 scope、commit-sealed evidence 与严格 replay/comparison mismatch rejection | unexplained composition/catalog-lock/backend/graph/scope mismatch 下仍继续 replay/comparison，或当前状态覆盖已提交 window | P5-A 默认 CPU-exact 有界切片已接受；更广 profile/backend 与完整 state replay 仍开放 |
| Cordis conformance | Cordis primitives 加仓库 profile/bundle layer 通过 owner lock lower 真实默认 request，生成 canonical manifest 并完成原生 realization | 原生侧不重新校验、Cordis 绕开 owner admission、存在私有 Cordis catalog，或 parity 仅覆盖 synthetic manifest fixture | accepted bounded P2-C1 default-profile slice；必需默认纵向路径已纳入 P8 closure |
| Binding isolation | Python/C++ 使用同一原生执行 owner；Node 在另行准入时也必须如此 | binding 拥有仿真真值、raw ECS bypass、逐 step callback，或 Node 成为离线 native/Python 必需依赖 | P7-A native-direct/本地 `ef_py` caller evidence 有界范围已接受；Node 仍开放 |
| Batch/performance | 代表性启动、内存、吞吐、determinism、teardown 测量 | mandatory per-world Node context、hot-path lookup/crossing 或未批准回归 | P7-A 32-world CPU-exact 回归 envelope 有界范围已接受；更广硬件/profile characterization 仍开放 |
| Security/provenance | 已接受范围的仓库拥有/准入 plugin policy | 未评审外部 native plugin 执行或缺失 artifact provenance | 仓库构建默认范围已接受；外部 artifact 由 `owner.security` held |
| Migration closure | caller inventory、removal gate、standard/reference 提升、index/archive 同步 | 双 composition path、永久未记录 wrapper 或 stale route | accepted bounded P8-A closure |

## 必需验证族

### 架构与依赖

- ownership/forbidden-include test；
- 单一 composition authority guard；
- 无 cross-language stage-call guard；
- 退役位置不再直接构造具体 model/backend；
- task label 不进入 production identifier。

### Contract

- schema generation/freshness；
- accepted/rejected manifest corpus；
- 跨 host/platform canonical serialization；
- dependency/conflict/capability resolution matrix；
- stable service-key/version compatibility test。

### Lifecycle

- construction 与逆依赖 teardown；
- 每个 resource index 的 constructor failure；
- nested scope isolation；
- reset、resize、backend failure、shutdown；
- 支持平台上的重复 create/destroy 与 sanitizer/leak check；
- provider/scope 迁移后无 dangling pointer。

### 仿真 parity

- default compatibility profile 下确定性 state/event trace；
- observation/action/reward/termination equivalence；
- exact-stage graph identity；
- replay/comparison mismatch handling；
- 既有 backend contract 下 CPU 与准入 CUDA profile parity。

### Host 与性能

- Node 缺失时 standalone C++/Python 正常运行；
- P2-C1 起的 Cordis producer lifecycle、failure 与 conformance；
- 仅在 P6-B 获准时要求 Node host lifecycle 与 exception translation；
- maintained step call graph 中没有 Node/Python/IPC frame；
- 大 world-batch 启动、内存、step、reset、teardown probe；
- 将 cold/warm composition 测量与 step throughput 分离。

## Evidence package 要求

最终验收必须保留 baseline revision/toolchain、manifest/schema version 与 fixture hash、
resolved composition/stage graph identity、精确验证命令和结果、host/backend/profile
matrix、性能环境和原始测量、failure-injection matrix、已知残余与禁止声明、已接受的
removal/compatibility 决定，以及同步后的文档/archive route。

## 部分验收

P2-B 作为有界 native slice，只有在以下六项阻塞项关闭后才能验收：native provider
构造已脱离 kernel concrete ownership/raw capture；一次受控 behavior/replay 对比；一条
production failure/teardown rollback 路径；重复 create/destroy；稳定 identity/generation；
以及无未解决 P1/P0 的最终独立审阅。其余 gate 属于 P2-C0、P2-C1、后续 implementation
cluster 或全局收口。

## 有界验收记录 — 2026-08-22

P2-B 已在 native production seam 接受：默认 provider catalog、受控 parity trace、
production failure/teardown rollback、重复 create/destroy evidence、稳定
requested/resolved identity 以及独立 `gpt-5.6-sol/max` 审阅均为绿色（`P0=0`、`P1=0`）。
P2-C0 已作为 producer-neutral request 与 owner-derived catalog-lock contract 接受：
generated schema/fixture、canonical identity 重算、负向 admission、native revalidation
与 offline low-level-only guard 均为绿色。

该验收不声明更广 Cordis profile、backend parity、Node host、外部 artifact signing 或
全局计划 closure。P2-C1 默认 profile producer/native 切片作为有界切片接受；更广
profile/bundle 覆盖与剩余 residual 仍开放。

P3-A 作为默认图有界切片接受。owner-derived registry 替换中央 component/system call，
并把 83 个 component row、34 个 manifest system row 与冻结 resolved artifact 对照校验；
manifest row 外的 2 个 kernel pre-update reset system 也被显式纳入其 owner。native 与
Python composition 回归、精确注册顺序 parity、CTest 与 P3-A composition/structural guard
均为绿色；全仓 include-direction ratchet 仍有一个既有 smoke-test violation。尚未开放
profile-specific package omission、全部 system 的完整 semantic-stage/read-write 声明或
外部 package trust。

P3-B 作为默认 profile projection 有界切片接受。版本化 projection contract 将具名
compatibility profile 绑定到 capability/policy set、6 个 owner-admitted catalog category、
83 个 component contribution identity 与 34 项 native system order。Cordis producer 仅在
request/lock join 后输出 projection；native conformance 在构造 `SimulationKernel` 前再次
校验同一 identity join。负向 fixture 覆盖 profile forgery、capability/policy substitution、
owner forgery 与 execution-order tampering。完整 semantic-stage/read-write metadata、更多
domain profile 与外部 package 仍开放。

P4-A 作为默认 provider 有界切片接受。`RuntimeFacade` 只通过 generated
profile/provider/version/capability admission 路径实例化维护中的
`cpu_exact.reference` backend；unsupported identity 在 factory 调用前被拒绝，factory 异常
封闭且不 fallback。更广 provider、CUDA parity 与多 profile catalog 仍开放。

P5-A 作为默认 CPU-exact composition-evidence 有界切片接受。
`runtime_composition_evidence.v1` artifact 绑定 request、requested/resolved manifest、
catalog lock、profile projection、全部 11 个 provider version、精确 backend identity，
以及由 owner registry 派生的 83 个 component、2 个 kernel system 与 34 个 resolved system
执行图。每个 realized world 记录全部五类 scope；单调 facade incarnation 阻止 resize 或
`configure_batch` ABA；zero-world evidence fail closed；window commit 封存 maintained replay
与 comparison 使用的 identity；所有无法解释的 mismatch 均被拒绝。已接受 host 字段仅表示
原生执行 owner（`native_cpp/native.v1`），包括 Python 作为粗粒度 caller 的情况；不声明
调用语言或物理模块来源证明。更广 profile/backend、完整 simulation-state replay、Node 与
外部 package provenance 仍开放。

P6-A 作为仓库自有默认 profile package 有界切片接受。Cordis package 暴露严格的
package/overlay SDK 定义，以确定性四节点图解析精确 Cordis runtime、profile module、
profile bundle 与默认 overlay，并拒绝缺失、重复、成环、冲突、未固定、unsafe path、
非 ASCII 或改变 truth 的输入。全部原始 hash 输入和五个 bundle artifact 均以 `-text`
保持 LF 字节稳定；package provenance 绑定 descriptor、dependency graph、overlay、producer/
package lock、request、catalog lock 与 profile projection，diagnostics 在报告 validated handoff
前再次把封存 provenance 与实际 artifact 对照。不变的 canonical request/lock/projection/
manifest 继续由既有 native conformance 路径接受。独立 `gpt-5.6-sol/max` 审阅返回
P0/P1/P2 = 0/0/0。该边界不准入更广或改变 truth 的 profile、外部签名/分发/plugin、
Node hosting 或 CUDA parity。

P7-A 作为默认 CPU-exact host/batch parity 有界切片接受。Cordis 继续只是 producer/control
plane，其 artifact 在 direct C++ 与本地 `ef_py` 行执行前先通过 native conformance。两行均
匹配独立封存的 semantic reference，覆盖非零 typed action、state/observation、window event
trace、非零 reward、termination/truncation、精确 composition 与 maintained replay evidence。
冻结的 32-world budget 分离 cold/warm construction 与 warmed stepping，在每次 timed reset
前恢复同一 loaded workload，测量 current/OS high-water RSS，并 gate teardown residual memory。
validator 重算派生值并拒绝重新封存的 semantic、replay、graph、metric、host/environment 与
integer-alias forgery。独立 `gpt-5.6-sol/max` 审阅返回 P0/P1/P2 = 0/0/0。Node 继续由 P6-B
held；更广 profile/backend、CUDA parity 与完整 replay 在有界闭合之外继续 held。

P8-A 作为有界 migration closure 接受。native builder 不再含隐式 empty-manifest fallback；
默认 constructor 显式使用 generated resolved artifact，并与 explicit Cordis/native manifest
bridge 汇入同一条路径。production 与已记录的 test-only publication-failure seam 共享一个
内部 native realizer。封存 live inventory 证明七个 model setter 与 kernel/facade 退场位置
的 concrete construction 不存在，分类十个 retained caller surface，并在接受 identity 前
重新验证 request、lock、projection、manifest、package bytes/provenance、composition evidence
与 parity evidence。严格 schema 与 focused attack test 会拒绝被修改的上游 payload、未分类
native caller、额外 authority/truth 字段与重新封存 closure forgery。稳定规则已进入维护中的
runtime composition baseline，work package 已归档，全部可选 residual 具有具名 held owner 与
activation gate。

native composition、Cordis producer/native 纵向切片、system/profile composition、
backend/evidence integration 与 Node hosting 可以分别作为有界切片验收，但父状态必须
写清边界。native composition 验收不代表 Cordis/Node 验收；Cordis manifest conformance
不代表外部 plugin trust；Node host 验收不代表测试矩阵外的性能/backend parity。独立
切片验收避免 conditional Node 或外部生态决策阻塞 native/runtime 进展，但不会从整体
计划 closure 中移除 Cordis 纵向切片。

已接受的 P2-A 边界仅包括独立 `ef_composition` library，以及 closed JSON ingestion、原生
hash revalidation、typed-scope guard、不可变 plugin/factory identity、进程内语义
service-type identity、lifecycle 状态机、transactional scoped construction、generation invalidation、串行化的
replacement-aware rebuild、重入 wrapper 生命周期保持、handover admission 与逆序 disposal。
普通 MSVC 与 MSVC AddressSanitizer 各自通过 14 个 test、430 个 assertion；composition
architecture suite 为 20 passed、1 个
toolchain-dependent skip。默认 provider 集成、真实 Flecs handover 证据、reset/replay parity、
system capture 修复、artifact provenance、外部 DSO ABI pinning 与全部 Cordis/host 声明
仍未完成。

## 收口规则

只有全部必需 gate 已接受，或迁入具名的独立 active/held owner 且不留下双重真值路径，
本子项目才可关闭。必需 gate 包含默认 provider parity、production composition identity、
显式 Experiment-to-runtime projection、版本化 owner-derived catalog lock，以及至少一条
仓库自有 Cordis producer/native realization 路径。推迟 Node host、marketplace、remote host
或外部 plugin distribution 与关闭兼容；推迟 P2-C0 contract、P2-C1 Cordis 纵向切片、
lifecycle、deterministic composition、
evidence identity 或 default-profile parity 与关闭不兼容。

本规则在有界默认 CPU-exact 范围内已满足；它不准入任何 held residual。
