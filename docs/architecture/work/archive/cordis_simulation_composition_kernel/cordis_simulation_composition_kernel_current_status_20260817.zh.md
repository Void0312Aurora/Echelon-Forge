# Cordis 仿真组合内核当前状态 — 2026-08-17

状态：`2026-08-23` P2-B production-provider migration、P2-C0
projection/catalog-lock、P2-C1 默认 profile Cordis/native、P3-A 默认
system-contribution migration、P3-B 默认 profile projection、P4-A 默认 backend-provider
migration、P5-A 默认 CPU-exact composition evidence 与 P6-A 默认 profile Cordis package
maturation、P7-A 默认 CPU-exact host/batch parity 与 P8-A migration closure 均已接受。
有界默认 CPU-exact 计划已闭合并归档；当前权威是维护中的 runtime composition baseline。
更广 profile/provider、Node、CUDA parity、外部 plugin distribution 与完整 replay 继续作为
held 残余。

语言：

- 英文规范页：[cordis_simulation_composition_kernel_current_status_20260817.md](cordis_simulation_composition_kernel_current_status_20260817.md)
- 中文配套页：`cordis_simulation_composition_kernel_current_status_20260817.zh.md`

Document kind: `task`
Lifecycle: `archived`
Canonical: `docs/architecture/work/archive/cordis_simulation_composition_kernel/cordis_simulation_composition_kernel_current_status_20260817.md`
Owner: `architecture/runtime-composition`
Last verified: `2026-08-23`

父项目：[Cordis 仿真组合内核](README.zh.md)

Contract baseline：
[P1-B manifest 与 resolution contract](cordis_simulation_composition_contract_20260817.zh.md)。

## 本 checkpoint 变化

- 创建并验证 owner-local active architecture 子项目；
- 确立 Experiment Face 为实验意图权威，建立显式 runtime projection seam，把 Cordis
  设为必需的长期声明式 composition control plane，由各 owner 准入实现，并把原生
  composition kernel 设为确定性 realization/lifecycle authority；
- 定义 host-neutral manifest、deterministic freeze、evidence 和离线部署方向；
- 将计划拆成可独立有界验收的任务切片，同时保留 Cordis producer/native 纵向路径作为
  整体 closure requirement，并把 Node hosting 保持为 conditional；
- 完成基于源码的 P1-A census，覆盖 constructor、setter、raw capture、service ref、
  system registration、backend selection、lifecycle、stage registry、binding、build ownership
  与 relevant test；
- 分类 7 个可替换 provider、3 个 kernel-owned service/event object、83 个中央 component
  registration、34 个 active system registration、30 个 exact stage、5 个 maintained
  stage-node manifest 与 3 个 Python runtime tier；
- 将 environment raw capture、backend admission/materialization 分裂、三种 scheduling
  truth surface 设为 P1-B 硬约束；
- 实现 host-neutral requested/resolved manifest contract，包含 5 个 scope、13 个稳定
  service key、稳定 failure code、显式 service binding、兼容规则与排除自身 hash 字段的
  SHA-256 identity；
- 增加 generated schema 与默认兼容 fixture，覆盖 11 个 provider、83 个 component、
  34 个 system，并增加 fail-closed invalid matrix 与 permutation-stability test；
- 增加隔离的 `ef_composition` static library，不依赖 engine、facade、Flecs、binding 或
  Cordis；
- 实现 closed requested/resolved JSON ingestion、原生 SHA-256 重算、typed-scope guard、冻结
  factory identity、lifecycle 状态转换、scoped transactional construction、typed generation
  handle、failure rollback、replacement-aware barrier rebuild、handover admission、确定性逆序
  disposal、value-snapshot identity accessor、串行化 lifecycle control、重入 wrapper 生命周期
  保持、完整 plugin/factory identity check、进程内语义 service-type identity check 与幂等
  shutdown；
- native lifecycle 通过 15 个 test case、443 个 assertion，default simulation smoke 通过
  41 个 test case、889 个 assertion；world-batch compatibility 还验证了跨 shutdown 的
  snapshot-owned visual scene；composition architecture/contract 为 32 passed、1 个
  toolchain-dependent `g++` skip；
