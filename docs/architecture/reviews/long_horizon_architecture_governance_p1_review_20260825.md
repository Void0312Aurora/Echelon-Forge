# Long-Horizon Architecture Governance P1 Independent Review

Status: `2026-08-25` accepted P1 architecture-decision review after initial
review, two repair reviews, and one focused final confirmation. The overall
long-horizon program remains not accepted and no runtime migration is proven.

Parent subproject:
[Long-Horizon Architecture Governance](../work/active/long_horizon_architecture_governance/README.md)

Reviewed decisions:

- [P1-A host lifecycle and episode authority](../work/active/long_horizon_architecture_governance/decisions/p1a_host_lifecycle_and_episode_authority_decision_20260825.md)
- [P1-B plan and RunReceipt authority](../work/active/long_horizon_architecture_governance/decisions/p1b_plan_and_run_receipt_authority_decision_20260825.md)
- [P1-C rollout, operations and security](../work/active/long_horizon_architecture_governance/decisions/p1c_rollout_operations_and_security_decision_20260825.md)

Document kind: `review`
Lifecycle: `maintained`
Canonical: `docs/architecture/reviews/long_horizon_architecture_governance_p1_review_20260825.md`
Owner: `cross-domain architecture review`
Last verified: `2026-08-25`

## Review Decision

Final integrated verdict: `pass`.

P1-A, P1-B and P1-C have no unresolved critical or high architecture-decision
finding. The final focused confirmation also closed the last medium checkpoint-
source ambiguity. No review detected replacement of the long-horizon outcome
with short-term cleanup or scope contraction.

This verdict accepts the target decisions and their phase dependencies. It does
not claim that host lifecycle, contracts, ArtifactLedger, RunReceipt, platform
support, package boundaries, rollout, operations or security are implemented.
P2/P3 may be dispatched subject to their own entry gates; P4-P8 remain planned.

## Independence And Review Configuration

The reviewer was an independent read-only agent using:

- model: `gpt-5.6-sol`;
- reasoning: `max`;
- write authority: none;
- review worktree:
  `D:\workshop\Research\Echelon-Forge\.worktrees\long-horizon-governance-architecture`;
- branch: `codex/long-horizon-governance-architecture`;
- reviewed HEAD before persistence:
  `bc5ee3515002f08ca88d6e432e3f63145fe99995`;
- remote baseline: `origin/main`
  `82d5b6e893c442950e334eb3e9ec92f8174eeb35`.

The reviewer did not draft or edit the decisions and did not run commands that
produce build/cache/temp artifacts. It inspected the project packet, P0
inventory, current runtime/binding/contract/package/CI source and each frozen
decision snapshot.

## Reviewed Snapshot Ledger

| Round | P1-A SHA-256 | P1-B SHA-256 | P1-C SHA-256 | Verdict |
| --- | --- | --- | --- | --- |
| initial | `8386dc05cdb82843e01719451d8931ebd9c425bc1a736cc6e573d44bf523971b` | `27fc409cce3d94e70a579525ac06ff8cbaec1f305bc1b5d44857591a6c587d92` | `3baea1d092e9ee7ae5536245782fe23b55939f9276ab0fd437839ffaa2901783` | repair-required |
| first repair | `7019736536a4c36ab25a23f63af8a39ecd2b360dc4d4a18e22f687b265342762` | `c6902e3e000cf996bd6576ef81143382c635dc964ae85305aa1471c4224064c0` | `3236a6e39c4ce93a5ca35967cbaf2409e27f84540565a8768d21bf88279a7279` | repair-required: original high findings closed, two new high lifecycle gaps |
| second repair | `310835bc87404c9daa0fb67c5e415f0ec034c584e47d09494c99a04106381cbf` | `95905e1b2cffe22ad3a2494838cba96ea1a29119b5e56df0bbea1f9ea705d3b1` | `8d5fa10f4a34710b8cbe361a01bb89b6fbcec969db16406e5ec517c024f835fb` | pass; one non-blocking medium clarification requested |
| final confirmation | unchanged | unchanged | `3a03b4d6997ed9ba8e603cb7d176e15f3b1c7919729a6abf79bca093a56031ed` | pass; final medium closed |

The final hashes above identify the accepted decision content. The subsequent
commits persist those bytes and this review record; commit identity is delivery
metadata, not a substitute for the content hashes.

## Initial Review Findings And Disposition

Initial review returned no critical finding, eight high findings, four medium
findings and two low findings.

| ID | Finding | Final disposition |
| --- | --- | --- |
| `H-01` | state export could occur before old truth stopped mutating | closed: explicit `quiescing -> transfer_commit_ready`, final hash/sequence fence and jointly linearized lease admission/publication |
| `H-02` | active failure could bypass drain and zero-lease reclamation | closed: `active_faulted` must recover, shut down or quarantine; retired is reachable only after verified reclamation |
| `H-03` | production canary preceded the claimed unique P5-D cutover | closed: conditional commit of the first `production_canary` RolloutDecision is the sole release linearization point |
| `H-04` | release, rollout and checkpoint objects could become unclassified truth authorities | closed: ReleaseManifest, RolloutDecision and StateCheckpoint have singular writers/validators, canonical identities and bidirectional RunReceipt bindings |
| `H-05` | canonical UTF-8/possible CBOR and self-hash rules conflicted | closed: RFC 8785-based UTF-8 JSON profile, strict schema constraints and domain-separated detached digest/signature envelope |
| `H-06` | RunReceipt journal lacked durable admission and recovery fencing | closed: header durable acknowledgement precedes mutation; frames detect torn tails; boot tombstone/fence and CAS finalization prevent stale writers |
| `H-07` | same-process instance rollback and native package rollback were conflated | closed: same-release recovery uses new epoch; binary/wheel rollback stops/restarts under new boot and reconnects callers |
| `H-08` | durable artifact storage was deferred until after the cutover that needed it | closed: P3-C establishes ledger foundations and P5-B qualifies production storage before P5-D; P7 extends long-term governance |
| `M-01` | current producer diagnostics/metadata/generated evidence artifacts were omitted | closed: each real artifact has derived/transitional role, reader route and retirement gate |
| `M-02` | broad caller classes did not crosswalk P0's nine surfaces/23 paths | closed: every path is named; the 11 mixed compatibility paths are individually classified |
| `M-03` | inner world/entity/episode/request generations lacked ABA/exhaustion rules | closed: zero-invalid, monotonic/tombstoned, enclosing-generation-bound and fail-closed exhaustion rules |
| `M-04` | quarantine was outside the resource bound | closed: one process-wide quarantine budget freezes replacement and excess requires fail-stop |
| `L-01` | immutable slot terminology obscured mutable services | closed: immutable identity/service pointers are separated from synchronized mutable truth/counters/journal |
| `L-02` | reviewed decisions were not yet persistently anchored | closed by the split commits that include final decision hashes and this review record |

