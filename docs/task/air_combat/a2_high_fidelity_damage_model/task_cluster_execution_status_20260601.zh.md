# A2 任务簇执行状态 - 2026-06-01

状态：`2026-06-01 / task_cluster_execution_status / G2 candidate acceptance entry / non-authoritative`。

本文记录按 [任务粒度与协调总账](task_granularity_and_coordination_20260601.zh.md)
分发并执行后的当前结果。它只确认 `G1 runtime` 和 `G2 candidate acceptance`
层级的就绪度，不创建 runtime descriptor，不授予 `effect_scale_authority`、
`component_failure_probability_authority`、`pk_authority` 或
`deterministic_fuze_authority`。

## 总体结论

新的 A2 子项目包已经可以作为后续任务分发入口使用；`TC-A2-BF-001-HASH`
已完成 retained manifest hash integrity 收口。当前就绪范围只到：

- `TC-A2-RUNTIME` / `G1 runtime engineering`：工程维护面已通过本轮回归验证；
- `TC-A2-BF-001..004` / `G2 candidate acceptance`：候选证据包具备可审阅、可复现、
  fail-closed 的非权威分发和验收入口形状；retained manifest hash integrity 已通过；
- `G3 residual`：只作为状态读取层，不作为本轮关闭条件；
- `TC-A2-AUTH-B`、`TC-A2-AUTH-C`、`TC-A2-KILLCHAIN`：仍为 backlog / deferred，
  本轮未启动、未验收、未放权。

不得把本文中的“就绪”或“通过”上卷为 full A2 kill-chain、stock runtime authority、
Pk 或 deterministic fuze 完成。

## 任务簇执行矩阵

| 任务簇 | 粒度 | 本轮结论 | 下一步 |
|---|---|---|---|
| `TC-A2-RUNTIME` | `G1` | 就绪为 non-authoritative runtime engineering 维护面 | 可继续在 runtime contract、binding、event/report consumer 层分发维护任务 |
| `TC-A2-BF-001` source / identity / retained evidence | `G2 candidate acceptance` | source admission、candidate docs 和 retained manifest integrity 通过；authority guards 全 false | 保持路径稳定，不移动 `source_pin_update*`、calibration narrative 或 retained artifacts |
| `TC-A2-BF-002` scope / geometry / warhead evidence | `G2 candidate acceptance`；只读 `G3 residual` 状态 | Stage B witness geometry / family-scope retained gate 可复现；真实 geometry/warhead truth 继续 open | 只可分发 review/retained-evidence hygiene，不可扩面到真实 AIM-120C/F-16 truth |
| `TC-A2-BF-003` mechanism admission evidence | `G2 candidate acceptance`；只读 `G3 residual` 状态 | TP-21 / BEC-O retained/fail-closed 状态可由 bundle 读取 | 若继续推进，必须处理 fail-closed blockers，不能消费为 release evidence |
| `TC-A2-BF-004` candidate bundle / regression | `G2 candidate acceptance` | candidate bundle CLI 和 regression 提供机器入口；retained manifest checker 通过；top-level authority guard 全 false | 可作为当前 candidate package acceptance 的 G2 分发/验收入口 |
| `TC-A2-AUTH-B` | `G4 deferred` | 未启动、未验收、未授予 stock runtime authority | 另起 release-grade promotion 任务前，不得复用本轮 G2 结论放权 |
| `TC-A2-AUTH-C` | `G4 deferred` | 未启动、未验收、未授予 stock runtime authority | 等 effect-scale promotion 或明确前置依赖后再分发 |
| `TC-A2-KILLCHAIN` | `G5 deferred` | deferred；未授予 Pk 或 deterministic fuze | Pk / deterministic fuze 必须另建证据链 |

## 分发记录

本轮并行分发了两个只读审阅任务：

- `G1 runtime` 审阅：确认 `DamageReport` 终局/非终局 flags、binding、contract 和
  WP22 guardrails 属于 reporting / engineering surface，不是 Pk、fuze 或 G4 authority；
- `G2 candidate` 审阅：检查 `README.zh.md`、`candidate_acceptance_status.zh.md`、
  candidate package README、`residual_register.zh.md`、retained manifests 和
  `a2_candidate_vps_bundle.py` 的入口一致性；