- 已将默认 model/event/service ownership 迁移到准入的 native provider 与 composition-root
  builder；system 通过 generation-aware Flecs ref 读取可替换 service，不再保留 registration-time
  raw capture；
- 已实现 P4-A 默认 backend-provider 有界接缝：`RuntimeFacade` 不再点名或构造
  `FlecsCpuBackend`；native provider catalog 会在调用 factory 前拒绝 unknown、diagnostics-only、
  unmaintained、profile mismatch、重复 identity 与 capability-invalid request。独立
  `gpt-5.6-sol` / `max` 审阅返回 P0/P1/P2 = 0/0/0。
- 已实现并接受 P6-A package maturation 有界切片：公开 Cordis SDK 定义严格仓库 package/
  overlay value，确定性解析四个固定依赖节点，使全部原始 hash 输入保持 LF 字节稳定，拒绝
  dependency/overlay/path/hash/version forgery，把 provenance 封存到实际 request/lock/profile
  projection，并仅在重验后输出无本机路径 diagnostics。Node package test 为 20/20，
  composition architecture suite 为 54 passed 加 1 个本机 `g++`-dependent skip，聚焦 native
  CTest 为 4/4，独立 `gpt-5.6-sol` / `max` 审阅返回 P0/P1/P2 = 0/0/0。

## 成熟度矩阵

| 表面 | 状态 | 当前证据 | 剩余工作 |
| --- | --- | --- | --- |
| 架构权威 | accepted / promoted | [runtime composition baseline](../../../standards/runtime_composition_baseline.zh.md)、归档 evidence package、父路由与文档验证 | 仅 owner-approved amendment |
| Composition census | P1-A pass | [基于源码的 census](cordis_simulation_composition_census_20260817.zh.md)，包含 owner/scope/replacement/disposition table | 在 generated evidence 替代前保持 census guard 同步 |
| Manifest contract | P1-B pass / repaired | requested/resolved generated schema、纯 C++ value type、canonical fixture、invalid corpus、deterministic test 与原生 requested/resolved hash 重算 | 持续守护 producer/schema/header parity；外部 admission 前证明 Cordis 逐字节等价输出与 artifact provenance |
| 原生 lifecycle kernel | P2-A pass / production-enabling substrate | `ef_composition`、typed-scope guard、不可变 factory metadata、lifecycle 状态机、scoped transaction、replacement-aware rebuild、handover admission、identity accessor、rollback/disposal test、CI wiring 与 MSVC ASan 证据 | 真实 registry handover 与更广原生验收证据 |
| Model/provider migration | P2-B accepted bounded slice | 11-provider default catalog、embedded resolved-plan、私有 native root-service accessor、production identity/generation accessor、operation lock、raw-world lease quarantine、fail-closed rebuild guard 与 smoke/lifecycle evidence | 后续 binding migration 与更广 provider package |
| System composition | P3-A 默认图有界切片已接受 | owner-derived registry 校验 count、identity、dependency edge 与 stage order；native conformance 在 realization 前另行校验冻结 default artifact | profile-specific omission、完整 semantic-stage/read-write join 与更广 package admission |
| Capability/profile projection | P3-B 默认 profile 有界切片已接受 | 版本化 projection contract join capability/policy、owner catalog、83 个 component identity 与 34 项 native system order；Cordis/native conformance 重复校验该 join | 更多 profile、完整 semantic-stage/read-write metadata 与外部 package admission |
| Backend composition | P4-A 默认 provider 有界切片已接受 | `RuntimeFacade` 通过从 generated resolved manifest 派生的 native provider catalog 实例化维护中的 CPU-exact backend；聚焦原生准入与 fail-before-factory 测试通过；独立审阅返回 P0/P1/P2 = 0/0/0 | 更广 maintained profile、CUDA parity、diagnostics/provider evidence |
| Composition evidence | P5-A 默认 CPU-exact 有界切片已接受 | 版本化 schema/generator 绑定 request、requested/resolved manifest、catalog lock、profile projection、11 个 provider version、精确 CPU backend、83+2+34 executable graph、全部 world/五类 scope 与原生执行 owner identity；直接 composition comparison 拒绝无法解释的 mismatch | 更广 profile/backend、完整 state replay、调用语言/模块来源证明、外部 package |
| Projection/catalog-lock control plane | P2-C0 accepted bounded slice | 已有 producer-neutral request 与 owner-derived lock schema、generated fixture、canonical identity 重算、负向 admission matrix、native revalidation 和 offline low-level-only guard | P2-C1/P3-B 默认 profile join 已作为有界切片接受；更广 profile 仍为 residual |
| Cordis control plane | P2-C1/P3-B/P6-A 默认 profile package 有界切片已接受 | 严格 package/overlay schema 与 SDK export 固定 Cordis `4.0.0-rc.8`、package lock、profile module/bundle 和默认 overlay；确定性解析、LF 稳定原始 hash、封存 provenance、diagnostics 与不变的 native admission 均通过；独立审阅返回 P0/P1/P2 = 0/0/0 | 更广/改变 truth 的 profile 需 owner 准入；外部签名/plugin、更广 backend parity 与 Node host 仍开放 |
| Host/batch parity | P7-A 默认 CPU-exact 有界切片已接受 | Cordis artifact 先通过 native conformance；native-direct 与本地 `ef_py` 行匹配同一冻结 action/state/event/window/composition-comparison reference 与精确 composition identity；32-world cold/warm、loaded reset、current/high-water RSS、teardown residual 与 throughput gate 通过；独立审阅返回 P0/P1/P2 = 0/0/0 | Node 行由 P6-B held；更广 profile/backend、CUDA parity、多轮 leak characterization 与完整 replay 仍开放 |
| Node host | absent | Node-API 只是候选 host boundary | 批准 binding target 与 lifecycle/parity test |
| Runtime acceptance | accepted bounded default CPU-exact closure | 默认 behavior、system、backend、evidence、Cordis producer、native/Python parity、caller inventory、retired-surface proof、standard promotion 与 archive routing | 具名 held 残余需独立 admission |

