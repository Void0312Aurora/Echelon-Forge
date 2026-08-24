# Cordis 仿真组合内核派发队列 — 2026-08-17

状态：`2026-08-23` 当前队列；P0、P1-A、P1-B、P2-A、P2-B、P2-C0、P2-C1 默认 profile
有界切片、P3-A 默认图、P3-B 默认 profile projection、P4-A 默认 provider、P5-A 默认
CPU-exact composition-evidence、P6-A 默认 profile Cordis package、P7-A 默认 CPU-exact
host/batch parity 与 P8-A migration closure 均已接受。本队列已闭合并归档。更广
profile/provider、Node host、CUDA、外部 plugin 与 replay 扩展继续由分别具名 owner held。

语言：

- 英文规范页：[cordis_simulation_composition_kernel_dispatch_queue_20260817.md](cordis_simulation_composition_kernel_dispatch_queue_20260817.md)
- 中文配套页：`cordis_simulation_composition_kernel_dispatch_queue_20260817.zh.md`

Document kind: `task`
Lifecycle: `archived`
Canonical: `docs/architecture/work/archive/cordis_simulation_composition_kernel/cordis_simulation_composition_kernel_dispatch_queue_20260817.md`
Owner: `architecture/runtime-composition`
Last verified: `2026-08-23`

父项目：[Cordis 仿真组合内核](README.zh.md)

## 队列

| 顺序 | Cluster | 状态 | 派发条件 | Write boundary | 必需返回 |
| --- | --- | --- | --- | --- | --- |
| 1 | `P0-A Authority Scaffold` | pass | 已完成文档回合 | 本子项目、architecture owner README、选定双语 registry 条目 | 文档/link/audit 结果与精确修改文件 |
| 2 | `P1-A Composition Census` | pass | P0-A 已通过 | 只读源码 inventory 与 current-status evidence 更新 | 完整 ownership/scope/replacement inventory |
| 3 | `P1-B Manifest And Resolution Contract` | pass | P1-A 已通过且 contract write set 保持有界 | runtime contract/schema input 与聚焦测试 | schema decision、fixture、invalid-manifest matrix、versioning/canonicalization evidence |
| 4 | `P2-A Native Lifecycle Kernel` | pass / independently repaired | P1-A/P1-B gate 已通过 | 隔离原生 composition library、聚焦 C++ test、architecture guard 与 CMake/CI wiring | 普通 MSVC 与 ASan build 均为 14 tests/430 assertions；hash、typed-scope、lifecycle-state、rollback、串行化 replacement rebuild、重入 lifetime、plugin/factory identity、进程内语义 service-type identity、handover、invalidation 与 deterministic validation 证据 |
| 5 | `P2-B Default Provider Migration` | accepted bounded slice | P2-A 已通过且 engine/provider write set 保持有界 | 默认 provider 入口、kernel builder、engine construction seam、聚焦 parity/lifetime test | 一条受控迁移前后 behavior/replay 对比、一个 production failure/teardown 路径、重复 create/destroy、独立复核 |
| 6 | `P2-C0 Projection And Catalog-Lock Contract` | accepted bounded slice | P2-B production composition/identity 稳定；有界 contract 切片已完成验证 | producer-neutral request DTO、owner-derived catalog-lock artifact/generator、identity 与负向 admission fixture | 唯一高层 request contract、可核验 owner lock，以及阻止 offline high-level lowering 的 guard |
| 7 | `P2-C1 Cordis Default-Profile Vertical Slice` | accepted bounded default-profile slice | P2-C0 accepted | 使用 Cordis primitives 加仓库 profile/bundle layer 的有界 Cordis package、production adapter、端到端 fixture | Experiment fixture -> request -> Cordis -> manifest/lock -> native production realization，包括负向 admission 与 offline regression |
| 8 | `P4-A Backend Provider Migration` | 默认 provider 有界切片已接受 | P3-B 默认 profile projection 有界切片已接受 | facade/provider contract、generated backend request identity、fixture/test、CMake/CI、有界文档 | 独立 P0/P1/P2 = 0/0/0 与复现证据 |
| 9 | `P5-A Composition Evidence Expansion` | 默认 CPU-exact 有界切片已接受 | P4-A 已接受且相关 P2/P3 identity join 可用 | evidence/replay contract、facade diagnostics、schema generator、聚焦测试、CMake/CI、有界文档 | 精确 request/manifest/lock/profile/provider/backend/graph/world/scope evidence、commit sealing、mismatch rejection 与独立审阅 |
| 10 | `P6-A Cordis Package Maturation` | 默认 profile package 有界切片已接受 | P2-C1/P3/P4/P5 有界 contract 已接受 | 获批 `packages/cordis-runtime/**`、workspace manifest/lockfile、fixture、package test、有界文档 | 仓库自有 overlay/bundle、LF 稳定原始 pin、封存 provenance/diagnostics/dependency evidence、canonical native parity 与独立 P0/P1/P2 = 0/0/0 |
| 11 | `P6-B Node Host Adapter` | conditional / held | P6-A 已接受且有显式 host decision | 仅限获批 Node adapter | 仅在获批时返回 native-owner lifecycle/parity evidence |
| 12 | `P7-A Host And Batch Parity` | 默认 CPU-exact 有界切片已接受 | P4-A/P5-A/P6-A 已接受；Node 行要求 P6-B | integration test、benchmark/probe tool、evidence package、有界修复 | 冻结 action/state/event/reward/termination/replay 语义、严格 producer/host join、批准的 32-world 测量与独立 P0/P1/P2 = 0/0/0 |
| 13 | `P8-A Migration Closure` | accepted bounded closure | 必需有界 native/Cordis/system/backend/evidence/parity gate 已接受 | composition caller/truth path、稳定 architecture rule、acceptance/archive、owner index | 完整 acceptance matrix、删除或显式保留 compatibility path、具名 residual owner 与同步文档 |
| 14 | 后续全部任务簇 | 由各自声明依赖 held | 各自 owner dependency 通过，或已有显式 independent-stream amendment | task-cluster write set | 任务簇专属 evidence packet |

