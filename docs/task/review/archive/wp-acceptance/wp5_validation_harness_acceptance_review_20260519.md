# WP5 Validation Harness Acceptance Review

Status: `2026-05-19` WP5 acceptance completed.

Scope: WP5-A harness inventory, WP5-B design/boundary gates, WP5-C trace/replay
gates, WP5-D information/belief gates, and WP5-E smoke promotion.

Related documents:

- [WP5 validation harness](../simulation_architecture/validation_harness_wp5_20260519.md)
- [WP5 first-wave acceptance review](wp5_first_wave_acceptance_review_20260519.md)
- [WP5-D information/belief acceptance review](wp5_information_belief_acceptance_review_20260519.md)
- [WP5-E smoke promotion notes](../simulation_architecture/wp5_smoke_promotion_notes_20260519.md)

## 1. Acceptance Decision

WP5 validation harness is accepted.

The accepted harness provides maintained evidence for all five validation tiers:
design conformance, trace conformance, boundary conformance,
information/belief leakage, and replay/evidence conformance. Metadata-dependent
checks remain explicitly deferred rather than being promoted into brittle smoke
failures.

## 2. Accepted Smoke Set

`tests/smoke/ci_smoke_suite.json` now includes:

1. `tests/architecture/test_runtime_facade_layering.py`
2. `tests/architecture/test_wp5_design_boundary_gates.py`
3. `tests/architecture/test_cmake_target_readiness.py`
4. `tests/runtime/core/test_env_config.py`
5. `tests/runtime/engagement`
6. `tests/runtime/facade/test_facade_step_evidence_gates.py`
7. `tests/runtime/facade/test_runtime_facade.py`
8. `tests/runtime/test_agent_shim.py`
9. `tests/world_batch/test_world_batch_runtime.py`

The tier rationale is recorded in
[WP5-E smoke promotion notes](../simulation_architecture/wp5_smoke_promotion_notes_20260519.md).

## 3. Validation

Focused WP5 command:

```bash
python -m pytest -q tests/architecture/test_wp5_design_boundary_gates.py tests/architecture/test_runtime_facade_layering.py tests/runtime/facade tests/runtime/engagement/test_trace_replay_gates.py tests/runtime/engagement/test_facade_engagement_evidence_gates.py tests/runtime/engagement/test_live_engagement_event_capture.py tests/runtime/engagement/test_diagnostics_trace_contract.py tests/runtime/facade/test_facade_step_evidence_gates.py tests/runtime/test_agent_shim.py
```

Result: `38 passed`.

Maintained smoke-suite command:

```bash
python tools/runners/run_pytest_suite.py --suite tests/smoke/ci_smoke_suite.json
```

Result: `95 passed`.

`git diff --check` passed for the WP5-E smoke suite and notes reviewed in the
main thread.

## 4. Deferred Follow-Up

These items remain visible but do not block WP5 acceptance:

1. Binding surface smoke promotion after
   `tests/runtime/bindings/test_bindings_engagement_surface.py` no longer fails
   its empty packet-shell world-index case.
2. Packet-level snapshot, barrier, source-time, and unified event-sequence
   metadata checks after DTO support exists.
3. Typed `DecisionBelief`, `RewardReport`, and termination reason-source
   checks after the contracts are promoted.
4. Dedicated diagnostics facade tests if a diagnostics facade surface is added.
5. Broad direct `sim.*` AST guards after maintained-path allowlists and
   compatibility/diagnostics exceptions are finalized.

## 5. Closure

WP0-WP5 now provide a documented and locally verified runtime-kernel evidence
baseline. Follow-on work should proceed as targeted contract/DTO or domain
validation increments rather than reopening the WP0-WP5 architecture sequence.