## 历史基线事实（P2-B 前，采集于 2026-08-17）

以下事实用于追溯迁移前 census，不应被理解为当前 P2-B 实现状态。

1. `SimulationKernel` 构造具体默认 model 与相关 service。
2. `SimulationKernel` 手工销毁 world 和 model/service owner。
3. model setter 更新部分 Flecs singleton ref，但没有统一 provider restart protocol。
4. `GroundContactSystem` 捕获注册时传入的 environment-model pointer。
5. 中央 system-registration 函数以显式有序清单安装多个 domain family。
6. `WorldBatchRuntime` 为每个 world 创建完整 `SimulationKernel`。
7. 尽管有 `IWorldBatchBackend`，`RuntimeFacade` 仍直接构造 CPU backend。
8. 维护中的 stage contract 已定义 Cordis 不得替代的确定性图语义。
9. 已检查仓库中没有维护中的 Cordis、Node package 或 Node-API integration surface。
10. executable registration、exact-stage inventory 与 maintained stage-node manifest 是三种
    独立且部分重叠的 truth surface。
11. 已检查范围内，provider setter 在 declaration/definition 与 architecture documentation
    外没有 production caller；这只降低 compatibility risk，不会让当前 replacement semantic
    变得安全。
12. 默认兼容 manifest 以确定方式表示 11 个 provider、83 个 component registration
    与 34 个 system registration。
13. P1-B resolution 有意保持无资源：它证明结构与语义的确定性，但不能授予由后续 runtime
    join 拥有的 stage、backend、domain、capability 或 artifact admission。
14. P2-A 能解析并重新校验冻结的默认 fixture；当时原生 realization 使用 test factory，
    production 默认 provider 尚未迁入 catalog。P2-B 已完成该迁移。
15. P2-A 现会按冻结 canonical field rule 独立重算 requested/resolved hash，并拒绝 stale/
    tampered identity；外部 Cordis/native producer trust 仍需逐字节 conformance 与 artifact
    provenance 证据。
