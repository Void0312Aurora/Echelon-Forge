# Domain Separation Split Acceptance Gate

Status: `2026-06-10` integration evidence ledger; implementation clusters have landed, but the subproject is not accepted.

Parent: [Domain Separation Split](README.md)

## Acceptance Decision

Overall subproject status: `partial / not accepted`.

Reason: the named implementation clusters through DS-M1-B have focused pass
evidence, but final acceptance is held by residual Air propulsion helper
dependency policy and broader architecture gates that currently fail on
existing/unrelated surfaces.

## Required Gates

| Gate | Required evidence | Current status |
| --- | --- | --- |
| `G0 Subproject Surface` | README, task clusters, current status, dispatch queue, acceptance, archive, and parent index links exist. | pass |
| `G1 Component Ownership` | `damage.h` and `weapon.h` are split into common/domain-owned headers or compatibility wrappers with explicit retention reasons. | pass |
| `G2 System Ownership` | `damage_system.h`, air runtime systems, and naval logistics are split from misleading generic owners. | partial |
| `G3 Model Ownership` | Effects and sensor default models route through common/domain adapters instead of directly hiding Air/Naval-only logic in generic files. | pass |
| `G4 Compatibility` | Existing public include paths that remain are wrappers only, with documented retention/deprecation reasons. | partial |
| `G5 Validation` | Focused C++ build, runtime tests, and architecture guards pass. | partial |
| `G6 Documentation` | `docs/task/review`, `docs/manual`, and affected source README files match the implemented ownership. | partial |
| `G7 Claim Boundary` | Ground shells and directory moves do not imply full domain maturity. | pass |

## Minimum Validation Commands

```bash
cmake --build build-workshop --target ef_py -j2
python -m pytest -q tests/architecture/compatibility_quarantine/test_guard_enforcement.py
python -m pytest -q tests/architecture/structural_boundaries
python -m pytest -q tests/runtime/naval
python -m pytest -q tests/runtime/air_combat
git diff --check -- src tests docs/task/review/domain_separation_split docs/task/review/README.md docs/task/review/README.zh.md docs/manual
```

Runtime test selectors may be narrowed per cluster, but final acceptance must
record which selectors were run and why any broader selector was held.

## Forbidden Acceptance Shortcuts

- Do not accept the subproject because directories exist.
- Do not accept an implementation cluster if the generic file still owns the
  domain-only behavior and merely includes a renamed header.
- Do not convert Ground placeholders into a full Ground capability claim.
- Do not hide behavior drift behind architecture cleanup; record the first
  failing stage and either fix or hold it.
- Do not count unrelated dirty worktree changes as evidence for this subproject.

## Evidence Ledger

| Date | Cluster | Evidence | Result | Notes |
| --- | --- | --- | --- | --- |
| `2026-06-09` | DS-P0-A | Subproject file set and parent review index links created; `git diff --check` on docs scope passed. | pass | Implementation gates pending. |
| `2026-06-09` | DS-P0-B | Inventory added to current status from read-only `rg` / file inspection; `git diff --check` on current-status files passed. | pass | Diagnostic only; no implementation accepted. |
| `2026-06-09` | DS-C1-A | `damage.h` reduced to compatibility umbrella; common/air/naval/ground damage owner headers added; combined `ef_py` build and component diff checks passed. | pass | System split still pending. |
| `2026-06-09` | DS-C1-B | `weapon.h` reduced to compatibility umbrella; common/air/naval/ground weapon owner headers added; combined `ef_py` build and component diff checks passed. | pass | Direct include migration remains later work. |
| `2026-06-09` | DS-S1-A | `damage_system.h` reduced to compatibility umbrella; common/air/naval/ground damage system headers added; combined `ef_py`, include search, and diff checks passed. | pass | G2 remains partial until naval logistics split. |
| `2026-06-09` | DS-S1-B | Air systems include `damage_air.h` directly; old physics/tuning paths remain include-only wrappers; combined `ef_py`, include search, and diff checks passed. | pass | Logistics Air fuel-flow helper dependency remains. |
| `2026-06-10` | DS-S1-C | `NavalUnderwayResupply` moved from generic logistics to `src/systems/naval/naval_logistics_system.h`; kernel registration updated after common logistics; `cmake --build build-local-win --target ef_py -j2`, focused naval underway tests, and scoped diff check passed. | pass | Air propulsion helper dependency remains outside naval extraction. |
| `2026-06-10` | DS-M1-A | `default_effects_model.cpp` now routes through `default_effects_domain_routing_detail.inc`; Air consequence logic is in `src/models/air/default_effects_air_domain.h`; Naval/Ground placeholder owner paths exist; focused structural/effects tests passed. | pass | Naval/Ground effects paths are placeholders only. |
| `2026-06-10` | DS-M1-B | `default_sensor_model.cpp` no longer directly includes or reads `ShipPlatform`; ship-specific maritime reads are in `src/models/naval/naval_sensor_maritime_adapter.h`; focused naval sensor tests passed. | pass | `default_acoustic_model.cpp` ship access is outside this sensor-routing packet. |
| `2026-06-10` | DS-T1-A | Added `test_domain_separation_split_generic_files_route_domain_owned_runtime`; selector `python -m pytest -q tests/architecture/structural_boundaries/test_structural_guardrails.py -k "domain_separation_split or structured_air_effects"` passed. | partial | Full architecture files still fail on unrelated direct-sim allowlists, binding-count assertions, and Windows snippet linking. |
| `2026-06-10` | DS-D1-A | Source model/naval README indexes and this task surface were updated to match the implemented ownership and residuals. | partial | Final accepted status is held until G2/G4/G5 residuals close or are explicitly retained. |

## Actual Validation Run

```bash
cmake --build build-local-win --target ef_py -j2
python -m pytest -q tests/runtime/naval/test_naval_ship_database.py -k "underway_replenishment"
python -m pytest -q tests/runtime/naval/test_naval_sensor_realism_runtime.py
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py -k "dfm_p4 or component_damage"
python -m pytest -q tests/architecture/structural_boundaries/test_structural_guardrails.py -k "domain_separation_split or structured_air_effects"
git diff --check -- src tests docs/task/review/domain_separation_split docs/task/review/README.md docs/task/review/README.zh.md docs/manual
```

The documented `build-workshop` directory does not exist in this checkout; the
usable local build tree is `build-local-win`.

Broader architecture attempts were held as residual evidence rather than
acceptance failures for this slice:

- `python -m pytest -q tests/architecture/compatibility_quarantine/test_guard_enforcement.py`
  fails on existing direct-sim allowlist hits and Windows snippet link failures
  against flecs socket symbols.
- `python -m pytest -q tests/architecture/structural_boundaries` fails on
  existing `bindings_core` allowlist/count assertions unrelated to this domain
  split.

## Retained Compatibility And Residuals

- `src/components/combat/damage.h`, `src/components/combat/weapon.h`, and
  `src/systems/combat/damage_system.h` remain compatibility umbrellas.
- Old `systems/physics/*` air-system headers and
  `components/physics/flight_dynamics_tuning.h` remain include-only wrappers.
- `src/models/weapons/detail/default_effects_air_platform_resolution_detail.inc`
  remains a compatibility bridge to the Air-owned effects helper.
- Generic physics/logistics files still consume Air propulsion helper state;
  this requires a named adapter or explicit retained-dependency decision before
  subproject acceptance.

## Acceptance Outcome Template

```md
status: accepted | partial | held | rejected
accepted clusters:
held clusters:
commands/outcomes:
compatibility wrappers retained:
claim boundaries:
next package:
```
