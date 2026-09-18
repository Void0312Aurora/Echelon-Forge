# Long-Horizon Architecture Governance P4-C Independent Review

Document kind: `review`
Lifecycle: `maintained`
Canonical: `docs/architecture/reviews/long_horizon_architecture_governance_p4c_review_20260919.md`
Owner: `cross-domain architecture`
Last verified: `2026-09-19`

Status: `pass` for the P4-C build-tree/internal candidate scope; production
acceptance remains gated by P5 and the remaining long-horizon phases.

## Review Scope

This review covers the first P4-C `RuntimeKernelCandidate` seam, its native
world-batch facade adapter, the Python shadow epoch fence, the P8-A caller
inventory exception, and the focused native/Python evidence. It does not
qualify maintained facade/binding migration, production publication, or the
P5 ArtifactLedger/cutover boundary.

Reviewer: independent `gpt-5.6-sol`, reasoning `max`.

## Verdict

The candidate-scope review found no unresolved Critical, High, Medium, or Low
finding. The following controls were specifically rechecked:

- Terminal host admission rejects truth-mutating leases; terminal spawn and
  kinematics writes are negative-tested, while reset remains explicit.
- Episode action idempotency keys remain monotonic across reset; terminal is a
  native/test fact rather than a caller payload convention.
- Initial plan hashes bind fail-closed to the sealed resolved composition,
  including malformed partial plans.
- Python receipts require complete canonical fields, digest, host/boot/
  incarnation identity, phase, step/barrier/reset semantics, strict u64
  values, replay/idempotency retention, and explicit acknowledgement.
- Snapshot digests derive from serialized native world state and snapshot IDs
  are candidate-unique and monotonic.
- Batch failure returns the successfully spawned prefix as an explicit
  non-atomic candidate contract; the negative path is tested.
- Target transfer admission is non-reentrant and blocks candidate world/entity
  operations and episode submission; shared kernel/control lifetime and
  value-captured deadline callbacks cover deferred host settlement.
- The candidate Python adapter is excluded from wheels, and the P8-A closure
  explicitly inventories the build-tree-only native manifest caller.

## Evidence

```text
native candidate: 3 cases, 44/44 assertions
P4-C CTest lanes: 3/3 passed
focused Python host/state-transfer/composition/P4-C gates: 42 passed
document links: 207 documents, 1760 links, 0 issues
git diff --check: passed (LF/CRLF conversion warnings only)
```

## Residuals Outside This Verdict

These are later gates, not candidate-scope findings: maintained
`RuntimeFacade`/binding/example/diagnostic migration and full parity;
production caller cutover and package publication; complete replacement,
recovery, restart, rollback, stress, resource and concurrency qualification;
cross-process WAL locking and released-version N-1 fixtures; durable
ArtifactLedger qualification; and retirement of the production rebuild truth
path.
