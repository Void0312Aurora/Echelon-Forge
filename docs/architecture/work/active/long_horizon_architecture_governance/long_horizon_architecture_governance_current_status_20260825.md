# Long-Horizon Architecture Governance Current Status

Status: `2026-08-25` P0 authority and baseline accepted against `origin/main`
at `82d5b6e893c442950e334eb3e9ec92f8174eeb35` and plan commit
`c668bae91900df4b5488099384c95d9820209de2`. P1 target-architecture decisions
are accepted after independent initial, repair and final-confirmation reviews.
All critical/high and the final medium finding are closed; no review detected
short-term substitution. P3-A is accepted after independent initial/repair/final
review; P2-A/P2-B and P3-B are ready. No runtime code migration is accepted.

Parent subproject: [Long-Horizon Architecture Governance](README.md)

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/long_horizon_architecture_governance/long_horizon_architecture_governance_current_status_20260825.md`
Owner: `cross-domain architecture`
Last verified: `2026-08-25`

## Verification Boundary

This checkpoint inspected the refreshed remote baseline without updating the
dirty primary worktree. The project branch and worktree were created directly
from the commit above.

Evidence commands included:

```powershell
git fetch origin --prune
git grep -n -I "rebuild_world_composition" origin/main -- src python tests
git grep -n -I "runtime_compatibility_quarantine" origin/main -- src python tests
python tools/runners/audit_test_system.py --format markdown --limit 100
$governancePaths = (Get-Content -Raw tests/suites/governance_audit_suite.json | ConvertFrom-Json).paths
python -m pytest -q --confcutdir tests/architecture @governancePaths
gh api repos/Void0312Aurora/Echelon-Forge/pulls/30
gh api repos/Void0312Aurora/Echelon-Forge/pulls/31
gh api repos/Void0312Aurora/Echelon-Forge/actions/runs/32745775275/jobs
```

The numerical measurements below are a dated baseline, not permanent limits.
They must be remeasured before an implementation or acceptance claim.

## What Changed At This Checkpoint

- Created a dedicated branch and worktree from the latest remote baseline.
- Routed the program through the cross-domain architecture owner.
- Established an explicit long-horizon target rather than a cleanup-only plan.
- Split the program into finite architecture, runtime, contract, boundary,
  test/CI, evidence, and acceptance clusters.
- Froze P1-A/B/C lifecycle, artifact-authority and rollout decisions, then
  repaired initial independent findings covering quiescence, failure lifecycle,
  release/state authorities, canonical wire/journal/storage, single canary
  cutover, rollback paths and exact caller/artifact crosswalks.
- Repaired first-review follow-ups with one-CAS initial/replacement/checkpoint-
  recovery publication, explicit terminal shutdown, exact per-path caller
  classification and singular checkpoint fragment/aggregate ownership.
- Persisted the [independent P1 review](../../../reviews/long_horizon_architecture_governance_p1_review_20260825.md)
  and its final content-hash ledger after all findings closed.
- Added independent plan review as a mandatory P0 gate.
- Completed the first independent review. It confirmed the long-horizon target
  was not substituted by short-term cleanup, but found missing fencing/episode
  authority, phase-order, mixed-version rollout, complete RunReceipt,
  forced-control-retirement, and operations/security obligations.
- Reordered contract/public boundary work before host publication and made
  state-transfer/episode authority a hard predecessor to caller cutover.
- Ran the maintained retirement gate and recorded the remote baseline conflict:
  20 tracked owner-archive documents violate a gate that the lifecycle and
  subproject standards currently contradict.
- Completed the first repair review; it closed every original plan finding but
  rejected the remaining double production-cutover ordering and four
  consistency/reproducibility defects. Those were repaired and returned for
  final re-review.
- Completed the final independent repair review. It found no new P0/P1/P2
  finding, no short-term substitution, and passed the plan while keeping P0
  inventories and every P1-P8 implementation obligation open.
- Accepted the reproducible
  [P0 authority inventory](evidence/p0_authority_inventory_20260825.md): nine
  caller surfaces/23 paths, a fresh 25-target MSVC/Ninja graph, the closed
  artifact chain, full control/CI counts, and the 72-document retention scope.
- Implemented and independently accepted P3-A: the build-tree-only
  `ef_runtime_contracts` target, `runtime_contracts::v1` host/incarnation and
  nested epoch-bearing identity values, generated public field lists through
  the existing `dto_schema` registry, final target/install graph evidence, and
  fail-closed negative dependency/schema gates.
- Persisted the [independent P3-A review](../../../reviews/long_horizon_architecture_governance_p3a_review_20260825.md):
  initial `pass_with_repairs`, then final `pass` after two high, four medium,
  one low, and three repair-review findings were closed.

## Observed Baseline

| Surface | Observed fact | Evidence boundary | Long-horizon implication |
| --- | --- | --- | --- |
| Primary checkout | local `main` remained behind the refreshed remote and contained unrelated user changes | read-only primary status plus isolated worktree creation | all implementation must stay in the dedicated worktree until integration is explicitly authorized |
| CI smoke manifest | 124 entries across 85 base files; 67 entries are architecture paths and 28 node IDs come from the runtime escape-hatch test | parsed `tests/smoke/ci_smoke_suite.json` at the verified commit | suite membership is already an architecture product and needs lifecycle ownership |
| Architecture test surface | repository audit reported 735 static architecture test items and 79 architecture Python files flagged as source-scan guards | repository `audit_test_system.py` heuristic | source scans are a material governance mode, but the heuristic alone does not prove each scan is redundant |
| Runtime escape hatch | maintained facade escape-hatch count is zero; one test-only direct `WorldBatchRuntime` construction remains allowlisted | helper inventory and 34 focused facade tests | stable facade rules can migrate toward physical target/package boundaries |
| UniversalEnv compatibility inventory | active caller fixture contains zero entries but remains under active governance | fixture and its focused inventory tests | the repository has at least one completed ratchet without an automatic retirement transition |
| In-kernel rebuild | `SimulationKernel::rebuild_world_composition` has tests and production definitions but no maintained non-test call or Python binding | source grep over current remote tree | in-place rebuild currently lacks a production consumer and must justify survival against host-level replacement |
| Rebuild reachability | raw-world lease acquisition or ordinary world/configuration mutation permanently closes rebuild | `simulation_kernel.cpp` and lifecycle tests | the implemented capability is structurally unavailable after most real use begins |
| Composition evidence | accepted default path binds request, catalog lock, projection, manifests, provenance, parity, and migration closure | runtime composition standard, fixtures, tools, and tests | reproducibility is strong, but derivation inputs and permanent authorities are not yet sharply separated |
| Fresh target graph | current-worktree MSVC/Ninja configure exposes 25 `ef_*` targets; `ef_composition` built in eight steps | fresh ignored build directory, target help, Ninja graph query, and focused build | composition is physically separate, but facade/raw bindings/public DTOs still expose core ownership |
| Closure inventory | existing generator validates nine caller surface groups, 23 caller paths, source truth, artifact joins, and held residuals | closure validation hash plus 69-pass/4-skip composition architecture suite | P1 can use the existing evidence owner without creating a second registry |
| Kernel smoke test | `test_simulation_kernel_smoke.cpp` contains 41 top-level cases across composition, lifecycle, concurrency, commands, spawning, exact stages, and basic runtime behavior | source inspection | failure ownership and migration-test retirement are obscured even when coverage is valuable |
| Numerical regression | the pre-P2-B short trace is explicitly labeled a same-toolchain migration baseline, not general physics correctness | named native test and comments | relocation or retirement needs replacement evidence; it is not proof that semantic tests are absent |
| Latest CI | the verified remote run completed successfully in about 11 minutes; Python smoke was about 38 seconds, while native build and isolated wheel were the dominant steps | GitHub Actions job timestamps | governance simplification is primarily a maintenance and authority concern, not currently the largest CI-time optimization |
| Archive governance | the complete governance manifest produced 53 passes and one failure: `test_archive_retirement.py` lists 20 tracked `docs/architecture/work/archive/**` files while lifecycle/subproject standards prescribe owner-local archives | exact PowerShell manifest expansion above uses `--confcutdir tests/architecture` and does not require local `ef_py`; the failing gate is not among selected CI-smoke nodes | policy, gate, suite placement, current routes, and retention provenance require one reviewed long-term decision rather than ad hoc deletion |
| Complexity history | PR 30 changed 1,373 files and deleted 360,503 lines; PR 31 then added 41,306 lines across 201 files, including real runtime code plus tests, tools, and documents | GitHub PR metadata and merge-parent diffs | episodic cleanup does not provide an endogenous control-retirement model |

## Maturity Matrix

| Area | State | Evidence | Blocker to next state |
| --- | --- | --- | --- |
| P0 project authority | accepted | owner route, isolated worktree, independent plan-review pass, and accepted P0 authority inventory | P1 decisions only; no implementation authority |
| Source/control baseline | accepted | reproducible caller, target/link, artifact, control/CI, and document commands in P0 evidence | remeasure at each decision/implementation acceptance boundary |
| Immutable-kernel/host decision | accepted | P1-A freezes one-CAS bootstrap/replacement/checkpoint recovery, terminal shutdown, final-state fence, active-fault drain, all generations and exact P0 caller crosswalk | P4 implementation remains gated by P3 |
| Host replacement | not implemented | no accepted host contract | P1 state machine plus P3 public contract/plan/rollout foundation |
| Contract consolidation decision | accepted | P1-B classifies artifacts and adds singular plan/release/rollout/checkpoint-fragment/aggregate/receipt authorities, canonical envelope and ledger journal | P3-A then P3-B/P3-C implementation |
| Rollout/operations decision | accepted | P1-C defines one production-canary decision, support rows, checkpoint-recovery/package-restart rollback, SLO/runbook and security gates | P2 measurements plus P3-C implementation |
| Public contract foundation | accepted P3-A | `ef_runtime_contracts` build/install manifests, eight registered public schemas, Windows/MSVC native checks and independent final review | P3-B canonical authority envelopes and P3-C rollout/ledger foundations |
| Physical facade boundary | planned | current facade direction and source guards | CMake/package topology and diagnostics migration design |
| Control lifecycle | planned | completed ratchet examples identified | accepted lifecycle vocabulary, owner model, and renewal/retirement process |
| Test/CI architecture | planned | suite and timing baseline | failure-audience model and replacement evidence for retired scans |
| Evidence/document lifecycle | baseline conflict | policy, gate, suite, and current archive inspected | reconcile retention authority, gate behavior, suite placement, retrieval, and migration |
| Long-horizon acceptance | not eligible | acceptance contract created | P3-P7 implementation plus independent P8 review |

## Required Support-Matrix Decision

P1-C must accept or explicitly revise this minimum long-horizon matrix with
owner and evidence. Removing a row requires a compatibility and user-impact
decision; absence from current CI is not sufficient.

| Dimension | Required planning baseline | Current evidence boundary |
| --- | --- | --- |
| Windows native | Windows AMD64 with MSVC developer environment | historical and current local native build paths exist; not exercised by the latest GitHub workflow |
| Linux native | Linux x86_64 on the maintained compiler/toolchain range | current GitHub `ubuntu-latest` native build and CTest |
| Installed package | isolated wheel behavior on every accepted OS/architecture row | current workflow proves the Linux wheel row only |
| Process topology | in-process native and local Python callers | current accepted composition evidence names the native execution owner; no multi-process host is accepted |
| Node/external host | unsupported and fail-closed until separately admitted | existing composition baseline holds Node and external distribution |
| CUDA canonical execution | unsupported as canonical until separately promoted | CPU exact remains canonical |

## Risk Register

| Risk | Severity | Current evidence | Required long-horizon disposition |
| --- | --- | --- | --- |
| `LHG-01 Permanent migration residue` | high | zero inventories, work-package names, closure fixtures, and source-absence scans remain executable | controls gain explicit retirement or renewal and are removed after structural replacement |
| `LHG-02 Partially dynamic kernel` | high | rebuild machinery exists but is closed by normal use and has no consumer | move replacement to a host boundary or prove identity-preserving in-place demand and full state transfer |
| `LHG-03 Multiple composition authorities` | high | several derivation and evidence artifacts are independently sealed and tested | distinguish build inputs from the singular runtime plan and per-run evidence |
| `LHG-04 Textual boundary fragility` | high | class/member/string scans carry important facade rules | enforce public ownership with include, link, type, package, and runtime boundaries |
| `LHG-05 Evidence retention growth` | medium-high | accepted work carries extensive bilingual review, response, status, queue, cluster, fixture, and generator surfaces | retain normative/current documents in-tree and route historical proof to review/archive/release/CI artifacts with retrieval |
| `LHG-06 Short-term substitution` | critical program risk | cleanup actions are easier to schedule and validate than host, contract, and boundary migration | phase work, but prohibit closure on cleanup-only outcomes |
| `LHG-07 Compatibility regression` | high | raw callers, diagnostics, wheel consumers, batch worlds, and replay/parity contracts span several owners | require caller-class migration maps and evidence before removing compatibility |
| `LHG-08 Governance of governance` | high | a new registry/schema/generator could reproduce the same problem | prefer one owner-readable lifecycle inventory and non-blocking measurements; automation must replace, not add to, existing chains |
| `LHG-09 Unfenced replacement` | high | current facade owns a bare backend pointer and public refs lack incarnation epoch | freeze publication linearization, leases, fencing, drain/reclamation, and stale-ref rejection before cutover |
| `LHG-10 Premature public seam` | high | current kernel accepts JSON and facade DTOs include engine/component headers | land final public-contract target and plan shell before truth-changing host publication |
| `LHG-11 Mixed-version dead end` | high | strict v1 artifacts can fail closed when producer/native/wheel upgrades are misordered | define N/N-1 matrix, single writer, bounded readers, canary/backout, and stored-plan rejection semantics |
| `LHG-12 Incomplete run provenance` | high | current composition evidence does not bind full run inputs and actual executable/package identity | require versioned RunReceipt with exact executable, platform, content, seed, lifecycle, result, and completion identity |
| `LHG-13 Operational adoption gap` | high | no host runbook/SLO/adoption/rollback telemetry or supported process topology gate exists | add operational owner, metrics, platform/topology matrix, and fail-closed multi-process/security activation |
| `LHG-14 Archive authority contradiction` | high | maintained standards prescribe owner-local archive while a maintained governance gate rejects all archive paths and latest remote tracks 20 offenders | choose one retention model, migrate atomically with provenance/retrieval proof, and align policy, subproject template, tests, suites, indexes, and current packages |

## Unknowns

- Whether a future maintained profile truly requires identity-preserving
  in-place replacement rather than host-level reconstruction.
- Whether later profiles require additional generation namespaces beyond the
  frozen host/world/entity/episode/request identities.
- The complete production and diagnostics link graph after generated and
  platform-specific targets are considered.
- Exact last-reader dates and removal evidence for the now-classified
  transitional/derived composition artifacts.
- The historical unique defect yield and false-positive rate of individual
  source-scan and meta-manifest controls.
- Concrete ArtifactLedger backend/provider, measured retention/availability
  budgets and long-term provider-migration route; minimum pre-cutover semantics
  are frozen.
- Exact DTO/schema implementation of the frozen native episode handshake.
- Release-specific N/N-1 producer/native/wheel generations and measured maximum
  rollback window; ordering and irreversible-write semantics are frozen.
- Exact release-qualified Windows/Linux toolchain and Python ABI rows; required
  target families are frozen but not yet proven supported.

Unknowns are P1-P2 evidence obligations. They may change mechanisms and sequence
but do not authorize replacement of the long-horizon target with a smaller
program.

## Recommended Action Order

1. Establish P2-A/P2-B control classification and measurements on disjoint
   governance/diagnostic surfaces.
2. Land P3-B canonical plan/release/state envelopes, then P3-C ledger/rollout
   foundations before any host publication; P3-A is the accepted public DTO
   predecessor for both.
3. Implement the P4 dark/shadow host, episode/state-transfer authority, and
   immutable internal candidate without production caller cutover.
4. Complete P5 plan/RunReceipt/facade-package gates, then execute the only
   production cutover, caller migration, rollback window, and rebuild retirement.
5. Replace test/CI and evidence/document controls only after their structural
   successors exist.
6. Run P8 acceptance and independent review before promoting standards or
   retiring this project through the admitted history route.

## Explicit Overclaim Refusals

- This checkpoint includes an accepted P3-A public-contract implementation, not
  host/runtime migration or overall program acceptance.
- Latest CI success does not validate the proposed architecture.
- Zero production rebuild callers do not by themselves prove safe deletion.
- A smaller source-scan suite does not prove stronger runtime boundaries.
- A consolidated schema does not prove a singular execution owner.
- Completing P0-P3-A does not justify marking the long-horizon program accepted.
- Passing dark/shadow host tests does not authorize caller cutover before epoch,
  state-transfer, episode-authority, rollout, and rollback gates.