## 已接受收口包

```text
cluster: P8-A Migration Closure
goal: 删除被取代的 composition truth path、提升已接受稳定规则，并在不删除历史证据的前提下路由全部 residual
write set:
  受影响 composition caller 与 compatibility seam
  architecture standard/reference、acceptance/archive 与 owner index
non-goals:
  静默扩大 profile/plugin/host 或把 Cordis 当作可选项
  删除历史，或把 held Node/外部计划吸收进本次 closure
validation:
  完整 acceptance matrix 与 Cordis/native vertical conformance
  caller/truth-path inventory、保留 compatibility proof、link/bilingual audit
closure:
  不再存在双 composition truth path；可选 Node/外部 residual 有具名 owner，且不能削弱
  已准入 producer/native 路径
```

## 队列规则

- P1 contract gate 已关闭；P2-B 必须把已接受 contract 作为输入，任何必需 contract 修改
  都要显式回到 P1 amendment。
- P1-A 可按 model/service、system/stage、backend、binding 拆分，但 ownership table
  整合保持串行。
- P1-B 必须使用已接受 census，不能仅因 migration 属于后续任务簇就省略 ownership edge。
- 实现任务簇不得在声明 write set 外建立未登记 compatibility path。
- 若发现与维护中的 architecture standard 冲突，暂停相关任务簇并路由有界 standard
  review；task 文档不得静默覆盖 standard。
- 新 acceptance 或 closure 声明必须有 implementation evidence。
- P2-C0 已冻结唯一高层 request/catalog-lock authority，P2-C1 证明 Cordis/native 默认
  路径，P3-A 拥有默认 component/system graph admission，P3-B 已绑定默认 profile
  projection；Node hosting、外部打包与
  private package pipeline 仍排除在已接受切片之外。
- 有界 closure 不代表更广 profile/backend/host 或外部 plugin 验收。Node hosting 仍取决于
  独立 host 决策。

## 归档 Queue 规则

本 queue 不再有 next eligible item。未来 residual 工作必须创建新的 active owner packet，
不得把本历史 dependency sequence 当作 active dispatch surface 重新开启或修改。
