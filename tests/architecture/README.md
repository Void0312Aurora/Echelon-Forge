# Architecture Tests

`tests/architecture/` holds source, documentation, and governance guardrails. It
is intentionally separate from runtime behavior tests under `tests/runtime/` and
from data-driven contract regressions under `tests/contracts/`.

## Layout

Use one semantic directory level under `tests/architecture/`:

- `build/` — build-system and target wiring readiness.
- `causal_runtime/` — stage manifests, replay/counterfactual envelopes, and worldline metadata.
- `command_tasking/` — command/tasking DTO shell and maintained tasking boundaries.
- `compatibility_quarantine/` — explicitly tolerated legacy escape hatches and allowlists.
- `damage_model/` — damage-model provenance, source admission, release, and retained-artifact gates.
- `governance/` — task, closure, and infrastructure documentation audits.
- `ground/` — ground-domain architecture and realism-release guardrails.
- `platform_spawn/` — typed platform spawn, capability materialization, and setup bridges.
- `policy_execution/` — policy, belief, role, intent, and information-transformation boundaries.
- `runtime_facade/` — facade layering and host-visible runtime DTO contracts.
- `runtime_profiles/` — backend, fidelity, and parity-budget profile contracts.
- `runtime_spine/` — clock-domain, legacy-path, and runtime-spine inventory gates.
- `structural_boundaries/` — broad C++/binding structural split and quarantine guards.

## Naming

File names should start from the architectural invariant, not from the work
package that introduced the check. Prefer names such as
`test_stage_node_manifest_registry.py` or `test_tasking_bridge_retirement.py`
inside the relevant semantic directory.

Keep historical labels such as `WP`, `A2`, or task IDs in test function names,
comments, or task documents when traceability matters. Domain labels such as
`RES`, `TP21`, `BECO`, and `blastfrag` may remain in file names when they are
part of the guarded contract rather than project-management bookkeeping.
