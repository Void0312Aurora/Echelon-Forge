# Naval Domain Surface Split Acceptance Gate

Status: `2026-06-01` gate defined; `P1-A/P1-B` accepted as the first slice,
but the full subproject is not accepted.

Parent project: [Naval Domain Surface Split](README.md)

## Acceptance Decision

Current decision: `not accepted`.

Reason: the first slice has completed inventory and guard tests, but the active
codebase still contains known compatibility adapters and blockers on the
maintained naval path: neutral `PilotAction` transport, flat `MissionCommand`
compatibility shell, Python-owned naval mission observation fallback, and
air-labeled environment backend knobs.

## Interim Evidence Accepted

`P1-A/P1-B` are accepted, but only for the first slice:

- `P1-A` classified active naval path dependencies on `PilotAction`,
  `MissionCommand`, `flight_shaping`, runway/takeoff/formation, gear/ILS,
  Python-owned observation fallback, and `WorldPilotActionAssignment` as
  accepted shared infrastructure, compatibility adapters, or blockers.
- `P1-B` added active naval config/eval guards covering `takeoff*` action modes,
  air mission-observation modes, and weapon/fire/damage/kill reward or action
  leakage.
- Main-thread acceptance commands:

```bash
git diff --check -- docs/task/naval tests/training tests/eval

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q \
  tests/training/test_naval_active_training_entries.py \
  tests/training/test_naval_n4_closure_gate.py \
  tests/eval/test_eval_naval_n4_baseline.py \
  tests/runtime/naval/test_naval_n4_reward_surface.py
```

Result: `git diff --check` was clean; pytest reported
`39 passed, 48 subtests passed in 35.66s`. Overall acceptance remains
`not accepted` until action, command, observation, and config ownership evidence
is complete.

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
  tests/training/test_naval_active_training_entries.py \
  tests/training/test_naval_n4_closure_gate.py \
  tests/eval/test_eval_naval_n4_baseline.py \
  tests/runtime/naval/test_naval_n4_reward_surface.py
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
