# Naval Domain Surface Split Acceptance Gate

Status: `2026-06-12` gate refresh; `P1-A/P1-B/P2-A/P3-A/P3-B/P4-A`
accepted as slices, but the full subproject is not accepted.

Parent project: [Naval Domain Surface Split](README.md)

## Acceptance Decision

Current decision: `not accepted`.

Reason: the accepted slices now cover inventory, guard tests, action command
surface, a bounded maintained naval observation adapter, the domain-neutral
config alias, and active/eval surface gates. The active codebase still contains
the flat `MissionCommand` compatibility shell and the not-yet-retired global
`PilotAction` carrier / `WorldPilotActionAssignment` transport path.

## Interim Evidence Accepted

`P1-A/P1-B/P2-A/P3-A/P3-B/P4-A` are accepted, but only for the dispatched slices:

- `P1-A` classified active naval path dependencies on `PilotAction`,
  `MissionCommand`, `flight_shaping`, runway/takeoff/formation, gear/ILS,
  the former Python-owned observation fallback, and `WorldPilotActionAssignment` as
  accepted shared infrastructure, compatibility adapters, or blockers.
- `P1-B` added active naval config/eval guards covering `takeoff*` action modes,
  air mission-observation modes, and weapon/fire/damage/kill reward or action
  leakage.
- `P2-A` established the `naval_station_command` action family and marked the
  remaining `PilotAction` path as a compatibility-only transport adapter. It did
  not touch `src/runtime/contracts/**`, so no binding rebuild was required.
- `P3-B` added the domain-neutral `shaping_backend` alias while preserving
  canonical `flight_shaping_backend` compatibility and CLI/canonical override
  precedence.
- `P3-A` bounded `naval_screen_station_v1` as a maintained Python observation
  adapter with `basic` used only as the compiled batch fallback, not the
  policy-visible vector.
- `P4-A` added active/eval `surface_gate` evidence for the action command
  surface, legacy transport adapter, and maintained naval observation adapter.
- Main-thread acceptance commands:

```bash
git diff --check -- docs/task/naval examples/config/training/active/naval \
  gym_envs/universal_env.py gym_envs/universal_env_parts python/env_config.py \
  python/rl/runtime tests/eval/test_evaluation_cli_contracts.py \
  tests/runtime/core/test_env_config.py tests/runtime/naval/test_naval_station_policy_surface.py \
  tests/training/test_naval_training_entry_contracts.py tests/world_batch/test_world_batch_vec_env.py

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q \
  tests/runtime/core/test_env_config.py \
  tests/training/test_naval_training_entry_contracts.py \
  tests/eval/test_evaluation_cli_contracts.py \
  tests/runtime/naval/test_naval_station_policy_surface.py

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q \
  tests/runtime/naval/test_naval_station_policy_surface.py \
  tests/world_batch/test_world_batch_vec_env.py \
  -k "transport_adapter or naval_action_family or naval_station3 or maintained_window"
```

Result: `git diff --check` was clean; pytest reported
`45 passed, 45 subtests passed in 34.50s` and
`13 passed, 74 deselected in 3.44s`. Overall acceptance remains `not accepted`
until `P2-B` command projection evidence is complete.

P3/P4 refresh commands:

```bash
pytest -q tests/runtime/mission/test_mission_obs_taxonomy.py
# 5 passed

pytest -q tests/runtime/naval/test_naval_station_policy_surface.py
# 19 passed

pytest -q tests/eval/test_evaluation_cli_contracts.py -k "NavalStationPolicyEvalTests"
# 8 passed, 5 deselected
```

After this refresh, the observation evidence is complete through the bounded
adapter path. Overall acceptance remains `not accepted` until `P2-B` command
projection is implemented or explicitly held with replacement criteria.

## Required Evidence

This subproject may be accepted only with all of the following evidence:

1. Action/intent ownership:
   active maintained naval entries no longer use `PilotAction` semantics as the
   policy-visible action truth, or any remaining carrier is explicitly documented
   and tested as compatibility-only.
2. Command ownership:
   naval stationing, ROE, assigned-target provenance, and later fire-control
   intent are protected by maintained shared-core and naval-owner projection
   tests, not broad air owner slice behavior.
3. Observation ownership:
   `naval_screen_station_v1` has a maintained packet or a formally bounded
   maintained adapter, and tests prove it does not expose air takeoff, runway,
   gear, ILS, or formation-role semantics as naval policy truth.
4. Config ownership:
   naval entries can use domain-neutral config names for runtime/control backend
   selection while existing air names remain compatible.
5. Regression safety:
   N4 contracts and active naval training-entry gates remain green.
6. Capability boundary:
   weapon release, hit/intercept, damage, kill, fleet C2, and learned-policy
   success remain out of scope unless separate accepted packages cover them.

## Expected Validation

At minimum:

```bash
git diff --check -- docs/task/naval

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q \
  tests/training/test_naval_training_entry_contracts.py \
  tests/training/test_naval_training_entry_contracts.py \
  tests/eval/test_evaluation_cli_contracts.py \
  tests/runtime/naval/test_naval_station_policy_surface.py
```

Additional build, binding, contract, or CLI smoke commands must be recorded if
the implementation touches C++ contracts, nanobind bindings, active configs,
eval tools, or scenario contracts.

## Fail-Closed Rules

- If the implementation still requires `takeoff*` action modes for active naval
  entries, mark failed.
- If the implementation reintroduces air formation/takeoff mission observation
  into active naval policy input, mark failed.
- If the implementation makes weapon/damage reward terms part of N4 acceptance,
  mark failed.
- If the implementation cannot explain every remaining air-first dependency as
  accepted shared infrastructure, compatibility adapter, or blocker, mark
  partial at best.
