# WP9 Contract And Infrastructure Closure Acceptance Review

Status: `2026-05-20` accepted with one tracked residual.

Language:

- English canonical: `wp9_contract_infrastructure_closure_acceptance_review_20260520.md`
- Chinese companion:
  [wp9_contract_infrastructure_closure_acceptance_review_20260520.zh.md](wp9_contract_infrastructure_closure_acceptance_review_20260520.zh.md)

Inputs:

- [WP9 Contract And Infrastructure Closure](../simulation_architecture/wp9_contract_infrastructure_closure/contract_infrastructure_closure_wp9_20260520.md)
- [WP9-A DTO Promotion Batch 1](../simulation_architecture/wp9_contract_infrastructure_closure/wp9_dto_promotion_batch1_cluster_20260520.md)
- [WP9-B DTO Promotion Batch 2](../simulation_architecture/wp9_contract_infrastructure_closure/wp9_dto_promotion_batch2_cluster_20260520.md)
- [WP9-C Infrastructure Closure](../simulation_architecture/wp9_contract_infrastructure_closure/wp9_infrastructure_closure_cluster_20260520.md)
- [WP9-D Guard Enforcement](../simulation_architecture/wp9_contract_infrastructure_closure/wp9_guard_enforcement_cluster_20260520.md)
- [WP9-E Integration And Index Sync](../simulation_architecture/wp9_contract_infrastructure_closure/wp9_integration_and_index_sync_cluster_20260520.md)
- [WP9 guard allowlist evidence](../simulation_architecture/wp9_contract_infrastructure_closure/wp9_guard_allowlist_evidence_20260520.md)

## 1. Verdict

WP9 is accepted. DTO promotion, diagnostics facade exposure, guard enforcement,
manifest completion, capability-trigger wording, facade split governance, and
index sync are complete and test-backed.

One residual remains tracked rather than hidden:

- `INF-6` real missile terminal effects capture remains blocked for a later
  owner because `src/systems/combat/damage_system.h` does not yet provide a
  narrow maintained kernel recorder seam. WP9 documents this handoff in the
  WP3 task family and keeps the current debug/synthetic recorder path visible.

## 2. Gate Verdicts

| Gate | Verdict | Evidence |
|------|---------|----------|
| `WP9-A DTO Promotion Batch 1` | pass | `runtime_dto_contracts.h`, facade result fields, Python bindings, and DTO/facade tests cover `RewardReport`, `TerminationSpec`, observation metadata, and `ObservationViewSpec`. |
| `WP9-B DTO Promotion Batch 2` | pass | `policy_contracts.h`, Python bindings, agent-shim alignment, and policy/belief tests cover `ActionIntentPacket`, `CoordinationIntentPacket`, `AgentRole`, and `DecisionBelief`. |
| `WP9-C Infrastructure Closure` | pass with tracked residual | INF-1 through INF-5 and INF-7 are closed; INF-6 is preserved as a named blocked handoff with owner context and test-visible evidence. |
| `WP9-D Guard Enforcement` | pass | `test_wp9_guard_enforcement.py` and `wp9_guard_allowlist_evidence_20260520.md` enforce labeled `sim.*` exceptions; binding smoke covers empty engagement packet shell defaults. |
| `WP9-E Integration And Index Sync` | pass | Simulation architecture README, WP9 docs, review index, and this bilingual acceptance packet are synchronized. |

## 3. DTO Evidence

| ID | Verdict | Evidence |
|----|---------|----------|
| DTO-1 `RewardReport` | pass | `src/runtime/contracts/runtime_dto_contracts.h`; `ExecutionBatchStepResult.reward_reports`; `ef_py.RewardReport`; `tests/runtime/facade/test_runtime_dto_promotion_batch1.py`. |
| DTO-2 `TerminationSpec` | pass | `src/runtime/contracts/runtime_dto_contracts.h`; `ExecutionBatchStepResult.termination_specs`; `ef_py.TerminationSpec`; batch-1 DTO tests. |
| DTO-3 `ObservationBatchPacket` metadata | pass | `snapshot_version`, `barrier_id`, and `source_time_s` on `ObservationBatchPacket`; binding and trace-replay tests. |
| DTO-4 `ObservationViewSpec` | pass | Typed view spec and compatibility report plus `evaluate_observation_view_checkpoint_compatibility`. |
| DTO-5 `ActionIntentPacket` | pass | `src/runtime/contracts/policy_contracts.h`; `ef_py.ActionIntentPacket`; policy surface tests. |
| DTO-6 `CoordinationIntentPacket` | pass | `src/runtime/contracts/policy_contracts.h`; `ef_py.CoordinationIntentPacket`; policy surface tests. |
| DTO-7 `AgentRole` | pass | C++ `AgentRole`, binding surface, and Python shim compatibility alignment. |
| DTO-8 `DecisionBelief` | pass | C++ `DecisionBelief`, binding surface, and architecture tests that keep truth/raw ECS paths diagnostics-only. |