- `TC-A2-BF-001-HASH` 执行：新增 retained manifest integrity checker 和 architecture test，
  并将 retained manifest hash mismatches 收口到 0；
- `TC-A2-BF-003-FAILCLOSED` 执行：新增 [mechanism admission fail-closed backlog](mechanism_admission_failclosed_backlog_20260601.zh.md)，
  拆解 `RES-005/006` 下一轮 blockers。

主线程负责集成与验证，不把 subagent 审阅结果单独作为 authority evidence。

## 已执行验证

```powershell
cmake --build build-local-win --target ef_core ef_py -j2
pwsh -NoProfile -ExecutionPolicy Bypass -File tools\maintenance\cmo_env.ps1 validate
pwsh -NoProfile -ExecutionPolicy Bypass -File tools\maintenance\cmo_env.ps1 python -m pytest tests\runtime\air_combat\test_weapon_guidance_realism_guards.py
pwsh -NoProfile -ExecutionPolicy Bypass -File tools\maintenance\cmo_env.ps1 python -m pytest tests\runtime\bindings\test_bindings_engagement_surface.py tests\runtime\engagement
pwsh -NoProfile -ExecutionPolicy Bypass -File tools\maintenance\cmo_env.ps1 python -m pytest tests\architecture\test_wp22_structural_guardrails.py
pwsh -NoProfile -ExecutionPolicy Bypass -File tools\maintenance\cmo_env.ps1 python -m pytest tests\architecture\test_a2_source_admission_audit.py tests\architecture\test_a2_blastfrag_geometry_warhead_row_provenance_gate.py tests\architecture\test_a2_blastfrag_res003_target_geometry_closeout_gate.py tests\architecture\test_a2_blastfrag_res004_warhead_scope_closeout_gate.py tests\architecture\test_a2_blastfrag_res011012_independent_review_closeout_gate.py
pwsh -NoProfile -ExecutionPolicy Bypass -File tools\maintenance\cmo_env.ps1 python tools\maintenance\a2_source_admission_audit.py --strict
pwsh -NoProfile -ExecutionPolicy Bypass -File tools\maintenance\cmo_env.ps1 python -m pytest tests\architecture\test_a2_retained_manifest_integrity.py
pwsh -NoProfile -ExecutionPolicy Bypass -File tools\maintenance\cmo_env.ps1 python tools\maintenance\a2_retained_manifest_integrity.py
pwsh -NoProfile -ExecutionPolicy Bypass -File tools\maintenance\cmo_env.ps1 python -m pytest tests\architecture\test_a2_candidate_vps_bundle.py
pwsh -NoProfile -ExecutionPolicy Bypass -File tools\maintenance\cmo_env.ps1 python tools\maintenance\a2_candidate_vps_bundle.py --output $env:TEMP\a2_candidate_vps_bundle_task_cluster_exec.json
git diff --check
```

当前结果：

- build：`ninja: no work to do`
- runtime realism guards：`146 passed`
- bindings / engagement：`52 passed`
- WP22 structural guardrails：`16 passed`
- source admission + retained/gate tests：`20 passed`
- source admission strict：`9 ledgers, 29 candidate docs, 51 calibration docs`
- retained manifest integrity tests：`8 passed`
- retained manifest integrity checker：`manifest_count=21`, `missing_total=0`,
  `sha_mismatch_total=0`, `guard_true_total=0`
- candidate VPS bundle tests：`2 passed`
- candidate VPS bundle CLI：exit 0
- Markdown local link check：`0 missing`
- old Linux absolute path scan：no matches
- `git diff --check`：exit 0，仅有 Windows LF/CRLF 提示

## 保持的边界

- `DamageReport.forced_landing`、`flight_control_kill`、`propulsion_kill`、`crew_kill`
  是 runtime consequence/reporting flags，不是 Pk；
- runtime debug authority state 仍是 diagnostic/debug surface，不是 stock authority grant；
- runtime-aligned authority exercise 只允许作为 test-local / candidate evidence，不得写入 stock DB；
- retained gate JSON 和 manifest 优先于叙事文档；manifest hash mismatch 不得被叙事覆盖；
- `RES-005/006` 的 fail-closed 状态不能被本轮 bundle 通过覆盖；
- `RES-013/014` 继续是 Pk / deterministic fuze boundary deferred。
