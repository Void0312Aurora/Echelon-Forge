# Engineering Governance P1

状态：`2026-06-04` active partial local-pass remediation slice；`P1-A`、`P1-B`、有边界的 `P1-C` 和窄 `P1-D1`/`P1-D2`/`P1-D3`/`P1-D4`/`P1-D5`/`P1-D6`/`P1-D7`/`P1-D8` 已在本地实现并验证，更宽的 callback 与 adapter split 切片继续暂缓。

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
重写的已验证问题：失效的架构守卫测试、主 scenario compiler 路径缺少集中
shape validation，以及 runtime facade adapter capability probing 的窄收敛。

它不声称整个 P1 已完成。第一轮 P1-C 只把 `RuntimeFacadeAdapter` 自身的
capability probing 集中到 capability snapshot；第一轮 P1-D1 只把 policy
distribution diagnostics 抽到兼容 wrapper 后方的 helper；P1-D2 将 HMoE policy
route/parameter diagnostics 抽到第二个兼容 wrapper 后方；P1-D3 将 action
diagnostics 抽到第三个兼容 wrapper 后方；P1-D4 将 leader diagnostics 抽到第四个
兼容 wrapper 后方；P1-D5 将 step reward-term diagnostics 抽到第五个兼容 wrapper
后方；P1-D6 将 A6 event-window info diagnostics 抽到第六个兼容 wrapper 后方。
P1-D7 将 A5 event info diagnostics 抽到第七个兼容 wrapper 后方。P1-D8 将
runway/gear step info diagnostics 抽到第八个兼容 wrapper 后方。更宽的 adapter
split 和完整 diagnostics callback 拆分仍需要单独切片处理。

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| 失效架构守卫 | local-pass | `tests/architecture/test_wp22_structural_guardrails.py`；聚焦测试通过 | 将守卫改为当前拆文件结构锚点；不改 weapon effects runtime 行为。 |
| Scenario compiler shape validation | local-pass | `python/scenario/compiler/validation.py`、`service.py`、`merge.py`、`tests/scenario/test_scenario_compiler.py`；聚焦 suite 通过 | 只验证 compiler 直接消费的 shape；不引入完整 JSON Schema 或领域语义验证。 |
| Runtime facade/world-batch capability probing | local-pass | `python/rl/runtime/world_batch/adapter.py`、`tests/world_batch/test_world_batch_vec_env.py`；聚焦 world-batch tests 通过 | 只集中 adapter-owned probing；不拆 world-batch env classes 或完整 adapter。 |
| Policy-distribution diagnostics helper | local-pass | `python/training/diagnostics.py`、`python/training_callbacks.py`；聚焦 training diagnostics tests 通过 | 只把一个诊断职责抽到现有 callback method 后方；不拆完整 callback class。 |
| HMoE diagnostics helper | local-pass | `python/training/diagnostics.py`、`python/training_callbacks.py`、`tests/training/test_cooperative_diagnostics_callback.py`；聚焦 training diagnostics tests 通过 | 抽取 HMoE route/parameter stats 记录，并保留 parameter-stat throttling；不拆 cooperative、leader 或 action diagnostics。 |
| Action diagnostics helper | local-pass | `python/training/diagnostics.py`、`python/training_callbacks.py`、`tests/training/test_cooperative_diagnostics_callback.py`；聚焦 training diagnostics tests 通过 | 抽取 full/hybrid action logging，并保留 full-action brake 与 combat switch 语义；不拆 cooperative 或 leader diagnostics。 |
| Leader diagnostics helper | local-pass | `python/training/diagnostics.py`、`python/training_callbacks.py`、`tests/training/test_cooperative_diagnostics_callback.py`；聚焦 training diagnostics tests 通过 | 抽取 leader observation/info/reward stats 记录；不拆 cooperative 或 event-window diagnostics。 |
| Reward diagnostics helper | local-pass | `python/training/diagnostics.py`、`python/training_callbacks.py`、`tests/training/test_cooperative_diagnostics_callback.py`；聚焦 training diagnostics tests 通过 | 抽取 step reward-term mean logging；不拆 terminal reward windows、cooperative diagnostics 或 event-window diagnostics。 |
| A6 event-window info helper | local-pass | `python/training/diagnostics.py`、`python/training_callbacks.py`、`tests/training/test_a6_event_value_diagnostics_callback.py`；聚焦 training diagnostics tests 通过 | 抽取 A6 first-event info logging；不拆 A5 event info、terminal/preterm windows 或 cooperative aggregation。 |
| A5 event info helper | local-pass | `python/training/diagnostics.py`、`python/training_callbacks.py`、`tests/training/test_cooperative_diagnostics_callback.py`；聚焦 training diagnostics tests 通过 | 抽取 A5 event info logging；不拆 basic reward/instrument scalar logging、terminal/preterm windows 或 cooperative aggregation。 |
| Runway/gear diagnostics helper | local-pass | `python/training/diagnostics.py`、`python/training_callbacks.py`、`tests/training/test_cooperative_diagnostics_callback.py`；聚焦 training diagnostics tests 通过 | 抽取 runway/gear step info logging；不拆 basic reward/instrument scalar logging、terminal/preterm windows 或 cooperative aggregation。 |
| Cooperative/event-window aggregation split | held | prior review residual | 更宽拆分仍暂缓到单独 packet，确保每个职责都有有边界 write set。 |

