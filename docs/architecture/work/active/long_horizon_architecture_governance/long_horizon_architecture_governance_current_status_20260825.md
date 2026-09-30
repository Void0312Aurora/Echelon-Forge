# Long-Horizon Architecture Governance Current Status

Status: `2026-09-28` P0 authority and baseline accepted against `origin/main`
at `82d5b6e893c442950e334eb3e9ec92f8174eeb35` and plan commit
`c668bae91900df4b5488099384c95d9820209de2`. P1 target-architecture decisions
are accepted after independent initial, repair and final-confirmation reviews.
All critical/high and the final medium finding are closed; no review detected
short-term substitution. P3-A, P3-B and the non-production P3-C ledger and
compatibility foundation, plus P4-A's dark/shadow host lifecycle candidate, are
accepted after independent adversarial, repair and final-confirmation reviews.
The P4-B dark/shadow state-transfer candidate also passed independent review;
the first P4-C build-tree/internal kernel/world-batch candidate seam and its
specified candidate verification are accepted after independent review.
P5-A now has an independently reviewed closed execution-plan contract accepted
for the current in-process default CPU-exact supported topology. P5-B now has
an independently reviewed durable ArtifactLedger/RunReceipt qualification
accepted for the same bounded local single-process topology. P5-C facade-only
package qualification is accepted for the tested Windows/MSVC CPython 3.12
row. P5-D now has an executable local single-process RolloutDecision admission
slice, an ArtifactLedger-backed durable rollout controller/snapshot reader, a
first maintained contract-caller migration slice, and a mandatory
release/RunReceipt binding at the local release-controller and production
adapter boundaries. The first operations telemetry, real process/package
rollback drill, and three-cycle supported-row SLO/adoption measurement are
also executable and pass their local targets. A real admission-bound facade
VecEnv reset/step canary check now passes on the tested local row. The durable
rollout path now exercises the complete local lifecycle through `stable` and
verifies rollback retention at that state. A long-lived local adapter now
rechecks the durable `adoption-expanding → rollback-window → stable` sequence
and fails closed after a subsequent kill switch. A separate fail-closed rebuild
retirement gate is implemented. By explicit project-owner decision, P5-D is accepted for main-plan continuation and the old production rebuild authority is retired; only the native test/fault-injection seam remains. Production caller cutover is represented by the bounded local caller path;
representative release cadence and production rollback-window operation are
post-acceptance governance probes. The
rebuild-unreachability guard now records zero maintained production callers and
zero Python binding references while keeping the native method explicitly
production authority retired. P2-A now has an implemented manifest-level
lifecycle baseline, and P2-B has an accepted repeatable local sustainability
baseline. Broader topology qualification and production publication remain
fail-closed or post-acceptance probes; bounded P6-P8 local work is accepted. P6-A now has an owner/lane
  metadata and derived-orphan-audit baseline covering 115 architecture tests.
  P6-B now has a maintained
five-lane declaration and workflow/job/CTest selector audit baseline;
  local repeated-run evidence is now recorded; hosted CI/resource/flake
  evidence and source-scan trend are post-acceptance probes.
  P7-A now has a maintained retention authority baseline that reconciles the
  owner-local Cordis archive with the Git-ledger route; P7-B local cleanup and
  restore checks are accepted. External provider drills are post-acceptance
  probes, and the bounded P8 acceptance is recorded.

Parent subproject: [Long-Horizon Architecture Governance](README.md)

