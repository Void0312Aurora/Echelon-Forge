# P1-B Plan And RunReceipt Authority Decision

Status: `2026-08-25` frozen P1-B decision candidate; implementation is not
authorized until the integrated P1 independent review passes.

Parent subproject: [Long-Horizon Architecture Governance](../README.md)

Document kind: `decision`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/long_horizon_architecture_governance/decisions/p1b_plan_and_run_receipt_authority_decision_20260825.md`
Owner: `runtime composition and evidence architecture`
Last verified: `2026-08-25`

## Decision

The durable production interchange chain is:

```text
ExperimentRequest --single PlanCompiler--> ResolvedCompositionPlan
        |                                          |
        +---------------- native admission --------+
                                                   |
                                      immutable RuntimeInstance
                                                   |
                                  native RunRecorder/RuntimeHost
                                                   |
                                              RunReceipt
```

`ExperimentRequest` is durable intent. `ResolvedCompositionPlan` is the only
closed executable authority. `RunReceipt` is the durable, native-owned record of
what actually ran and how it ended. This per-run chain is governed by three
orthogonal durable authorities: a `ReleaseManifest` defines admitted package and
support-row bytes; a `RolloutDecision` singularly authorizes writer/routing and
cutover/backout transitions; and a native `StateCheckpoint` is the only state
that may cross an instance or package rollback. They constrain execution but do
not resolve experiment intent or create a second runtime publisher.

Current lock, projection, requested/resolved manifest, generated-header, parity
and migration artifacts retain the policy, build, qualification or historical
roles classified below; they do not remain parallel runtime interchange
authorities.

The production plan writer is one versioned `PlanCompiler` owned by
`architecture/runtime-composition`. Its reference implementation remains the
Cordis runtime producer unless a later reviewed migration replaces it atomically.
Native code parses, validates and admits complete plan bytes but does not fill
hidden defaults or independently resolve high-level intent. Python, fixtures,
diagnostics, packages and documentation cannot write an executable plan.

## Current Contract Basis And Gaps

The current repository has separately versioned and hashed request, owner
registry, admitted catalog lock, profile projection, requested manifest,
resolved composition, generated native header, backend-provider request,
composition evidence, package provenance, host/batch parity and migration
closure artifacts.

The accepted default chain establishes owner admission and deterministic
composition identity, but its current per-runtime evidence does not bind actual
executable/module/wheel bytes, full build/toolchain/ABI/platform identity,
scenario/content/config/seed, run/world/episode identity, lifecycle transitions,
result hashes or final completion. Several derivation products are also
independently sealed and permanently tested, which obscures which bytes are
authoritative at execution.

P1-B preserves every reproducibility input while reducing execution authority
to one plan and one per-attempt receipt.

## Artifact Roles And Migration Routes

Definitions:

- `durable authority`: supported long-term input, policy or evidence with its
  own retention/version contract;
- `derived`: reproducible output that can be regenerated from named durable
  inputs and tool identity;
- `transitional`: compatibility interchange accepted only during migration and
  carrying an explicit final reader/removal gate;
- `historical`: immutable prior acceptance evidence, never a live execution
  input.

| Artifact | Current role | Target classification | Target route |
| --- | --- | --- | --- |
| runtime composition request | experiment/profile intent | durable authority: `ExperimentRequest` | evolve through a versioned adapter; retain original canonical bytes/hash |
| owner authority registry | category/owner governance | durable policy authority | version independently; plan binds the exact admitted registry/decision identity |
| admitted catalog lock | sealed request-to-catalog selection | derived admission receipt, transitional interchange | PlanCompiler embeds the selected immutable entries/provenance in the plan; retain lock hash for old-plan reproduction until last reader retires |
| runtime profile projection | owner contribution join | derived build diagnostic, transitional interchange | embed resolved contributions and policies in plan; keep projection as explain/debug output, not runtime input |
| requested compatibility manifest | expanded requested graph | derived transitional build input | PlanCompiler-only intermediate; no production reader after P5-A |
| resolved simulation composition/manifest | current executable graph | transitional predecessor of `ResolvedCompositionPlan` | one P3 adapter maps and revalidates it; P5-A removes it from production interchange |
| resolved-manifest generated compatibility header | compiled default artifact | derived build output | generated only from canonical plan bytes and tool digest; cannot become a writer or fallback |
| backend provider request | internal materialization selection | derived private plan view | native validator projects it from an admitted plan; no standalone writer |
| runtime composition evidence | construction identity evidence | derived compatibility evidence | fields migrate into `RunReceipt`; old API remains a read-only projection through its reader window |
| `runtime_composition_evidence.v1.generated.h` | compiled default evidence anchor | derived transitional build output | generated from the admitted plan/evidence projection; CMake last reader migrates to plan/receipt views before removal |
| `runtime_package_diagnostics.v1.json` | Cordis package diagnostics | derived diagnostic evidence | PlanCompiler/Cordis may emit it for explanation; readers migrate to `ReleaseManifest`/receipt projections and it never controls admission |
| `producer_metadata.json` | Cordis producer/build metadata | derived release-build input | canonical producer/tool identity is admitted into `ReleaseManifest`; raw metadata retires after its build/test last readers migrate |
| package provenance/dependency graph | release/package supply-chain evidence | durable release evidence | receipt references exact immutable provenance/SBOM/attestation identities and actual package digest |
| parity budget | qualification policy | durable policy authority | versioned independently and referenced by plan/receipt where applicable |
| host/batch parity and semantic reference | qualification result and fixture | durable qualification evidence; reference fixture derived | stored outside execution authority; receipt/evidence hashes link comparable runs |
| migration closure | prior migration acceptance | historical | retained through the admitted history route; never loaded by runtime |
| fixture and invalid matrices | contract test material | derived test evidence | regenerate or retain only where it detects a lasting reader/writer invariant |
| `ResolvedCompositionPlan` | absent | durable executable authority | introduced in P3-B, closed in P5-A |
| `RunReceipt` | absent | durable run evidence | introduced in P5-B and emitted by native runtime for every attempt |
| `ReleaseManifest` | absent | durable release authority | singular release pipeline writes admitted binary/wheel/toolchain/support-row set; native/release admission validates it |
| `RolloutDecision` | absent | durable release-control authority | singular release controller writes signed prepared/cutover/adoption/backout decisions; operator approvals are inputs only |
| `StateCheckpoint` | incomplete state-replay residual | durable native state authority | per-world coordinators author fragments; `RuntimeHost` alone assembles/finalizes the aggregate; native state validator admits against plan/schema/epoch and irreversible-write boundary |

Classification does not authorize deletion. A transitional artifact retires
only after caller census, last-reader telemetry, stored-artifact migration,
reproducibility proof and its rollback window all pass.

## Release And State Authorities

| Authority | Singular writer/finalizer | Validator/admitter | Required bindings |
| --- | --- | --- | --- |
| `ReleaseManifest` | release-engineering artifact pipeline for one release identity | native release validator plus qualification gate | source/toolchain, executable/module/wheel/plugin digests, SBOM/provenance, supported rows, reader/writer generations and signing identity |
| `RolloutDecision` | one release controller using authorized operator approvals | runtime admission verifies signature, predecessor sequence and referenced manifest | release manifest, routing cohort, writer generation, P5-D cutover identity, rollback deadline/checkpoint and irreversible-write boundary |
| `StateCheckpoint` | one `RuntimeHost` aggregate writer/finalizer at an admitted barrier | native state-schema validator in the target package | complete per-world coordinator fragments plus source plan/release/run/host/boot/epoch/world/episode, transfer fence, state digests and compatible target generations |

Operator approval authorizes a proposed `RolloutDecision`; it cannot write a
plan, publish a host slot or finalize a run. The controller emits one monotonic,
signed decision log. Its `production_canary_cutover` entry is the sole P5-D
release cutover receipt; later cohort expansion and writer advancement are
successor decisions on the same routing authority, not new execution seams.

Every RunReceipt binds the exact ReleaseManifest and RolloutDecision effective
at admission. Every decision binds the admitted plan-generation range and
checkpoint (when any), and its run/canary evidence set binds the corresponding
RunReceipt identities and hashes. A StateCheckpoint binds the RunReceipt event
that committed it, and any consuming RunReceipt binds the checkpoint bytes/hash
and validation result. This bidirectional identity graph prevents an operator
record, checkpoint or package manifest from becoming an untracked second truth.

Each world `EpisodeCoordinator` is the sole semantic author of its immutable
world/episode checkpoint fragment at the native barrier. It cannot publish an
aggregate checkpoint. The `RuntimeHost` verifies expected-world coverage,
fragment identities/order/schema and the common transfer fence, then is the sole
assembler and semantic finalizer of the aggregate StateCheckpoint payload. The
native state validator is the sole consumer-side admitter. ArtifactLedger only
performs fenced conditional persistence of the already finalized envelope; it
cannot add, remove or rewrite semantic payload fields.

## ExperimentRequest Contract

The request records human/tool intent without claiming executable completeness.
It must contain:

- schema version, request identity/version and canonical bytes/hash;
- simulation/evaluation/policy intent identities;
- requested profile and capability/policy constraints;
- content, scenario and configuration references with digest requirements;
- seed or seed-generation policy;
- determinism, topology and platform constraints;
- submitter/tenant/security context where the topology requires it;
- request creation provenance and the requested PlanCompiler compatibility
  generation.

It may contain selectors and ranges. It cannot contain an untracked hidden
default. The original request is immutable and retained even when resolution is
repeated under a later admitted catalog.

## Canonical Wire, Digest And Signature Envelope

All durable authorities in this decision use UTF-8 JSON payloads and the frozen
`echelon_forge.canonical_json.v2` profile. CBOR is not an alternative wire for
these authority artifacts. The profile adopts RFC 8785 JSON Canonicalization
Scheme object ordering, string escaping and finite IEEE-754 number serialization
exactly, then adds stricter schema rules: valid Unicode without implicit
normalization; no BOM, duplicate object names, invalid escapes, NaN, infinity or
unknown authority fields. Counters/identities that may exceed the cross-language
exact integer range are lowercase unsigned decimal strings; hashes are lowercase
hexadecimal strings. Arrays preserve declared semantic order and set-like arrays
must be sorted and duplicate-free before serialization. Native and Cordis
fixtures cover negative zero, exponent thresholds, escaping, non-ASCII keys,
large counter strings and duplicate-key rejection.

Digest and signature fields are detached from the payload to avoid self-
reference. The envelope contains `envelope_version`, exact vendor media type,
`domain`, canonical `payload`, detached `payload_sha256`, and zero or more
signatures/attestations. The digest input is:

```text
UTF8("echelon-forge-authority-v1") || 0x00 ||
UTF8(domain) || 0x00 || UTF8(media_type) || 0x00 || canonical_payload_bytes
```

Signatures cover the domain-separated digest plus signer/key/algorithm context;
they never sign an ambiguous reserialization. Each artifact has a distinct
domain/media type. Parsing first rejects duplicate/unknown fields and invalid
numbers, then canonicalizes and verifies the detached digest before semantic
admission. `plan_sha256`, `receipt_sha256`, checkpoint identity and decision
identity mean the detached payload digest and are not fields inside the hashed
payload. Schema fixtures must prove identical bytes in Cordis and native code.

Local in-process integrity requires the digest envelope. External or
multi-process activation additionally requires an admitted signature,
revocation and timestamp policy under P1-C.

## ResolvedCompositionPlan Contract

The plan payload is immutable canonical JSON under the envelope above.

At minimum it binds:

1. schema and semantic contract versions, writer identity/version, plan ID and
   source request bytes/hash; the detached envelope binds plan bytes/hash;
2. the exact owner registry/admission decision and immutable catalog entries,
   implementation IDs/versions/digests and trust decisions;
3. complete plugin/provider/service bindings, provider construction order,
   component/system contributions, system registration/execution graph and
   stage contract version;
4. backend/profile/capabilities, scope and reconfiguration policies, and the
   CPU-exact canonicality decision;
5. complete configuration including time step, seed policy, content/scenario
   digests, determinism profile and platform/topology constraints;
6. compatibility generation, minimum/maximum reader generation, feature flags,
   state-schema generation and explicit rejection behavior;
7. evidence/receipt policy, required release provenance and qualification
   references;
8. no unresolved selector, environment-dependent default, filesystem search,
   network lookup or post-hash mutation.

Native admission recomputes canonical identity, validates every owner and
implementation against compiled/admitted capabilities, checks all version and
topology constraints, and constructs only from the admitted bytes. A missing or
unknown truth-affecting field rejects the plan. Native code may derive private
views such as a backend provider request; it may not repair or resolve the plan.

The checked-in default is plan bytes emitted by the same PlanCompiler, not a
special native fallback. Generator/tool identity and output hash are recorded so
the compiled header can be reproduced and compared byte-for-byte.

## Single Writer And Derivation Ownership

| Operation | Owner | Constraint |
| --- | --- | --- |
| author request | authorized caller/tool | writes intent only |
| resolve request and write plan | production `PlanCompiler` | exactly one admitted writer generation at a time |
| validate/admit plan | native plan validator | no defaults, graph rewrites or alternative resolution |
| project private provider/build views | native/build adapters | pure named derivations from admitted plan |
| instantiate and publish runtime | P1-A `RuntimeHost` | exact admitted plan bytes/hash |
| record lifecycle/results | native `RunRecorder` and host | sole production `RunReceipt` writer |
| publish release bytes/support set | release-engineering artifact pipeline | sole `ReleaseManifest` writer for one release ID |
| authorize rollout/cutover/backout | release controller | sole monotonic `RolloutDecision` writer; operator signature is authorization input |
| author per-world checkpoint fragment | that world's native episode coordinator | only at admitted barrier; fragment cannot be published as aggregate truth |
| assemble/finalize aggregate checkpoint | native `RuntimeHost` | sole semantic aggregate writer; complete ordered fragment set required |
| validate state checkpoint | target-package native state validator | exact source/target plan, schema, epoch and irreversible-boundary checks |
| persist/fence authority envelopes | evidence `ArtifactLedger` | conditional immutable writes and storage CAS only; does not author or semantically finalize payload truth |
| display/analyze evidence | Python/Cordis/diagnostics | read-only projections; cannot finalize receipt |

A replacement PlanCompiler implementation requires dual-production byte
comparison for every supported profile, independent review, a single cutover
receipt and retirement of the previous writer. Two production writers are
never accepted merely because their outputs usually match.

## RunReceipt Contract And Finalization

There is one receipt per ledger-admitted run attempt, including construction,
execution, cancellation, failure, post-header rejection and crash-reconciliation
outcomes. A failure to acquire/commit the journal header is a typed pre-admission
rejection, not an admitted run and not permission to execute. The native
`RunRecorder` first obtains a monotonic journal fencing token and conditionally
commits an append-only journal header to the durable `ArtifactLedger`. Durable
commit acknowledgement is the run-admission linearization point: no world,
episode or external truth mutation may occur before it. Store/fence
unavailability rejects the attempt.

Each record is length-framed and contains journal/run/fence identity, monotonic
sequence, prior-record hash, payload digest and frame checksum. A record is
visible only after the store's durable conditional append acknowledgement;
readers discard and report torn/partial tails. The recorder finalizes one
immutable receipt envelope by conditional state transition from `open` to one
terminal state. A finalized receipt cannot be appended or rewritten.

Crash reconciliation first atomically tombstones the prior boot and acquires a
strictly newer journal fence. Every live writer verifies its current fence
before a simulation step, external side effect or append; a resumed stale
writer fails stop. A recovery owner may then append only a terminal
`incomplete/crashed` record and finalize through compare-and-swap. On a local
filesystem backend, exclusive lock plus fsynced temporary file, atomic rename
and parent-directory fsync must provide equivalent semantics. Uncertain process
death blocks takeover until the prior process is terminated; timeout alone does
not prove death or permit two finalizers.

Required fields include:

- receipt schema/version, run/attempt/host/boot/incarnation identities and
  creation/finalization timestamps;
- exact request and plan canonical bytes or durable content-addressed locations,
  plus hashes and PlanCompiler identity;
- executable, native module/shared library, wheel/package and relevant plugin
  digests; exact `ReleaseManifest` and `RolloutDecision` identities; release
  provenance/SBOM/attestation references;
- source revision, dirty-state declaration, build mode, compiler/linker,
  toolchain, standard library, C/C++ ABI, Python/Node ABI where used, OS,
  architecture, CPU/GPU/driver and runtime dependency identity;
- scenario/content/database/configuration and seed/seed-stream identities;
- backend/profile/provider/system graph, stage contract and determinism profile;
- world, entity, episode and request identities with the P1-A epochs/generations;
- ordered construction, validation, publication, episode, drain, rollback,
  shutdown and reclamation lifecycle records;
- result/output hashes, source/created `StateCheckpoint` identities and native
  validation results, qualification comparison references and any external-
  side-effect receipts;
- terminal state `completed`, `failed`, `cancelled`, `rejected`, `crashed` or
  `incomplete`, with typed reason and the last durable sequence;
- canonicalization/hash algorithms, detached receipt payload digest, retention
  class and, where required, authenticity/signature/attestation.

Python may supply policy intent, observations or derived accounting records,
but native code validates and binds those claims before including them. A
Python-authored JSON file is not a receipt. A successful HTTP/process return is
not completion without the native terminal lifecycle record and result hashes.

Large outputs may be content-addressed rather than embedded. The receipt must
bind their digests, media types, sizes, availability/retention class and
retrieval location. It cannot point only to an ephemeral workspace path.

## Minimum Durable ArtifactLedger Foundation

P3-C establishes the non-production ledger contract and simulated backend;
P5-B qualifies the production backend before any P5-D cutover. The ledger is an
evidence/storage authority, not a plan, release or runtime writer. It provides:

- immutable content-addressed blob put/get with size/media-type/digest checks;
- conditional create, monotonic compare-and-swap and fenced append/finalize;
- durable acknowledgement, torn-write detection, tombstones and audit identity;
- access control for plan, release, checkpoint, journal, receipt and recovery
  roles;
- release-manifest retention classes covering active runs and the complete
  rollback window, plus availability and hash-correctness telemetry;
- backup/restore on every P5-D support row and a proven recovery path before
  cutover.

P7 extends this already admitted foundation with long-term history routing,
provider migration, policy consolidation and periodic restore governance. It
does not select the first durable store after P5-D.

## Version And Stored-Artifact Compatibility

`N` and `N-1` denote adjacent admitted release compatibility generations, not
arbitrary semantic-version strings.

- one PlanCompiler writer generation is active;
- an N native reader must read plans N and N-1 and emit receipts N;
- an N receipt reader must read receipts N and N-1;
- an N-1 native reader is not required to read N plans or receipts;
- unknown truth-affecting features, state schema or topology reject even when
  the outer schema parses;
- readers never silently discard fields or downgrade canonical bytes.

Upgrade order is reader-first: deploy N readers while the writer remains N-1,
prove shadow/canary behavior, then advance the sole writer to N. Stored N-1
plans remain readable during the bounded window. After the writer advances, an
N-1 rollback may execute only an existing admitted N-1 plan/checkpoint. It
cannot consume N bytes. If compatible, the original request may be resolved
again by the admitted N-1 writer; this creates a new plan identity and is never
called a downgrade of the N plan.

An N-only irreversible external write, state checkpoint or plan feature closes
the N-1 execution rollback path. The rollout must then roll forward on N or
stop. Every release manifest records reader/writer generations, last-reader
date, stored-artifact inventory and irreversible-write boundary.

## Compatibility And Migration Sequence

1. P3-B lands the canonical envelope and plan/release/rollout/checkpoint/receipt
   version shells and adapters without changing runtime truth.
2. Existing request/lock/projection/manifests are resolved by the current Cordis
   writer and adapted into candidate plan bytes; native/Cordis byte and negative
   admission conformance must pass.
3. P3-C implements N/N-1 readers, writer sequencing, stored-artifact inventory,
   `ReleaseManifest`/`RolloutDecision` shells, the minimum ArtifactLedger
   contract/simulated backend, rejection and rollback simulation.
4. P4 host work consumes the final plan shell only in dark/shadow.
5. P5-A closes all plan fields and removes hidden native/default resolution.
6. P5-B qualifies the production ArtifactLedger, native checkpoint validation,
   durable pre-admission journals and complete receipts while compatibility
   evidence remains available as read-only projections.
7. P5-D conditionally commits the sole production-canary RolloutDecision,
   advances writer/adoption only through successor decisions on that authority,
   and starts the bounded last-reader/rollback window.
8. P7-B retires transitional artifacts and controls only after stored readers,
   reproducibility and retrieval gates pass.

## Negative And Acceptance Matrix

The implementation must reject or prove all of the following:

| Case | Required result |
| --- | --- |
| request references absent/untrusted catalog entry | PlanCompiler rejection; no plan |
| plan hash/canonical bytes disagree | native admission rejection |
| plan contains unresolved/default-dependent field | writer or native rejection |
| Cordis and reference PlanCompiler outputs differ | release blocked; no majority/fallback choice |
| native reader sees N+1 or unknown truth feature | fail closed with typed incompatibility |
| N-1 reader sees stored N plan | explicit unsupported result; no downgrade |
| generated header differs from admitted plan | build/admission failure |
| executable or wheel digest differs at launch | run rejected and receipt finalized `rejected` |
| release manifest, rollout decision or checkpoint digest/signature/binding differs | admission rejected; operator approval cannot override |
| Python attempts to finalize a receipt | type/capability boundary rejection |
| process crashes before terminal record | recovery finalizes `crashed/incomplete`, never `completed` |
| durable journal header/fence cannot commit before mutation | attempt rejected before execution |
| stale boot resumes after recovery takeover | fence check fails and stale process stops before mutation/append |
| lifecycle/result identity carries another epoch | result rejected; stale record retained as failure evidence |
| referenced large artifact is unavailable | run/evidence acceptance fails according to retention class |

P1-B is accepted only when every current artifact has the classification and
version route above, the writer/validator/recorder owners are singular, and an
independent reviewer finds no unresolved critical/high reproducibility,
compatibility, rollback, authenticity or duplicate-authority gap.

## Rejected Alternatives

- Keeping every current hash-sealed intermediate as permanent interchange is
  rejected because it multiplies runtime authorities and migration obligations.
- Collapsing provenance, qualification policy and run evidence into plan bytes
  is rejected because policy/release evidence has independent retention and a
  run must bind actual execution, not only intended composition.
- Letting native code and Cordis both resolve intent is rejected even if tests
  compare outputs; equality tests do not create a singular writer.
- Silent schema downgrade or ignore-unknown behavior is rejected for
  truth-affecting fields.
- Treating composition evidence as a complete run receipt is rejected because
  actual binary/package, input, lifecycle, result and completion identity are
  absent.

## Residuals

- Concrete schemas and signing/key algorithms land in P3/P5, but UTF-8 canonical
  JSON, domain-separated detached digests and singular authority owners are
  frozen here.
- External authenticity and multi-process durable receipt transport remain
  disabled until P1-C activation gates pass.
- P3-C/P5-B must implement and qualify the minimum durable ArtifactLedger before
  P5-D; P7 owns long-term provider migration and history governance afterward.
- This decision does not delete fixtures, closure evidence or compatibility
  readers and does not claim the target chain is implemented.
