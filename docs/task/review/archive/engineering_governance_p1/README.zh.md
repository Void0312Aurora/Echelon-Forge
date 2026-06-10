# Engineering Governance P1

状态：`2026-06-04` closed local-pass remediation slice。`P1-A`、`P1-B`、
有边界的 `P1-C` 和本 P1 范围内的 `P1-D` diagnostics callback split 已在本地实现并验证。

语言：

- 英文规范页：`README.md`
- 中文配套页：`README.zh.md`

输入：

- [Review task area](../README.zh.md)
- [Engineering Governance P0](../engineering_governance_p0/README.zh.md)
- [Engineering discipline review](../../../evaluation/engineering_discipline_review_20260603.md)
- [Architecture claim verification](../../../evaluation/architecture_review_claim_verification_20260603.zh.md)
- [Agent subproject standard](../../../agent/rules/subproject_creation_standard.zh.md)
- [Subagent usage policy](../../../standards/governance/subagent_usage_policy.zh.md)

## Purpose

本子项目执行 P0 之后的 P1 治理修复。它处理已有明确 owner 边界的已验证问题：
失效架构守卫、scenario compiler 主路径缺少集中 shape validation、
adapter-owned capability probing 重复，以及 `CMODiagnosticsCallback` 诊断 owner 过宽。

闭合边界必须明确。`P1-C` 将 `RuntimeFacadeAdapter` 自身的 capability probing
收敛到 capability snapshot；它不声称完成 full adapter 或 world-batch class hierarchy
拆分。更大的 adapter 拆分属于后续架构任务，不再作为本 P1 的 held residual。
`P1-D` 针对 diagnostics callback owner 已闭合：step scalars、action/policy/HMoE/A5/A6/
leader/reward/runway logging、terminal reward windows、preterm snapshots 和 cooperative
event-window aggregation 均已进入 `python/training/diagnostics.py` 中的聚焦 helper。

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| 失效架构守卫 | local-pass | `tests/architecture/structural_boundaries`；聚焦测试通过 | 将 guard 改为当前 split-file 结构锚点；不改 weapon effects runtime 行为。 |
| Scenario compiler shape validation | local-pass | `python/scenario/compiler/validation.py`、`service.py`、`merge.py`、`tests/scenario/test_scenario_compiler.py`；聚焦 suite 通过 | 只验证 compiler 直接消费的 shape；不引入完整 JSON Schema 或领域语义 validator。 |
| Runtime facade/world-batch capability probing | local-pass | `python/rl/runtime/world_batch/adapter.py`、`tests/world_batch/test_world_batch_vec_env.py`；聚焦 world-batch tests 通过 | 为 adapter-owned probing 增加集中 capability snapshot；不拆 world-batch env classes 或完整 adapter。 |
| Diagnostics callback helper extraction | local-pass | `python/training/diagnostics.py`、`python/training_callbacks.py`；training diagnostics tests 通过 | 将 diagnostics calculation 与 event-window state 移出 `CMODiagnosticsCallback`；不改变 RL algorithm 或 logged key 语义。 |
| Task and evaluation documentation | local-pass | 本子项目、父 review index 与 architecture evaluation 更新 | 记录 P1 已闭合，同时不宣称无关架构工作已完成。 |

## Scope

In scope:

- 修复因为代码已拆分而测试仍搜索旧 inline text 导致的 stale architecture guard。
- 为主 compile path 和 prefab merge path 增加小型集中 shape validator。
- 为 runtime facade adapter 增加集中 capability snapshot，减少 adapter 自身 writer/reader
  方法中散落的 probing。
- 将 diagnostics calculation 与 state 从 `CMODiagnosticsCallback` 抽到
  `python/training/diagnostics.py`，同时保留既有 callback wrapper 和 logged scalar keys。
- 为 invalid scenario roots、invalid shape cases、facade replacement 后 capability refresh
  和 diagnostics helper behavior 增加聚焦测试。
- 如实记录验证证据和闭合边界。

Out of scope:

