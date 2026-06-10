# Ground Bootstrap Plan Acceptance

Status: `2026-06-05` accepted and archived for
`ground_domain_bootstrap_plan_20260521`.

## Accepted Scope

This accepts the bootstrap planning lane, not route movement or full ground
runtime behavior. The plan's success criteria are satisfied because the current
ground records now give stable answers for:

- third-domain placement: `services/army` remains the service-profile boundary,
  while `ground/` is the execution-specialization lane;
- first maintained scope: G0/G1 tasking, static status, static command metadata,
  and native schema identity;
- together-required surfaces: standards, task profile dispatch, content seed,
  contracts, scenario smoke fixtures, native schema evidence, owner-slice DTOs,
  Python bindings, and no private ground runtime path;
- deferred boundaries: route movement, terrain, sensing, fires, damage, combat,
  observation export, and full ground runtime behavior;
- G0 commitments before G1: naming, aliases, platoon-centered starter scope,
  first task family, capability-composition direction, cadence assumptions, and
  information-state boundaries.

## Evidence

- [Ground current progress](../ground_current_progress_20260524.md) records the
  accepted G0-G6-E state and the `2026-06-05` static command-authoring update.
- [Ground dispatch queue](../ground_subagent_dispatch_queue_20260521.md) records
  accepted G0-G6-E packages and keeps route movement held for a later release
  vote.
- Focused validation recorded in the progress tracker includes `ef_py` build,
  domain-shell guard tests, mission-command round-trips, native ground schema
  tests, ground scenario tests, profile semantics, and lifecycle bridge tests.
- Closeout verification on `2026-06-05`:

```bash
cmake --build build-workshop --target ef_py -j2
# [100%] Built target ef_py

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/architecture/command_tasking/test_dto_domain_shell_guard.py tests/runtime/mission/test_mission_command_ground_fields_roundtrip.py tests/runtime/ground/test_ground_native_platform_schema.py tests/runtime/ground/test_ground_mvp_scenario.py tests/runtime/ground/test_ground_realism_gradient_mvp_scenarios.py tests/leader/test_tasking_profile_contracts.py tests/runtime/mission/test_ground_runtime_lifecycle_bridge.py
# 40 passed

git diff --check
# clean
```

## Residuals

- `G2 route move implementation` remains held until a later G6-D3/G6-F
  route-move release vote consumes the accepted G6-E2/E3 native schema evidence
  and names movement evidence gates.
- This acceptance does not release terrain-aware movement, sensing, fires,
  damage, combat, observation export, a learned ground policy, ground action
  space, rewards, curriculum, or evaluation suite.

## Index Sync

- The bootstrap plan was moved to
  [ground_domain_bootstrap_plan_20260521.md](ground_domain_bootstrap_plan_20260521.md).
- No active-path copy is retained under `docs/task/ground/`.
- The parent ground README and progress tracker now point to the archived
  accepted baseline.
- New work must open a fresh follow-on package rather than editing the archived
  bootstrap plan.
