# WP4 Second Wave Acceptance Review

Status: `2026-05-19` second-wave acceptance completed.

Scope: WP4-G facade evidence gates, WP4-H information/agent shim, WP4-I
compatibility guard review.

Related documents:

- [WP4 first-wave acceptance review](wp4_first_wave_acceptance_review_20260519.md)
- [WP4-G facade evidence notes](../simulation_architecture/wp4_facade_evidence_notes_20260519.md)
- [WP4-H agent shim implementation notes](../simulation_architecture/wp4_agent_shim_implementation_notes_20260519.md)
- [WP4-I compatibility guard notes](../simulation_architecture/wp4_compat_guard_notes_20260519.md)
- [WP4 facade alignment](../simulation_architecture/facade_alignment_wp4_20260519.md)

## 1. Acceptance Decision

WP4 second-wave work is accepted.

The second wave moved WP4 from documentation-only discovery into focused
evidence and minimal compatibility scaffolding:

1. Facade evidence gates now cover engagement producer coverage, deferred
   placeholders, diagnostics piggybacking, multi-world retagging, and current
   execution-step semantic shape.
2. A passive Python-side `AgentRole` / intent / provenance shim now exists
   without changing policy inference or public C++ bindings.
3. Compatibility guard coverage has been reviewed and staged so WP5 can enforce
   stronger leakage checks once provenance metadata is available.

## 2. Accepted Artifacts

| Area | Artifact | Acceptance note |
|------|----------|-----------------|
| Engagement evidence gates | `tests/runtime/engagement/test_facade_engagement_evidence_gates.py` | Accepted as focused WP4 guards for producer coverage, deferred placeholders, piggyback diagnostics, and multi-world effects/damage/trace retagging. |
| Step semantic gate | `tests/runtime/facade/test_facade_step_evidence_gates.py` | Accepted as a guard for the current `ExecutionBatchStepResult` shape without forcing new DTO fields. |
| Agent shim | `python/rl/runtime/agent_shim.py` and `tests/runtime/test_agent_shim.py` | Accepted as passive compatibility scaffolding. It does not promote new public C++ facade or binding surfaces. |
| Guard review | `wp4_compat_guard_notes_20260519.md` | Accepted as the current compatibility boundary assessment and WP5 handoff basis. |

## 3. Validation

Main-thread verification repeated the narrow checks:

```bash
python -m py_compile python/rl/runtime/agent_shim.py tests/runtime/test_agent_shim.py
python -m pytest -q tests/runtime/test_agent_shim.py
python -m pytest -q tests/runtime/engagement/test_facade_engagement_evidence_gates.py tests/runtime/facade/test_facade_step_evidence_gates.py
```

Results:

- `tests/runtime/test_agent_shim.py`: `6 passed`.
- WP4-G facade evidence gates: `4 passed`.

## 4. Residual Risks

These do not block WP4 second-wave acceptance, but they must remain visible in
the WP4-F/WP5 handoff:

1. `ObservationBatchPacket` still lacks full WP2.5 snapshot/barrier/source-time
   provenance fields.
2. Reward fact/shaping attribution remains JSON/string shaped, not typed
   `RewardReport`.
3. Termination reason source is not yet typed.
4. `DiagnosticsTrace` remains engagement-piggyback evidence, not a dedicated
   diagnostics facade surface.
5. Direct `sim.*` bans across all policy paths must wait for provenance labels
   and allowlists to mature.

## 5. Handoff Decision

WP4 should now move to `WP4-F Integration And Docs`:

1. integrate first-wave and second-wave accepted findings into the WP4 task
   document;
2. record focused validation commands;
3. mark deferred DTO/runtime metadata items as WP5 or post-WP4 follow-up;
4. prepare a final WP4 acceptance review after integration.
