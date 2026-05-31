# A2 任务簇分发包 - 2026-06-01

状态：`2026-06-01 / dispatch_packet / non-authoritative`。

本文是按 [任务粒度与协调总账](task_granularity_and_coordination_20260601.zh.md)
分发执行任务的唯一入口。它不重新验证任务簇是否成立，只把已经确定的 `TC-A2-*`
拆成可交付工作包。

## 分发原则

- 每个任务必须先标注粒度：`G1`、`G2`、`G3`、`G4` 或 `G5`；
- `G2` candidate 包可以被分发执行，但不得写成 `G4/G5` authority；
- `G4/G5` 只能在明确启动 release-grade promotion / kill-chain 任务后分发；
- subagent 不做“再判断任务簇是否成立”的泛审阅，只接收有文件边界和验收输出的执行任务；
- 不移动 `calibration/**`、`retained_artifacts/**`、`source_pin_update*.zh.md`
  或 source ledgers，除非同步更新工具和测试。

## 当前分发队列与验收状态

| 优先级 | 任务 ID | 任务簇 | 粒度 | 状态 | 执行目标 | 写入范围 | 验收输出 |
|---:|---|---|---|---|---|---|---|
| 1 | `TC-A2-BF-001-HASH` | `TC-A2-BF-001` | `G2` | accepted | 固化 retained manifest hash integrity 检查，并修正 retained manifest 与产物 hash 不一致的问题 | `tools/maintenance/**`、`tests/architecture/**`、相关 `retained_artifacts/**/manifest.json` | `manifest_count=21`, `missing_total=0`, `sha_mismatch_total=0`, `guard_true_total=0` |
| 2 | `TC-A2-BF-004-PACKAGE` | `TC-A2-BF-004` | `G2` | accepted | 将 candidate bundle 输出和任务簇执行状态整理成当前 G2 acceptance entry | `candidate_acceptance_status.zh.md`、`task_cluster_execution_status_20260601.zh.md` | 文档只声明 G2 candidate acceptance 入口和 residual blockers，不上卷到 G4/G5 |
| 3 | `TC-A2-BF-003-FAILCLOSED` | `TC-A2-BF-003` | `G2` + `G3` 状态读取 | accepted as backlog split | 把 `RES-005/006` fail-closed blockers 拆成下一轮可执行项 | [mechanism_admission_failclosed_backlog_20260601.zh.md](mechanism_admission_failclosed_backlog_20260601.zh.md) | 不消费 TP-21 / BEC-O 为 release evidence，只输出 blocker closeout plan |
| 4 | `TC-A2-RUNTIME-FINALIZE` | `TC-A2-RUNTIME` | `G1` | accepted | 收口当前 `DamageReport` consequence flags 的工程说明和测试映射 | `runtime_status.zh.md`、相关 runtime tests 如需补注 | 明确 flags 是 reporting / consequence surface，不是 Pk/fuze |

## 暂不分发

| 任务簇 | 原因 |
|---|---|
| `TC-A2-AUTH-B` | 需要另起 release-grade `effect_scale_authority` promotion，不得混入当前 G2 |
| `TC-A2-AUTH-C` | 依赖 Stage C fragility truth / review closeout，当前仍 blocked |
| `TC-A2-KILLCHAIN` | `Pk` 与 deterministic fuze 仍是 boundary deferred，必须另建证据链 |

## Subagent 投递模板

### `TC-A2-BF-001-HASH`

负责修复 retained manifest integrity。不要重新审阅任务簇是否成立。

写入范围：

- `tools/maintenance/` 下新增或扩展 A2 retained manifest integrity checker；
- `tests/architecture/` 下新增对应测试；
- 仅在 checker 明确指出 hash mismatch 时更新相关 `retained_artifacts/**/manifest.json`。

验收：

- checker 输出 `missing_total=0`、`sha_mismatch_total=0`；
- authority guard 中任意 `*_authority*`、`stock_*`、`pk_*`、`fuze_*` 不得变为 true；
- 不移动 calibration narrative、source ledger 或 retained artifact 文件。

### `TC-A2-BF-004-PACKAGE`

负责整理 G2 candidate acceptance record。不要补写 G4/G5 结论。

写入范围：

- `candidate_acceptance_status.zh.md`
- `task_cluster_execution_status_20260601.zh.md`

验收：

- 明确 `TC-A2-BF-001..004` 是 `G2 candidate acceptance`，且 `G4/G5 deferred`；
- 记录 `RES-005/006` fail-closed 不被覆盖；
- 记录 `G3 residual` 只读取状态；
- 若 `TC-A2-BF-001-HASH` 未完成，不能声明 retained manifest 强验收通过。

### `TC-A2-BF-003-FAILCLOSED`

负责把 mechanism admission 的 fail-closed blocker 拆成下一轮执行项。

写入范围：

- blocker note 或 backlog 文档；
- 不修改 retained gate JSON，除非主线程明确要求重生 gate。

验收：

- 每个 blocker 有 owner、输入、输出、不得越界项；
- 不把 TP-21 / BEC-O comparison output 消费为 release evidence；
- 不授予 fragment/blast row authority。

### `TC-A2-RUNTIME-FINALIZE`

负责 G1 runtime 说明收口。

写入范围：

- `runtime_status.zh.md`
- 需要时补 runtime test 注释或断言名。

验收：

- `DamageReport` flags 被描述为 consequence/reporting flags；
- 不使用 `Pk calibrated`、`fuze released`、`authority promoted` 等措辞。
