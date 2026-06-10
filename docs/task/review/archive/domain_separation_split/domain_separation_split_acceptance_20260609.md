# Domain Separation Split Acceptance Gate

Status: `2026-06-10` accepted evidence ledger; old domain-split compatibility entry points are retired and broad architecture guards validate.

Parent: [Domain Separation Split](README.md)

## Acceptance Decision

Overall subproject status: `accepted`.

Reason: the named implementation clusters through DS-M1-B have focused pass
evidence, and the old public compatibility paths are no longer intentionally
retained. The no-compatibility-entry slice validates, and the previously held
broad architecture residual has been closed by updating the binding-surface
guard to parse current multi-line bindings and the current explicit allowlist.

## Required Gates

| Gate | Required evidence | Current status |
| --- | --- | --- |
| `G0 Subproject Surface` | README, task clusters, current status, dispatch queue, acceptance, archive, and parent index links exist. | pass |
| `G1 Component Ownership` | `damage.h` and `weapon.h` are retired public entry points; consumers include common/domain-owned headers directly. | pass |
| `G2 System Ownership` | `damage_system.h`, air runtime systems, naval logistics, and propulsion readouts are split from misleading generic owners. | pass |
| `G3 Model Ownership` | Effects and sensor default models route through common/domain adapters instead of directly hiding Air/Naval-only logic in generic files. | pass |
| `G4 Compatibility` | No domain-split compatibility include path is intentionally retained; retired paths are guarded against recreation. | pass |
| `G5 Focused Validation` | Focused C++ build, runtime tests, retired-include search, and architecture guards pass. | pass |
| `G6 Documentation` | `docs/task/review`, `docs/manual`, and affected source README files match the implemented ownership. | pass |
| `G7 Claim Boundary` | Ground shells and directory moves do not imply full domain maturity. | pass |
| `G8 Broad Architecture Residual` | Unrelated broad architecture baselines are either fixed or explicitly held outside this domain split. | pass |

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
| `2026-06-09` | DS-C1-A | Common/air/naval/ground damage owner headers added. Initial migration used a public umbrella, now retired by the 2026-06-10 cleanup. | pass | Consumers must include owner headers directly. |
| `2026-06-09` | DS-C1-B | Common/air/naval/ground weapon owner headers added. Initial migration used a public umbrella, now retired by the 2026-06-10 cleanup. | pass | Consumers must include owner headers directly. |
| `2026-06-09` | DS-S1-A | Common/air/naval/ground damage system headers added. Initial migration used a registrar umbrella, now retired by the 2026-06-10 cleanup. | pass | Kernel registration calls owner registrars directly. |
| `2026-06-09` | DS-S1-B | Air systems include `damage_air.h` directly; old physics/tuning include paths are now deleted rather than retained as wrappers. | pass | Kernel includes Air system owners directly. |
| `2026-06-10` | DS-S1-C | `NavalUnderwayResupply` moved from generic logistics to `src/systems/domains/naval/naval_logistics_system.h`; kernel registration updated after common logistics; focused naval underway tests and scoped diff check passed. | pass | Generic logistics now uses `components/physics/propulsion_readouts.h` for propulsion readouts. |
| `2026-06-10` | DS-M1-A | `default_effects_model.cpp` now routes through `default_effects_domain_routing_detail.inc`; Air consequence logic is in `src/models/domains/air/default_effects_air_domain.h`; Naval/Ground placeholder owner paths exist; focused structural/effects tests passed. | pass | Naval/Ground effects paths are placeholders only. |
| `2026-06-10` | DS-M1-B | `default_sensor_model.cpp` no longer directly includes or reads `ShipPlatform`; ship-specific maritime reads are in `src/models/domains/naval/naval_sensor_maritime_adapter.h`; focused naval sensor tests passed. | pass | `default_acoustic_model.cpp` ship access is outside this sensor-routing packet. |
| `2026-06-10` | DS-T1-A | Added `test_domain_separation_split_generic_files_route_domain_owned_runtime`; selector `python -m pytest -q tests/architecture/structural_boundaries/test_structural_guardrails.py -k "domain_separation_split or structured_air_effects"` passed. | pass | Retired path guard is focused on this split. |
| `2026-06-10` | DS-T1-A | Structural guard updated to fail if retired domain-split public paths are recreated or old include strings return in maintained source files; refreshed focused selector passed. | pass | Retired include search over `src src/tests` returned no matches. |
| `2026-06-10` | DS-T1-B | `tests/architecture/structural_boundaries/test_structural_guardrails.py` binding parser now handles multi-line `.def(...)` bindings, de-duplicates overload names, and explicitly allowlists `debug_get_ground_contact_state`. | pass | Full `tests/architecture/structural_boundaries` passes. |
| `2026-06-10` | DS-D1-A | Source README indexes and this task surface were updated to match the no-compatibility-entry implementation. | pass | `git diff --check` on scoped paths passed. |

## Actual Validation Run

```bash
cmake --build build-workshop --target ef_py -j2
python -m pytest -q tests/runtime/naval/test_naval_ship_database.py -k "underway_replenishment"
python -m pytest -q tests/runtime/naval/test_naval_sensor_realism_runtime.py
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py -k "dfm_p4 or component_damage"
python -m pytest -q tests/architecture/structural_boundaries/test_structural_guardrails.py -k "domain_separation_split or structured_air_effects"
python -m pytest -q tests/architecture/compatibility_quarantine/test_guard_enforcement.py
python -m pytest -q tests/architecture/structural_boundaries
git diff --check -- src tests docs/task/review/domain_separation_split docs/task/review/README.md docs/task/review/README.zh.md docs/manual
```

Outcomes in this checkout:

- `cmake --build build-workshop --target ef_py -j2`: pass.
- `test_naval_ship_database.py -k "underway_replenishment"`: 2 passed, 20 deselected.
- `test_naval_sensor_realism_runtime.py`: 5 passed.
- `test_weapon_guidance_realism_guards.py -k "dfm_p4 or component_damage"`: 8 passed, 170 deselected.
- `test_structural_guardrails.py -k "domain_separation_split or structured_air_effects"`: 2 passed, 16 deselected.
- `test_guard_enforcement.py`: 15 passed.
- `tests/architecture/structural_boundaries`: 18 passed.
- Retired include search over `src src/tests`: no matches.
- Retired path existence check: no retired file exists.
- Scoped `git diff --check`: pass.

The current checkout validates against `build-workshop`.

The previous broad architecture residual is closed in this slice: compatibility
quarantine and structural-boundary guards both pass after the binding-surface
guard was refreshed for the current `bindings_core.cpp` formatting and explicit
debug allowlist.

## Retired Paths And Residuals

Retired domain-split public paths:

- `src/components/combat/damage.h`
- `src/components/combat/weapon.h`
- `src/systems/combat/damage_system.h`
- `src/components/physics/flight_dynamics_tuning.h`
- `src/systems/physics/aero_state_system.h`
- `src/systems/physics/aerodynamics_system.h`
- `src/systems/physics/control_system.h`
- `src/systems/physics/propulsion_system.h`
- `src/models/weapons/detail/default_effects_air_platform_resolution_detail.inc`

Non-blocking follow-up boundaries:

- Naval/Ground effects paths and Ground damage/weapon shells remain ownership
  placeholders, not full domain capability claims.

## Acceptance Outcome Template

```md
status: accepted | partial | held | rejected
accepted clusters:
held clusters:
commands/outcomes:
compatibility wrappers retained: none for this domain-split package
claim boundaries:
next package:
```
