# WP4-F Integration And Handoff

Status: `2026-05-19` integration handoff complete; WP4 final acceptance published.

Language:

- English canonical: `wp4_integration_handoff_20260519.md`
- Chinese companion: [wp4_integration_handoff_20260519.zh.md](wp4_integration_handoff_20260519.zh.md)

Inputs:

- [WP4 facade alignment](facade_alignment_wp4_20260519.md)
- [WP4 first-wave acceptance review](../review/wp4_first_wave_acceptance_review_20260519.md)
- [WP4 second-wave acceptance review](../review/wp4_second_wave_acceptance_review_20260519.md)
- [WP4-A surface inventory draft](wp4_surface_inventory_wp4a_20260519.md)
- [WP4-G facade evidence notes](wp4_facade_evidence_notes_20260519.md)
- [WP4-H agent shim implementation notes](wp4_agent_shim_implementation_notes_20260519.md)
- [WP4-I compatibility guard notes](wp4_compat_guard_notes_20260519.md)

## 1. Integration Summary

WP4 has produced a maintained facade alignment baseline, focused evidence
gates, and passive Python-side metadata shims without reopening simulation
semantics.

Accepted WP4 outputs:

| Output | Status | Notes |
|--------|--------|-------|
| Surface inventory | Accepted as WP4-A vocabulary input. | Classifies maintained, compatibility, diagnostics-only, and deferred surfaces. |
| Engagement/step alignment notes | Accepted as bounded evidence. | Documents producer coverage, deferred slots, diagnostics piggybacking, and step/lifecycle gaps. |
| Policy/binding alignment notes | Accepted as discovery input. | Maps current adapters to `AgentRole`, intent, observation, and compatibility classifications. |
| Facade evidence tests | Accepted and locally verified. | Adds focused guards for engagement export and step-result semantic shape. |
| Passive agent shim | Accepted and locally verified. | Adds Python-only `AgentRole`, `ActionIntentCompat`, `CoordinationIntentCompat`, and `ObservationProvenance` shells. |
| Compatibility guard notes | Accepted as current guard review. | Keeps broad direct `sim.*` bans pending until provenance labels and allowlists mature. |

## 2. Maintained WP4 Validation Commands

Focused commands verified in the main thread:

```bash
python -m py_compile python/rl/runtime/agent_shim.py tests/runtime/test_agent_shim.py
python -m pytest -q tests/runtime/test_agent_shim.py
python -m pytest -q tests/runtime/engagement/test_facade_engagement_evidence_gates.py tests/runtime/facade/test_facade_step_evidence_gates.py
```

Worker-verified broader focused command:

```bash
python -m pytest -q tests/runtime/engagement/test_facade_engagement_evidence_gates.py tests/runtime/engagement/test_facade_engagement_export.py tests/runtime/engagement/test_live_engagement_event_capture.py tests/runtime/engagement/test_diagnostics_trace_contract.py tests/runtime/facade/test_facade_step_evidence_gates.py tests/runtime/facade/test_runtime_facade.py
```

Result reported by worker: `23 passed`.

## 3. WP5 Handoff

WP5 can validate immediately:

1. Facade evidence gates for engagement producer coverage and step-result shape.
2. Agent shim metadata classification and invalid status/merge-policy rejection.
3. Raw runtime escape hatch documentation and existing architecture-layering
   guards.
4. Engagement diagnostics as piggyback evidence.
5. Surface inventory classifications as validation labels.

WP5 should wait for runtime/facade metadata before enforcing:

1. `ObservationViewSpec` schema compatibility as a runtime DTO.
2. `ObservationPacket` source `SnapshotVersion`, barrier, and source-time
   provenance.
3. Typed `DecisionBelief` provenance.
4. Typed `AgentRole` authority/action-interface metadata in C++ bindings.
5. Typed `RewardReport` fact/shaping attribution.
6. Typed termination reason-source attribution.
7. Dedicated diagnostics facade surface requirements.

## 4. Deferred Or Post-WP4 Items

| Item | Route |
|------|-------|
| `launch_requests` and `munition_lifecycle_packets` engagement producers | Add producer and retagging tests when maintained producers exist. |
| Dedicated `DiagnosticsTrace` facade surface | WP5 trace conformance decision or later diagnostics architecture work. |
| Runtime `ObservationViewSpec` DTO | WP5 information-state metadata enforcement or later facade DTO work. |
| C++ bindings for `AgentRole`, `DecisionBelief`, `ActionIntentPacket`, `CoordinationIntentPacket` | Wait until WP4-A names and DTO fields are stable enough for maintained API exposure. |
| Broad direct `sim.*` ban | Add allowlist-based AST guard after agent/provenance shims are adopted by maintained adapters. |
| RuntimeFacade split | Planning trigger only if maintained public method count crosses the documented threshold. |

## 5. Final Acceptance Recommendation

WP4 is ready for WP5 validation after index sync, final acceptance publication,
and final `git diff --check`.

Final acceptance publication criteria:

1. All WP4 accepted outputs are indexed.
2. Focused WP4 tests pass locally.
3. Compatibility-only and diagnostics-only paths remain visibly separated from
   maintained policy/training truth.
4. WP5 handoff lists immediate gates and metadata-dependent gates separately.
