# WP4 Facade Alignment Acceptance Review

Status: `2026-05-19` final WP4 acceptance completed.

Scope: WP4 facade surface inventory, engagement/step alignment, policy/binding
alignment, facade evidence gates, passive agent shim, compatibility guard
review, and WP5 handoff.

Related documents:

- [WP4 facade alignment](../simulation_architecture/facade_alignment_wp4_20260519.md)
- [WP4 first-wave acceptance review](wp4_first_wave_acceptance_review_20260519.md)
- [WP4 second-wave acceptance review](wp4_second_wave_acceptance_review_20260519.md)
- [WP4-F integration handoff](../simulation_architecture/wp4_integration_handoff_20260519.md)
- [WP5 validation harness](../simulation_architecture/validation_harness_wp5_20260519.md)

## 1. Acceptance Decision

WP4 facade alignment is accepted.

The accepted scope is intentionally implementation-light. WP4 did not promote
new public C++ DTOs for agent roles, decision beliefs, action intents, or
coordination intents. Instead, it stabilized the maintained facade vocabulary,
added focused evidence gates around existing facade behavior, and published a
passive Python shim that makes policy/agent metadata explicit without changing
runtime behavior.

## 2. Accepted Evidence

| Area | Accepted evidence | Decision |
|------|-------------------|----------|
| Facade surface classification | `wp4_surface_inventory_wp4a_20260519.md` | Maintained, compatibility-only, diagnostics-only, and deferred surfaces are visible enough for WP5 validation. |
| Engagement and step alignment | `wp4_engagement_step_alignment_notes_20260519.md` | Current producer coverage and step-result semantic shape are documented with explicit deferred slots. |
| Policy and binding alignment | `wp4_policy_binding_alignment_notes_20260519.md` | Current adapters are classified without prematurely expanding C++ bindings. |
| Facade evidence gates | `tests/runtime/engagement/test_facade_engagement_evidence_gates.py`, `tests/runtime/facade/test_facade_step_evidence_gates.py` | Focused tests cover current engagement export evidence and execution-step shape. |
| Agent metadata shim | `python/rl/runtime/agent_shim.py`, `tests/runtime/test_agent_shim.py` | Passive Python compatibility scaffolding is accepted. |
| Compatibility guard review | `wp4_compat_guard_notes_20260519.md` | Broad raw-runtime bans are deferred until provenance labels and allowlists are ready. |
| Integration handoff | `wp4_integration_handoff_20260519.md` | WP5 immediate and metadata-dependent gates are separated. |

## 3. Validation

Focused commands recorded for WP4:

```bash
python -m py_compile python/rl/runtime/agent_shim.py tests/runtime/test_agent_shim.py
python -m pytest -q tests/runtime/test_agent_shim.py
python -m pytest -q tests/runtime/engagement/test_facade_engagement_evidence_gates.py tests/runtime/facade/test_facade_step_evidence_gates.py
```

Previously reported broader focused command:

```bash
python -m pytest -q tests/runtime/engagement/test_facade_engagement_evidence_gates.py tests/runtime/engagement/test_facade_engagement_export.py tests/runtime/engagement/test_live_engagement_event_capture.py tests/runtime/engagement/test_diagnostics_trace_contract.py tests/runtime/facade/test_facade_step_evidence_gates.py tests/runtime/facade/test_runtime_facade.py
```

Reported result: `23 passed`.

## 4. Residual Risks Routed To WP5

These items do not block WP4 acceptance because they require runtime metadata,
new maintained producers, or broader validation policy:

1. `ObservationBatchPacket` still lacks full source-time, barrier, and
   snapshot-version provenance as typed runtime metadata.
2. `DecisionBelief` remains a policy/agent-side concept rather than a public
   C++ facade DTO.
3. Reward fact/shaping attribution and termination reason-source attribution
   are not yet typed contracts.
4. `DiagnosticsTrace` remains piggyback evidence inside engagement export, not
   a dedicated diagnostics facade surface.
5. Broad direct `sim.*` policy-path bans require provenance labels and
   allowlists before they can be enforced safely.

## 5. Handoff Decision

WP5 may start from the accepted WP4 labels and evidence gates. The first WP5
wave should inventory existing validation coverage, strengthen design/boundary
gates, and add trace/replay checks without reopening facade semantics.

WP4 status should move from `active` to `complete`; WP5 should become the active
simulation-architecture work package.
