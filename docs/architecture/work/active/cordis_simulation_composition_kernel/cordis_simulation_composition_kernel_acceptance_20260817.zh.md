# Cordis 仿真组合内核验收合同 — 2026-08-17

状态：`2026-08-17` acceptance contract；documentation/authority、composition-census 与
contract/canonicalization gate 已通过。P2-A 隔离原生 lifecycle baseline 获得部分验收；
与迁移相连的 runtime realization 仍未完成。

语言：

- 英文规范页：[cordis_simulation_composition_kernel_acceptance_20260817.md](cordis_simulation_composition_kernel_acceptance_20260817.md)
- 中文配套页：`cordis_simulation_composition_kernel_acceptance_20260817.zh.md`

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/cordis_simulation_composition_kernel/cordis_simulation_composition_kernel_acceptance_20260817.md`
Owner: `architecture/runtime-composition`
Last verified: `2026-08-17`

父项目：[Cordis 仿真组合内核](README.zh.md)

## 验收边界

验收表示本范围内的长期组合架构已经实现、集成、形成证据并完成路由；不表示未来所有
第三方 plugin、backend、domain、remote host 或 hot-reload 模式均已验收。

## 门禁矩阵

| 门禁 | 必需证据 | 拒绝条件 | 状态 |
| --- | --- | --- | --- |
| 文档与权威 | 双语 active package、父路由、有效链接、同步元数据、显式 Experiment projection/Cordis/admission/native 权威链 | orphan task、composition owner 竞争或 runtime 过度声明 | pass |
| Composition census | constructor、replacement、registration、backend、stage、reset、binding、test 的可复现 inventory | 迁移范围内仍有未知 owner 或未分类 replacement path | pass |
| Contract/canonicalization | versioned schema、invalid-input matrix、canonical byte fixture、permutation-stable hash | 结果依赖发现顺序、host 或歧义 provider 语义 | pass |
| 原生 lifecycle | scope isolation、transactional construction、dependency-safe teardown、rollback、failure injection | 部分 runnable state、stale handle 或 teardown 顺序歧义 | partial：P2-A baseline pass；production migration 证据未完成 |
| 默认行为 parity | 迁移前后 state、event、observation、reward、termination、replay comparison | 通过 tolerance/fallback 隐藏无法解释的语义差异 | planned |
| Stage graph integrity | 既有 stage contract validation 与精确默认图 comparison | plugin/host event order 影响 stage execution | planned |
| Domain profile admission | minimal/common/air/naval/ground/combined 对 owner contract 的校验 | profile 绕开领域成熟度或创建私有 lifecycle | planned |
| Backend admission | facade 选择准入 provider；CPU/CUDA 与 unsupported-profile gate | 具体 backend 仍是构造真值或拒绝 profile 静默 fallback | planned |
| Evidence/replay | 先在 P2-B 输出 production manifest identity，再扩展 provider/graph/backend/host/catalog identity 并执行 mismatch policy | unexplained composition mismatch 下仍继续 replay/comparison | planned |
| Cordis conformance | 仓库自有 Cordis 默认 profile producer 与原生 compatibility producer 生成等价的准入 canonical manifest 和原生 realization | 原生侧不重新校验、Cordis 绕开 owner admission 或私有 Cordis identity 泄漏到 contract | planned / program closure required |
| Binding isolation | Python/C++ 始终使用同一 native owner；Node 在另行准入时也必须如此 | binding 拥有仿真真值、raw ECS bypass、逐 step callback，或 Node 成为离线 native/Python 必需依赖 | planned |
| Batch/performance | 代表性启动、内存、吞吐、determinism、teardown 测量 | mandatory per-world Node context、hot-path lookup/crossing 或未批准回归 | planned |
| Security/provenance | 已接受范围的仓库拥有/准入 plugin policy | 未评审外部 native plugin 执行或缺失 artifact provenance | planned |
| Migration closure | caller inventory、removal gate、standard/reference 提升、index/archive 同步 | 双 composition path、永久未记录 wrapper 或 stale route | planned |

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
- Node/Cordis host lifecycle 与 exception translation；
- maintained step call graph 中没有 Node/Python/IPC frame；
- 大 world-batch 启动、内存、step、reset、teardown probe；
- 将 cold/warm composition 测量与 step throughput 分离。

## Evidence package 要求

最终验收必须保留 baseline revision/toolchain、manifest/schema version 与 fixture hash、
resolved composition/stage graph identity、精确验证命令和结果、host/backend/profile
matrix、性能环境和原始测量、failure-injection matrix、已知残余与禁止声明、已接受的
removal/compatibility 决定，以及同步后的文档/archive route。

## 部分验收

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
显式 Experiment-to-runtime projection、按 owner 分类的 admission，以及至少一条仓库自有
Cordis producer/native realization 路径。推迟 Node host、marketplace、remote host 或外部
plugin distribution 与关闭兼容；推迟 Cordis 纵向切片、lifecycle、deterministic composition、
evidence identity 或 default-profile parity 与关闭不兼容。
