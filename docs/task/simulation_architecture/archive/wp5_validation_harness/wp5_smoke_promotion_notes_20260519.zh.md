# WP5-E Smoke Promotion 与文档笔记

状态：`2026-05-19` smoke promotion 已完成。

语言版本：

- 英文主文：[wp5_smoke_promotion_notes_20260519.md](wp5_smoke_promotion_notes_20260519.md)
- 中文辅文：`wp5_smoke_promotion_notes_20260519.zh.md`

输入：

- [WP5-E smoke promotion 分发单](wp5_smoke_promotion_cluster_20260519.zh.md)
- [WP5 第一波验收审查](../review/wp5_first_wave_acceptance_review_20260519.zh.md)
- [WP5-D information/belief 笔记](wp5_information_belief_notes_20260519.zh.md)
- 当前 `tests/smoke/ci_smoke_suite.json`

## 1. 决定

WP5-E 将一组低成本、聚焦的 validation gate 提升到
`tests/smoke/ci_smoke_suite.json`。它保留既有 smoke entry，只新增已经本地通过且
具备明确 WP5 tier ownership 的测试。

Binding surface tests 本轮不提升。聚焦试跑发现
`tests/runtime/bindings/test_bindings_engagement_surface.py` 当前在 empty packet-shell
测试中用 `RuntimeFacade(1)` 导出 `world_index = 2` 时失败。该项记录为候选修复，而不是 WP5-E blocker。

## 2. 已提升 Smoke 条目

| Smoke entry | WP5 tier 覆盖 | 理由 |
|-------------|---------------|------|
| `tests/architecture/runtime_facade` | Design、boundary。 | 既有 facade layering 与 raw-runtime escape-hatch containment 架构 guard。 |
| `tests/architecture/runtime_facade/test_design_boundary_gates.py` | Design、boundary。 | 新增 WP5-B guard，覆盖 maintained facade header isolation、runtime owner exposure 与 deferred broad `sim.*` ban。 |
| `tests/architecture/build/test_cmake_target_readiness.py` | Design。 | 既有 architecture/build ownership smoke。 |
| `tests/runtime/core/test_env_config.py` | Operational support。 | 保留既有环境/config smoke，作为 runtime health 支撑。 |
| `tests/runtime/engagement` | Trace、replay/evidence。 | 既有 engagement 目录 smoke 现在包含 WP5-C trace/replay gates、facade evidence gates、diagnostics trace contract、live event capture 与 adapter checks。 |
| `tests/runtime/facade/test_facade_step_evidence_gates.py` | Trace、replay/evidence、boundary。 | WP4/WP5 已验收的 execution-step evidence shape 聚焦 gate。 |
| `tests/runtime/facade/test_runtime_facade.py` | Boundary、design、evidence。 | Maintained facade request/result 行为，覆盖 setup、observation、engagement export 与 step。 |
| `tests/runtime/test_agent_shim.py` | Information/belief leakage、agency boundary。 | WP5-D label-first gate，覆盖 `ObservationProvenance`、`AgentRole`、action intent 与 coordination intent metadata。 |
| `tests/world_batch/test_world_batch_runtime.py` | Operational support。 | 保留既有 runtime health smoke baseline，不作为严格 WP5 tier proof。 |

## 3. Deferred 候选

| Candidate | 原因 |
|-----------|------|
| `tests/runtime/bindings/test_bindings_engagement_surface.py` | 当前从 `RuntimeFacade(1)` 导出 `world_index = 2` empty packet shell 时失败；修复或收窄后再提升。 |
| `tests/runtime/bindings/test_bindings_command_surface.py` | 有用的 boundary 候选，但本轮五层覆盖不依赖它；随 binding-surface cleanup 再提升。 |
| Packet-level snapshot/barrier/source-time checks | DTO metadata 尚不存在。 |
| Typed `DecisionBelief`、`RewardReport` 与 termination reason-source checks | 依赖 metadata/DTO。 |
| Dedicated diagnostics facade tests | `DiagnosticsTrace` 仍是 piggyback evidence。 |
| Broad direct `sim.*` AST ban | 需要 maintained-path allowlist 与 compatibility/diagnostics exceptions。 |

## 4. 已发布验证命令

WP5 聚焦验证命令：

```bash
python -m pytest -q tests/architecture/runtime_facade/test_design_boundary_gates.py tests/architecture/runtime_facade tests/runtime/facade tests/runtime/engagement/test_trace_replay_gates.py tests/runtime/engagement/test_facade_engagement_evidence_gates.py tests/runtime/engagement/test_live_engagement_event_capture.py tests/runtime/engagement/test_diagnostics_trace_contract.py tests/runtime/facade/test_facade_step_evidence_gates.py tests/runtime/test_agent_shim.py
```

Maintained smoke-suite 命令：

```bash
python tools/runners/run_pytest_suite.py --suite tests/smoke/ci_smoke_suite.json
```

## 5. 验收备注

WP5-E 在 promoted smoke entries 通过 maintained suite runner、上方 tier rationale
保持索引、metadata-dependent 候选继续 deferred 而不是变成脆弱 smoke failure 时满足分发表。
