# WP5-A Harness Inventory Notes

Status: `2026-05-19` first inventory pass; docs-only, no smoke-suite edits.

Language:

- English canonical: `wp5_harness_inventory_notes_20260519.md`
- Chinese companion: [wp5_harness_inventory_notes_20260519.zh.md](wp5_harness_inventory_notes_20260519.zh.md)

Inputs:

- [WP5 validation harness](validation_harness_wp5_20260519.md)
- [WP4 facade alignment acceptance review](../review/wp4_facade_alignment_acceptance_review_20260519.md)
- [WP4-F integration handoff](wp4_integration_handoff_20260519.md)
- Current `tests/architecture/`, `tests/runtime/`, and `tests/smoke/ci_smoke_suite.json`

## 1. Purpose

WP5-A maps the current evidence base to the five WP5 validation tiers before
any test promotion. This pass does not change runtime behavior and does not
edit the smoke suite. It separates gates that can run immediately from gates
that still depend on runtime/facade metadata that WP4 deliberately deferred.

## 2. Tier Inventory

| Validation tier | Current coverage | Candidate coverage | Gap / next decision |
|-----------------|------------------|--------------------|---------------------|
| Design conformance | `tests/architecture/runtime_facade/test_layering.py` checks facade layering, compatibility escape-hatch documentation, contract/facade header isolation, and hidden engine ownership. `tests/architecture/build/test_cmake_target_readiness.py` checks CMake source grouping and mission episode detail ownership. `tests/runtime/engagement/test_engagement_contract_shape.py` checks engagement contract placement and field shape. | Keep the two architecture files in smoke. Consider explicit design gates for `tests/runtime/bindings/test_bindings_engagement_surface.py` and `tests/runtime/bindings/test_bindings_command_surface.py` after WP5-B decides whether binding surface shape belongs in design or boundary tier. | Missing a `StageNodeManifest` / `P0-P10` manifest conformance gate. Existing design checks are file/layer focused, not full stage-manifest coverage. |
| Trace conformance | `tests/runtime/engagement/test_diagnostics_trace_contract.py` checks synthetic track, launch request/event, munition lifecycle, effects, damage, and observation-version ancestry. `tests/runtime/engagement/test_facade_engagement_evidence_gates.py` checks producer coverage, deferred engagement slots, diagnostics piggybacking, and multi-world retagging. `tests/runtime/engagement` is already in the smoke suite. | Add or promote focused checks for current facade step output from `tests/runtime/facade/test_facade_step_evidence_gates.py`, especially reward, termination, phase, and observation packet shape. Keep engagement trace tests as the first WP5-C anchor. | Current facade-generated diagnostics are piggyback traces and only link track-derived diagnostics. Dedicated diagnostics facade, launch-request producers, and munition-lifecycle producers remain deferred. |
| Boundary conformance | `tests/architecture/runtime_facade/test_layering.py` forbids raw `RuntimeFacade.runtime()` and `WorldBatchRuntime` escape from maintained batch/leader paths. `tests/runtime/facade/test_runtime_facade.py` checks maintained request/result shells for setup, observation, engagement export, execution step, and batch setup. `tests/runtime/engagement/test_launch_adapter_static_shape.py` checks the weapon adapter stays a contract converter instead of live engine owner. | Add `tests/runtime/test_agent_shim.py` as a candidate smoke member for passive policy/agent boundary labels. Consider `tests/runtime/core/test_world_setup_compat.py` for compatibility adapter behavior if WP5-B wants setup-path coverage. | Broad direct `sim.*` policy-path bans are still unsafe until provenance labels and allowlists are defined. Boundary gates must avoid blocking documented compatibility adapters. |
| Information/belief leakage | `tests/runtime/test_agent_shim.py` checks `ObservationProvenance`, `AgentRole`, `ActionIntentCompat`, `CoordinationIntentCompat`, diagnostics-only world-truth labels, and invalid status / merge-policy rejection. `tests/runtime/facade/test_runtime_facade.py` checks typed observation packet export. | Promote `tests/runtime/test_agent_shim.py` to smoke after WP5-D confirms the shim labels are the accepted maintained vocabulary. Add docs-backed AST checks only for maintained packages with a clear compatibility allowlist. | Runtime `ObservationBatchPacket` lacks typed source-time, barrier, and full `SnapshotVersion` provenance. `DecisionBelief` is not a public C++ DTO. Any truth-leakage guard must distinguish maintained policy paths from diagnostics/oracle tests. |
| Replay/evidence conformance | Existing trace tests check deterministic ids and ancestry fields where current DTOs expose them. `tests/runtime/facade/test_facade_step_evidence_gates.py` checks step result evidence shape. Engagement smoke currently exercises packet export and diagnostics evidence through `tests/runtime/engagement`. | WP5-C should define the first replay envelope gate using existing seeds, trace ids, event ids, observation packet versions, and facade request/result exports. WP5-E can later promote a narrow replay/evidence command into smoke. | No deterministic replay comparison harness yet. Snapshot-version, barrier-visibility, event-order envelope, and clock-domain merge metadata from WP2.5 are not all available in runtime DTOs. |

## 3. Smoke Suite Membership Review

Current `tests/smoke/ci_smoke_suite.json` members:

| Smoke member | Current WP5 value | Recommendation |
|--------------|-------------------|----------------|
| `tests/architecture/runtime_facade/test_layering.py` | Primary design and boundary evidence for facade layering and raw-runtime escape-hatch containment. | Keep. This is the strongest immediate WP5-B smoke anchor. |
| `tests/architecture/build/test_cmake_target_readiness.py` | Design evidence for source grouping and mission-controller ownership. | Keep. It is low-level but valuable for architecture drift. |
| `tests/runtime/core/test_env_config.py` | Runtime configuration smoke, not a primary WP5 facade/evidence tier. | Keep as existing operational smoke, but do not count it as the main WP5 tier proof. |
| `tests/runtime/engagement` | Broad engagement directory coverage, including contract shape, launch adapters, diagnostics trace contract, facade evidence gates, live event capture, and launch/damage adapter tests. | Keep for now. If cost grows, split to a focused WP5-C subset instead of removing coverage. |
| `tests/runtime/facade/test_runtime_facade.py` | Maintained facade request/result and observation/engagement/execution evidence. | Keep. Add `test_facade_step_evidence_gates.py` separately if WP5-E wants explicit step semantic smoke. |
| `tests/world_batch/test_world_batch_runtime.py` | Existing batch runtime regression outside the WP5-A input scope. | Keep as existing smoke baseline, but treat as supporting runtime health rather than facade-alignment proof. |

High-value candidates not currently promoted:

| Candidate | Tier value | Promotion note |
|-----------|------------|----------------|
| `tests/runtime/test_agent_shim.py` | Information/belief and boundary labels. | Immediate candidate after WP5-D accepts shim vocabulary. Low runtime cost. |
| `tests/runtime/facade/test_facade_step_evidence_gates.py` | Trace/evidence and boundary shape for execution-step results. | Immediate candidate; already accepted by WP4 as focused evidence. |
| `tests/runtime/bindings/test_bindings_engagement_surface.py` | Design/boundary evidence for engagement DTO bindings. | Candidate for WP5-B or WP5-E if binding drift becomes a smoke concern. |
| `tests/runtime/bindings/test_bindings_command_surface.py` | Boundary evidence for command/action binding shape. | Candidate after WP5-B decides command binding shape is part of maintained harness. |
| `tests/runtime/core/test_world_setup_compat.py` | Boundary evidence for setup compatibility helpers. | Candidate only if setup adapter drift becomes a WP5-B concern. |

Tests that should not be promoted by WP5-A:

| Area | Reason |
|------|--------|
| Broad `tests/runtime/air_combat`, `tests/runtime/naval`, `tests/runtime/mission`, `tests/runtime/multi_agent`, and `tests/runtime/link` directories | Valuable domain regressions, but too broad for the first WP5 maintained validation harness. Promote only focused gates with clear tier ownership. |
| Metadata-dependent observation, belief, replay, and diagnostics-facade checks | They require DTO metadata that WP4 explicitly deferred. Document first, enforce after runtime fields exist. |

## 4. Immediate Gates

These gates can proceed without reopening facade semantics:

1. Keep architecture layering checks as WP5-B design/boundary anchors.
2. Keep engagement contract, adapter, diagnostics trace, and facade evidence
   tests as WP5-C trace anchors.
3. Promote or document `tests/runtime/facade/test_facade_step_evidence_gates.py`
   as the current execution-step evidence gate.
4. Use `tests/runtime/test_agent_shim.py` to validate passive
   `ObservationProvenance`, `AgentRole`, action intent, and coordination intent
   labels.
5. Keep `RuntimeFacade::runtime()` / raw `WorldBatchRuntime` allowed only in
   documented compatibility or diagnostics surfaces.

## 5. Metadata-Dependent Gates

These gates should stay pending until the named runtime/facade metadata exists:

1. Runtime-enforced `ObservationViewSpec` schema compatibility.
2. `ObservationPacket` source `SnapshotVersion`, barrier, source-time, and
   clock-domain metadata.
3. Typed `DecisionBelief` provenance and consumed observation/source versions.
4. Typed C++ `AgentRole`, `ActionIntentPacket`, and `CoordinationIntentPacket`
   binding surfaces.
5. Typed `RewardReport` fact/shaping attribution.
6. Typed termination reason-source attribution.
7. Dedicated `DiagnosticsTrace` facade query/export separate from engagement
   piggyback evidence.
8. Deterministic replay comparison harness using event order, seeds, snapshot
   versions, barriers, and replay metadata.
9. Broad direct `sim.*` policy-path AST ban outside an explicit compatibility
   allowlist.

## 6. Dispatch Advice

| Next cluster | Recommended ownership | Avoid overlap |
|--------------|-----------------------|---------------|
| `WP5-B Design And Boundary Gates` | Own `tests/architecture/`, binding-surface candidate decisions, and narrow facade/boundary docs. Strengthen raw-runtime and facade-only gates without touching runtime code. | Do not implement broad direct `sim.*` bans until WP5-D defines maintained labels and allowlists. |
| `WP5-C Trace And Replay Gates` | Own `tests/runtime/engagement/` and narrow `tests/runtime/facade/` evidence fixtures for trace ancestry, step evidence, and replay envelope presence. | Do not require missing WP2.5 replay metadata as runtime DTO fields yet; mark such checks pending. |
| `WP5-D Information And Belief Gates` | Own `tests/runtime/test_agent_shim.py` promotion advice and docs-backed information/belief leakage checks. Start with labels and allowlists, not broad bans. | Do not classify diagnostics/oracle fixtures as maintained policy inputs. |
| `WP5-E Smoke Promotion And Docs` | Own `tests/smoke/ci_smoke_suite.json`, WP5 index sync, final validation command publication, and smoke rationale. | Run after WP5-B/C/D settle candidate file lists; avoid changing test behavior during smoke promotion. |

## 7. Acceptance Notes

WP5-A satisfies the dispatch sheet when this inventory is used as the handoff
map: every validation tier has current coverage, candidate coverage, or an
explicit gap; smoke candidates are listed with rationale; immediate gates are
separated from metadata-dependent gates; and WP5-B/C/D/E have non-overlapping
ownership boundaries.