- 修改 weapon effects runtime 逻辑。
- 用完整 JSON Schema 替换现有 scenario compiler。
- 给所有领域特定 scenario 字段添加语义验证。
- 拆分完整 runtime adapter 或 world-batch env class hierarchy。
- 修改 RL algorithms、reward semantics、A5/A6 行为或 training config。
- 清理无关 worktree 改动。

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | 冻结 P1 范围。 | P0 本地修复已存在。 | P1 clusters 和非目标已记录。 | pass |
| `P1-A Guard Repair` | 让失效架构守卫匹配当前拆分实现。 | 失效 guard 可复现。 | 聚焦 architecture guard 通过。 | pass |
| `P1-B Compiler Guard` | 增加集中 compiler shape validation。 | 编辑前 compiler tests 可作为基线。 | 带负向测试的聚焦 compiler suite 通过。 | pass |
| `P1-C Adapter Narrowing` | 减少 runtime capability probing 重复。 | P1-A/B local-pass，runtime surface 安静。 | Capability snapshot 已实现且聚焦 world-batch 验证通过。 | pass |
| `P1-D Diagnostics Callback Split` | 将 diagnostics calculation 与 event-window state 移出 `CMODiagnosticsCallback`。 | P1-C local-pass，callback responsibilities 已识别。 | Training diagnostics helpers 覆盖 policy、HMoE、actions、leader、rewards、A5/A6、runway/gear、basic step scalars、terminal/preterm windows 和 cooperative aggregation。 | pass |
| `P2 Closure` | 同步文档、残余和父 review index。 | P1-A/B/C/D 验证完成。 | 状态体现 P1 已闭合，后续工作不再列为 held P1。 | pass |

## Task Clusters

- Task cluster plan：`engineering_governance_p1_task_clusters_20260603.md`

## Outputs And Evidence

- `tests/architecture/structural_boundaries`
- `python/scenario/compiler/validation.py`
- `python/scenario/compiler/service.py`
- `python/scenario/compiler/merge.py`
- `python/rl/runtime/world_batch/adapter.py`
- `python/rl/runtime/world_batch/__init__.py`
- `python/training/diagnostics.py`
- `python/training_callbacks.py`
- `tests/scenario/test_scenario_compiler.py`
- `tests/world_batch/test_world_batch_vec_env.py`
- `tests/training/test_diagnostics_callback_contracts.py`
- `tests/training/test_diagnostics_callback_contracts.py`
- 本任务子项目及父 review index 条目。

Validation evidence:

- `./.venv/bin/python -m pytest tests/architecture/structural_boundaries/test_domain_separation_boundaries.py::test_a2_structured_air_effects_do_not_write_rl_score_authority -q` passed。
- `./.venv/bin/python -m pytest tests/architecture/structural_boundaries -q` passed，17 tests。
- `./.venv/bin/python -m pytest tests/scenario/test_scenario_compiler.py -q` passed。
- Scenario/prefab shape scan 针对 `scenarios/`、`examples/scenarios/` 和
  `examples/config/prefabs/` 下 50 个 JSON 文件 passed。
- `./.venv/bin/python -m pytest tests/world_batch/test_world_batch_vec_env.py -k "adapter_capability_snapshot or legacy_task_order_batch_writer_is_removed or task_order_reverse_projection_stays_removed or task_order_write_routes_through_maintained_helper or apply_launch_requests or step_worlds" -q` passed，6 selected tests。
- `./.venv/bin/python -m pytest tests/training/test_diagnostics_callback_contracts.py tests/training/test_diagnostics_callback_contracts.py -q` passed，17 tests。
- `./.venv/bin/python -m ruff check ...` 针对触碰 Python 文件 passed。
- `git diff --check -- ...` 针对触碰 P1 文件 passed。

## Acceptance Gate

本 P1 子项目只有在以下条件成立时才算 accepted：

- 架构守卫断言当前结构所有权，而不是过时的 inline text anchor。
- 主 scenario compiler path 对直接消费的错误 shape fail closed，而不是静默转为空容器。
- Prefab import shape errors 在 merge mutation 前报告。
- RuntimeFacadeAdapter-owned capability checks 使用命名 capability snapshot，并在测试替换 facade object 后刷新。
- `CMODiagnosticsCallback` 不再拥有 diagnostics calculations 或 terminal/preterm/cooperative
  window state；它委托给 `python/training/diagnostics.py`。
- 聚焦测试证明 helper behavior，并保留既有 logged scalar keys。
- 文档记录 P1 已闭合，但不宣称 future adapter、JSON Schema、domain semantic validation
  或 broader runtime refactors 已完成。

## Residuals And Next Steps

已闭合的 P1 不再保留 held P1 work。以下内容如成为优先级，应建立独立后续任务：

- 完整 runtime adapter/world-batch env class hierarchy split。
- 可选 public JSON Schema 或更深的 scenario domain semantic validation。
- 主架构 review 已记录的更宽 refactor，例如 `DefaultUnitFactory::spawn()` 和 world-batch env duplication。
- 如果并行改动触碰同一 architecture guard、compiler、adapter 或 training diagnostics 文件，合入前重新运行聚焦验证。

## Archive

历史或被替代的治理记录只有在存在 replacement current-status 或 closeout surface
后才移动到 `archive/README.md`。