## First Repair Review Findings And Disposition

The first repair review confirmed the original high findings were closed, then
returned two new high findings caused by missing lifecycle paths.

| ID | Finding | Final disposition |
| --- | --- | --- |
| `NH-01` | first host bootstrap and checkpoint recovery had no legal publication path | closed: mutually exclusive `initial`, `replacement` and `checkpoint_recovery` transactions share one `publish_slot` CAS, lifecycle ticket and receipt authority; faulted truth is never exported and absence of a checkpoint fails closed |
| `NH-02` | normal shutdown had no legal non-failure transition | closed: idempotent terminal shutdown shares the lifecycle ordering domain, has explicit publication-race winner rules, cancels candidates, drains published slots and never reports clean stop with quarantine/live leases |
| `NM-01` | checkpoint author/aggregate writer/storage finalizer roles were still combined | closed: each world coordinator authors one fragment, RuntimeHost alone assembles/finalizes the aggregate, native validator alone admits, and ArtifactLedger only fences/persists |

## Final Medium Confirmation

The second repair review passed with one non-blocking precision finding:

| ID | Finding | Final disposition |
| --- | --- | --- |
| `N-M-01` | package-restart text could imply checkpoint creation from faulted/quarantined truth | closed: only a healthy source at an admitted barrier may author a new checkpoint; a faulted/quarantined source uses a previously durable admitted checkpoint or abandons the attempt and starts a new run |

The final reviewer confirmation reported no new critical/high, no second
checkpoint authority and an integrated `pass`.

## Accepted Long-Horizon Decisions

P1 acceptance freezes these outcomes:

1. One native host owns initial, replacement and checkpoint-recovery publication
   through one CAS/ticket/receipt primitive, plus a separate terminal shutdown
   transaction in the same ordering domain.
2. Normal replacement stops old truth mutation before final export; recovery
   never exports faulted truth; all generations, leases, drain, quarantine and
   reclamation fail closed.
3. Native code is the only episode barrier owner; Python uses a versioned,
   idempotent intent/receipt handshake after the unique production cutover.
4. ExperimentRequest, ResolvedCompositionPlan and RunReceipt are the per-run
   chain, constrained by singular ReleaseManifest, RolloutDecision and
   StateCheckpoint authorities.
5. Authority payloads use canonical JSON with detached domain-separated
   digests; durable journal admission and recovery fencing precede truth
   mutation.
6. P3-C/P5-B establish and qualify ArtifactLedger before P5-D. P7 owns later
   retention/provider-migration governance, not first storage selection.
7. The first production-canary RolloutDecision is the only P5-D release cutover;
   later decisions only advance its admitted cohort/writer schedule.
8. Same-release checkpoint recovery and stop/restart package rollback are
   distinct, receipt-bound protocols.
9. Windows/Linux native and wheel rows remain required target families but are
   not called supported until release qualification passes. Unsupported Node,
   external and multi-process paths fail closed; CPU exact remains canonical.

## Validation Evidence

The main thread ran these non-runtime decision gates on the repaired worktree:

- `git diff --check`: pass (line-ending conversion warnings only);
- document link audit: `203 documents`, `1716 links`, `0 issues` before this
  review file was added;
- bilingual maintained-surface audit: `74/74 synced`;
- focused documentation architecture tests: `25 passed`;
- composition architecture tests: `69 passed, 4 skipped` using the repository's
  architecture `--confcutdir` boundary;
- simulation composition and composition evidence contract checks: pass;
- request/lock projection validation returned the accepted request/lock hashes;
- migration closure validation returned
  `498c64f4f9fc85395939e9056280ad9bd5e4ebc6df84d58b83763cb16f85d5b2`.

The initial unqualified top-level composition pytest invocation failed because
`tests/conftest.py` correctly refused to load an `ef_py` extension outside the
current worktree. It was not counted as a project regression; the architecture
entry with `--confcutdir tests/architecture` passed. No P1 runtime implementation
test is claimed because P1 contains decisions only.

## Remaining Boundaries

- The concrete ArtifactLedger backend and its Windows/Linux durability are not
  implemented or accepted.
- Lifecycle model checking, process restart, fault injection, restore, wheel and
  platform gates remain P3-P8 work.
- Exact DTO/checkpoint schemas and native/Python handshake code do not yet
  exist.
- Current production runtime, raw bindings and in-kernel rebuild remain
  unchanged until the unique P5-D cutover and rollback gate.
- Overall program acceptance remains `not accepted`.
