# Ground Systems Owner Admission Task Clusters

Status: `2026-09-21` finite task-cluster plan for
[Ground Systems Owner Admission README.md](README.md).

Parent subproject:
[Ground Systems Owner Admission](README.md).

## Boundary Decision

This package may move an already-registered ground runtime system to a
ground-owned directory and reconcile the pages that describe it. It may not
create ground behavior that does not exist, may not make the ground damage route
reachable, and may not claim any ground combat capability.

Two decisions are fixed here because they are otherwise easy to reopen by
accident:

1. `src/systems/combat/README.md` is not edited. Relocating the file satisfies
   its prohibition; widening the prohibition to legalize the code would convert
   an ownership boundary into an allowlist change.
2. The registered contribution keeps its id (`builtin.system.ground_damage`),
   its stage (30), and its `domain` label (`ground`). The move changes an include
   path and a file location, nothing else.

## Finite Task Cluster List

| Cluster | Owner | Capability tier / model ID / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `GA-A` | main thread | n/a | Reconcile the Ground-owned pages with the shipped code, separating ownership from capability. | `docs/domains/ground/standards/specialization_baseline.md`, `docs/domains/ground/standards/specialization_baseline.zh.md`, `docs/domains/ground/README.md`, `docs/domains/ground/README.zh.md`, plus the generated bilingual cluster registry refresh for those two pairs | no capability promotion; no movement, sensing, fires, or terrain claims; no P2 node text | `cmo_python tools/maintenance/document_link_audit.py`; `cmo_python -m pytest -q tests/architecture/governance -p no:cacheprovider` | No Ground-owned page calls the route a placeholder, and none claims it works. Three independent rounds raised nine findings (`F1`-`F6`, `N1`-`N3`) and all are closed. The listed commands must show no failure beyond the branch-point baseline: the governance suite is red for three reasons unrelated to Ground, so "passes" is not the criterion and "introduces nothing new" is. The third round raised one further blocking finding outside this write set (a source comment that kept the retracted reading) and authorised promotion on the grounds that both earlier objections are resolved. | parallel with `GA-D` | 3 (raised from 2: one round was consumed by a fix applied to the wrong file) | pass |
| `GA-B` | main thread | n/a | Admit `src/systems/domains/ground/` and relocate the damage system into it. | `src/systems/domains/ground/README.md`, `src/systems/domains/ground/damage_system_ground.h`, `src/systems/combat/damage_system_ground.h` (deleted), `src/core/engine/system_contribution_registry.cpp` (include only), `src/systems/domains/README.md`, `src/systems/domains/README.zh.md` | no new system, no coefficient change, no behavior change, no combat README edit | `cmo_python -m pytest -q tests/architecture/composition -p no:cacheprovider`; `cmo_python -m pytest -q tests/runtime/ground tests/architecture/ground -p no:cacheprovider` | Directory exists; composition validates with unchanged contribution counts; ground suites match their pre-move result. Met: the directory exists, the composition suite reports the same failure set as the pre-move baseline (`ba0b408f` run in a temporary worktree), and the ground suites are unchanged at `20 passed, 4 xfailed`. | after `GA-A` | 2 | pass |
| `GA-C` | main thread | n/a | Update the guards and plan text that encode the pre-move state, and the two guards left stale by this branch's earlier registration change. | `tests/architecture/governance/test_standards_documentation_governance.py`, `docs/architecture/work/issues/modularization_plan.md` (proposal only), `tests/architecture/composition/test_simulation_composition_contract.py` (two stale component-count assertions), `tests/architecture/structural_boundaries/test_domain_separation_boundaries.py` (one stale gate regex) | no weakening of unrelated assertions; no new guard file; no widening of required strings to empty placeholders; no behaviour change in the code the guards read | `cmo_python -m pytest -q tests/architecture/governance -p no:cacheprovider`; `cmo_python -m pytest -q tests/architecture/structural_boundaries -p no:cacheprovider`; composition on the host that has `jsonschema` | The guard asserts the admitted owner instead of absence, the plan names the Ground systems owner, and no guard still encodes a superseded count or flag name. | after `GA-B` | 2 | pass |
| `GA-D` | main thread | n/a | Measure `DM-G1`: locate where the component disappears between the spawn write and the first reader. | `src/models/core/default_unit_factory.h`, `src/models/domains/ground/default_effects_ground_domain.h`, `src/systems/combat/damage_system_ground.h` (probe lines only; removed before closure), `docs/systems/combat/reviews/ground_damage_reachability_20260921.md` | no predicate relaxation, no behavior fix, no test-marker change, no new file | single-test-scoped run of `tests/runtime/ground/test_ground_damage_response.py` with probes; the probe lines are deleted before the cluster closes | A measurement names the cause, with the same entity and generation reported by writer and reader. Met, then narrowed by review: the factory and registration units resolve the component to id `94` and the effects unit resolves a duplicate `105`, so only the effects route is unreachable and the per-tick system does match. The probes are gone, `git status -- src` is empty, and the ground suites match their pre-measurement result (`20 passed, 4 xfailed`). The fourth round confirmed the source-comment fix and reported no blocking finding, so the measurement is promoted. | parallel with `GA-A`; independent of `GA-B` | 2 | pass |
| `GA-E` | main thread | n/a | Run the acceptance gate and record outcomes. | `docs/domains/ground/reviews/ground_systems_owner_admission_20260921/ground_systems_owner_admission_acceptance_20260921.md` (written under `work/active/`, moved here by the retirement this package's Archive clause requires), `ground_systems_owner_admission_current_status_20260921.md`, `README.md` and `README.zh.md` (status cells and the passages that contradict them), `docs/domains/ground/README.md` and `README.zh.md` (the owner page's absence claim), this table (own status cell and write set), `tests/architecture/governance/document_tier_census_baseline.json` (refreshed in the same change as the added record) | no acceptance without the named commands; no silent carry-over of a failing gate | all commands in the validation plan | Acceptance record lists scope, commands, outcomes, open residuals, and refused claims. | after `GA-A`..`GA-D`; serial, never parallel | 1 | pass |

