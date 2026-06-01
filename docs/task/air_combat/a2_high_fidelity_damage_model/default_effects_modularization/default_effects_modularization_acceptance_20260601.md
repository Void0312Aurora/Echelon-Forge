# Default Effects Modularization Acceptance

Status: `2026-06-01 accepted round-1 DFM-P4/DFM-P5 fixture hardening`.

Subproject:

- [README.md](README.md)
- [Task clusters](default_effects_modularization_task_clusters_20260601.md)
- [Current status](default_effects_modularization_current_status_20260601.md)

## Accepted Scope

This acceptance records only the first `DFM-P4` / `DFM-P5` round:

- Four runtime regression fixtures were added for default-effects helper
  modularization:
  - direct component hit;
  - direct protected-system fallback;
  - broad spatial near miss;
  - non-broad component-limited near miss.
- The guard collector imports and includes the new mixin.
- Lovelace's read-only diagnostics packet was accepted; the integration pass
  avoided over-pinning exact random samples and exact broad projected-hitbox
  counts.

This does not mark the whole subproject closed. `DFM-P3` remains partial and
`DFM-P6` remains planned.

## Validation

```bash
CMO_BUILD_DIR=/home/void0312/Workshop/CMO/build python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py -k dfm_p4
# 4 passed, 150 deselected in 0.38s

CMO_BUILD_DIR=/home/void0312/Workshop/CMO/build python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
# 154 passed in 33.71s
```

## Evidence Artifacts

- [default_effects_modularization.py](../../../../../tests/runtime/air_combat/weapon_guidance_realism/default_effects_modularization.py)
- [test_weapon_guidance_realism_guards.py](../../../../../tests/runtime/air_combat/test_weapon_guidance_realism_guards.py)
- Ohm worker packet: `019e83ce-25d8-7170-82c0-b3c856cea1d3`
- Lovelace diagnostics packet: `019e83ce-b49b-7773-a449-71e916f89d7f`

## Residuals

- Structured air-platform loss/destruct early-return remains held because the
  available convenience helpers make a destroyed target path brittle and
  cumulative.
- `DFM-P3` consequence-block splitting remains frozen until the accepted
  fixtures are present on the branch.
- Project-wide C++ unit-test framework adoption remains deferred.

## Forbidden Claims

- Do not state that A2 high-fidelity damage modeling is fully mature.
- Do not state that Pk, deterministic fuze behavior, or industrial admission has
  been released.
- Do not state that these fixtures prove formula correctness or evidence
  authority; they only pin route shape and event fields for the modularized
  default effects model.

## Index Sync

- [README.md](README.md) links this acceptance record.
- [README.zh.md](README.zh.md) links this acceptance record.
- [Current status](default_effects_modularization_current_status_20260601.md)
  reflects round-1 acceptance.
