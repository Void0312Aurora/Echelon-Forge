# WP5-E Smoke Promotion And Docs Notes

Status: `2026-05-19` smoke promotion pass completed.

Language:

- English canonical: `wp5_smoke_promotion_notes_20260519.md`
- Chinese companion: [wp5_smoke_promotion_notes_20260519.zh.md](wp5_smoke_promotion_notes_20260519.zh.md)

Inputs:

- [WP5-E smoke promotion dispatch](wp5_smoke_promotion_cluster_20260519.md)
- [WP5 first-wave acceptance review](../review/wp5_first_wave_acceptance_review_20260519.md)
- [WP5-D information/belief notes](wp5_information_belief_notes_20260519.md)
- Current `tests/smoke/ci_smoke_suite.json`

## 1. Decision

WP5-E promotes a focused set of low-cost validation gates into
`tests/smoke/ci_smoke_suite.json`. It preserves the existing smoke entries and
adds only tests that passed locally and have clear WP5 tier ownership.

The binding surface tests are not promoted in this pass. A focused trial found
`tests/runtime/bindings/test_bindings_engagement_surface.py` currently fails on
an out-of-range world index in the empty packet-shell test. That is recorded as
a candidate fix, not a WP5-E blocker.

## 2. Promoted Smoke Entries

| Smoke entry | WP5 tier coverage | Rationale |
|-------------|------------------|-----------|
| `tests/architecture/test_runtime_facade_layering.py` | Design, boundary. | Existing architecture guard for facade layering and raw-runtime escape-hatch containment. |
| `tests/architecture/test_wp5_design_boundary_gates.py` | Design, boundary. | New WP5-B guard for maintained facade header isolation, runtime owner exposure, and deferred broad `sim.*` bans. |
| `tests/architecture/test_cmake_target_readiness.py` | Design. | Existing architecture/build ownership smoke. |
| `tests/runtime/core/test_env_config.py` | Operational support. | Existing environment/config smoke retained as supporting runtime health. |
| `tests/runtime/engagement` | Trace, replay/evidence. | Existing engagement directory smoke now includes WP5-C trace/replay gates, facade evidence gates, diagnostics trace contract, live event capture, and adapter checks. |
| `tests/runtime/facade/test_facade_step_evidence_gates.py` | Trace, replay/evidence, boundary. | Focused execution-step evidence shape gate accepted by WP4/WP5. |
| `tests/runtime/facade/test_runtime_facade.py` | Boundary, design, evidence. | Maintained facade request/result behavior for setup, observation, engagement export, and step. |
| `tests/runtime/test_agent_shim.py` | Information/belief leakage, agency boundary. | WP5-D label-first gate for `ObservationProvenance`, `AgentRole`, action intent, and coordination intent metadata. |
| `tests/world_batch/test_world_batch_runtime.py` | Operational support. | Existing smoke baseline retained for runtime health outside strict WP5 tier proof. |

## 3. Deferred Candidates

| Candidate | Reason |
|-----------|--------|
| `tests/runtime/bindings/test_bindings_engagement_surface.py` | Currently fails when exporting an empty packet shell for `world_index = 2` from `RuntimeFacade(1)`. Fix or narrow before promotion. |
| `tests/runtime/bindings/test_bindings_command_surface.py` | Useful boundary candidate, but not required for five-tier coverage in this pass. Promote with binding-surface cleanup. |
| Packet-level snapshot/barrier/source-time checks | DTO metadata is not present yet. |
| Typed `DecisionBelief`, `RewardReport`, and termination reason-source checks | Metadata/DTO-dependent. |
| Dedicated diagnostics facade tests | `DiagnosticsTrace` remains piggyback evidence. |
| Broad direct `sim.*` AST ban | Requires maintained-path allowlist and compatibility/diagnostics exceptions. |

## 4. Published Validation Commands

Focused WP5 validation command:

```bash
python -m pytest -q tests/architecture/test_wp5_design_boundary_gates.py tests/architecture/test_runtime_facade_layering.py tests/runtime/facade tests/runtime/engagement/test_trace_replay_gates.py tests/runtime/engagement/test_facade_engagement_evidence_gates.py tests/runtime/engagement/test_live_engagement_event_capture.py tests/runtime/engagement/test_diagnostics_trace_contract.py tests/runtime/facade/test_facade_step_evidence_gates.py tests/runtime/test_agent_shim.py
```

Maintained smoke-suite command:

```bash
python tools/runners/run_pytest_suite.py --suite tests/smoke/ci_smoke_suite.json
```

## 5. Acceptance Notes

WP5-E satisfies the dispatch sheet when the promoted smoke entries pass through
the maintained suite runner, the tier rationale above remains indexed, and
metadata-dependent candidates stay deferred instead of becoming brittle smoke
failures.