16. typed handle 在成功替换 generation 时失效，但 lifecycle rebuild/stop 必须发生在受治理
    quiescent barrier；调用方不得让 `try_get()` 返回的裸指针跨越该 barrier。
17. material composition iteration 必须独立审阅。默认矩阵覆盖 lifecycle/ownership、
    contract/canonicalization 与 integration/CI/documentation；未解决 P1 会阻断下一 cluster。

## 残余登记

| 残余 | 风险 | 必需处置 | Owner phase |
| --- | --- | --- | --- |
| 长生命周期 provider service 中残留 raw dependency reference | 正确性/use-after-free | 当前路径保留 kernel operation lock；后续改为 handle 并补齐 replay/fault-injection evidence | P2-C1/P2-C2 |
| raw Flecs compatibility lease 会永久关闭 provider rebuild | 可扩展性与 broad ECS surface 被长期保留的风险 | 保持显式且由 operation lock 保护的 lease；引入可重新开启的 world-reconfiguration lease 前，把剩余 consumer 迁移到 typed kernel/facade operation | P2-C2/P3 |
| 残余 profile-specific system package selection | 扩展性/profile 歧义 | 在已接受 owner-derived registry 上补齐 semantic-stage/read-write join 与 profile projection，并保持 native owner admission | P6/P7 |
| 超出维护中 CPU-exact 默认值的更广 backend-provider 准入 | backend 演进与 parity 风险 | 增加 owner 批准的 provider/profile contract 与 evidence，不得静默提升 diagnostics 或 unmaintained candidate | P4/P5/P7 |
| 调用语言或物理模块来源的 host 证明 | provenance 过度声明风险 | P5-A host identity 仅记录原生执行 owner；只有后续获准用例确有需要时才建立独立 module-origin contract | P6/P7 或独立 host decision |
| MSVC Release 优化 `bindings_runtime.cpp` 时单个翻译单元可持续超过一小时 | 构建可复现性与开发吞吐 | 拆分或以其他方式约束模板密集 binding 翻译单元，并证明未修改生成构建图的干净 Release `ef_py` 构建；本地 `/Od /Ob0` edge override 只算回归证据 | build infrastructure / binding owner |
| Experiment/Cordis/native 权威重叠 | composition truth 竞争 | 显式 intent projection、owner catalog lock、canonical request、native revalidation | P2-C0/P2-C1/P3/P6 |
| 异步 Cordis lifecycle | 若直接复制会使 teardown 非确定 | 原生 dependency-safe lifecycle transaction | P2/P6 |
| per-world host overhead | world-batch 规模风险 | shared resolved profile + 轻量 native world scope | P2/P7 |
| 跨语言调用诱因 | 吞吐与确定性风险 | architecture guard 与 call-graph test | P6/P7 |
| plugin provenance/trust | 供应链与 truth authority 风险 | 外部插件前建立独立 admission/signing/sandbox 计划 | deferred |
| compatibility wrapper | 永久双路径风险 | 显式 owner、evidence、removal gate | 所有迁移阶段 |

## 闭合后 residual 顺序

1. 仅在 profile、package 与 signing residual 分别有界后，继续扩展已接受的默认 package
   profile path；
2. 仅通过 owner-admitted artifact 证明更广 backend/profile parity；
3. 仅在另行批准后增加 Node host，再把其行加入 producer/host/backend/batch parity 并
   移除双路径。

## P8-A Migration Closure — 2026-08-23

P8-A 删除 production native builder 的隐式 empty-manifest fallback。`SimulationKernel()`
现在把唯一 generated 默认 resolved artifact 显式交给 explicit Cordis/native manifest bridge
所用的同一个 builder。七个 superseded model-replacement setter、`SimulationKernel` 内 concrete
provider construction 与 `RuntimeFacade` 内 concrete backend construction 保持不存在。
production 与已记录的 test-only publication-failure seam 委托同一个内部 native realizer。

