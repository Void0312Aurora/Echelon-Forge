# Cordis 仿真组合内核派发队列 — 2026-08-17

状态：`2026-08-17` 当前队列；P0、P1-A、P1-B 与 P2-A 已通过。P2-B 是下一 eligible
cluster，尚未派发。

语言：

- 英文规范页：[cordis_simulation_composition_kernel_dispatch_queue_20260817.md](cordis_simulation_composition_kernel_dispatch_queue_20260817.md)
- 中文配套页：`cordis_simulation_composition_kernel_dispatch_queue_20260817.zh.md`

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/cordis_simulation_composition_kernel/cordis_simulation_composition_kernel_dispatch_queue_20260817.md`
Owner: `architecture/runtime-composition`
Last verified: `2026-08-17`

父项目：[Cordis 仿真组合内核](README.zh.md)

## 队列

| 顺序 | Cluster | 状态 | 派发条件 | Write boundary | 必需返回 |
| --- | --- | --- | --- | --- | --- |
| 1 | `P0-A Authority Scaffold` | pass | 已完成文档回合 | 本子项目、architecture owner README、选定双语 registry 条目 | 文档/link/audit 结果与精确修改文件 |
| 2 | `P1-A Composition Census` | pass | P0-A 已通过 | 只读源码 inventory 与 current-status evidence 更新 | 完整 ownership/scope/replacement inventory |
| 3 | `P1-B Manifest And Resolution Contract` | pass | P1-A 已通过且 contract write set 保持有界 | runtime contract/schema input 与聚焦测试 | schema decision、fixture、invalid-manifest matrix、versioning/canonicalization evidence |
| 4 | `P2-A Native Lifecycle Kernel` | pass / independently repaired | P1-A/P1-B gate 已通过 | 隔离原生 composition library、聚焦 C++ test、architecture guard 与 CMake/CI wiring | 普通 MSVC 与 ASan build 均为 13 tests/277 assertions；hash、typed-scope、lifecycle-state、rollback、replacement rebuild、handover、invalidation 与 deterministic validation 证据 |
| 5 | `P2-B Default Provider Migration` | ready / not dispatched | P2-A 已通过且 engine/provider write set 保持有界 | 默认 provider 入口、kernel builder、engine construction seam、聚焦 parity/lifetime test | 默认 behavior/replay parity 与移除具体 model 构造/raw capture |
| 6 | 后续全部任务簇 | held | 各自依赖通过 | task-cluster write set | 任务簇专属 evidence packet |

## 下一派发包

```text
cluster: P2-B Default Provider Migration
goal: 通过 production native provider 与 kernel builder 实现已接受的默认兼容 profile
write set:
  src/core/engine/** construction/ownership seam
  与 model/service owner 相邻的获准默认 provider 入口
  聚焦 lifecycle、behavior、replay 与 ownership test
  本子项目内有界 design/status 更新
non-goals:
  system-family contribution 拆分或替换中央 registration list
  backend 或 binding migration
  Cordis package 或 Node host
validation:
  迁移前后默认 behavior/replay comparison
  production provider construction 与逆序 teardown failure injection
  reset/rebuild 与重复 create/destroy lifetime evidence
  SimulationKernel 不再构造具体默认 model
  已注册 system 不再保留可替换 provider raw pointer
closure:
  默认 profile 通过 ef_composition 构造当前 kernel，且无语义漂移或第二套 construction truth
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
- 在实现证据存在前，不派发 acceptance/closure。

## 下次更新触发

P2-B 派发或完成、任务簇 blocked/rescoped，或 accepted 结果改变下一依赖时更新。
不得仅为记录时间流逝而更新。
