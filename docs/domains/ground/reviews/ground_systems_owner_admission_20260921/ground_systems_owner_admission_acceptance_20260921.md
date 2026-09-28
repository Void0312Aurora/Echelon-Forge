# Ground Systems Owner Admission — Acceptance

Status: `2026-09-21` acceptance record for
[Ground Systems Owner Admission README.md](README.md), written by the `GA-E` cluster.

Parent subproject:
[Ground Systems Owner Admission README.md](README.md).

## Scope

This record accepts the package against the seven criteria in the
[Acceptance Gate](README.md#acceptance-gate) and records the outcome of every command in
the [validation plan](ground_systems_owner_admission_task_clusters_20260921.md).

It does not accept anything the package refused to claim. The refusals are restated
below rather than dropped, because an acceptance record that quietly widens the boundary
is how a capability claim gets made by accident.

## Acceptance Gate Against Evidence

| # | Criterion | Result | Evidence |
| --- | --- | --- | --- |
| 1 | `src/systems/domains/ground/` exists and owns the previously combat-filed damage system | met | [src/systems/domains/ground/](../../../../../src/systems/domains/ground/README.md) holds `damage_system_ground.h`, and no **ground** damage system remains under `src/systems/combat/` — the air, common and naval damage systems stay there and are not this package's |
| 2 | Default composition validates, and the registered ground contribution keeps its id and stage | met, with the count qualified below | `builtin.system.ground_damage` keeps its id, its `ground` domain label and stage `30` ([`system_contribution_registry.cpp`](../../../../../src/core/engine/system_contribution_registry.cpp)); the resolved system count stays 34 |
| 3 | No maintained page calls the route a placeholder, and none claims it works | met | `GA-A`; see the [reconciled declarations](../../standards/specialization_baseline.md) |
| 4 | The `src/systems/combat/` boundary README is true again without being edited | met | `git log cfb9924e..HEAD -- src/systems/combat/README.md` is empty, `cfb9924e` being the merge base with `origin/main`; its prohibition on ground damage runtime ownership is now true because the system is filed elsewhere |
| 5 | The governance guard reflects the admitted owner instead of asserting absence | met | [`test_standards_documentation_governance.py`](../../../../../tests/architecture/governance/test_standards_documentation_governance.py) asserts the directory is present |
| 6 | `DM-G1` has a recorded measurement, and a fix only with its own package | met | [DM-G1 diagnosis](../../../../systems/combat/reviews/ground_damage_reachability_20260921.md); the fix is deliberately not taken here |
| 7 | Ground and architecture suites pass with no new failures | met, with the carried failures enumerated below | see [Validation](#validation) |

**Qualification on criterion 2.** The relocation changed neither contribution count. The
*component* count is 85, having moved from 83 earlier on this branch in `10945ffc` when
`GroundPlatformDamageState` and `NavalCommandIntent` were registered. That change is not
this package's and is not claimed by it. Stating "unchanged counts" without this
qualification would be false at the package boundary.

## Validation

Run on the Windows MSVC host at the revision carrying this record. The plan's commands
are given in the [cluster table](ground_systems_owner_admission_task_clusters_20260921.md).

| Command | Outcome |
| --- | --- |
| `cmo_python -m pytest -q tests/architecture/governance` | `3 failed, 169 passed, 1 xfailed` — the three carried failures below and the same three node ids as the branch baseline, no arrivals. The pass count is seven above the baseline because seven tests were added since: the two-language phase-table guard, the review-log round-count guard, the review-kind guard, and four census-enumeration tests. It is recorded at the revision carrying this record. It moves when a guard is added, and also when a document is added without its census refresh — the latter being a failure rather than a pass. It is not repinned on unrelated page edits, which is the treadmill that got `links_checked` removed from the rows below |
| `cmo_python -m pytest -q tests/architecture/composition` | `72 passed, 1 skipped` |
| `cmo_python -m pytest -q tests/runtime/ground tests/architecture/ground` | `20 passed, 4 xfailed` |
| `cmo_python -m pytest -q tests/architecture/structural_boundaries` | `2 failed, 14 passed` — the two carried boundary failures below |
| `cmo_python tools/maintenance/document_link_audit.py` | `documents_checked: 200`, `issues: 0` — this selection covers four of the five documents this change edits; see the scope limit below |
| `cmo_python tools/maintenance/document_link_audit.py --full-tree` | `documents_checked: 828`, `issues: 71`, **none under a ground path** — this row also covers the Chinese mirror the default selection leaves out |
| `cmo_python tools/maintenance/translate_docs_batch.py audit` | `pair_count: 74`, `diverged: 0` |
| `runtime_profile_projection_contract.py check` | exit 0 |
| `runtime_composition_evidence_contract.py check` | exit 0 |
| `runtime_composition_migration_closure.py validate` | exit 0 |
| `runtime_host_batch_parity_contract.py validate` | exit 0 |
| `npm test` in `packages/cordis-runtime` | `20 passed, 0 failed` |

These rows carry the document counts and the issue counts, and they deliberately omit
`links_checked`. That figure moves whenever any page anywhere in the tree gains or loses a
link, and three successive revisions of this record recorded it wrongly for that reason. The
document count shows the audit ran over a large surface rather than a filtered one, and
`issues: 0` is the claim that matters; a number that every later edit invalidates was
contributing noise rather than evidence.

### Scope Limits On This Evidence

Two limits are recorded rather than left for a reader to discover:

- `document_link_audit.py` selects through `select_documents`. The default selection
  contains `modularization_plan.md`, the package `README.md`, this record and the status
  page, and it **excludes `README.zh.md`** — which is why the `--full-tree` row carries the
  wider claim. A round measured zero issues in every edited document, in a ground path, and
  in the Chinese mirror, so the conclusion holds. An earlier revision of this note said the
  selection excluded every edited document; a re-measurement showed that to be false, and it
  is corrected rather than left standing.
- `translate_docs_batch.py audit` covers the 74 registered bilingual pairs, and this
  package's `README` pair is not among them — the registry holds
  `docs/domains/ground/README`, `minimal_task_structure` and `specialization_baseline`
  only. Its `diverged: 0` therefore cannot see the pair this change edited, and that
  pair's parity is asserted by reading both files rather than by the tool.

## Failures Carried Forward, Not Silently

Five failures are open and none of them arrives with this package. Each was reproduced on
a tree that does not contain this work, which is the claim that matters. The commit
attribution is weaker than it looks and is stated as such: `9d9c8aae`, `13c73a10` and
`33f54dfd` are the commits that installed or last touched the guards, not necessarily the
ones that introduced each defect. A round checked the underlying history and found the
diagnostics scripts and the archived documents arriving in later commits than those. The
attribution is therefore recorded as the guards' provenance, not as a causal claim.

- `test_archive_retirement::test_no_tracked_document_lives_under_a_retired_archive_path` —
  twenty documents under `docs/architecture/work/archive/`, and the guard hardcodes a
  retirement date of `2026-08-13`;
- `test_docs_information_architecture::test_owner_local_work_and_reviews_declare_minimum_metadata` —
  `docs/systems/effects/reviews/continuous_rod_component_load_admission_20260914/README.md`
  declares no `Document kind:`;
- `test_tools_script_governance::test_diagnostics_top_level_sprawl_never_grows` — fifteen
  `kill_chain_*` scripts;
- two binding-quarantine boundaries under `tests/architecture/structural_boundaries/`.

"Passes" is therefore not the criterion this package is accepted on, and
"introduces nothing new" is. The acceptance rests on the empty difference, not on a green
suite.

## Transferred Ownership: Composition Registry Sync

This package reported a defect it does not own, and the transfer is named rather than
implied. While pursuing `DM-G1` the package found that the composition evidence chain
disagreed with the component registry: `10945ffc` registered two components and updated
the requested and resolved manifests, then left every derived surface at the previous
census.

That debt is owned by
[runtime_composition_registry_sync.md](../../../../architecture/work/issues/runtime_composition_registry_sync.md)
and has been repaired there. None of its surfaces — the Cordis bundle pins, the package
descriptor pin, the producer-sealed provenance, the host/batch parity evidence and its
semantic reference, the migration closure, and the projection tool — lie inside this
package's write set. Widening the write set to reach them would have made a domain package
the owner of a cross-domain composition concern, which is what
[modularization_plan.md](../../../../architecture/work/issues/modularization_plan.md)
exists to prevent.

Accepting this package does not accept that debt, and it does not accept that the
composition suite is green because of anything done here. At `b74e100a`, the revision this
acceptance was measured on, the suite reported nine errors and eight failures. A round
measured `10 failed, 50 passed, 4 skipped, 9 errors` at the earlier `31ced82f` and
recorded it as unconfirmed rather than as a contradiction, because its baseline worktree
resolved a native build directory from the HEAD worktree. The two figures belong to
different revisions and both states are red, which is the point: this package reports that
state and does not repair it.

## Refused Claims

- **Ground damage is not a capability, and this package does not make it one.** The
  per-tick system matching spawned ground entities does not mean the mechanism works. At
  review time the effects route was still unreachable; it became reachable on
  `2026-09-22`, and this refusal is unchanged either way — reachability is a mechanism
  property, and the repair package claims no capability from it.
- **"Only the effects route is affected" holds for the routes measured** and for the
  static include graph. Its universality is unverified.
- **The retired `docs/task/ground/` plan is provenance, not current authority.** It has no
  retrieval address in the archive ledger; that belongs to documentation governance.
- **No facade-visibility promotion for Ground.** Nothing here changes what the facade
  exposes.

## Open Residuals

Lifecycle note `2026-09-22`: the entries below are the residual set **as of this
acceptance**. The `DM-G1` item and the `xfail`-marker item are discharged by the
[Ground Damage Effects Route Repair](../../work/active/ground_damage_effects_route_repair/README.md)
package, which landed on that date; the readings are kept as the record of what was open
then. The capability refusal above and the held areas below are unchanged.

- `DM-G1` remains open with a located and narrowed cause: the factory and registration
  units resolve `GroundPlatformDamageState` to component `94`, the effects unit resolves a
  duplicate `105`, so only the effects route is unreachable. Choosing the fix is a
  separate package; the candidates are resolving the component once in the composition
  path and passing the id down, or having the effects route look it up by name.
- The four `xfail(strict=True)` nodes stay until that fix lands. They are not CI smoke
  material, and the unmarked monotonicity test in the same file can pass through the
  placeholder fallback; both are evidence-honesty items for the fix package.
- The `P2` stage node is a separate tasking-side package: the only stage Ground claims has
  no registered node.
- Movement, terrain, sensing, and fires stay held until their own packages name the
  declarations the architecture standard requires.
- The refusal and residual set now lives in four maintained copies: the package `README`
  residuals, this record's refused claims and open residuals, the status page's residual
  register and overclaim refusals, and the cluster table's residual map. The closure gate
  mandates the restatement, so the copies stay, but they are the drift surface this
  package has had to repair twice and a later round should treat them as one claim.

## Acceptance Statement

The seven gate criteria are met against the evidence above, with criterion 2 qualified and
criterion 7 resting on an unchanged failure set rather than a green suite. The package is
accepted on those terms.

The status cells this outcome implies were withheld until a round authorised them, and
round 10 did. `GA-E` is `pass`; phases `P5`, `P0` and `P1` carry `accepted (round 10)`.
`P3` and `P4` carry `accepted (via round 5's GA-B/GA-C authorisation)` and the owner
directory carries `admitted (via round 5's GA-B authorisation)` — those annotations name
the derivation rather than reading as if the round voted on those cells, because round 5
authorised the `GA-B` and `GA-C` promotions those cells report.

Promotion on authorisation is the discipline this package adopted, and the
[Review Log](ground_systems_owner_admission_current_status_20260921.md) is where that
authorisation is recorded; round 10's sentence is quoted there verbatim. The sequence is
worth keeping in view: a first revision of this record promoted those cells before any
round had seen it, which is the same gap round 4 objected to. A round caught it, the
promotions were withdrawn to pending, and they were landed in the same change as the
authorising row rather than before it.
