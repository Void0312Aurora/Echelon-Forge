# Long-Horizon Architecture Governance Acceptance Contract

Status: `2026-08-25` acceptance contract established; P0 authority/baseline,
P1 target decisions, P3-A public-contract foundation, and P3-B authority-shell
foundation are accepted, while the overall program remains `not accepted` because
P2-B/P3-C-P8 are not
complete.

Parent subproject: [Long-Horizon Architecture Governance](README.md)

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/long_horizon_architecture_governance/long_horizon_architecture_governance_acceptance_20260825.md`
Owner: `cross-domain architecture`
Last verified: `2026-08-25`

## Acceptance Decision

Current decision: `not accepted`.

Planning documents, inventories, source scans, green documentation tests, or
short-term repository cleanup cannot accept this program. Acceptance requires
the implemented long-horizon runtime, contract, boundary, control, CI, and
evidence transitions defined below.

## Strategic Outcome Contract

The accepted result must have all of these properties:

1. Kernel composition is immutable for the maintained production lifecycle.
2. Replacement uses a host state machine with one publication linearization
   point, monotonic incarnation epoch, fenced world/entity/request/result
   references, jointly linearized instance leases, pre-publication quiescence
   and final-state transfer fence, bounded drain/cancellation/backpressure and
   quarantine, deterministic reclamation, and one native-owned episode barrier.
3. Any admitted in-place replacement exception proves a real
   identity-preserving consumer, complete versioned state transfer, stale-handle
   rejection, failure rollback, concurrency safety, and replay meaning.
4. Experiment intent resolves to one closed executable plan that native code
   revalidates and executes. Cordis, Python, fixtures, packages, and diagnostics
   cannot create parallel execution truth.
5. Mixed-version rollout has one writer, bounded N/N-1 readers, explicit
   stored-plan rejection/re-resolution rules, canary/shadow receipts, rollback
   checkpoints, kill switches, and quantitative backout triggers.
   ReleaseManifest, RolloutDecision and StateCheckpoint authorities have
   singular writers/validators and one production-canary cutover decision.
6. A versioned `RunReceipt` binds plan bytes/hash, executable/module/wheel
   digests, build/toolchain/ABI/platform, scenario/content/config/seed,
   world/episode/run identity, lifecycle receipts, determinism profile, result
   hashes, and completion state.
   Durable journal admission precedes truth mutation, crash finalization is
   fenced, and required artifacts are restorable before production cutover.
7. Production bindings and packages physically depend on facade/contracts, not
   raw engine ownership. Raw access is separately built, named, packaged, and
   admitted for diagnostics only.
8. Permanent controls protect stable semantic or qualification obligations.
   Migration metadata is attached to existing gate declarations. Expiration
   requires retirement, permanent re-admission, or at most one independently
   sponsored bounded renewal with a forced removal date.
9. Every maintained test has one execution owner/strategy. CI lanes have
   explicit audiences and preserve native, wheel, facade, replay/parity,
   failure, performance/resource, release, and test-orphan evidence.
10. Maintained standards and references remain concise current authority;
   reviews, acceptance receipts, generated evidence, and historical task
   packets have retention, availability, backup/restore, access, provider
   migration, and retrieval rules without remaining active authority.
11. Supported platforms and process topologies are explicit and have an
   operational owner, runbook, SLOs, adoption/rollback telemetry, and resource
   leak/skew monitoring. Unsupported multi-process execution fails closed until
   leader fencing, persistent epochs, crash recovery, authentication,
   authorization, authenticity, and quotas are admitted.

Mechanisms may change after evidence and review. These outcome properties may
not be replaced by a narrower or short-term program.

## Phase Acceptance Gates

### P0 Authority And Baseline

- latest remote revision, worktree, branch, and dirty-root separation recorded;
- live callers, controls, artifacts, targets, CI lanes, and documents have
  reproducible baseline commands;
- project files and parent owner links pass document checks;
- independent plan review has no unresolved critical/high finding.

P0 acceptance authorizes P1 decisions only. It proves no runtime change.

### P1 Target Architecture

- immutable-kernel/host replacement decision covers state, identity, drain,
  lifecycle states, one-CAS initial/replacement/checkpoint-recovery publication,
  terminal shutdown, epoch/fencing/leases, construction, pre-publication
  quiescence/final-transfer fence,
  drain/cancellation/backpressure, bounded quarantine/reclamation, active-fault
  paths, shutdown, concurrency, recovery, and native episode authority;
- contract decision maps every current request, lock, projection, manifest,
  generated evidence/diagnostics/metadata, provenance, parity, closure, plan,
  release/rollout/checkpoint, and RunReceipt artifact to a durable, derived,
  transitional, or historical role with singular writer/validator;
- canonical wire/detached-digest rules, durable run-admission journal,
  recovery fencing and minimum pre-cutover artifact storage are explicit;
- N/N-1 compatibility, rollout, canary, kill-switch, rollback-window, stored
  artifact, and irreversible-write plans cover C++, Python, RL, visualization,
  diagnostics, world batch, Cordis, native binaries, wheels, and replay;
- supported platform/process topology, operational owner/SLO/runbook, and
  multi-process security activation decisions are explicit;
- independent architecture review accepts the decisions.

### P2 Control Lifecycle

- every blocking architecture control has an owner, protected defect class,
  unique detection claim, enforcement type, creation reason, review trigger,
  and lifecycle disposition;
- every migration ratchet has a measurable target and retirement gate;
- lifecycle metadata lives with the existing gate/suite declaration and
  includes owner, invariant, kind, created/expiry, successor, renewal count,
  and removal proof;
- expiration cannot silently renew: at most one bounded independent renewal is
  allowed before retirement or permanent semantic re-admission;
- control-yield, false-positive, source-scan, CI latency, maintenance,
  evidence-growth, host adoption, drain/rollback, stale-ref, resource leak,
  version-skew, and evidence-retrieval measurements are repeatable and owned;
- lifecycle automation replaces existing duplicate machinery rather than
  adding another blocking meta-governance chain.

### P3 Contract And Public Boundary Foundation

- an engine-independent public contracts target owns epoch-bearing
  world/entity/request/result DTOs before host publication;
- canonical JSON authority envelopes, versioned resolved-plan,
  ReleaseManifest, RolloutDecision and StateCheckpoint shells plus single-owner
  adapters exist before host implementation becomes execution truth;
- current engine/component headers are absent from the future public facade
  contract shell;
- one writer, bounded readers, stored-plan rejection, minimum ArtifactLedger
  conditional storage/fencing, non-authoritative shadow, rollback checkpoint,
  kill switch, and backout triggers are executable;
- host work may run dark/shadow only until these gates pass.

#### P3-A Public Identity And Target Foundation — Accepted

P3-A is accepted independently after its `gpt-5.6-sol` max initial, repair and
final reviews. Its accepted evidence is limited to:

- the build-tree-only `ef_runtime_contracts` target and `runtime_contracts::v1`
  same-build value-contract family with distinct host/incarnation identities;
- generated public field lists owned by the existing `dto_schema` registry;
- actual configure-time target/consumer checks plus generated target/install
  manifests and negative graph/schema injection tests;
- Windows AMD64 MSVC/Ninja compile and focused native/runtime-contract gates;
- no public caller, facade, engine, binding, install/export or host publication
  cutover.

P3-A explicitly does not accept canonical JSON/storage (P3-B), rollout/ledger
storage (P3-C), host freshness/lease validation (P4), Linux qualification, SDK
ABI, or production migration. P3-B was eligible to start from this boundary;
after its independent acceptance, P3-C is the next eligible implementation
phase. Host work remains dark/shadow and the overall program remains
`not accepted`.

#### P3-B Authority Envelope Foundation — Accepted

P3-B is accepted independently after the `gpt-5.6-sol` max repair review. The
accepted foundation includes:

- one versioned envelope and payload-schema owner for resolved plans, releases,
  rollout decisions, and state checkpoints;
- Python semantic validation, a one-way current-artifact adapter with explicit
  request/manifest provenance binding, Cordis canonical parsing/digest support,
  and a native strict validator with an explicit read-only legacy parser edge;
- owner-scoped writer roles, exact fields, typed identifiers/hashes, generation
  windows, `prepared` rollout state, typed rollback policy, UTF-16 ordering and
  fail-closed signature/media/domain checks;
- exact checked-in canonical bytes/digest vectors consumed directly by Python,
  Cordis and native tests, including rollout/checkpoint lanes and negative plan
  admission tests;
- fresh Windows/MSVC native authority and boundary CTest plus Python/Cordis and
  composition architecture evidence.

P3-B does not accept durable ArtifactLedger storage, N/N-1 reader sequencing,
host freshness/leases/tombstones, state transfer, package/SDK publication,
Linux qualification, production caller migration, or host publication. P3-C
remains the next long-horizon implementation phase.

### P4 Host Lifecycle And Immutable Kernel

- the host state machine constructs, validates, quiesces the old truth,
  proves final transfer commit, boots from absent, recovers only from admitted
  checkpoints without exporting faulted truth, jointly linearizes lease
  admission/publication, terminates idempotently, drains, fences, quarantines
  and reclaims runtime instances;
- monotonic epochs reject stale references and in-flight work during candidate
  replacement, shadow transfer, and simulated cutover;
- native simulation owns the episode barrier and Python mirrors use a versioned
  handshake rather than independent autoreset authority;
- the state census covers ECS, RNG, clock, delayed events/queues, command/link
  pending state, Python mirrors, backend/device leases, and in-flight requests;
- P4-A runs dark/shadow; P4-B state/episode semantics are a hard predecessor of
  the P4-C internal candidate seam;
- P4-C migrates only test/shadow adapters and proves the candidate path
  immutable, state-complete, fenced, and rollback-capable;
- P4 cannot publish production truth, migrate maintained production callers,
  or retire production in-kernel rebuild.

### P5 Plan, Evidence, And Binding Consolidation

- one closed resolved executable plan binds owner admission, provider/system
  graph, backend, implementation versions, configuration, and canonical bytes;
- Cordis and native paths agree on the plan without hidden defaults or
  independent high-level lowering;
- `RunReceipt` binds actual executable/package/platform/run inputs, lifecycle
  transitions, results, and completion;
- production ArtifactLedger qualification proves durable pre-mutation journal
  admission, torn-write detection, stale-writer recovery fencing, immutable
  release/rollout/checkpoint authorities and restore before P5-D;
- CMake include/link visibility makes private engine ownership unavailable to
  production bindings; raw diagnostics use a separate opt-in target/module;
- isolated wheels pass maintained facade/world-batch behavior on every
  supported platform;
- P5-D is the only truth-changing production cutover and cannot start until
  P5-A closes the executable plan, P5-B emits complete RunReceipt, and P5-C
  proves facade-only production packaging;
- P5-D conditionally commits one production-canary RolloutDecision, migrates
  maintained callers, expands only its predeclared routing schedule, runs
  version-skew, same-release and process-restart package rollback, drain,
  stale-ref, leak, storage and operator drills, and retires production rebuild
  only after the rollback gate passes;
- unsupported process topologies fail closed;
- redundant migration closure/interchange authorities retire without losing
  reproducible provenance.

### P6 Test And CI Architecture

- each permanent gate has a stable failure audience and non-duplicate detection
  purpose;
- retired source scans and manifest meta-tests have structural/behavior
  replacement evidence or a documented demonstration of redundant detection;
- every maintained test retains one owner and execution strategy through a
  single runner-native declaration or derived non-authoritative orphan report;
- P6 does not edit archive-retention policy, its gate, or its suite node; those
  surfaces remain under the serial P7-A retention decision;
- fast, qualification, nightly, release, and research lanes run the appropriate
  gates without silently weakening branch protection;
- repeated CI evidence establishes feedback, resource, and flake budgets;
- exact migration snapshots are owned by an exact/migration lane and retire or
  renew deliberately.

### P7 Evidence And Documentation Lifecycle

- standards contain lasting rules, references contain verified current facts,
  active work contains only current execution state, and the admitted review or
  retired-history route retains bounded historical judgment;
- lifecycle policy, subproject template, retirement gate, suite placement,
  repository paths, indexes, and retrieval instructions express one retention
  model; the current owner-archive contradiction is closed by reviewed migration;
- P7-A's normative retention decision precedes every archive-specific gate,
  suite, path, index, or history migration;
- closed dispatch, response, acceptance, and intermediate evidence packets no
  longer occupy maintained authority;
- externally retained CI/release evidence has versioned manifests, checksums,
  minimum retention, availability, backup/restore, access-control,
  provider-migration, retrieval, and periodic restore-drill owners;
- P7 extends the production storage foundation already accepted by P5-B; it
  cannot defer selection of the first durable run/rollback store until after
  P5-D;
- required bilingual entry surfaces are synchronized without forcing all
  historical evidence into permanent translation governance;
- link, lifecycle, archive, and sampled retrieval audits pass.

### P8 Long-Horizon Acceptance

- supported caller, platform, and process-topology migrations are complete or
  have explicitly accepted compatibility residuals that do not create a second
  truth; unsupported topology fails closed;
- native/Python/Cordis plan identity, replay/parity, packaging,
  mixed-version canary/backout, RunReceipt, failure-injection,
  performance/resource, stale-ref, leak/skew, and teardown evidence pass;
- operational owner, runbook, SLO, adoption/rollback telemetry, security
  activation, and evidence restore drills pass;
- control and evidence sustainability measurements meet their admitted budgets
  over representative changes, not one synthetic run;
- an independent source/build/evidence review reports no unresolved
  critical/high finding;
- lasting decisions are promoted to owner standards/reviews, parent indexes are
  current, and this task packet is ready for the admitted retirement route.

## Failure Conditions

The program must remain `not accepted` if any of the following is true:

- kernel composition is described as immutable while maintained callers still
  depend on production in-place rebuild;
- host replacement silently discards or preserves undeclared state;
- old truth can mutate after final state export or an active fault can bypass
  drain/quarantine and zero-lease reclamation;
- bootstrap, checkpoint recovery or normal shutdown requires an unreviewed
  second publication/terminal path, faulted truth export, or default empty state;
- publication lacks a linearization point, monotonic epoch, leases/fencing, or
  deterministic old-instance reclamation;
- Python and native runtime can independently advance authoritative episode
  phase or autoreset state;
- production caller cutover occurs outside P5-D or before the public-contract
  target, closed executable plan, rollout/backout contract, state-transfer gate,
  complete RunReceipt, and facade-only production package;
- production in-kernel rebuild retires before the single production cutover
  passes its rollback window and caller-adoption gate;
- more than one component can author the production executable plan;
- release routing, checkpoint or receipt state has multiple writers, or
  production canary and full adoption use separate truth-selection seams;
- fixture, generated header, package, Cordis, Python, or documentation state is
  treated as execution truth without native admission;
- production wheel or bindings expose an implicit raw engine path;
- temporary migration controls remain permanent merely because they are green;
- an expired migration control is repeatedly renewed without a forced
  successor/removal date or permanent semantic re-admission;
- a maintained test loses its execution owner/lane during manifest
  simplification;
- a run is accepted without binding actual executable/package, platform,
  scenario/content/config/seed, lifecycle transitions, result, and completion;
- truth mutation begins before durable journal admission, recovery can race a
  stale writer, or rollback artifacts are ephemeral/unrestorable at P5-D;
- an unsupported process topology runs without fail-closed fencing, recovery,
  authentication, authenticity, and quota gates;
- externalized evidence lacks retention, restore, access, availability, or
  provider-migration guarantees;
- lifecycle policy authorizes a history route that a maintained gate rejects,
  or repository history remains on a path forbidden by its governing gate;
- evidence is deleted without reproducible retrieval or kept active without a
  current authority role;
- CI timing is improved by removing high-value behavior/native/wheel evidence
  without replacement;
- a review closes long-horizon gaps by recommending only a smaller or
  short-term scope.

## Required Independent Reviews

| Gate | Review scope | Minimum verdict |
| --- | --- | --- |
| `P0-B` | plan completeness, source basis, strategic coherence, missing migration and acceptance obligations | no unresolved critical/high plan finding |
| `P1 review` | lifecycle/episode authority, artifact/version rollout, platform/process topology, operations/security decisions | accepted architecture with compatibility and backout route |
| `P3 review` | public-contract target, resolved-plan shell, mixed-version rollout foundation | no public cutover on transitional types or second writer |
| `P4/P5 review` | fenced host/state transfer, native/Cordis plan, RunReceipt, build/package boundary, canary/backout operations | no unresolved critical/high implementation finding |
| `P8-B` | complete source, build, behavior, evidence, governance, and documentation result | independent acceptance; no unresolved critical/high finding |

Review independence means the reviewer did not author the reviewed plan or
implementation. The main thread owns finding disposition and local
revalidation.

## Current Evidence

Accepted P0 evidence:

- refreshed remote baseline and isolated branch/worktree;
- source-backed governance and runtime observations in the
  [current-status file](long_horizon_architecture_governance_current_status_20260825.md);
- finite [task clusters](long_horizon_architecture_governance_task_clusters_20260825.md);
- explicit [dispatch order](long_horizon_architecture_governance_dispatch_queue_20260825.md);
- reproducible [P0 authority inventory](evidence/p0_authority_inventory_20260825.md)
  covering callers, targets/links, artifacts, controls/CI, and documents;
- independent P0-B plan-review verdict with no unresolved critical/high finding.

Accepted P1 evidence:

- the three linked P1-A/P1-B/P1-C decisions with final SHA-256 ledger;
- [independent P1 architecture review](../../../reviews/long_horizon_architecture_governance_p1_review_20260825.md)
  covering initial, two repair and final-confirmation rounds;
- no unresolved critical/high finding, all recorded medium findings closed, and
  no short-term substitution detected;
- synchronized phase dependencies requiring P3 contract/ledger foundations
  before P4 host publication and P5-B storage/receipt qualification before the
  sole P5-D production-canary cutover.

Accepted P3-A evidence:

- [independent P3-A review](../../../reviews/long_horizon_architecture_governance_p3a_review_20260825.md)
  with initial `pass_with_repairs` and final `pass`, no unresolved finding,
  and no short-term substitution;
- `ef_runtime_contracts` Windows/MSVC native compile and CTest boundary gates,
  fresh `BUILD_TESTING=OFF` target build, 110-entry DTO manifest with eight
  public schemas, and schema/flat-directory/negative injection tests;
- explicit residual boundaries for P3-B canonical serialization, P3-C
  rollout/ledger, P4 freshness/leases, P5 package/cutover and Linux support.

Accepted P3-B evidence:

- [independent P3-B review](../../../reviews/long_horizon_architecture_governance_p3b_review_20260825.md)
  with final `pass`, no unresolved Critical/High finding, and no short-term
  substitution;
- four typed authority schemas, exact canonical vectors, one-way adapter and
  cross-language Python/Cordis/native conformance tests;
- fresh Windows/MSVC native CTest `2/2`, Python authority/schema `12 passed`,
  full composition architecture `81 passed, 4 skipped`, and Cordis authority
  lane `4 passed`;
- explicit residual boundaries for P3-C ledger/compatibility, P4 host
  freshness/state transfer, P5 package/cutover and Linux support.

P0/P1 authorized P2-A/P2-B and P3-A entry. P3-A and P3-B are now accepted and
authorize P3-C entry only. These decisions do not accept P2-A/P2-B
implementation, P3-C-P8 implementation beyond the next bounded phase,
platform support, host migration or production
cutover.

## Residual Policy

A residual is acceptable at final closure only when it:

- has an owner outside the accepted core;
- cannot bypass immutable composition, native execution authority, facade
  containment, or control lifecycle;
- has an explicit activation and review gate;
- is not required by a maintained caller;
- is linked from the promoted standard or owner issue.

External plugins, remote catalogs, Node hosting, CUDA canonical promotion, and
identity-preserving live reload may remain residuals, but their deferral cannot
weaken the architecture required for current and future profiles, domains,
backends, and bindings.
