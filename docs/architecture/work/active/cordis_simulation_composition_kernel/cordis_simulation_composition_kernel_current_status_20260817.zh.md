# Cordis 仿真组合内核当前状态 — 2026-08-17

状态：`2026-08-20` P2-B production-provider migration 已完成实现；在 P2-A
原生 lifecycle baseline 与独立审阅修复基础上，默认 kernel 现通过原生 composition root
构造，但在 P2-C0/P2-C1 完成前不声明 Cordis 集成。

语言：

- 英文规范页：[cordis_simulation_composition_kernel_current_status_20260817.md](cordis_simulation_composition_kernel_current_status_20260817.md)
- 中文配套页：`cordis_simulation_composition_kernel_current_status_20260817.zh.md`

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/cordis_simulation_composition_kernel/cordis_simulation_composition_kernel_current_status_20260817.md`
Owner: `architecture/runtime-composition`
Last verified: `2026-08-20`

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
  33 个 test case、837 个 assertion；composition architecture/contract 为 21 passed、1 个
  toolchain-dependent `g++` skip；
- 已将默认 model/event/service ownership 迁移到准入的 native provider 与 composition-root
  builder；system 通过 generation-aware Flecs ref 读取可替换 service，不再保留 registration-time
  raw capture；backend provider 当前只承担 identity/admission，backend execution migration 仍属
  P4；Cordis package 与 Node host 不在本切片内。

## 成熟度矩阵

| 表面 | 状态 | 当前证据 | 剩余工作 |
| --- | --- | --- | --- |
| 架构权威 | P0 pass / project active | 父 README、目标架构、父路由与文档验证 | 后续提升已接受 runtime 规则 |
| Composition census | P1-A pass | [基于源码的 census](cordis_simulation_composition_census_20260817.zh.md)，包含 owner/scope/replacement/disposition table | 在 generated evidence 替代前保持 census guard 同步 |
| Manifest contract | P1-B pass / repaired | requested/resolved generated schema、纯 C++ value type、canonical fixture、invalid corpus、deterministic test 与原生 requested/resolved hash 重算 | 持续守护 producer/schema/header parity；外部 admission 前证明 Cordis 逐字节等价输出与 artifact provenance |
| 原生 lifecycle kernel | P2-A pass / production-enabling substrate | `ef_composition`、typed-scope guard、不可变 factory metadata、lifecycle 状态机、scoped transaction、replacement-aware rebuild、handover admission、identity accessor、rollback/disposal test、CI wiring 与 MSVC ASan 证据 | 真实 registry handover 与更广原生验收证据 |
| Model/provider migration | P2-B implemented / 待独立审阅 | 11-provider default catalog、embedded resolved-plan、native root-service handle、production identity、generation/quiescence guard、world rebuild 与 smoke/lifecycle evidence | replay 对比、fault-injected teardown、重复 create/destroy evidence、最终独立审阅 |
| System composition | absent | 静态注册与 stage manifest 并存 | contribution contract 与 graph compilation |
| Backend composition | partial baseline | 已有语义 backend interface/capability contract | provider selection 与 facade construction migration |
| Composition evidence | P2-B production identity 已实现 / 待审阅 | `SimulationKernel` 输出 generated requested/resolved identity，world rebuild 保持 identity | P2-C0/P2-C1 接入 request/catalog-lock identity，随后 P5-A 扩展 graph/backend/host/replay evidence |
| Cordis control plane | absent / required target | 已有架构与 P1-B 低层 producer contract；不存在高层 request/catalog-lock artifact 或仓库内 Cordis package | P2-C0 projection/catalog-lock contract、P2-C1 默认 profile producer/native 纵向切片，随后 P6-A package maturation |
| Node host | absent | Node-API 只是候选 host boundary | 批准 binding target 与 lifecycle/parity test |
| Runtime acceptance | partial | P2-A 证明隔离 lifecycle 边界 | 默认行为、system、backend、evidence、Cordis、host、parity 与 closure gate |

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
| 中央静态 system list | 扩展性/profile 歧义 | contribution descriptor 编译到 stage contract | P3 |
| 直接具体 backend 构造 | backend 演进和测试隔离 | backend provider admission | P4 |
| Experiment/Cordis/native 权威重叠 | composition truth 竞争 | 显式 intent projection、owner catalog lock、canonical request、native revalidation | P2-C0/P2-C1/P3/P6 |
| 异步 Cordis lifecycle | 若直接复制会使 teardown 非确定 | 原生 dependency-safe lifecycle transaction | P2/P6 |
| per-world host overhead | world-batch 规模风险 | shared resolved profile + 轻量 native world scope | P2/P7 |
| 跨语言调用诱因 | 吞吐与确定性风险 | architecture guard 与 call-graph test | P6/P7 |
| plugin provenance/trust | 供应链与 truth authority 风险 | 外部插件前建立独立 admission/signing/sandbox 计划 | deferred |
| compatibility wrapper | 永久双路径风险 | 显式 owner、evidence、removal gate | 所有迁移阶段 |

## 推荐下一步顺序

1. 完成 P2-B 独立审阅，补齐 behavior/replay parity、重复 rebuild、provider failure/teardown
   与 create/destroy lifetime evidence；
2. 执行 P2-C0：冻结 producer-neutral 高层 request 与 owner-derived catalog-lock
   artifact/identity，并禁止第二个 offline high-level resolver；
4. 执行 P2-C1：通过 Cordis primitives 加仓库 profile/bundle layer lower 默认 request，
   并证明端到端 native realization 与负向 admission；
5. 编译 owner 准入的 system package 与 capability/profile projection；
6. 迁移 backend selection，并把 evidence 扩展到 graph/backend/host 表面；
7. 成熟化 Cordis package 与 tooling；
8. 仅在另行批准后增加 Node host，再运行适用的 producer/host/backend/batch parity 并
   移除双路径。

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
以原子方式刷新完整 root-handle 集，输出 world-scope generation，并在存在 `SimObject`
实体或 exact-stage trace frame 使 world 非 quiescent 时拒绝 rebuild。这解决了当前 native
路径已审阅的 provider UAF/concurrent-refresh 缺口，但不宣称长生命周期 raw dependency
reference 或 replay/fault-injection evidence 已全部完成。

当前 migration evidence 为 15 个 native lifecycle case / 443 个 assertion、33 个 simulation
smoke case / 837 个 assertion、21 个 composition architecture/contract test（1 个 toolchain
skip）以及 12 个 include-direction/flat-boundary test。新增 evidence 覆盖 generation 递增、
quiescent rebuild 拒绝、并发 rebuild 串行化与 kernel-wide ECS operation lock。P2-B 仍待最终
独立审阅、replay parity、fault-injected provider teardown 与重复 create/destroy evidence。

## 显式拒绝的声明

- Cordis 集成尚未实现；P2-A 是其 host-neutral 原生 substrate，不是 Cordis 本身。该缺失
  限制当前验收声明，但不会让 Cordis 在目标计划中变为可选。
- Cordis 不会拥有实验意图、语义实现准入或确定性执行；明确这些边界是安全引入 Cordis
  的前置条件。
- 当前 runtime 尚不是 plugin-composed。
- 本方案本身不会自动提升仿真性能。
- 已有 interface 不证明生命周期安全替换。
- Cordis plugin 加载成功不等于 runtime admission。
- 文档验收不能代表 runtime、parity、replay 或 performance 验收。