### Write Set Widening

`GA-E` opened with a single-file write set, because on paper "run the acceptance gate and
record outcomes" produces one new document. Reading the surfaces it has to report on
showed that the plan described a package state that no longer exists: the status page
still called the owner directory `held` and asserted the governance guard checks for its
absence, still listed `GA-B` and `GA-C` as unstarted, and still recommended them as the
next actions, while the `README` phases `P0` through `P4` were still `active` or
`planned`. An acceptance record written on top of a status page that contradicts it would
have produced a package disagreeing with itself.

The write set therefore widened to the status page, the `README` pair, and this table.
Recording the new document also changed the tier census, so that baseline is refreshed in
the same change and named here rather than left out.

A later round showed the widening was still one surface short. The package's own pages
were corrected and the **domain owner's** page was not: `docs/domains/ground/README.md`
kept the claim that no ground runtime-system owner exists, eight lines below the bullet
pointing at the admitted system. The owner `README` pair belongs to this write set, and
the guard that asserts the directory is present now also asserts that the retired absence
sentence is gone.

The widening is recorded here rather than applied silently.

## Dispatch Rules

- Every worker packet must map to exactly one cluster above.
- Each cluster's write set lists its work product. The package's own `README.md`,
  `README.zh.md`, and the status cells in this cluster table are updated by
  whichever cluster last changed the recorded state, so they are not repeated in
  every row.
- Do not allow two workers to edit the same normative table, scenario contract,
  public API, or status line concurrently. `GA-A` and `GA-C` both touch
  governance-visible text and must not run together.
- Keep acceptance and closure clusters serial.
- If a cluster exceeds its round cap, stop and re-scope before adding a follow-up
  wave.
- Follow [Subagent Usage Policy](../../../../engineering/automation/standards/subagent_usage_policy.md).

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
source tools/maintenance/cmo_env.sh
cmo_python -m pytest -q tests/architecture/governance -p no:cacheprovider
cmo_python -m pytest -q tests/architecture/composition -p no:cacheprovider
cmo_python -m pytest -q tests/runtime/ground tests/architecture/ground -p no:cacheprovider
cmo_python tools/maintenance/document_link_audit.py
cmo_python tools/maintenance/translate_docs_batch.py audit --root docs \
  --registry docs/engineering/documentation/reference/bilingual_document_clusters.json
```

`tests/architecture/composition` requires `jsonschema` in the active
interpreter; run it with the maintained environment helper rather than a bare
interpreter.

## Acceptance Criteria

- `src/systems/domains/ground/` exists and owns the relocated damage system.
- The default composition validates with unchanged component and system
  contribution counts, the same contribution id, and the same stage.
- No maintained page describes the ground damage route as a placeholder, and no
  maintained page claims it works.
- `src/systems/combat/README.md` is true again and was not edited.
- The governance guard asserts the admitted owner rather than the absence.
- `DM-G1` has a recorded measurement; a fix exists only if it arrived with its own
  package.
- No new test file was created.

## Residual Map

Immediate:

- `DM-G1` stays open; this package measures it and stops.
- The unmarked monotonicity test in `tests/runtime/ground/test_ground_damage_response.py`
  can pass through the placeholder fallback and is therefore weak evidence.

Follow-on:

- a `DM-G1` fix package, if the measurement names a bounded cause;
- a `ground_p2_stage_node` package on the tasking side, which needs its own
  declarations before the Ground surface has a registered node for its only
  claimed stage;
- an archive-ledger registration for the retired `docs/task/ground/` records,
  owned by documentation governance and blocked on the registry's hardcoded
  retirement date.

Deferred:

- ground movement, route following, terrain, sensing, fires, logistics, and
  observation export;
- any facade-visibility promotion for Ground;
- ground counterfactual participation, which depends on the WP21-B
  snapshot/restore boundary.