## 4. Infrastructure Evidence

| ID | Verdict | Evidence |
|----|---------|----------|
| INF-1 `clock_merge_policy` naming | pass | Architecture and WP2.5 docs reserve `clock_merge_policy` for scheduler semantics and `merge_policy` for cross-layer intent requests. |
| INF-2 diagnostics facade surface | pass | `RuntimeFacade::export_diagnostics_traces`, Python binding, facade and engagement tests. |
| INF-3 `RuntimeCapabilities` trigger | pass | WP6, WP7, and architecture docs state richer projection waits for a maintained non-reference backend profile. |
| INF-4 `StageNodeManifest` registry completion | pass | WP2.5 manifest cluster includes P0-P10 examples; architecture doc test checks English and Chinese coverage. |
| INF-5 facade split threshold | pass | Architecture doc and facade READMEs document the roughly 40-method split rule and target groups. |
| INF-6 terminal effects capture | tracked residual | WP3 task docs record the blocked handoff; no broad damage-system rewrite was attempted in WP9. |
| INF-7 recent-event storage strategy | pass | Recent-event capture is formalized as a monotonic id, exported sorted recent window aligned with event-order evidence. |

## 5. Guard Evidence

| ID | Verdict | Evidence |
|----|---------|----------|
| GUA-1 `sim.*` AST guard | pass | `tests/architecture/test_wp9_guard_enforcement.py` enforces labeled direct-sim access allowlists. |
| GUA-2 binding surface smoke promotion | pass | `tests/runtime/bindings/test_bindings_engagement_surface.py` covers the empty engagement packet shell with default `world_index=0`. |

## 6. Validation Commands

Passed:

```bash
git diff --check
cmake --build build --target ef_py -j2
CMO_BUILD_DIR=/home/void0312/Workshop/CMO/build pytest -q tests/architecture/test_runtime_dto_contracts_batch1.py tests/architecture/test_policy_belief_boundaries.py tests/architecture/test_wp9_guard_enforcement.py tests/architecture/test_wp9_infrastructure_closure_docs.py tests/runtime/bindings/test_bindings_runtime_dto_surface.py tests/runtime/bindings/test_bindings_policy_surface.py tests/runtime/bindings/test_bindings_engagement_surface.py tests/runtime/facade/test_runtime_dto_promotion_batch1.py tests/runtime/facade/test_runtime_facade.py tests/runtime/engagement/test_facade_engagement_export.py tests/runtime/engagement/test_live_engagement_event_capture.py tests/runtime/engagement/test_trace_replay_gates.py tests/runtime/test_agent_shim.py tests/runtime/mission/test_policy_contract_shape.py
```

The focused integration test command passed with `89 passed`.

Final validation passed:

```bash
CMO_BUILD_DIR=/home/void0312/Workshop/CMO/build pytest -q tests/architecture tests/runtime/bindings tests/runtime/engagement tests/runtime/facade
rg -n "WP9|Contract And Infrastructure Closure|RewardReport|TerminationSpec|ObservationViewSpec|ActionIntentPacket|CoordinationIntentPacket|AgentRole|DecisionBelief|DiagnosticsTrace|StageNodeManifest|sim\\.\\*" docs/task/simulation_architecture docs/task/review docs/plan/architecture src tests
```

The final scoped validation command passed with `121 passed`.

## 7. Residual Risks

- `INF-6` remains intentionally open as a named follow-up. The next owner should
  add a narrow maintained recorder seam around guidance/effects terminal hit
  resolution before migrating the recent-event DTO capture away from
  debug/synthetic proximity-hit paths.
- Full repository pytest was not run as part of this review; the checked
  focused and final scoped commands cover WP9 architecture, bindings,
  engagement, facade, DTO, guard, and integration surfaces.

## 8. Bilingual Alignment

The WP9 task family, all five cluster documents, the guard allowlist evidence,
the simulation architecture README, and this acceptance review have English and
Chinese entries where the project convention requires them.
