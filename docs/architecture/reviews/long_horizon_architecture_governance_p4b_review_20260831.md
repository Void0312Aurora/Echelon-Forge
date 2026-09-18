# Long-Horizon Architecture Governance P4-B Independent Review

Document kind: `review`
Lifecycle: `maintained`
Canonical: `docs/architecture/reviews/long_horizon_architecture_governance_p4b_review_20260831.md`
Owner: `cross-domain architecture`
Last verified: `2026-09-13`

Status: `pass` for the P4-B dark/shadow candidate; production acceptance remains gated by P5

Review target: `codex/long-horizon-governance-architecture` in the isolated
worktree created from `origin/main` at
`82d5b6e893c442950e334eb3e9ec92f8174eeb35`.

Reviewer: independent `gpt-5.6-sol`, reasoning `max`; first integrated audit
and post-repair re-review of the P4-B state-transfer and episode-authority
candidate.

## Retention Note

This record was persisted on `2026-09-01`, after the repair pass it describes.
The first audit's findings had until then been summarized only inside the
subordinate [P4-B remediation route](../work/active/long_horizon_architecture_governance/p4b_remediation_route_20260830.md),
which the program's own P0-C protocol does not accept as a substitute for a
persisted review with finding dispositions. The findings and dispositions below
are reconstructed from that route's post-audit repair record and from the
implementing commits; the verdict, severities and repair content are unchanged.
Consequently this document is `maintained`, not `accepted`: it carries no
content-hash ledger of its own, and the pending re-review supersedes it.

## Review Scope

This review covers the P4-B state-transfer and episode-authority candidate only:

- host-issued single-use owner admission handles bound to host boot identity,
  slot incarnation, resource identity, generation and authenticator;
- durable owner import transactions with monotonic status, deadline,
  cancellation, idempotent commit/abort and interruption recovery;
- the twelve-category typed decoder and replay matrix with exact N/N-1 behavior,
  unknown-field policy and directional compatibility;
- native episode-barrier authority and the versioned Python mirror handshake.

It does not qualify production handle authentication, the P5-B production
ArtifactLedger, cross-process replay, P4-C candidate integration, or caller
cutover.

## Findings And Dispositions

### Critical

`P4B-C1` — Host publication could decide commit or rollback without first
running durable owner recovery, so an interrupted transfer could be resolved
against stale authority state.
**Disposition: repaired.** Publication now retains the pre-CAS authority
snapshot, invokes durable owner recovery before deciding, and keeps an explicit
source-slot link for retryable ambiguous outcomes. A recovery retry can either
restore the source or complete the target publication; unresolved outcomes stay
fail-closed and quarantined.

`P4B-C2` — Composite imports could leave already-committed child owners
committed after a later owner failed, producing partially transferred truth with
no compensation path.
**Disposition: repaired.** Owner transactions expose explicit
recovery/compensation hooks, and composite imports compensate committed children
in reverse order. World and component-subset restore paths take a pre-image and
compensate mutation failures.

### High

`P4B-H1` — Terminal WAL rows could be reopened without verifying the owner that
wrote them.
**Disposition: repaired.** Terminal rows require owner verification on reopen.

`P4B-H2` — A torn tail in the append-only journal was not truncated during
journal construction.
**Disposition: repaired.** Torn tails are truncated at construction and the file
append path takes an OS-level writer lock.

`P4B-H3` — The decoder matrix disposition was advisory rather than enforced, so
a profile could admit an owner whose disposition contradicted the P1-A table.
**Disposition: repaired.** Disposition is enforced at profile admission.

`P4B-H4` — Source and target registries could be the same object or capture the
same kernel, allowing a transfer to be "proved" against itself.
**Disposition: repaired.** Registries must be distinct and owner-bound; the
opaque owner pointer is retained as a provenance token so two registries
capturing one kernel cannot be paired.

`P4B-H5` — Replacement proofs could pass with a zero drain deadline, and a
target control without real transfer exclusivity could authorize import.
**Disposition: repaired.** Replacement proofs require a non-zero drain deadline;
target controls must expose a real transfer fence around the owner reservation,
and the base control fails closed until that fence exists.

`P4B-H6` — ECS export accepted unresolved `msg_arg` references, and
`SystemHealth` decoding accepted missing required keys.
**Disposition: repaired.** Entity-bearing `msg_arg` variants are mapped through
logical entity identities and unresolved references are rejected, while generic
message arguments and tactical track identities retain their scalar domain;
`SystemHealth` decoding rejects missing required keys.

