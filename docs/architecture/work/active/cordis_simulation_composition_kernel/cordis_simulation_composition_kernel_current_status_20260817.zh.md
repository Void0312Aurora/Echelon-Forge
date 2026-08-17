# Cordis 仿真组合内核当前状态 — 2026-08-17

状态：`2026-08-17` P2-A 原生 lifecycle baseline 加独立审阅修复；composition
ownership/migration edge 已分类，P1-B contract 与隔离的原生 realization kernel 已通过，
下一步是 P2-B，不声明已实现 Cordis 集成。

语言：

- 英文规范页：[cordis_simulation_composition_kernel_current_status_20260817.md](cordis_simulation_composition_kernel_current_status_20260817.md)
- 中文配套页：`cordis_simulation_composition_kernel_current_status_20260817.zh.md`

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/cordis_simulation_composition_kernel/cordis_simulation_composition_kernel_current_status_20260817.md`
Owner: `architecture/runtime-composition`
Last verified: `2026-08-17`

父项目：[Cordis 仿真组合内核](README.zh.md)

Contract baseline：
[P1-B manifest 与 resolution contract](cordis_simulation_composition_contract_20260817.zh.md)。

## 本 checkpoint 变化

- 创建并验证 owner-local active architecture 子项目；
- 确立 Cordis 为长期 composition control plane，而非确定性 stage executor；
- 确立原生组合内核为 realization/lifecycle authority；
- 定义 host-neutral manifest、deterministic freeze、evidence 和离线部署方向；
- 将计划拆成有限 contract、native、migration、Cordis、host、parity 和 closure 任务簇；
- 完成基于源码的 P1-A census，覆盖 constructor、setter、raw capture、service ref、
  system registration、backend selection、lifecycle、stage registry、binding、build ownership
  与 relevant test；
- 分类 7 个可替换 provider、3 个 kernel-owned service/event object、82 个中央 component
  registration、34 个 active system registration、30 个 exact stage、5 个 maintained
  stage-node manifest 与 3 个 Python runtime tier；
- 将 environment raw capture、backend admission/materialization 分裂、三种 scheduling
  truth surface 设为 P1-B 硬约束；
- 实现 host-neutral requested/resolved manifest contract，包含 5 个 scope、12 个稳定
  service key、稳定 failure code、显式 service binding、兼容规则与排除自身 hash 字段的
  SHA-256 identity；
- 增加 generated schema 与默认兼容 fixture，覆盖 11 个 provider、82 个 component、
  34 个 system，并增加 fail-closed invalid matrix 与 permutation-stability test；
- 增加隔离的 `ef_composition` static library，不依赖 engine、facade、Flecs、binding 或
  Cordis；
- 实现 closed requested/resolved JSON ingestion、原生 SHA-256 重算、typed-scope guard、冻结
  factory identity、lifecycle 状态转换、scoped transactional construction、typed generation
  handle、failure rollback、replacement-aware barrier rebuild、handover admission、确定性逆序
  disposal、value-snapshot identity accessor、串行化 lifecycle control、重入 wrapper 生命周期
  保持、完整 plugin/factory identity check、进程内语义 service-type identity check 与幂等
  shutdown；
- 普通 MSVC build 与 MSVC AddressSanitizer 下均通过 14 个聚焦 C++ test case、430 个
  assertion；composition architecture/contract 为 20 passed、1 个 toolchain-dependent
  `g++` skip；
- 未迁移默认 provider、kernel/facade constructor、system registration、backend selection、
  binding、Cordis package 或 Node host。

## 成熟度矩阵

| 表面 | 状态 | 当前证据 | 剩余工作 |
| --- | --- | --- | --- |
| 架构权威 | P0 pass / project active | 父 README、目标架构、父路由与文档验证 | 后续提升已接受 runtime 规则 |
| Composition census | P1-A pass | [基于源码的 census](cordis_simulation_composition_census_20260817.zh.md)，包含 owner/scope/replacement/disposition table | 在 generated evidence 替代前保持 census guard 同步 |
| Manifest contract | P1-B pass / repaired | requested/resolved generated schema、纯 C++ value type、canonical fixture、invalid corpus、deterministic test 与原生 requested/resolved hash 重算 | 持续守护 producer/schema/header parity；外部 admission 前证明 Cordis 逐字节等价输出与 artifact provenance |
| 原生 lifecycle kernel | P2-A pass / isolated / repaired | `ef_composition`、typed-scope guard、不可变 factory metadata、lifecycle 状态机、scoped transaction、replacement-aware rebuild、handover admission、identity accessor、rollback/disposal test、CI wiring 与 MSVC ASan 证据 | P2-B 接入真实默认 provider；广义原生验收前增加迁移特有 reset/replay 与真实 registry handover 证据 |
| Model/provider migration | absent | 既有 interface/setter | provider factory、kernel builder、lifetime-safe consumption |
| System composition | absent | 静态注册与 stage manifest 并存 | contribution contract 与 graph compilation |
| Backend composition | partial baseline | 已有语义 backend interface/capability contract | provider selection 与 facade construction migration |
| Composition evidence | absent | 既有 replay/diagnostics 基础可用 | manifest/graph identity 集成 |
| Cordis control plane | absent | 只有外部架构参考 | package workspace、plugin SDK、manifest producer、conformance test |
| Node host | absent | Node-API 只是候选 host boundary | 批准 binding target 与 lifecycle/parity test |
| Runtime acceptance | partial | P2-A 证明隔离 lifecycle 边界 | 默认行为、system、backend、evidence、Cordis、host、parity 与 closure gate |

## 已核验基线事实

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
12. P1-B 默认兼容 manifest 以确定方式表示 11 个 provider、82 个 component registration
    与 34 个 system registration。
13. P1-B resolution 有意保持无资源：它证明结构与语义的确定性，但不能授予由后续 runtime
    join 拥有的 stage、backend、domain、capability 或 artifact admission。
14. P2-A 能解析并重新校验冻结的默认 fixture，但原生 realization 目前使用 test factory；
    production 默认 provider 尚未迁入 catalog。
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
| `unique_ptr`、singleton ref、captured pointer 形成双重 model ownership | 正确性/use-after-free | 将 production default 迁到 P2-A scoped handle 并移除 raw capture | P2-B |
| 中央静态 system list | 扩展性/profile 歧义 | contribution descriptor 编译到 stage contract | P3 |
| 直接具体 backend 构造 | backend 演进和测试隔离 | backend provider admission | P4 |
| 多个潜在 manifest producer | composition truth 分叉 | canonical schema、native revalidation、stable hash | P1/P6 |
| 异步 Cordis lifecycle | 若直接复制会使 teardown 非确定 | 原生 dependency-safe lifecycle transaction | P2/P6 |
| per-world host overhead | world-batch 规模风险 | shared resolved profile + 轻量 native world scope | P2/P7 |
| 跨语言调用诱因 | 吞吐与确定性风险 | architecture guard 与 call-graph test | P6/P7 |
| plugin provenance/trust | 供应链与 truth authority 风险 | 外部插件前建立独立 admission/signing/sandbox 计划 | deferred |
| compatibility wrapper | 永久双路径风险 | 显式 owner、evidence、removal gate | 所有迁移阶段 |

## 推荐下一步顺序

1. 通过 P2-B provider 与 kernel builder 迁移默认 profile，同时证明 behavior/replay parity
   并移除 raw provider capture；
2. 增加迁移特有 reset、重复 rebuild 与 lifetime 证据；
3. 拆分 system/backend composition；
4. 将 composition identity 纳入 evidence；
5. 增加 Cordis producer，然后才增加 Node host；
6. 运行 host/backend/batch parity 并移除双路径。

## 显式拒绝的声明

- Cordis 集成尚未实现；P2-A 是 host-neutral 原生前置条件，不是 Cordis 本身。
- 当前 runtime 尚不是 plugin-composed。
- 本方案本身不会自动提升仿真性能。
- 已有 interface 不证明生命周期安全替换。
- Cordis plugin 加载成功不等于 runtime admission。
- 文档验收不能代表 runtime、parity、replay 或 performance 验收。
