# P1-C Rollout, Operations And Security Decision

Status: `2026-08-25` frozen P1-C decision candidate; implementation is not
authorized until the integrated P1 independent review passes.

Parent subproject: [Long-Horizon Architecture Governance](../README.md)

Document kind: `decision`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/long_horizon_architecture_governance/decisions/p1c_rollout_operations_and_security_decision_20260825.md`
Owner: `runtime release and operations architecture`
Last verified: `2026-08-25`

## Decision

Runtime architecture changes use a reader-first N/N-1 rollout, one active plan
writer, dark/shadow validation, bounded canary, one P5-D production cutover,
and an explicit rollback window. The P1-A host epoch and P1-B plan/receipt
identities are the rollout units; version switching cannot be implemented as an
independent Python, Cordis, wheel or backend toggle.

The release-level linearization point is the ArtifactLedger's conditional commit
of the first signed `RolloutDecision` in state `production_canary`. It binds one
`ReleaseManifest`, routing schedule, plan writer generation, package set,
episode-owner mode, checkpoint and irreversible-write boundary. That commit is
the sole P5-D truth-changing cutover. Each selected process still performs its
P1-A local slot publication, but it cannot choose a release path outside the
effective decision.

The target supported production topology is in-process native execution,
including local Python through the facade-only native extension, on qualified
Windows AMD64/MSVC and Linux x86_64/glibc rows. Qualification is per concrete
release manifest and includes native and isolated-wheel evidence. These are
required target rows, not claims that current CI already proves them.

Node, remote/external host and multi-process execution remain unsupported and
must fail closed. Multi-process activation requires the security, fencing,
recovery and operations gates below; a network endpoint or shared filesystem is
not sufficient admission. CPU exact remains canonical. CUDA remains an
unmaintained/diagnostics candidate until separately promoted.

## Current Evidence Boundary

- Current GitHub `ci-smoke` runs on `ubuntu-latest`, Python 3.11 and Node 22,
  builds native targets, runs focused CTest/Python gates, builds an isolated
  Linux wheel and exercises both a raw kernel binding and `WorldBatchVecEnv`.
- Current local Windows evidence uses an MSVC developer environment; the remote
  workflow does not qualify Windows or a Windows wheel.
- `pyproject.toml` declares Python `>=3.10`, but one Linux 3.11 job does not
  qualify every interpreter/ABI allowed by metadata.
- Current composition contracts hold Node/external distribution and canonical
  CUDA execution. No admitted multi-process leader, persistent epoch, crash
  recovery, authentication/authorization, authenticity or quota system exists.
- There is no current runtime-host runbook, replacement SLO, adoption/skew
  dashboard, cutover receipt or operator backout drill.

The target matrix therefore separates `required target`, `currently evidenced`
and `accepted for production`. Absence from CI never silently removes a target
row, and a target row is not supported until its gate passes.

## Platform, Package And Topology Matrix

| Row | Long-term state | Qualification requirement | Current state |
| --- | --- | --- | --- |
| Windows AMD64 native, MSVC ABI family | required target | pinned OS/toolset/compiler/runtime manifest, clean native build, lifecycle/failure/parity/resource gates | local build evidence only; not production-qualified by this decision |
| Windows AMD64 CPython wheel | required target | supported CPython ABI declared per release, isolated install, facade-only linkage, scenario/world-batch behavior, receipt digest | unproven |
| Linux x86_64 glibc native | required target | pinned distro baseline/compiler/libstdc++/glibc manifest, native lifecycle/failure/parity/resource gates | current Ubuntu CI is partial evidence |
| Linux x86_64 CPython wheel | required target | declared Python/manylinux-or-equivalent ABI row, isolated install and facade behavior | current Linux 3.11 isolated wheel is partial evidence |
| in-process native facade | supported target topology | P3-P5 host/plan/receipt/cutover gates | current facade exists; target host not implemented |
| local Python native extension | supported target topology | production wheel links facade/contracts only and uses native episode handshake | current package exposes raw and facade surfaces |
| raw kernel/world-batch bindings | diagnostics-only target | separately named opt-in build/package, never installed transitively | currently present in the main `ef_py` module |
| Node host | unsupported, fail closed | separate use case and full host/security/receipt admission | explicitly held |
| remote/multi-process host | unsupported, fail closed | all activation gates in this decision | absent |
| CUDA exact/canonical | unsupported as canonical | independent exactness, lifecycle, resource and operations promotion | CPU exact remains canonical |

Each release manifest pins exact OS image or minimum baseline, compiler/linker,
C++ standard library and ABI, CMake/build mode, Python ABI tags, native/package
digests and dependency versions. Evergreen labels such as `latest`, `v143`,
`glibc` or `Python >=3.10` are not sufficient receipt identity. Adding or
removing a row requires user-impact analysis, a deprecation window, stored-plan
and wheel compatibility disposition, and independent release review.

## Compatibility Generations

N/N-1 rules are coordinated across these components:

| Component at generation N | Required read/interaction range | Writer rule |
| --- | --- | --- |
| PlanCompiler | emits N only after reader-first gate | sole production plan writer |
| native plan reader/host | plans N and N-1 | writes no plan |
| native `RunRecorder` | reads lifecycle inputs N/N-1; emits receipt N | sole production receipt writer |
| receipt/evidence tooling | receipts N and N-1 | read-only, except admitted crash reconciler |
| Python binding/wheel | native ABI/package matrix for its exact release; plan/receipt readers N/N-1 through facade | cannot resolve plan or finalize receipt |
| Cordis caller/producer | request compatibility N/N-1; production PlanCompiler N only | cannot coexist with a second writer |
| stored plans/checkpoints | N and N-1 during declared window | immutable; never silently downgraded |

The release manifest names `compatibility_generation`, `writer_generation`,
`minimum_reader_generation`, `state_schema_generation`, rollback deadline and
irreversible-write flags. Major semantic changes outside the admitted N/N-1
range require an offline migration with new identities, not a wider implicit
reader promise.

## Rollout State Machine

| State | Production writer | Production execution | Entry evidence | Exit |
| --- | --- | --- | --- | --- |
| `prepared` | N-1 | N-1 | N reader parses N/N-1; packages and support rows built | `shadow` |
| `shadow` | N-1 | N-1 authoritative; N observes/replays only | plan-byte, lifecycle, episode, result and resource comparisons | `canary-ready` or `backed-out` |
| `canary-ready` | N-1 | N readers deployed; N remains non-authoritative and no N plan is written | mixed-version, storage/restore and rollback drill | P5-D `production-canary` commit |
| `production-canary` | initially N-1 | first bounded, preselected production attempts use the complete N package/host/native-episode path; others remain entirely N-1 | sole conditional P5-D `RolloutDecision` commit and quantitative triggers | successor `adoption-expanding` decision or `backed-out` |
| `adoption-expanding` | N-1, then N only after every eligible reader is N | same prebound N path serves increasing cohorts; no second execution seam | caller/support-row evidence; successor decision may advance writer/cohort only | `rollback-window` or `backed-out` |
| `rollback-window` | N | N through the same routing authority; compatible N-1 package/checkpoint retained | full adoption plus continuous skew/drain/stale-ref/leak/result telemetry | `stable` or `backed-out` |
| `stable` | N | N | rollback deadline passed, no unresolved high finding, stored N-1 inventory dispositioned | next `prepared` |
| `backed-out` | writer/reader selected by compatibility boundary | same-release instance rollback or restarted N-1 package, as applicable | typed successor `RolloutDecision` and rollback receipt | repaired `prepared` or stop |

Before `production-canary`, N execution is shadow-only. The P5-D decision is the
first and only authorization for N production truth. Later successor decisions
use the same manifest, execution path and native episode authority and may only
advance the predeclared cohort/writer schedule; they do not introduce another
publisher or toggle. Advancing the PlanCompiler writer to N occurs only after
every eligible reader is N and is recorded in that same monotonic decision log.
No feature flag may independently select plan writer, host, episode owner or
package.

Canary cohort selection occurs before process/run/episode admission. An N canary
attempt uses native episode authority for its whole lifetime; an N-1 attempt
uses the legacy package for its whole lifetime. No episode crosses packages and
no process permits Python and native code to both reset the same world. The
rollout may temporarily compare two release generations across disjoint runs,
but one RolloutDecision is the singular router and every receipt binds its
selected generation.

Stored N plans are never handed to N-1 readers. Before an irreversible N-only
write, rollback may publish an admitted N-1 instance at a new epoch using a
compatible N-1 plan and checkpoint. After that boundary, rollback means stop or
roll forward with N. It cannot fabricate an N-1 state or reuse the old epoch.

Rollback has two distinct protocols:

1. `same-release instance rollback` constructs another instance from a plan
   admitted by the already loaded package, fences/settles the faulted source,
   validates a previously durable native checkpoint without exporting faulted
   truth, and uses P1-A's `checkpoint_recovery` publication transaction in the
   same process/boot at a new incarnation epoch;
2. `binary/wheel/package rollback` closes admission, drains or quarantines,
   and durably finalizes/flushes journals. A healthy source that reaches its
   admitted native barrier may commit a new checkpoint before stop. A faulted or
   quarantined source must not author a new checkpoint: rollback selects a
   previously durable admitted checkpoint or abandons the attempt and starts a
   new run. The operator then stops the process, installs/starts the admitted
   N-1 release, validates package and any selected checkpoint, creates a new
   boot identity, and forces caller reconnect/resynchronization before accepting
   work.

Loaded `.pyd/.so` or statically linked native code is never treated as safely
unloadable/reloadable in place. Package rollback cannot be described as merely
publishing an old slot at a new epoch. Both protocols bind the source and target
ReleaseManifest/RolloutDecision in their receipts and stop at the irreversible-
write boundary.

## Canary, Kill Switch And Backout Triggers

Canary selection is deterministic and receipt-visible by run/tenant/workload,
never by silently changing scientific truth within an episode. CPU-exact
semantic comparison is the reference. The canary includes every required
platform/package row and representative long-running, reset-heavy, failure and
resource workloads before full adoption.

Any of the following triggers automatic admission closure and operator backout
or stop:

- wrong-epoch result, duplicate publication, stale reference accepted, episode
  double-reset, result identity mismatch or receipt integrity/authenticity
  failure: threshold `1`;
- native/Cordis plan-byte divergence, hidden default, unsupported reader or
  topology acceptance: threshold `1`;
- deterministic CPU-exact result mismatch outside an independently admitted
  profile budget: threshold `1`;
- unreclaimed/quarantined instance beyond the declared lease-grace window,
  persistent resource growth over the release budget, or drain deadline breach:
  threshold set in the release operational budget, with no unsafe destruction;
  any unresolved quarantine immediately freezes further replacement in that
  host, and exceeding the host-wide quarantine budget forces fail-stop;
- replacement, crash-recovery, receipt-finalization, artifact-retrieval or
  availability SLO breach over its rolling window;
- security authentication/authorization, replay, signature, leader-fencing or
  quota bypass: threshold `1`.

The kill switch closes new admissions and freezes writer advancement. It may
route future compatible work to the last accepted release/plan; it cannot relabel
in-flight N results, mutate stored plan bytes, downgrade irreversible state or
skip the P1-A drain protocol.

## Operational Ownership And SLO Contract

The `runtime operations owner` owns release readiness, host health, drain and
rollback; `runtime composition` owns plan compatibility; `runtime evidence`
owns receipt finalization/retrieval; `release engineering` owns qualified
platform/wheel rows; `security` owns multi-process activation. A release cannot
use an unassigned aggregate owner.

Correctness objectives are zero-tolerance:

- zero accepted stale/wrong-epoch references or results;
- zero duplicate production publication or episode reset;
- zero execution of unadmitted plan/package bytes or unsupported topology;
- 100% of admitted attempts have a terminal receipt, including a typed
  crash/incomplete reconciliation;
- 100% of active and rollback plans/checkpoints are retrievable and hash-valid;
- zero destruction of an instance while a lease remains active.

Initial launch objectives, to be measured and ratified by P2-B before P4/P5
acceptance, are:

| Objective | Initial launch gate | Evidence window |
| --- | --- | --- |
| admitted replacement success | at least `99.9%` excluding injected failures | representative qualification set plus rolling release window |
| bounded drain | at least `99%` complete within the profile's configured deadline; default planning ceiling `30 s` | stress/reset/failure workloads |
| backout recovery | admission closed immediately and last compatible slot available within `5 min`, or fail-stop declared | operator drill on every supported row |
| crash receipt reconciliation | terminal `crashed/incomplete` record within `5 min` of detection | kill/crash drill |
| lifecycle resource residual | zero live host instances after successful shutdown; byte/thread/handle residual within measured release budget | repeated construct/replace/shutdown cycles |
| stored artifact retrieval | at least `99.9%` availability with 100% hash correctness | scheduled restore drills |

P2-B may tighten these values or propose evidence-backed topology-specific
values. Weakening a value requires risk acceptance and independent review; it
cannot be done to make a failing canary green. Safety invariants remain
zero-tolerance regardless of availability targets.

Required telemetry is epoch/plan/release tagged and includes admission counts,
replacement duration/result, drain age and lease count, cancellations,
quarantines, stale-reference rejections, episode resyncs, writer/reader/version
skew, caller adoption, receipt lag/final state, artifact retrieval, instance
thread/handle/memory/device residuals, rollback readiness and security denials.
Telemetry cannot contain secrets or become an alternative run receipt.

## Runbook Contract

Before cutover, the operator must be able to:

1. identify exact source/release/package/plan digests and support row;
2. verify N/N-1 reader deployment while writer remains N-1;
3. run dark/shadow comparisons, fault injection and ArtifactLedger restore
   checks; production canary begins only at the P5-D decision;
4. prove rollback plan/checkpoint retrieval and the irreversible-write boundary;
5. verify host/episode/receipt telemetry and all named owners are on-call;
6. authorize the signed P5-D `production_canary` RolloutDecision, then advance
   cohort/writer only through its admitted successor decisions;
7. close admissions with the kill switch, drain/quarantine safely, execute the
   same-release instance rollback or the stop/restart package rollback protocol,
   or declare fail-stop;
8. reconcile incomplete receipts and preserve failure artifacts;
9. decide after the rollback window whether N-1 readers/artifacts may retire.

The runbook contains command/role prerequisites, expected outputs, typed failure
codes, escalation owners and rehearsal cadence. A document-only walkthrough is
not acceptance; P5-D/P8 require operator drills on every supported row.

## Fail-Closed Unsupported Topology

Until separately admitted, build/package/plan admission must make remote or
multi-process production execution unavailable:

- no production network listener or remote-host provider capability is shipped;
- plans requesting such a topology are rejected before runtime construction;
- environment variables, Python flags or diagnostic modules cannot bypass the
  capability check;
- raw diagnostics cannot publish production results or receipts;
- process discovery or a shared file/lock is not treated as leader election.

## Multi-Process Security Activation Gates

Every gate below is mandatory before even a canary topology is admitted:

1. one strongly consistent leader election/lease and fencing-token service;
2. a durable, monotonic per-host epoch/sequence store with atomic compare-and-
   swap, restart recovery, tombstones and exhaustion handling;
3. authenticated workload and operator identities, mutual transport security,
   least-privilege authorization for plan write/admit/run/cancel/receipt/read;
4. signed or attestable plan, binary/package and receipt identities with key
   rotation, revocation and timestamp/replay protection;
5. durable request idempotency, result deduplication, crash recovery and
   partition behavior that cannot create two publishers;
6. tenant/workload CPU, memory, GPU, queue, request-rate and artifact quotas,
   bounded backpressure and denial-of-service isolation;
7. secret management, audit log integrity, data classification, artifact access
   control and retention/deletion policy;
8. version-skew negotiation that still obeys one writer and N/N-1 readers;
9. failure injection for leader loss, split brain, clock skew, replay, forged
   artifacts, storage unavailability, partial writes and network partitions;
10. the same native episode, lifecycle and RunReceipt owners as in-process
    execution, plus on-call SLOs and recovery drills.

Security activation cannot fork a remote execution authority. The leader may
coordinate admission, but only the native host owning the leased epoch may
publish execution truth and finalize its receipt. Failure to prove any row keeps
the topology unsupported.

## Implementation Sequence And Gates

1. P2-B establishes reproducible lifecycle/rollout/resource/retrieval baselines.
2. P3-B freezes the canonical wire envelopes and plan/release/rollout/checkpoint
   contract shells.
3. P3-C implements reader-first compatibility, the minimum ArtifactLedger
   contract/simulated backend, stored-artifact rejection, non-authoritative
   shadow receipts, writer sequencing, kill switch and simulated backout.
4. P4 runs the host only dark/shadow and proves the P1-A lifecycle/episode
   rules under the target support rows.
5. P5-A/B/C close plan, qualify the production ArtifactLedger and durable
   pre-admission journal/recovery fence, close receipt/checkpoint authority, and
   prove package identity before production change.
6. P5-D qualifies every supported row, rehearses both rollback protocols,
   conditionally commits one production-canary cutover and holds the rollback
   window.
7. P8 repeats compatibility, failure, security-denial, resource and restore
   evidence before long-horizon acceptance.

P1-C is accepted only when the integrated independent reviewer finds no
unresolved critical/high gap in version order, stored artifacts, rollback,
platform/package claims, operations, SLO ownership, fail-closed topology or
security activation.

## Rejected Alternatives

- A writer-first deployment is rejected because N-1 readers could receive N
  plans with no safe interpretation.
- Broad `>=` version acceptance or ignore-unknown parsing is rejected because it
  hides truth-affecting skew.
- Independent toggles for Cordis writer, native host, Python autoreset and wheel
  selection are rejected because they create mixed authority.
- Calling Windows or all Python `>=3.10` supported from metadata/local build
  alone is rejected; support is a qualified release property.
- Enabling multi-process behind an undocumented experimental flag is rejected;
  fail-closed capability absence is required.
- Backout by epoch reuse, receipt rewrite or silent stored-plan downgrade is
  rejected.

## Residuals

- Exact release images/toolchain/Python ABI rows are pinned by each release and
  remain unaccepted until qualification evidence exists.
- SLO values are initial launch gates pending P2-B measurement; this is not an
  assertion that current runtime meets them.
- Multi-process and Node remain unsupported, not merely deferred documentation.
- External evidence durability and provider migration integrate with P7.
- CPU exact remains canonical and CUDA promotion is outside P1-C acceptance.
