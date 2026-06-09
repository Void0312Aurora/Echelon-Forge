# WP5 验证套件验收审查

状态：`2026-05-19` WP5 验收已完成。

范围：WP5-A harness inventory、WP5-B design/boundary gates、WP5-C trace/replay
gates、WP5-D information/belief gates 与 WP5-E smoke promotion。

相关文档：

- [WP5 验证套件](../simulation_architecture/validation_harness_wp5_20260519.zh.md)
- [WP5 第一波验收审查](wp5_first_wave_acceptance_review_20260519.zh.md)
- [WP5-D information/belief 验收审查](wp5_information_belief_acceptance_review_20260519.zh.md)
- [WP5-E smoke promotion 笔记](../simulation_architecture/wp5_smoke_promotion_notes_20260519.zh.md)

## 1. 验收决定

WP5 validation harness 予以验收。

已验收 harness 为五个验证层级提供维护中的证据：design conformance、trace
conformance、boundary conformance、information/belief leakage 与 replay/evidence
conformance。Metadata-dependent checks 继续明确 deferred，而不是被提升成脆弱的
smoke failure。

## 2. 已验收 Smoke Set

`tests/smoke/ci_smoke_suite.json` 现在包含：

1. `tests/architecture/runtime_facade/test_layering.py`
2. `tests/architecture/test_wp5_design_boundary_gates.py`
3. `tests/architecture/build/test_cmake_target_readiness.py`
4. `tests/runtime/core/test_env_config.py`
5. `tests/runtime/engagement`
6. `tests/runtime/facade/test_facade_step_evidence_gates.py`
7. `tests/runtime/facade/test_runtime_facade.py`
8. `tests/runtime/test_agent_shim.py`
9. `tests/world_batch/test_world_batch_runtime.py`

Tier rationale 记录在
[WP5-E smoke promotion 笔记](../simulation_architecture/wp5_smoke_promotion_notes_20260519.zh.md)。

## 3. 验证

WP5 聚焦命令：

```bash
python -m pytest -q tests/architecture/test_wp5_design_boundary_gates.py tests/architecture/runtime_facade/test_layering.py tests/runtime/facade tests/runtime/engagement/test_trace_replay_gates.py tests/runtime/engagement/test_facade_engagement_evidence_gates.py tests/runtime/engagement/test_live_engagement_event_capture.py tests/runtime/engagement/test_diagnostics_trace_contract.py tests/runtime/facade/test_facade_step_evidence_gates.py tests/runtime/test_agent_shim.py
```

结果：`38 passed`。

Maintained smoke-suite 命令：

```bash
python tools/runners/run_pytest_suite.py --suite tests/smoke/ci_smoke_suite.json
```

结果：`95 passed`。

主线程审阅的 WP5-E smoke suite 与 notes 通过 `git diff --check`。

## 4. Deferred 后续项

以下项目保持可见，但不阻断 WP5 验收：

1. `tests/runtime/bindings/test_bindings_engagement_surface.py` 的 empty
   packet-shell world-index case 不再失败后，再提升 binding surface smoke。
2. DTO 支持存在后，再加入 packet-level snapshot、barrier、source-time 与 unified
   event-sequence metadata checks。
3. Contract 提升后，再加入 typed `DecisionBelief`、`RewardReport` 与 termination
   reason-source checks。
4. 如果新增 diagnostics facade surface，再加入 dedicated diagnostics facade tests。
5. Maintained-path allowlist 与 compatibility/diagnostics exceptions 定稿后，再加入宽泛 direct `sim.*` AST guard。

## 5. 收口

WP0-WP5 现在形成了文档化且本地验证过的 runtime-kernel evidence baseline。后续工作应作为目标明确的 contract/DTO 或 domain validation 增量推进，而不是重新打开 WP0-WP5 架构序列。