## Scope

In scope:

- 修复因为代码已拆文件、测试仍搜索旧 inline 文本而失效的架构守卫。
- 为主 compile path 和 prefab merge path 增加小型集中 shape validator。
- 为 runtime facade adapter 增加小型集中 capability snapshot，减少 adapter
  自身 writer/reader 方法中散落的 probing。
- 将 policy-distribution diagnostics 抽到聚焦 helper，同时保留现有
  `CMODiagnosticsCallback` method 作为兼容 wrapper。
- 将 HMoE policy route/parameter diagnostics 抽到聚焦 helper，同时保留
  callback 的 parameter-stat throttle state。
- 将 full/hybrid action diagnostics 抽到聚焦 helper，同时保留现有 callback
  wrapper 与已记录 scalar keys。
- 将 leader observation/info/reward diagnostics 抽到聚焦 helper，同时保留现有
  callback wrapper 与已记录 scalar keys。
- 将 step reward-term diagnostics 抽到聚焦 helper，同时保留现有 callback
  wrapper 与已记录 scalar keys。
- 将 A6 first-event info diagnostics 抽到聚焦 helper，同时保留现有 callback
  wrapper 与已记录 scalar keys。
- 将 A5 event info diagnostics 抽到聚焦 helper，同时保留现有 callback
  wrapper 与已记录 scalar keys。
- 将 runway/gear step info diagnostics 抽到聚焦 helper，同时保留现有 callback
  wrapper 与已记录 scalar keys。
- 为过去会被静默 coercion 或忽略的错误 shape 增加聚焦负向测试。
- 为测试替换 facade 后 capability snapshot 自动刷新增加聚焦回归测试。
- 如实记录验证证据和残余工作。

Out of scope:

- 修改 weapon effects runtime 逻辑。
- 用完整 JSON Schema 替换现有 scenario compiler。
- 给所有领域特定 scenario 字段添加语义验证。
- 在本切片大范围拆分 runtime facade adapters、world-batch env classes 或 diagnostics callbacks。
- 清理无关 worktree 改动。

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | 冻结 P1 范围。 | P0 本地修复已存在。 | P1 clusters 和非目标已记录。 | pass |
| `P1-A Guard Repair` | 让失效架构守卫匹配当前拆分实现。 | 失效 guard 可复现。 | 聚焦架构 guard 通过。 | pass |
| `P1-B Compiler Guard` | 增加集中 compiler shape validation。 | 编辑前 compiler 测试可作为基线。 | 带负向测试的聚焦 compiler suite 通过。 | pass |
| `P1-C Adapter Narrowing` | 减少 runtime capability probing 重复。 | P1-A/B local-pass，runtime surface 安静。 | Capability snapshot 已实现且聚焦 world-batch 验证通过。 | pass |
| `P1-D1 Policy Helper` | 在当前 callback wrapper 后方抽取 policy-distribution diagnostics。 | P1-C local-pass，callback 编辑面足够窄。 | 聚焦 cooperative/A6 diagnostics tests 通过。 | pass |
| `P1-D2 HMoE Helper` | 在当前 callback wrapper 后方抽取 HMoE route/parameter diagnostics。 | P1-D1 local-pass。 | 聚焦 training diagnostics tests 证明 route logging 与 parameter-stat throttling。 | pass |
| `P1-D3 Action Helper` | 在当前 callback wrapper 后方抽取 full/hybrid action diagnostics。 | P1-D2 local-pass。 | 聚焦 training diagnostics tests 证明 full-action brake 与 combat switch logging。 | pass |
| `P1-D4 Leader Helper` | 在当前 callback wrapper 后方抽取 leader observation/info/reward diagnostics。 | P1-D3 local-pass。 | 聚焦 training diagnostics tests 证明 leader observation、bucket、C2 与 reward logging。 | pass |
| `P1-D5 Reward Helper` | 在当前 callback wrapper 后方抽取 step reward-term diagnostics。 | P1-D4 local-pass。 | 聚焦 training diagnostics tests 证明 reward-term mean logging 与 missing-key behavior。 | pass |
| `P1-D6 A6 Event Info Helper` | 在当前 callback wrapper 后方抽取 A6 first-event info diagnostics。 | P1-D5 local-pass。 | 聚焦 A6 diagnostics tests 证明 label-count logging 与 stable zero behavior。 | pass |
| `P1-D7 A5 Event Info Helper` | 在当前 callback wrapper 后方抽取 A5 event info diagnostics。 | P1-D6 local-pass。 | 聚焦 training diagnostics tests 证明 event-rate、rejection、state 与 component logging。 | pass |
| `P1-D8 Runway/Gear Helper` | 在当前 callback wrapper 后方抽取 runway/gear step info diagnostics。 | P1-D7 local-pass。 | 聚焦 training diagnostics tests 证明 runway、cross-track tail、gear-collapse 与 gear-stress logging。 | pass |
| `P1-D Callback Split` | 拆分剩余 diagnostics callback 职责。 | 每个剩余职责都有有边界 packet。 | 单独完整 callback split 和训练诊断测试存在。 | held |
| `P2 Closure` | 同步文档、残余和父 review index。 | P1-A/B/C/D1/D2/D3/D4/D5/D6/D7/D8 验证完成。 | 状态准确区分已实现和暂缓项。 | active |

## Task Clusters

- Task cluster plan: `engineering_governance_p1_task_clusters_20260603.md`

## Outputs And Evidence

- `tests/architecture/test_wp22_structural_guardrails.py`
- `python/scenario/compiler/validation.py`
- `python/scenario/compiler/service.py`
- `python/scenario/compiler/merge.py`
- `python/rl/runtime/world_batch/adapter.py`
- `python/rl/runtime/world_batch/__init__.py`
- `python/training/diagnostics.py`
- `python/training_callbacks.py`
- `tests/scenario/test_scenario_compiler.py`
- `tests/world_batch/test_world_batch_vec_env.py`
- 本任务子项目及父 review index 条目。

Validation evidence:

- `./.venv/bin/python -m pytest tests/architecture/test_wp22_structural_guardrails.py::test_a2_structured_air_effects_do_not_write_rl_score_authority -q` passed。
- `./.venv/bin/python -m pytest tests/architecture/test_wp22_structural_guardrails.py -q` passed，17 tests。
- `./.venv/bin/python -m pytest tests/scenario/test_scenario_compiler.py -q` passed。
- `./.venv/bin/python -m ruff check ...` 针对本轮 Python 触碰文件 passed。
- `git diff --check -- ...` 针对本轮 P1 触碰文件 passed。
- Scenario/prefab shape scan 针对 `scenarios/`、`examples/scenarios/` 和
  `examples/config/prefabs/` 下 50 个 JSON 文件 passed。
- `./.venv/bin/python -m pytest tests/world_batch/test_world_batch_vec_env.py -k "adapter_capability_snapshot or legacy_task_order_batch_writer_is_removed or task_order_reverse_projection_stays_removed or task_order_write_routes_through_maintained_helper or apply_launch_requests or step_worlds" -q` passed，6 selected tests。
- `./.venv/bin/python -m pytest tests/training/test_cooperative_diagnostics_callback.py tests/training/test_a6_event_value_diagnostics_callback.py -q` passed，15 tests。

## Acceptance Gate

已实现的 P1-A/P1-B 切片只有在以下条件成立时才能标为 accepted：

- 架构守卫断言当前结构所有权，而不是过时的 inline 文本锚点。
- 主 scenario compiler path 对直接消费的错误 shape fail closed，而不是静默转为空容器。
- Prefab import 的 shape 错误在 merge mutation 前报告。
- RuntimeFacadeAdapter 自身的 capability checks 使用命名 capability snapshot，并在测试替换 facade object 后刷新。
- Policy-distribution diagnostics 已隔离到 `python/training/diagnostics.py`，且不改变现有 callback entry point。
- HMoE route/parameter diagnostics 已隔离到 `python/training/diagnostics.py`，
  且 callback-owned throttling behavior 有测试保护。
- Full/hybrid action diagnostics 已隔离到 `python/training/diagnostics.py`，
  且 full-action brake 与 combat-switch behavior 有测试保护。
- Leader observation/info/reward diagnostics 已隔离到
  `python/training/diagnostics.py`，且 leader bucket、C2 transition 与 reward
  behavior 有测试保护。
- Step reward-term diagnostics 已隔离到 `python/training/diagnostics.py`，
  且 logged scalar keys 与 missing-key behavior 有测试保护。
- A6 first-event info diagnostics 已隔离到 `python/training/diagnostics.py`，
  且 label-count 与 stable-zero behavior 有测试保护。
- A5 event info diagnostics 已隔离到 `python/training/diagnostics.py`，且
  event-rate、rejection、state 与 component logging 有测试保护。
- Runway/gear step info diagnostics 已隔离到 `python/training/diagnostics.py`，
  且 runway、cross-track tail、gear-collapse 与 gear-stress logging 有测试保护。
- 聚焦本地测试和残余 blocker 已记录。

更宽的 P1 program 仍未完成，直到暂缓的 callback 和更宽 adapter/world-batch class split 切片各自拥有任务记录和验证。

## Residuals And Next Steps

- 如果后续还有并行改动落入，合入 clean branch 前再次运行完整架构守卫文件。
- 决定 scenario compiler validation 后续是否升级为公开 JSON Schema，或保持轻量内部 shape guard。
- 后续决定是否在 adapter split 中引入 `typing.Protocol` loader/runtime surfaces；当前 adapter-owned probing 已先集中到 capability snapshot。
- 继续 P1-D，以有边界 packet 拆分 basic reward/instrument scalar logging、
  terminal/preterm windows 与 cooperative/stateful event-window aggregation；
  P1-D1/D2/D3/D4/D5/D6/D7/D8 已抽取 policy distribution、HMoE、action、
  leader、step reward、A6 event-window info、A5 event info 与 runway/gear
  diagnostics。

## Archive

历史或被替代的治理记录只有在存在 replacement current-status 或 closeout surface
后才移动到 `archive/README.md`。