Current P4-B remediation entry point: [P4-B remediation route](p4b_remediation_route_20260830.md).
This subordinate route does not replace this status document, the task-cluster
plan, dispatch queue, or acceptance contract.

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/long_horizon_architecture_governance/long_horizon_architecture_governance_current_status_20260825.md`
Owner: `cross-domain architecture`
Last verified: `2026-09-28`

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
- Implemented and independently accepted P3-B authority envelopes: one schema
  owner, typed plan/release/rollout/checkpoint shells, explicit one-way legacy
  adapter provenance binding, Cordis/native consumers, exact canonical vectors,
  and fail-closed owner/compatibility checks. P3-B review found no unresolved
  Critical/High finding and no short-term substitution.
- Implemented and independently accepted P3-C's non-production ArtifactLedger
  and compatibility foundation: content-addressed artifacts, role/media ACLs,
  fenced slots and writers, journals/checkpoints/snapshot validation, exact
  N/N-1 plan/checkpoint/package readers, durable qualification/kill/backout
  recovery, and fail-closed production authorization. The final
  [P3-C review](../../../reviews/long_horizon_architecture_governance_p3c_review_20260827.md)
  found no unresolved Critical/High/Medium blocker after the durable
  kill-to-backout restart repair.
- Implemented and independently accepted P4-A's dark/shadow host lifecycle:
  one-CAS initial/replacement/recovery publication and unpublish, host/object
  fencing, bounded candidate deadlines, cancellation/quarantine/reclamation,
  jointly linearized leases and results, terminal shutdown, timeout CAS-loss
  retry, reentrant injector safety and orphan ownership. The final
  [P4-A review](../../../reviews/long_horizon_architecture_governance_p4a_review_20260827.md)
  passed with no unresolved Critical/High/Medium finding.
- Implemented a P4-B dark/shadow candidate: native episode coordinator and
  barrier, source/target owner registry separation, typed owner artifacts,
  source-census equality, host-issued single-use owner handles bound to
  admission intent, statusful import transaction phases with bounded
  commit/abort/recovery and explicit ambiguity, host-owned native control,
  N/N-1 normalization, multi-world fail-closed behavior, strict unknown-field
  rejection, and explicit CI native/mirror lanes. The fixed twelve-owner
  registry now has real candidate adapters for ECS truth, delayed/command
  subsets, episode reward/termination, Python cache rederive, CPU backend
  rehydrate policy, and host-fenced in-flight drain in addition to
  composition/RNG/clock, explicit external-effect rejection, and telemetry
  reset policy. A real host replacement test commits all twelve rows and
  reopens the target WAL to recover the terminal composite transaction. P4-B
  implementation and independent integrated review are complete for the
  dark/shadow candidate; production/P5 qualification remains open. See [P4-B candidate snapshot]
  (p4b_state_transfer_candidate_20260830.md) and the maintained [owner adapter
  inventory](p4b_owner_adapter_inventory_20260830.md).

- Implemented and independently reviewed P5-A's closed execution-plan contract
  for the current in-process default CPU-exact topology. The generated plan
  binds request, catalog lock, profile projection, backend request, requested
  and resolved manifests, and the unique admitted backend owner. Python and
  Cordis emit identical canonical bytes; native admission rejects stale or
  resealed owner joins; the default native constructor now admits the closed
  plan before extracting its compatibility manifest. Evidence and residuals
  are recorded in [P5-A resolved execution-plan evidence]
  (p5a_resolved_execution_plan_20260919.md). P5-B durable ledger/RunReceipt is
  accepted for the bounded local single-process topology; P5-C facade-only
  packaging is accepted for the tested Windows/MSVC row; P5-D local integration
  and bounded P6-P8 closure are recorded, while wider activation remains
  outside scope.

- Implemented the first P5-D maintained contract-caller migration slice. The
  loader command-chain, route-generator, comm, and kernel contract callers now
  use the facade-owned batch adapter and scenario-loader proxy. The native
  facade exposes the bounded command-link and communication-query surfaces
  required by the migrated contracts, with generated DTO schema coverage and
  explicit CUDA unsupported-path rejection. Focused architecture and
  migrated-contract gates pass. The randomized route-origin and leader-fixture
  parity residuals were repaired and their focused contracts pass; the full
  unit batch still reports unrelated legacy flight-model rows and an explicit
  skip for an unavailable historical frozen-model artifact. See [P5-D caller
  migration evidence](evidence/p5d_facade_caller_migration_20260923.md). This
  is not production cutover or P5-D acceptance.

- Migrated the standalone native `src/main.cpp` caller to `RuntimeFacade`.
  `ef_app` now loads the example scenario, applies facade-owned batch setup,
  steps, and queries observations without constructing the raw
  `SimulationKernel`; its Debug build and 60-tick runtime smoke returned exit
  code `0`. The P8-A closure inventory consequently removes `src/main.cpp`
  from native default-kernel callers. This is a local maintained smoke path,
  not production caller cutover.

- Retired the last maintained native default `SimulationKernel()` construction
  in `WorldBatchRuntime`; it now passes the generated
  `kDefaultResolvedExecutionPlanJson` explicitly. The closure inventory reports
  zero native default constructors and one explicit generated-plan caller.
  The Debug build, `ef_app` runtime smoke, closure validator, and 13-test
  closure gate pass. This is explicit-plan hygiene, not production cutover.

- Added the P5-D process-lifetime admission recheck. A maintained production
  adapter now reloads the durable rollout slot before setup, command/launch
  mutation, stepping, and runtime-window execution; a kill switch or typed
  backout therefore closes an already-running process before its next
  truth-changing action. The focused gate and adapter tests pass. See
  [P5-D process-resync evidence]
  (evidence/p5d_process_restart_admission_resync_20260923.md). This remains a
  local admission safeguard, not package rollback or production cutover.

- Revalidated the admission-bound P5-D canary against the current local Release
  binding on 2026-09-25: the two real facade VecEnv canary tests passed in
  16.99 seconds, and the real process/package rollback drill passed in 13.87
  seconds. These are refreshed local supported-row checks, not production
  publication or production rollback-window evidence.

- Made release/RunReceipt binding mandatory for production-state commits and
  for `RuntimeFacadeAdapter(require_production_admission=True)`. Canonical
  release-manifest and receipt bytes are checked against the admitted release,
  plan, decision, package, and wheel identities before the slot or production
  caller is accepted; receipt completion must be durably acknowledged. Added a
  secret-free telemetry/SLO projection and explicit prerequisite checks for
  same-release checkpoint recovery and stop/restart package rollback. The
  focused binding, admission, facade, caller, and operations gates pass. See
  [P5-D production binding and operations evidence]
  (evidence/p5d_production_binding_operations_20260923.md). This initial
  operations slice precedes the SQLite controller integration recorded below;
  the real process/package drill and measured multi-run SLO/adoption evidence
  are recorded in the follow-up packets below. Local rollback retention and
  rebuild retirement are recorded; production observation is post-acceptance.

- Added the first ArtifactLedger-backed rollout controller on the qualified
  local SQLite backend. Release, decision, receipt, and evidence blobs now
  enter one durable transaction with decision/evidence CAS slots; restart
  reads revalidate the complete authority graph, and a kill switch closes the
  evidence slot without rewriting the signed decision. The maintained facade
  can consume the durable snapshot and recheck it before mutation. The
  durable test now covers the complete local state graph through `stable` and
  verifies the storage-side rollback retention classes at that point. See
  [P5-D SQLite rollout controller evidence]
  (evidence/p5d_sqlite_rollout_controller_20260923.md). This remains a local
  controller integration, not a production cutover.

- Added the separate P5-D rebuild-retirement gate. It requires a fresh
  zero-caller inventory, a matching durable `stable` admission and retention
  check, and an exact production cutover/adoption/rollback attestation before
  producing a production-authority-only retirement proof. The gate is
  read-only and retains the native test capability; its positive test now also
  consumes the actual durable SQLite `stable` admission/retention projection.
  The gate also binds attested adoption/rollback digests to the retained
  rollout-evidence digest, cross-checks the four retention digests against the
  admission projection, and checks admission/evidence version equality. It does not claim that
  production authority has been retired. See [P5-D
  rebuild retirement gate evidence](evidence/p5d_rebuild_retirement_gate_20260924.md).

- Started P6-A's test-authority migration baseline. The two architecture tier
  manifests and the two CI runner manifests now declare owner, failure
  audience, and execution strategy; a
  derived non-authoritative audit rejects stale, missing, duplicate, and
  cross-tier assignments while preserving the existing source-scan residual
  signal. It also caught and restored the previously unlisted P5-D retirement
  gate test. Native CTest now exposes primary lane labels for all 25 entries;
  native registry and platform-capability source-scan replacements move exact
  field/vocabulary checks into compiled probes, reducing the residual
  source-scan count from 88 to 86. The focused P6-A
  authority/manifest/lifecycle/replacement set passes 31 tests and the CTest
  label check passes 3 tests. The five-lane P6-B declaration maps fast,
  qualification, nightly, release, and research to existing workflow jobs with
  explicit runner, timeout, build/test parallelism, failure audience, declared
  labels, and actual workflow-selected CTest labels; its focused lane/CTest
  checks pass 8 tests, and the 17-test local
  selector subset passed three fresh consecutive repeats (33.638 s, 32.626 s,
  33.577 s) on 2026-09-27. This is repeatable local declaration behavior; hosted CI
  resource/flake or branch-protection evidence is a post-acceptance probe.
  A read-only GitHub check on 2026-09-25 found `main` unprotected and no
  repository rulesets; hosted control-plane evidence is recorded as not-run for
  the bounded acceptance.
  See [P6-A test-authority audit evidence]
  (evidence/p6a_test_authority_audit_20260924.md). P6-A replacement and
  retirement decisions, repeated P6-B CI evidence, and P7 archive-specific
  work are covered by the bounded local baseline. See [P6-B CI lane evidence]
  (evidence/p6b_ci_lane_manifest_20260924.md).

- Implemented the P7-A retention authority baseline; see the [P7-A retention
  evidence packet](evidence/p7a_retention_authority_20260924.md). The machine-readable
  `retention_authority.json` now makes Git history plus owner ledgers the
  default retired-document route, explicitly registers the already accepted
  Cordis owner-local archive, and requires ArtifactLedger-backed evidence
  manifests to carry restore, access, backup, provider, and provider-migration
  fields. The lifecycle standard and Chinese companion, archive gate, and
  governance suite are bound to that authority; the initial focused
  retention/archive baseline passed **11 tests**, while the current revalidation
  passes 42. Local retention and routing are accepted; external provider
  restore is a post-acceptance probe.

- Completed the first P7-B cleanup slice. The zero-entry UniversalEnv
  compatibility inventory, its fixture, and its dedicated architecture test
  were removed after the maintained facade/VecEnv successor gates passed 39
  focused tests. The historical survival table remains as provenance, while
  `test_runtime_escape_hatches.py` and
  `test_scenario_setup_facade_boundary.py` reject new raw compatibility
  opt-ins. At that initial slice the derived authority inventory covered 113
  architecture tests, 113 manifest entries, and 86 source-scan residuals; the
  refreshed derived report covers 115/115/88 (113 files with source-scan
  references). Remaining provider/restore work is post-acceptance governance.

- Completed a second P7-B cleanup slice. The superseded
  `archive_retirement_transition` lifecycle registration was removed after
  P7-A's retention authority, archive gate, repository indexes, and Git-ledger
  restore route were verified. The executable archive-retirement gate remains
  in the governance suite. Its focused retention/archive/lifecycle/manifest/
  link set passes **42 tests**; external provider restore and migration/source-
  scan trends are post-acceptance governance.

- Added a bounded P7-B local SQLite restore drill. The supported local ledger
  now persists a fenced checkpoint alongside the release/rollout/RunReceipt
  chain, restores the backup into a distinct root, and revalidates retention
  classes plus checkpoint release/decision identity. The initial focused
  runtime-host file passed **7 tests** and the current file passes 8; this is
  local provider evidence; external provider restore and production
  rollback-window operation are post-acceptance probes. See
  [the local restore packet](evidence/p7b_local_sqlite_restore_drill_20260924.md).

- Revalidated the current P7 evidence on 2026-09-25: the focused
  retention/archive set passed **42 tests**, the SQLite admission/restore file
  passed **8 tests**, and the complete governance suite passed **79 tests**.
  The retention checks now also build and validate an in-memory,
  provider-neutral manifest projection from the actual local SQLite stable
  projection, including digest, restore, access, backup, provider, and
  migration fields; the digest is revalidated after a distinct-root SQLite
  restore. The manifest is also persisted as a separate `evidence-short`
  ArtifactLedger blob and re-read after restore. These are the local results
  used by bounded acceptance; external provider restore and production
  rollback-window operation are post-acceptance probes.

- Established the P8-A derived acceptance matrix at
  `evidence/p8_acceptance_matrix_20260924.json`. It enumerates all six P8
  contract requirements, five platform/process rows, owner and residual
  evidence, and records the bounded decision `accepted`; unsupported
  multi-process, external-host, and CUDA-canonical rows are explicitly
  fail-closed. The matrix validator and manifest checks pass 17 tests.

- The P8-A local acceptance baseline is recorded in [the P8-A evidence
  packet](evidence/p8_acceptance_baseline_20260924.md): the full governance
  suite now passes **79 tests**, including the corrected P2-B baseline and
  candidate teardown/state-transfer lanes. Representative cadence, provider
  restore drills, and P8-B review are not blockers under the revised scope.
  P5-D owner acceptance and production rebuild-authority retirement are
  recorded separately. The current derived authority report covers 115 architecture tests
  and 115 manifest entries after the P5-D retirement gate was restored and the
  P8 matrix validator was added; the P6-A/P7-B counts above remain historical
  snapshots of those earlier batches.

- Executed the first real local process/package rollback drill. Two existing
  Windows CPython 3.12 `ef_py` build outputs were loaded by separate child
  processes; the current process read the SQLite production-canary snapshot
  through `RuntimeFacadeAdapter`, verified the signed release/RunReceipt
  binding, and constructed `RuntimeFacade` only after admission. The durable
  kill switch stopped it, and a typed backout restarted the rollback build with
  a new boot identity and epoch. See [P5-D real process/package rollback
  evidence](evidence/p5d_real_process_package_rollback_20260923.md). The
  child now verifies the imported binding path plus RunReceipt package/wheel
  digests and rejects a mismatched build before readiness; the backout process
  remains evidence-bound but non-authoritative. This closes the local
  admitted-process drill prerequisite; production-canary
  publication is outside the bounded acceptance; local rollback retention and
  rebuild retirement are recorded.

- Extended the local rollback evidence with a long-lived adapter recheck. The
  same signed release was advanced through `adoption-expanding`,
  `rollback-window`, and `stable` while the adapter remained alive; each
  durable refresh stayed production-authorized, and a subsequent kill switch
  was rejected before the next mutation. The SQLite admission file now passes
  **8 tests**. This closes the local rollback-window recheck slice; production
  rollback-window operation is a post-acceptance probe.

- Repeated the supported-row process path for three cycles using the current
  and rollback Windows CPython 3.12 builds. All three replacements, drains,
  crash receipts, backouts, artifact reads, and caller-adoption observations
  passed the initial P1-C targets; maximum replacement startup was 1.0988426 s
  and maximum backout recovery was 1.1253792 s. See [P5-D supported-row
  measurement evidence](evidence/p5d_supported_row_measurement_20260923.md).
  This is the local measurement baseline used by bounded acceptance; longer
  cadence/sample-size sustainability and production observation are monitored
  after acceptance.

- Attached lifecycle metadata to the four existing smoke and architecture
  suite manifests. The current metadata covers six controls: five permanent
  and one migratory, with owners, invariants, expiry, successors, bounded
  renewal fields, removal proof, and coverage paths. The architecture tier
  partition now lists every current architecture test file exactly once; the
  P2-A validator and manifest checks pass 15 focused tests after the P7-B
  retirement. See [P2-A control lifecycle
  inventory evidence](evidence/p2_control_lifecycle_inventory_20260923.md).
  This is the accepted local implementation baseline; longer measurements are
  post-acceptance governance and no new independent review is required.

- Re-ran the P2-B sustainability baseline on 2026-09-25. Four check groups ran
  three times (12/12 passed, 0 healthy-sample failures) and the supported row
  completed three replacement/backout cycles with 3/3 SLO runs passing. The
  latest sample observed a 1.4249537 s maximum replacement startup, 1.4229253
  s maximum backout recovery, 6/6 resource snapshots, 47,042,560-byte maximum
  peak working set, and 135 maximum handles. See [P2-B sustainability
  baseline evidence](evidence/p2b_sustainability_baseline_20260923.md). This
  is a local Windows baseline; representative cadence and long-term resource
  budgets are post-acceptance monitoring items.

- Extended the supported-row process measurement with real child-process
  working-set and handle observations. The latest three-cycle sample had 6/6
  available resource snapshots, a maximum peak working set of 47,042,560
  bytes, and a maximum peak handle count of 135. These are observation-only
  values; no long-term resource budget or leak verdict has been accepted.

- Made the P2-B release cadence sample explicit: each supported-row report
  carries release ID and plan digest, and the aggregate records observed
  current/rollback package pairs. Three logical release IDs in the dated
  baseline all used one plan digest and one package pair, so its status is
  `local_repeat_only`. This is the local short-cycle baseline; representative
  cadence is a post-acceptance monitoring item.

- Added a real cadence follow-up using the accepted P5-A plan digest and four
  separate two-cycle child-process batches. All batches passed the initial SLOs
  and kept a consistent package pair; the fourth batch used the reverse build
  pair, so the classifier now reports
  `distinct_package_batches_observed` (four release IDs, one plan digest, three
  package pairs). This is sufficient for the bounded local evidence. See [P2-B release cadence follow-up evidence]
  (evidence/p2b_release_cadence_followup_20260924.md).

- Added the P5-D rebuild-unreachability inventory and guard. The live tree has
  only the native declaration/implementation and test-only smoke calls for
  `SimulationKernel::rebuild_world_composition`; maintained production callers
  and Python binding references are zero. The production package guard remains
  facade-only, and the inventory explicitly refuses to assert retirement before
  the unique cutover and rollback-window gate. See [P5-D rebuild
  unreachability evidence](evidence/p5d_rebuild_unreachability_20260923.md).
- Added the real admission-bound facade VecEnv canary check. File-backed and
  durable SQLite-snapshot cases validate `WorldBatchVecEnv` reset/step with
  signed rollout admission, release/RunReceipt/package binding, and the native
  `RuntimeFacade` mutation path; this remains a canary-path result rather than
  production publication.
  See [P5-D facade VecEnv canary evidence](evidence/p5d_facade_vecenv_canary_20260923.md).

## Observed Baseline

| Surface | Observed fact | Evidence boundary | Long-horizon implication |
| --- | --- | --- | --- |
| Primary checkout | local `main` remained behind the refreshed remote and contained unrelated user changes | read-only primary status plus isolated worktree creation | all implementation must stay in the dedicated worktree until integration is explicitly authorized |
| CI smoke manifest | 124 entries across 85 base files; 67 entries are architecture paths and 28 node IDs come from the runtime escape-hatch test | parsed `tests/smoke/ci_smoke_suite.json` at the verified commit | suite membership is already an architecture product and needs lifecycle ownership |
| Architecture test surface | repository audit reported 735 static architecture test items and 79 architecture Python files flagged as source-scan guards | repository `audit_test_system.py` heuristic | source scans are a material governance mode, but the heuristic alone does not prove each scan is redundant |
| Runtime escape hatch | maintained facade escape-hatch count is zero; one test-only direct `WorldBatchRuntime` construction remains allowlisted | helper inventory and 34 focused facade tests | stable facade rules can migrate toward physical target/package boundaries |
| UniversalEnv compatibility inventory | zero-entry inventory retired in P7-B after successor facade/VecEnv boundary gates passed | historical survival table plus `test_runtime_escape_hatches.py` and `test_scenario_setup_facade_boundary.py` | new raw compatibility opt-ins fail through maintained structural boundary checks; no active inventory remains |
| In-kernel rebuild | `SimulationKernel::rebuild_world_composition` is private; maintained production-call and Python-binding inventories are zero; the test-only accessor remains for rollback/fault-injection coverage | executable [P5-D rebuild-unreachability inventory](evidence/p5d_rebuild_unreachability_20260923.md) and [owner acceptance/retirement packet](evidence/p5d_owner_acceptance_and_rebuild_retirement_20260927.md) | production authority retired by explicit project-owner decision; native test capability retained |
| Rebuild reachability | raw-world lease acquisition or ordinary world/configuration mutation permanently closes rebuild | `simulation_kernel.cpp` and lifecycle tests | the implemented capability is structurally unavailable after most real use begins |
| Composition evidence | accepted default path binds request, catalog lock, projection, manifests, provenance, parity, and migration closure | runtime composition standard, fixtures, tools, and tests | reproducibility is strong, but derivation inputs and permanent authorities are not yet sharply separated |
| Fresh target graph | current-worktree MSVC/Ninja configure exposes 25 `ef_*` targets; `ef_composition` built in eight steps | fresh ignored build directory, target help, Ninja graph query, and focused build | composition is physically separate, but facade/raw bindings/public DTOs still expose core ownership |
| Closure inventory | existing generator validates nine caller surface groups, 23 caller paths, source truth, artifact joins, and held residuals | closure validation hash plus 69-pass/4-skip composition architecture suite | P1 can use the existing evidence owner without creating a second registry |
| Kernel smoke test | `test_simulation_kernel_smoke.cpp` contains 41 top-level cases across composition, lifecycle, concurrency, commands, spawning, exact stages, and basic runtime behavior | source inspection | failure ownership and migration-test retirement are obscured even when coverage is valuable |
| Numerical regression | the pre-P2-B short trace is explicitly labeled a same-toolchain migration baseline, not general physics correctness | named native test and comments | relocation or retirement needs replacement evidence; it is not proof that semantic tests are absent |
| Latest CI | the verified remote run completed successfully in about 11 minutes; Python smoke was about 38 seconds, while native build and isolated wheel were the dominant steps | GitHub Actions job timestamps | governance simplification is primarily a maintenance and authority concern, not currently the largest CI-time optimization |
| Archive governance | the current complete governance suite passes 79 tests; the prior archive contradiction is replaced by the P7-A retention authority and P7-B zero-inventory retirement slice | `governance_audit_suite.json`, P7-A retention evidence, and P7-B cleanup evidence | remaining P7-B residual retirement and provider/restore drills require evidence; no ad hoc deletion or P8 closure follows from the green local suite |
| Complexity history | PR 30 changed 1,373 files and deleted 360,503 lines; PR 31 then added 41,306 lines across 201 files, including real runtime code plus tests, tools, and documents | GitHub PR metadata and merge-parent diffs | episodic cleanup does not provide an endogenous control-retirement model |

## Maturity Matrix

| Area | State | Evidence | Blocker to next state |
| --- | --- | --- | --- |
| P0 project authority | accepted | owner route, isolated worktree, independent plan-review pass, and accepted P0 authority inventory | P1 decisions only; no implementation authority |
| Source/control baseline | accepted | reproducible caller, target/link, artifact, control/CI, and document commands in P0 evidence | remeasure at each decision/implementation acceptance boundary |
| Immutable-kernel/host decision | accepted; P4-C candidate-scope task accepted | P1-A freezes one-CAS bootstrap/replacement/checkpoint recovery, terminal shutdown, final-state fence, active-fault drain, all generations and exact P0 caller crosswalk; P4-A/P4-B implement the bounded dark/shadow host and transfer candidates; [P4-C seam packet](p4c_internal_candidate_seam_20260915.md) adds the build-tree-only kernel/world-batch adapter and candidate verification | full maintained-facade parity, production truth and P5 qualification |
| Host replacement | dark/shadow candidate implemented; P4-B independently passed; P4-C candidate task accepted | `RuntimeHostCandidate`, host replacement integration test, P4-B twelve-owner review and evidence routes, P4-C native/Python candidate, stress, parity and rollback gates | full maintained-facade parity and P5 production qualification |
| Contract consolidation decision | accepted | P1-B classifies artifacts and adds singular plan/release/rollout/checkpoint-fragment/aggregate/receipt authorities, canonical envelope and ledger journal | P4 candidate evidence and P5-A/P5-B production closure |
| Executable plan authority | accepted for current in-process default CPU-exact topology | P5-A closed plan fixture/schema/generated header, Python/Cordis byte parity, native owner-join admission and negative tests; [P5-A evidence](p5a_resolved_execution_plan_20260919.md) | P5-D production canary and broader topology |
| Production run evidence | accepted for current local single-process topology | [P5-B ledger qualification](evidence/p5b_production_ledger_qualification_20260919.md), [independent P5-B review](../../../reviews/long_horizon_architecture_governance_p5b_review_20260922.md), native/Python qualification and restart/recovery gates | P5-D caller cutover and ledger-only rollback, P8 provider/topology expansion |
| Rollout/operations decision | accepted | P1-C defines one production-canary decision, support rows, checkpoint-recovery/package-restart rollback, SLO/runbook and security gates | P2 measurements, P4 candidate evidence and P5 production qualification |
| Public/runtime foundation | accepted P3-A/P3-B/P3-C/P4-A; P4-B passed; P4-C candidate task accepted; P5-B accepted for bounded topology; P5-C accepted for tested Windows/MSVC row; P5-D owner-accepted with production rebuild authority retired | `ef_runtime_contracts`, authority/ledger schemas, exact vectors, qualified durable ledger/recovery, `RuntimeHostCandidate`, twelve-row P4-B state-transfer candidate, `RuntimeKernelCandidate`/world-batch adapter, facade-only production wheel, signed local RolloutDecision slot, fresh Windows/MSVC checks, focused facade-contract gates, owner acceptance and retirement evidence | broader topology remains fail-closed; later probes are tracked in the P8 governance monitor |
| Physical facade boundary | accepted for tested Windows/MSVC local CPU-canonical topology | private shared facade backend with explicit RuntimeFacade exports, facade-only production wheel, diagnostics opt-in build/import, fresh wheel/link-map evidence and [P5-C independent review](../../../reviews/long_horizon_architecture_governance_p5c_review_20260922.md) | P5-D caller cutover, broader platform/topology matrix, and P8 final acceptance |
| Production rollout admission | local single-process gate, ArtifactLedger-backed durable controller/snapshot reader, maintained caller migration slice, process-lifetime recheck, mandatory release/RunReceipt binding, real process/package rollback drill, three-cycle supported-row SLO/adoption measurement, four local cadence batches covering three distinct package pairs, admission-bound facade VecEnv reset/step canary, complete local lifecycle/retention check, fail-closed rebuild-retirement gate, and retired production rebuild authority; owner decision accepts P5-D for plan continuation | [P5-D local admission evidence](evidence/p5d_local_rollout_admission_20260922.md), [owner acceptance/retirement packet](evidence/p5d_owner_acceptance_and_rebuild_retirement_20260927.md), and the existing P5-D evidence packets | production-authority retirement is complete for the branch; longer cadence and production probes are post-acceptance governance |
| Control lifecycle | P2-A baseline plus refreshed P2-B local sustainability sample, process resource observation, and a four-batch/three-package-pair follow-up | four existing suite manifests carry six current controls; lifecycle/manifest validators pass 15 focused tests after the P7-B retirements; four P2-B check groups pass 12/12 over three repetitions; supported-row resource observations are 6/6 available (47,042,560-byte max peak working set, 135 max handles); [P2-A evidence](evidence/p2_control_lifecycle_inventory_20260923.md), [P2-B baseline](evidence/p2b_sustainability_baseline_20260923.md), and [cadence follow-up](evidence/p2b_release_cadence_followup_20260924.md) | longer cadence and resource trends are post-acceptance governance |
| Test/CI architecture | accepted bounded local baseline | suite, lane, selector, and repeated local evidence | hosted CI/branch-protection drift is monitored |
| Evidence/document lifecycle | accepted bounded local route | retention authority, archive gate, SQLite restore, and current archive inspected | external provider readiness is monitored |
| Long-horizon acceptance | accepted bounded scope | acceptance contract, matrix, 79-test Windows suite, and 15-test HEI Linux governance subset | broader platform/package qualification remains fail-closed or optional follow-up |

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

1. Complete P2-B control-yield, cost, and sustainability measurements on the
   P2-A manifest-level lifecycle baseline.
2. Implement P4-B episode/state-transfer authority and P4-C immutable internal
   candidate integration, consuming the accepted P4-A dark/shadow host without
   production caller cutover.
3. Continue with P5-C facade-package gates after the accepted P5-A plan and
   bounded P5-B ledger/RunReceipt qualification, before any truth-changing
   activation.
4. Finish maintained caller parity and execute the sole P5-D production cutover
   only after those gates, then complete the rollback window and rebuild
   retirement.
5. Replace test/CI and evidence/document controls only after their structural
   successors exist.
6. Run P8 acceptance and independent review before promoting standards or
   retiring this project through the admitted history route.

## Explicit Overclaim Refusals

- This checkpoint includes accepted P3-A/P3-B/P3-C contract, compatibility and
  non-production ledger foundations plus the P4-A dark/shadow host candidate,
  not production truth publication, production caller/runtime cutover or
  overall program acceptance.
- Latest CI success does not validate the proposed architecture.
- Zero production rebuild callers do not by themselves prove safe deletion.
- A smaller source-scan suite does not prove stronger runtime boundaries.
- Passing the P3-C simulator does not prove a production-qualified durable
  backend, authenticity, singular runtime publication, or a complete RunReceipt.
- Passing P4-A dark/shadow tests does not prove state-complete transfer, native
  episode authority, immutable candidate integration, production packaging,
  caller migration or production cutover.
- Passing the P4-B candidate tests proves only the local dark/shadow owner
  adapters, strict decoding, WAL lifecycle, and host replacement evidence; it
  does not authorize production caller migration, authenticated deployment,
  P5 durability, or production cutover.
- Completing P0-P3 does not justify marking the long-horizon program accepted.
- Passing dark/shadow host tests does not authorize caller cutover before epoch,
  state-transfer, episode-authority, rollout, and rollback gates.