封存 closure record 绑定已接受 request、catalog lock、profile projection、requested/resolved
manifest、package provenance/dependency graph、composition evidence 与 P7 parity evidence。live
inventory 分类维护中的 `RuntimeFacade`、默认 kernel compatibility/diagnostic、
`WorldBatchRuntime`、Cordis/native bridge 与 test-only fault-injection caller，
共九个 retained surface。validator 从 payload 与 live package bytes 重算上游 artifact
identity，并拒绝 strict-schema、caller-classification、lexical、underlying-payload 与重新封存
forgery attack。稳定规则已提升到 runtime composition baseline，owner index 已把本 package
路由为 completed work；Node、更广 profile/provider、CUDA、外部 plugin signing/distribution
与完整 replay 具有显式 held owner 和 activation gate。

## P7-A 实现修订 — 2026-08-23

已接受的 P7-A 切片保持 Cordis 的 producer/control-plane 角色，每项输出 artifact 均先通过
既有 native conformance binary。直接 C++ 与本地 `ef_py` caller 行随后证明精确 composition
join，并匹配独立封存的 semantic reference；该 reference 覆盖非零 typed pilot action、
observation/state、window event trace 与直接 composition comparison。batch evidence 分离
cold/warm construction，测量 32-world warmed step loop，
在每次 timed reset 前重建同一 loaded workload，并记录 current/OS high-water RSS 与 teardown
residual memory。validator 重算全部派生 metric，拒绝重新封存的 semantic、composition、identity、
metric、host 与 environment forgery。独立 `gpt-5.6-sol/max` 审阅返回 P0/P1/P2 = 0/0/0。

该验收不增加 Node 行、不扩大准入 profile/backend、不声明 CUDA parity，也不声明完整
replay。这些排除在有界计划闭合后仍成立。

## P2-B 实现修订 — 2026-08-20

默认 model、event-store、unit-factory、effects、sensor、acoustic、control、guidance、
damage-bridge 与 weapon-release 的 ownership 现通过 native provider catalog 与 composition
root 进入。`SimulationKernel` 输出 production requested/resolved identity；可替换 system
consumer 从带 generation 语义的 Flecs ref 解析 service，不再保留 registration-time raw capture。
backend provider 在本切片只记录已准入的默认 profile identity，backend execution migration 仍属 P4。

这是真实 Cordis 后续切片所需的 production seam，不是退回 native-only：P2-C0 将把
request/catalog-lock evidence 绑定到该 root，P2-C1 必须通过 Cordis primitives 加仓库
profile/bundle layer 把默认 request lower 到该真实路径。P2-B 不声明 Cordis 已集成。

本次 lifecycle 修复批次将 kernel ECS/provider operation 与 world rebuild、shutdown 串行化，
以原子方式刷新完整 root-handle 集，输出 world-scope generation，并用显式 RAII world
lease 保护剩余 raw Flecs access。lease 在存续期间持有 rebuild/shutdown 共用的 operation
lock；一旦获取，当前 fail-closed provider-rebuild barrier 将永久关闭。存在受监管
`SimObject`、发生 provider/world/clock state mutation，或 exact-stage trace frame 活跃时也会拒绝
rebuild；compatibility visual scene 只携带复制的 environment snapshot，不保存 provider pointer。
这是保守的 compatibility quarantine，不代表已证明任意 Flecs entity 均 quiescent，也不代表
已实现可重新开启的 world lease。

当前 migration evidence 为 15 个 native lifecycle case / 443 个 assertion、41 个 simulation
smoke case / 889 个 assertion、6 个 world-batch runtime case / 55 个 assertion、32 个
composition architecture/contract test（1 个 toolchain skip）以及 12 个
include-direction/flat-boundary test。新增 evidence 覆盖 generation 递增、
受监管实体/provider/clock-state-mutation/raw-world rebuild 拒绝、并发 rebuild 串行化、
getter/setter 同步、moved-from lease fail-closed、world lease 对 shutdown 的串行化，以及
shutdown 后 snapshot-only visual rendering，以及 ABI-compatible legacy visual field tombstone。
新增的有界 gate 已覆盖：同一 MSVC toolchain 下以 pre-P2-B commit `a618b423` 为基线的
固定十步默认短 trace、真实 default catalog 的 effects-publication failure rollback，以及
八次 kernel create/destroy。最终独立复核已为绿色，P2-B 有界验收已记录；不引入通用 replay framework，也不把
CUDA/backend parity 或 Cordis vertical slice提前纳入本切片。

