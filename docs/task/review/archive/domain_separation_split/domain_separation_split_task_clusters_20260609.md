# Domain Separation Split Task Clusters

Status: `2026-06-10` finite task-cluster plan and progress ledger for [Domain Separation Split](README.md).

## Boundary Decision

This subproject implements the direct large split from the domain-separation
audit. It does not require Naval to become a demonstration domain first. The
split must preserve existing behavior unless a cluster explicitly records and
validates a behavior change.

Compatibility wrappers were allowed only as migration scaffolding. The direct
split now retires the old public include paths instead of retaining them as
final ownership surfaces. Ground-owned files may be introduced as ownership
shells, but they must not imply full Ground runtime maturity without executable
systems and tests.

## Finite Task Cluster List

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DS-P0-A` | main thread | n/a | Create durable subproject, status, queue, and acceptance surfaces. | `docs/task/review/domain_separation_split/**`, `docs/task/review/README*` | Code split, acceptance claim | Markdown inspection; `git diff --check` | Required files exist and parent review index links them. | First; serial | 1 | pass |
| `DS-P0-B` | diagnostics worker | n/a | Produce current include/type ownership inventory before code edits. | `docs/task/review/domain_separation_split/*current_status*` only | Rewriting audit baseline | `rg` inventory; no code edits | Inventory lists current generic files and target owners. | After DS-P0-A; can run before implementation | 1 | pass |
| `DS-C1-A` | implementation worker | n/a | Split common combat damage structs/helpers from Air/Naval/Ground-specific damage ownership and retire the old public aggregate. | deleted `src/components/combat/damage.h`, `src/components/combat/common/**`, `src/components/domains/air/combat/**`, `src/components/domains/naval/combat/**`, `src/components/domains/ground/combat/**` | Damage model recalibration, new lethality claims | C++ build; architecture include guard | Consumers include common/domain owner headers directly; old aggregate path is absent. | After DS-P0-B; serial with DS-S1-A | 3 | pass |
| `DS-C1-B` | implementation worker | n/a | Split combat weapon component ownership and retire the old public aggregate. | deleted `src/components/combat/weapon.h`, `src/components/combat/common/**`, `src/components/domains/air/combat/**`, `src/components/domains/naval/combat/**`, `src/components/domains/ground/combat/**`, direct include users | Weapon behavior rebalance, ammo schema expansion beyond moved types | C++ build; old-include `rg`; architecture include guard | Naval/Air/Ground weapon-only types live in domain headers; old aggregate path is absent. | After DS-P0-B; can run parallel with DS-C1-A only if files do not overlap | 3 | pass |
| `DS-S1-A` | implementation worker | n/a | Split combat damage ECS systems into common routing plus air/naval/ground update paths and retire the old registrar. | deleted `src/systems/combat/damage_system.h`, `src/systems/combat/*damage*`, `src/core/engine/simulation_kernel_systems.cpp`, focused tests | New damage mechanics, broad effects rewrite | `cmake --build build-workshop --target ef_py -j2`; focused damage/runtime tests | Kernel registers common/air/naval/ground owner systems directly. | After DS-C1-A; serial | 4 | pass |
| `DS-S1-B` | implementation worker | n/a | Finish Air runtime ownership migration and retire old physics/tuning include paths. | `src/systems/domains/air/**`, `src/components/domains/air/platform/**`, deleted old `src/systems/physics/*` Air paths, deleted old `src/components/physics/*` tuning path, source/manual README indexes | Removing unrelated compatibility surfaces outside this audit | C++ build; include-path `rg`; structural guard pytest | Air-only systems and tuning are canonical under `air`; old physics/tuning public paths are absent. | Partial candidate exists; can proceed after DS-P0-A | 2 | pass |
| `DS-S1-C` | implementation worker | n/a | Extract naval underway resupply and other naval platform-system logic from generic platform systems. | `src/systems/systems/logistics_system.h`, `src/systems/domains/naval/**`, registration entry points, focused naval runtime tests | Naval survivability expansion, replenishment realism calibration | C++ build; focused naval tests; architecture guard | Generic logistics no longer owns naval-only ECS system bodies. | After DS-P0-B; avoid overlap with DS-S1-A registration edits | 3 | pass |
| `DS-M1-A` | implementation worker | `gpt-5.4` / high | Add model-layer domain routing for weapon effects. | `src/models/weapons/default_effects_model.cpp`, `src/models/weapons/detail/**`, `src/models/domains/air/**`, `src/models/domains/naval/**`, `src/models/domains/ground/**`, effects interfaces if needed | Lethality recalibration, new public Pk claims | C++ build; focused effects/damage tests | Effects model routes common/air/naval/ground paths without hiding air-only details in generic files. | After DS-C1-A and DS-S1-A public surfaces settle | 4 | pass |
| `DS-M1-B` | implementation worker | `gpt-5.4` / high | Remove direct ship-specific dependency from generic sensor model through a domain adapter/router. | `src/models/systems/default_sensor_model.cpp`, `src/models/domains/naval/**`, sensor interfaces/helpers, focused sensor tests | Sensor fidelity expansion, acoustic model rewrite | C++ build; naval sensor tests; `rg` guard for `ShipPlatform` in generic sensor | Generic sensor model no longer directly owns ship-only state access. | Can run after DS-P0-B; avoid overlap with model interface edits | 3 | pass |
| `DS-T1-A` | test/architecture worker | n/a | Add architecture guards for domain-only type leakage and retired path resurrection. | `tests/architecture/**`, `tests/runtime/**` focused collectors if needed | Full test-suite reorganization | `python -m pytest -q <new guards>`; build smoke | Guards fail on regressions named by this subproject. | Can run after each implementation surface stabilizes | 3 | pass |
| `DS-D1-A` | integration worker | n/a | Sync docs/manual indexes and acceptance evidence. | `docs/manual/**` affected entries, `src/**/README*`, this subproject docs, parent review README | Archive unrelated reviews, claim full domain maturity | Link/path inspection; `git diff --check` | Status and evidence match implementation without overclaim. | Last; serial | 2 | pass |

## Dispatch Rules

- Do not create new Codex conversation sessions or threads for this subproject.
- Every worker packet must map to exactly one cluster above.
- Two workers must not edit the same public header, registration file, normative
  status table, or acceptance line concurrently.
- Component split clusters must land before system/model clusters that depend on
  their public types.
- Acceptance and closure clusters are serial.
- If a cluster exceeds its round cap, stop and re-scope before adding a new wave.
- Follow [Subagent Usage Policy](../../../../standards/governance/subagent_usage_policy.md)
  for any in-thread subagent-style delegation.

## Worker Packet Requirements

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

## Validation Plan

```bash
cmake --build build-workshop --target ef_py -j2
python -m pytest -q tests/architecture/compatibility_quarantine/test_guard_enforcement.py
python -m pytest -q tests/architecture/structural_boundaries
rg -n '#include "systems/physics/(aero_state_system|aerodynamics_system|control_system|propulsion_system)' src tests
rg -n '#include "components/physics/flight_dynamics_tuning' src tests
rg -n '#include "components/combat/(damage|weapon)\.h"|#include "systems/combat/damage_system\.h"' src tests
test ! -e src/components/combat/damage.h
test ! -e src/components/combat/weapon.h
test ! -e src/systems/combat/damage_system.h
git diff --check -- src tests docs/task/review/domain_separation_split docs/task/review/README.md docs/task/review/README.zh.md docs/manual
```

## Acceptance Criteria

- All implementation and validation clusters required by the acceptance document
  are `pass`.
- Focused build and architecture gates pass.
- No domain-split compatibility wrapper is intentionally retained.
- No documentation claims full Air/Naval/Ground maturity from a directory move or
  ownership shell alone.

## Follow-Up Map

Immediate:

- No blocking residual remains for this domain-separation split acceptance gate.
- Naval/Ground effects paths are ownership placeholders only; do not read them
  as full damage-fidelity implementations.

Follow-on:

- Ground movement/sensing/fires/damage runtime implementation packages.
- Calibration and realism upgrades after ownership split is stable.
- Architecture guard maintenance should keep broad binding-surface parsing
  format-aware as `bindings_core.cpp` evolves.

Deferred:

- Broad public capability claims for full domain maturity.
- Training behavior changes not required to preserve split compatibility.
