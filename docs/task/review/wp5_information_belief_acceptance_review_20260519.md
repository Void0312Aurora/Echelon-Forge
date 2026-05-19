# WP5-D Information And Belief Acceptance Review

Status: `2026-05-19` WP5-D acceptance completed.

Scope: information-state labels, agent role metadata, action/coordination
intent compatibility metadata, truth/oracle leakage boundary, and
DecisionBelief deferral.

Related documents:

- [WP5-D information/belief notes](../simulation_architecture/wp5_information_belief_notes_20260519.md)
- [WP5-D dispatch sheet](../simulation_architecture/wp5_information_belief_cluster_20260519.md)
- [WP5 first-wave acceptance review](wp5_first_wave_acceptance_review_20260519.md)

## 1. Acceptance Decision

WP5-D is accepted.

The accepted gate is label-first. It validates current information and belief
boundaries through the passive Python shim without changing policy inference,
runtime behavior, diagnostics/oracle helpers, or smoke-suite membership.

## 2. Accepted Evidence

| Area | Accepted evidence | Decision |
|------|-------------------|----------|
| Shim vocabulary | `tests/runtime/test_agent_shim.py` | Accepted as the maintained information/belief label gate. |
| Truth/oracle boundary | `wp5_information_belief_notes_20260519.md` | `raw_world_truth` and `diagnostics_oracle` remain diagnostics-only, not maintained policy input. |
| Maintained-path allowlist sketch | `wp5_information_belief_notes_20260519.md` | Future direct `sim.*` restrictions must be allowlist based and cannot be global yet. |
| DecisionBelief boundary | `wp5_information_belief_notes_20260519.md` | Belief-layer labeling is testable today; typed DTO enforcement remains deferred. |

## 3. Validation

```bash
python -m pytest -q tests/runtime/test_agent_shim.py
```

Result: `11 passed`.

```bash
python -m py_compile python/rl/runtime/agent_shim.py tests/runtime/test_agent_shim.py
```

Result: passed.

`git diff --check` passed for the WP5-D notes and tests reviewed in the main
thread.

## 4. Handoff

WP5-E may promote `tests/runtime/test_agent_shim.py` as the maintained
information/belief smoke gate. Metadata-dependent checks for typed
`DecisionBelief`, packet provenance, typed reward attribution, and termination
reason-source remain deferred.