## P2-C0 Projection And Catalog-Lock Contract — 2026-08-21

首个有界 P2-C0 切片已写入目标工作树，当前保持未提交，但有界验收已记录。新增内容包括
`src/runtime/contracts/composition/` 下 producer-neutral 的
`RuntimeCompositionRequest` contract 与 owner-derived `AdmittedCatalogLock`
contract、C++ token mirror、Python generator/validator、canonical fixture 以及负向
admission matrix。当前可重算 request identity：
`5c2954d6d04c77fe803130db14d7e5b56391dcf51e482c73ac8cd96877698d6f`；lock identity：
`ec36d4f134e003e852a87f0dc2edb8095bbd798855d88b099e0174d45efa7f94`；owner-authority
registry identity 为 `5c360890992168709c79fc3b633808d5ff564b52d4f55cd7ee019811ba8d651f`。

该 contract 明确不是第二套 resolver：不会 lower 到 P1-B manifest，不构造 provider，
不引入 Cordis 或 Node 依赖，也不改变 native production path。composition architecture
suite 为 `36 passed, 1 skipped`，native revalidation 已接入 focused C++ lifecycle target；
该切片随后完成了 P2-C0 有界验收，P2-C1 现为下一派发。

## 独立审阅 — 2026-08-21

按要求使用 `gpt-5.6-sol`、`max` reasoning 执行独立只读审阅。未发现 P0；初始切片发现
三个 P1：request 与 lock 未交叉绑定、request/lock string-array 校验未落实 schema 的
ASCII/NFC 约束、以及字段齐全但类型畸形的 entry 可能抛异常而非 fail-closed。以上已修复；
当前 composition suite 为 `36 passed, 1 skipped`，故意错配的 request/lock 已被 CLI 拒绝。

owner 自声明阻塞已在 repository-contract 层关闭：新增生成并带 hash 的
`owner_authority_registry.v1` repository authority artifact；每个 lock 携带其 SHA-256，
builder 与 validator 都会拒绝 owner/category forgery 和不完整 authority coverage。P2-C0
有界验收已记录。native revalidation 已通过 `ef_composition` 检查 request、lock、authority
registry、canonical bytes、SHA-256 identity、owner/category coverage、required capability
和 package provenance hash。剩余 P2 残余是外部 artifact signing/attestation，以及 C++
value struct 仍以 JSON bytes 作为递归 schema 边界，而不是自动生成的递归类型。

## Native Projection 校验加固 — 2026-08-22

native revalidation boundary 现已应用与 Python/schema contract 相同的 lock 元数据校验：
`contract_version` 必须等于准入的 v1 contract，`lock_id` 必须是稳定 identifier，
`lock_version` 必须是 semantic version。聚焦 native test 新增了这三个字段的负向 case，
并显式加入直接依赖 `<utility>`。

当前验证结果为 native lifecycle `16/16`、`462` 个 assertion，composition architecture
test `40` 项通过、1 项 toolchain skip，聚焦 CTest target 通过。P2-C0 有界验收已记录；
没有引入 Cordis 或 Node 依赖。

## P2-C1 默认 Profile 纵向切片 — 2026-08-22

已接受的 P2-C0 artifact 现通过仓库自有 Cordis producer 接入
`packages/cordis-runtime`。该 package 固定 `cordis@4.0.0-rc.8`，使用 Context、plugin、
event、service、injection 与 fiber disposal，拒绝未知 profile，并通过 profile 匹配的低层
manifest template lower 冻结的默认 request。CLI 会先重算 canonical request SHA-256 并要求
其等于准入 lock 的 `request_sha256`，再将准入 lock 与 lower 后的 manifest 一并交给 native
conformance seam。Producer metadata 同时记录固定的 Cordis 版本与原始
`package-lock.json` SHA-256；外部签名仍不属于本有界切片。

