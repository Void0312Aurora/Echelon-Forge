# Long-Horizon Architecture Governance P3-C Independent Review

Document kind: `review`
Lifecycle: `accepted`
Canonical: `docs/architecture/reviews/long_horizon_architecture_governance_p3c_review_20260827.md`
Owner: `cross-domain architecture`
Last verified: `2026-08-27`

Status: `pass`

Review target: `codex/long-horizon-governance-architecture` in the isolated
worktree created from `origin/main` at
`82d5b6e893c442950e334eb3e9ec92f8174eeb35`.

Reviewer: independent `gpt-5.6-sol`, reasoning `max`, after adversarial,
repair, and final-confirmation rounds.

## Review Scope

This review covers only the non-production P3-C ledger and compatibility
foundation:

- deterministic content-addressed storage, media/role ACLs, conditional slots,
  monotonic fences, writer tombstones, journals, checkpoints, audit identity,
  snapshot restore and retention validation;
- exact N/N-1 plan, checkpoint, package and reader-first admission;
- one rollout writer, state/writer/plan coupling, non-authoritative shadow and
  qualification evidence, durable kill switches, restart recovery and typed
  backout/reopen behavior;
- Python, Cordis and native authority compatibility extensions plus generated
  fixtures and negative architecture gates.

It does not qualify a production ArtifactLedger, authenticity/signature policy,
native pre-mutation journal/RunReceipt closure, supported-row restore drills,
P4 host publication, P5-D production activation or the overall program.

## Evidence

- Focused P3-C ledger suite: `19 passed`.
- Full composition architecture suite: `102 passed, 4 skipped`.
- Cordis authority lane: `4 passed`.
- Windows/MSVC native runtime authority/contracts CTest: `4/4 passed`.
- Authority and ledger generator freshness: passed.
- `ruff check` and `git diff --check`: passed; diff check reported only the
  repository's LF/CRLF conversion warnings.
- The full Cordis producer test remains uncollected because the isolated
  worktree has no installed `cordis` package. The standalone authority lane is
  valid evidence; the missing dependency is not represented as a passing
  producer lane.

## Acceptance Conditions

P3-C can pass only if no unresolved Critical, High or Medium blocker remains;
the simulator cannot authorize production; exact N/N-1 members and rollback
state must survive restart; and a reviewer recommendation cannot replace the
long-horizon outcome with a short-term subset.

## Findings And Repair Disposition

Initial and repair reviews returned failures. The repaired tree closes the
following finding classes:

- durable controller recovery, hash-linked qualification replay and mirrored
  live/restart writer-plan-state invariants;
- exact single N/N-1 plan/checkpoint/package selection, package digest reader
  admission and checkpoint-to-decision identity binding;
- early and post-decision kill persistence, monotonic trigger union across
  restart/backout, writer freeze, typed backed-out state and explicit repaired
  reopen;
- fenced immutable checkpoint slots, single active writer, process-termination
  proof before tombstone, and recovery-only crash finalization;
- journal/checkpoint/blob/stat/snapshot ACL bypasses, journal header/frame/media
  identity, role-specific append/finalize rights and snapshot-export isolation;
- snapshot slot/fence/journal/audit/namespace/media/retention validation and
  fail-closed restore of open or terminal journals;
- proof-backed shadow/qualification evidence, exact eligible-reader identities,
  bounded state/features/topology admission and non-production-only semantics.

The final repair review specifically reproduced and then confirmed closure of
the last Medium finding: `kill -> backed-out -> restart -> new kill` now
preserves the existing durable kill record and unions reasons monotonically.
Only a typed `backed-out -> prepared` repair clears that binding and reopens
admission.

## Residual Boundaries

- P4 may consume this foundation only for dark/shadow candidate work. It still
  cannot publish production truth or retire production rebuild.
- P5-B owns selection and qualification of the real durable backend, actual
  crash/atomicity guarantees, native pre-admission journals/checkpoints,
  complete RunReceipt, authenticity/attestation, access policy and restore
  drills.
- P5-D owns supported-row qualification, the sole production-canary decision,
  caller activation, operator rollback drills and production cutover.
- Linux, package/SDK publication and the missing installed Cordis producer
  dependency are not accepted by this review.

## Verdict

`pass`

No unresolved Critical, High or Medium P3-C blocker remains, and no short-term
scope substitution was accepted. This verdict accepts only the non-production
P3-C foundation described above; the overall long-horizon program remains
`not accepted`.