`P4B-H7` — The Python cache rederive path did not rebuild all mirror surfaces,
leaving poisoned caches after a transfer.
**Disposition: repaired.** The rederive path clears and rebuilds command-chain,
behavior, scripted-controller and reward mirror state. Host-bound native owner
registries require a target callback for invoking the hook after native import;
host-neutral fixtures may omit it.

## Evidence At Repair Close

Remeasured `2026-09-01` on the committed tree:

```text
targeted native candidate tests: 60 cases, 59 passed / 1 failed;
                                 1607 assertions, 1607 passed
focused Python architecture/mirror tests: 16 passed
document link audit: 206 documents, 1753 links, 0 issues
bilingual audit: 74 pairs, 74 synced, 0 diverged
governance architecture tests: 25 passed
git diff --check: passed (LF/CRLF conversion warnings only)
```

The `1609 assertions` figure previously recorded in the candidate document
predates this repair pass and no longer reproduces.

## Open Defect Carried Into Re-Review (first-round snapshot)

The following records the first-round audit state before the child-entity
closure repair. It remains in the review history so the finding disposition is
traceable; the current implementation evidence is recorded in the follow-up
note below.

`ECS owner covers maintained database platform definitions` fails closed with an
unresolved `active_helo_entity_id` reference. This is a child-entity transfer
scope decision, not a codec defect: `SimulationKernel::spawn_unit` tags only the
entity the factory returns, so factory-internal children (the pre-spawned
embarked helo, the per-station munitions) stay outside the `SimObject` snapshot
set while `EmbarkedAirOps` still references the helo. Every candidate repair
moves an authority the reviewer owns — widening the tag pulls `ChildOf` pairs
into the snapshot and shifts the rebuild barrier's `SimObject` count, declaring
the field rederive contradicts the P1-A `transfer` disposition, and dropping the
guard reintroduces dangling references. Full analysis is in the remediation
route's open-defect section.

The re-review must disposition this explicitly rather than accept a widened tag
as an incidental fix.

## Post-repair verification note (2026-09-13)

The implementation now admits the transitive factory-owned `ChildOf` closure
into the `SimObject` transfer set, carries hierarchy edges as logical-name
pairs, and keeps unresolved non-zero entity-bearing references fail-closed.
Tactical track identities and generic message arguments retain their typed
scalar meaning, while target-bearing compatibility messages map `msg_arg`
through entity identities. World restore requires the explicit `SimObject` tag,
component-subset restore rejects non-`SimObject` name collisions, and live WAL
objects truncate a torn tail before same-instance recovery. The maintained
database-platform round-trip covers a mutated embarked-helo child, loadout
munition state, hierarchy restoration, malformed relation rejection, and
destroyed-child non-resurrection. The fresh Windows/MSVC candidate executable
reports:

```text
test cases: 66 | 66 passed | 0 failed | 0 skipped
assertions: 1717 | 1717 passed | 0 failed
```

The independent post-repair review re-ran the integrated audit against the
current shared tree and found no residual Critical, High, Medium, or Low finding
within the declared P4-B dark/shadow candidate scope.

## Verdict

- first-round findings: 2 critical, 7 high — repaired and independently
  re-verified; current candidate-scope findings: 0 critical, 0 high, 0 medium,
  0 low.
- short-term substitution detected: no.
- verdict: `pass` for the P4-B dark/shadow candidate only.

Production-boundary residuals remain outside this verdict: cross-process WAL
reader/truncate locking, real released-version N-1 fixtures, and ChildOf
ownership outside the `SimulationKernel::spawn_unit` factory-owned closure.
These remain P5 qualification work and must not be represented as production
acceptance.

## Post-repair independent review record (2026-09-13)

The independent reviewer verified the current source, diff, native candidate,
focused Python contract/execution/bootstrap tests, CTest candidate lanes, and
maintained documentation audits. Evidence:

```text
candidate native: 66/66 test cases, 1717/1717 assertions
P4-B CTest lanes: 2/2 passed
focused Python P4-B plus message/track regressions: 54 passed, 2 subtests passed
document links: 206 documents, 1754 links, 0 issues
bilingual audit: 74 pairs, 74 synced, 0 diverged
```

The full CTest invocation is intentionally not treated as green because the
build directory does not contain 17 unrelated legacy executables; those tests
are `Not Run`, not P4-B failures.