新增的 `ef_cordis_runtime_conformance_test` 会重新校验 request/lock/authority，检查默认
request 到 manifest 的 policy/configuration join 与 exact lock-to-default selection，摄取生成的
requested/resolved manifest，从传入 resolved artifact 构造 production `SimulationKernel`，
应用 request 的 seed/time-step 并执行一步。本机证据包括当前 9 个 Cordis test、4 个纵向 architecture
test、Python fixture/identity 校验、CTest 注册，以及带有 `providers=11`、
`production_generation=1`、request SHA-256 与 lock SHA-256 的 native 输出。这是首个纵向切片，
不声明更广 profile、backend parity、Node hosting 或外部 plugin admission。
该有界 native seam 不是针对任意低层 manifest 的通用防火墙：已强制 profile-specific
request/configuration/lock join，但自洽重算 hash 的低层扩展仍是已声明的 P2 residual。

## P2-B/P2-C0 最终独立复核 — 2026-08-22

对 P2-C1 之前的 P2-B/P2-C0 切片执行的独立 `gpt-5.6-sol` / `max` 审阅返回
`P0=0`、`P1=0`；P2-C0 有界验收已记录。该历史复核不关闭 P2-C1 gate，复现了
native `16/16`、`462` 个 assertion 以及 Python fixture identity 校验。剩余观察均为当时
已声明的 P2 residual：递归 configuration 仍以 canonical JSON bytes 表示，外部 artifact
signing/attestation 尚未实现，真实 Cordis lowering 属于 P2-C1。

## P2-C1 有界切片最终独立复核 — 2026-08-22

对最新工作树执行的独立 `gpt-5.6-sol` / `max` 审阅返回 `P0=0`、`P1=0`，复现了
MSVC build、CTest conformance/lifecycle、Cordis package test、composition architecture
test、Ruff、clang-format 以及 native 正负 handoff。默认 profile 的 P2-C1 切片在声明边界
内接受。P2 residual 仍包括任意自洽重算 hash 的低层扩展、direct API 的后置校验、跨 host
canonical comparator 加固与外部 bundle signing/attestation。更广 profile、backend/host
parity、外部 plugin 与全局 closure 仍未接受。

## P3-A System Contribution Migration — 2026-08-22

原先位于 central engine 的 component 与 system call list 已替换为
`src/core/engine/system_contribution_registry.cpp`（systems layer declaration 位于
`src/systems/system_contribution_registry.h`）中的 owner-derived registry。该 registry
声明 83 个 component contribution 与 34 个 system contribution，包含稳定 contribution ID、
factory ID、domain、stage-order label 与 dependency edge。触碰 Flecs 前，它会对缺失或重复
contribution entry、无效 factory/domain metadata、向前 dependency edge 与 stage-order drift
fail closed。
native conformance path 会在 production realization 前另行解析并重新校验冻结 resolved
compatibility artifact 的 component/system identity join。`SimulationKernel` 只保留两个
registry entry point；另有 2 个显式 kernel-owned pre-update reset entry，位于同一 registry
但不属于 34-row manifest compatibility list。package/discovery order 不会成为 Flecs execution
order，也没有 package 私有 pipeline。

有界验收覆盖精确 default graph parity、native `ef_test_all`、composition lifecycle/conformance
CTest、40 项 composition architecture test（1 项 toolchain skip）以及既有 Python/native
回归。尚未声明 profile-specific contribution omission、全部 34 个 system 的完整
semantic-stage/read-write join 或更广外部 package admission 已完成。

## P3-B Capability And Profile Projection — 2026-08-23

P3-B 有界切片新增 `runtime_profile_projection.v1`：它把默认 compatibility profile 的
capability/policy requirement、6 个 catalog-lock category、83 个 component contribution
identity 与 34 项 native system registration order 做成确定性 owner-derived join。Python
contract generator/schema 生成 canonical fixture，projection identity 为
`a6983836e82df80805ac3f0f4f4a6975edccf3024d8ff231a67009a596a28c09`，并提供 profile、
capability、policy、owner、component、claim、order 与 schema-invalid type tampering 负向
matrix。catalog row 与每个 row 的 capabilities 在生成 canonical bytes/identity 前均按 UTF-8
字节序规范化。

