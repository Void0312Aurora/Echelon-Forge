# Domain Separation Split Acceptance Gate

Status: `2026-06-09` initial gate definition; no implementation cluster is accepted yet.

Parent: [Domain Separation Split](README.md)

## Acceptance Decision

Overall subproject status: `not accepted`.

Reason: only the durable execution surface has been created. The primary
ownership hotspots named by the audit still require implementation clusters and
validation evidence.

## Required Gates

| Gate | Required evidence | Current status |
| --- | --- | --- |
| `G0 Subproject Surface` | README, task clusters, current status, dispatch queue, acceptance, archive, and parent index links exist. | pass |
| `G1 Component Ownership` | `damage.h` and `weapon.h` are split into common/domain-owned headers or compatibility wrappers with explicit retention reasons. | pass |
| `G2 System Ownership` | `damage_system.h`, air runtime systems, and naval logistics are split from misleading generic owners. | partial |
| `G3 Model Ownership` | Effects and sensor default models route through common/domain adapters instead of directly hiding Air/Naval-only logic in generic files. | pending |
| `G4 Compatibility` | Existing public include paths that remain are wrappers only, with documented retention/deprecation reasons. | pending |
| `G5 Validation` | Focused C++ build, runtime tests, and architecture guards pass. | pending |
| `G6 Documentation` | `docs/task/review`, `docs/manual`, and affected source README files match the implemented ownership. | pending |
| `G7 Claim Boundary` | Ground shells and directory moves do not imply full domain maturity. | pending |

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
