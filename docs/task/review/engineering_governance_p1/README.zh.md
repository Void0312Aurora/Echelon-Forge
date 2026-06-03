# Engineering Governance P1

状态：`2026-06-03` active partial local-pass remediation slice；`P1-A` 和 `P1-B` 已在本地实现并验证，更宽的 runtime/callback 切片继续暂缓。

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

本子项目执行 P0 之后的下一组有边界治理修复。当前只处理不需要大范围 runtime
重写的已验证问题：失效的架构守卫测试，以及主 scenario compiler 路径缺少集中
shape validation。

它不声称整个 P1 已完成。Runtime facade/world-batch adapter 的 capability probing
收敛，以及 cooperative diagnostics callback 拆分，仍需要单独切片处理。

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| 失效架构守卫 | local-pass | `tests/architecture/test_wp22_structural_guardrails.py`；聚焦测试通过 | 将守卫改为当前拆文件结构锚点；不改 weapon effects runtime 行为。 |
| Scenario compiler shape validation | local-pass | `python/scenario/compiler/validation.py`、`service.py`、`merge.py`、`tests/scenario/test_scenario_compiler.py`；聚焦 suite 通过 | 只验证 compiler 直接消费的 shape；不引入完整 JSON Schema 或领域语义验证。 |
| Runtime facade/world-batch capability probing | held | prior review residual | 等待单独 adapter 切片和更宽 runtime validation。 |
| Cooperative diagnostics callback split | held | prior review residual；当前 A5/A6 worktree 噪声较高 | 暂缓，避免和无关 callback 编辑重叠。 |

## Scope

In scope:

- 修复因为代码已拆文件、测试仍搜索旧 inline 文本而失效的架构守卫。
- 为主 compile path 和 prefab merge path 增加小型集中 shape validator。
- 为过去会被静默 coercion 或忽略的错误 shape 增加聚焦负向测试。
- 如实记录验证证据和残余工作。

Out of scope:

- 修改 weapon effects runtime 逻辑。
- 用完整 JSON Schema 替换现有 scenario compiler。
- 给所有领域特定 scenario 字段添加语义验证。
- 在本切片重构 runtime facade adapters、world-batch adapters 或 diagnostics callbacks。
- 清理无关 worktree 改动。

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | 冻结 P1 范围。 | P0 本地修复已存在。 | P1 clusters 和非目标已记录。 | pass |
| `P1-A Guard Repair` | 让失效架构守卫匹配当前拆分实现。 | 失效 guard 可复现。 | 聚焦架构 guard 通过。 | pass |
| `P1-B Compiler Guard` | 增加集中 compiler shape validation。 | 编辑前 compiler 测试可作为基线。 | 带负向测试的聚焦 compiler suite 通过。 | pass |
| `P1-C Adapter Narrowing` | 减少 runtime capability probing 重复。 | P1-A/B 已收口，runtime surface 安静。 | 单独 adapter 切片和更宽 runtime 验证存在。 | held |
| `P1-D Callback Split` | 拆分 diagnostics callback 职责。 | A5/A6 callback 编辑稳定。 | 单独 callback 切片和训练诊断测试存在。 | held |
| `P2 Closure` | 同步文档、残余和父 review index。 | P1-A/B 验证完成。 | 状态准确区分已实现和暂缓项。 | active |

## Task Clusters

- Task cluster plan: `engineering_governance_p1_task_clusters_20260603.md`

## Outputs And Evidence

- `tests/architecture/test_wp22_structural_guardrails.py`
- `python/scenario/compiler/validation.py`
- `python/scenario/compiler/service.py`
- `python/scenario/compiler/merge.py`
- `tests/scenario/test_scenario_compiler.py`
- 本任务子项目及父 review index 条目。

Validation evidence:

- `./.venv/bin/python -m pytest tests/architecture/test_wp22_structural_guardrails.py::test_a2_structured_air_effects_do_not_write_rl_score_authority -q` passed。
- `./.venv/bin/python -m pytest tests/architecture/test_wp22_structural_guardrails.py -q` passed，17 tests。
- `./.venv/bin/python -m pytest tests/scenario/test_scenario_compiler.py -q` passed。
- `./.venv/bin/python -m ruff check ...` 针对本轮 Python 触碰文件 passed。
- `git diff --check -- ...` 针对本轮 P1 触碰文件 passed。
- Scenario/prefab shape scan 针对 `scenarios/`、`examples/scenarios/` 和
  `examples/config/prefabs/` 下 50 个 JSON 文件 passed。

## Acceptance Gate

已实现的 P1-A/P1-B 切片只有在以下条件成立时才能标为 accepted：

- 架构守卫断言当前结构所有权，而不是过时的 inline 文本锚点。
- 主 scenario compiler path 对直接消费的错误 shape fail closed，而不是静默转为空容器。
- Prefab import 的 shape 错误在 merge mutation 前报告。
- 聚焦本地测试和残余 blocker 已记录。

更宽的 P1 program 仍未完成，直到暂缓的 adapter 和 callback 切片各自拥有任务记录和验证。

## Residuals And Next Steps

- 如果后续还有并行改动落入，合入 clean branch 前再次运行完整架构守卫文件。
- 决定 scenario compiler validation 后续是否升级为公开 JSON Schema，或保持轻量内部 shape guard。
- 在单独 P1-C 任务中收敛 runtime facade/world-batch capability probing。
- 等 A5/A6 编辑稳定后，在单独 P1-D 任务中拆分 cooperative diagnostics callback。

## Archive

历史或被替代的治理记录只有在存在 replacement current-status 或 closeout surface
后才移动到 `archive/README.md`。