Cordis producer 现在在写出前对 frozen bundle 验证并 lower 该 projection；native conformance
executable 接收可选 projection artifact，在构造 `SimulationKernel` 前重校验 request/lock
identity、owner catalog entry、component identity 与 system order。native 会重构同一规范化
payload，拒绝未准入 profile version 和非 canonical array permutation，并重算 canonical
bytes 与 SHA-256。当前证据包括 5 个 profile-contract test、9 个 Cordis package test、4 个
纵向切片 test、composition architecture `45 passed, 1 skipped` 与 2 个聚焦 CTest。该切片
保持 capability requirement 为主，具名 profile 只是显式 compatibility alias；更多 profile、完整
semantic-stage/read-write metadata 与外部 package trust 仍未开放。

## P3-B 有界切片最终独立复核 — 2026-08-23

对修复后 P3-B 工作树执行的独立 `gpt-5.6-sol` / `max` 审阅返回 `P0=0`、`P1=0`、
`P2=0`。审阅复核了 canonical profile、capability/policy、owner catalog、component 与
native system-order join，以及 Cordis/native 正负 handoff。默认 profile projection 有界
切片已接受；更广 profile 与外部 package trust 仍开放。

## P4-A Backend Provider Migration — 2026-08-23

该有界实现从 generated resolved native manifest 派生默认 backend request，并通过 native
provider catalog 实例化维护中的 `builtin.backend.flecs_cpu@1.0.0`。production composition
provider 与 facade materializer 共用 provider identity 常量；`RuntimeFacade` 只依赖内部
backend SPI，不再点名或构造具体 Flecs backend。

以下情况均在调用 factory 前 fail closed：unknown schema/profile/provider、diagnostics-only
或 unmaintained candidate profile、空/重复/unsupported capability、provider/profile mismatch、
重复 provider identity、implementation-version drift 与无效 provider capability metadata。
当前本机证据为：聚焦 native 8 个 case / 71 个 assertion，聚焦 architecture 10 项，完整
runtime-facade architecture 76 passed，composition architecture 45 passed / 1 skipped，Cordis 9/9，三项聚焦 CTest
3/3。CI 现会在 composition suite 旁执行 P4-A architecture guard。最终独立
`gpt-5.6-sol` / `max` 审阅返回 P0=0、P1=0、P2=0，因此维护中的默认 CPU-exact
provider 有界切片已接受。更广 provider、CUDA parity 与 provider evidence 不在本次接受边界内。

Python 回归所用现有 `ef_py` artifact 是在本地 generated build 中仅对异常慢的
`bindings_runtime.cpp` 编译边关闭优化后生成，约 33 秒完成，但它不属于正式 Release
证据。同一模板密集翻译单元的干净 MSVC Release 尝试在单核持续工作、working set 约
2.4 GiB 的情况下超过一小时，因此 Release binding-build 收口仍是显式构建设施残余，
不能算作 P4 语义结果。

## P4-A 有界切片最终独立复核 — 2026-08-23

独立 `gpt-5.6-sol` / `max` 审阅未发现可执行问题，返回 `P0=0`、`P1=0`、`P2=0`。
复核覆盖 generated profile/provider/implementation-version/capability 精确准入、factory 前
fail closed、factory 异常封闭、generated-header freshness、CI wiring，以及 native/Cordis/Python
architecture 证据。P4-A 仅接受维护中的默认 CPU-exact provider；multi-provider、CUDA、
diagnostics/evidence 与完整 catalog 工作仍属后续 gate。

## 显式拒绝的声明

- Cordis 集成目前限于已记录验收的默认 profile 纵向切片；更广的 profile、backend、
  host 与外部 plugin admission 尚未纳入验收。P2-A 是其 host-neutral 原生 substrate，
  不是 Cordis 本身。
- Cordis 不会拥有实验意图、语义实现准入或确定性执行；明确这些边界是安全引入 Cordis
  的前置条件。
- 当前 runtime 尚不是 plugin-composed。
- 本方案本身不会自动提升仿真性能。
- 已有 interface 不证明生命周期安全替换。
- Cordis plugin 加载成功不等于 runtime admission。
- 文档验收不能代表 runtime、parity、replay 或 performance 验收。
