# Long-Horizon Architecture Governance P3-B Independent Review

Document kind: `review`
Lifecycle: `accepted`
Canonical: `docs/architecture/reviews/long_horizon_architecture_governance_p3b_review_20260825.md`
Owner: `cross-domain architecture`
Last verified: `2026-08-25`

Status: `pass`

Review target: `codex/long-horizon-governance-architecture` in the isolated
worktree created from `origin/main` at
`82d5b6e893c442950e334eb3e9ec92f8174eeb35`.

Reviewer: independent `gpt-5.6-sol`, reasoning `max`, after initial, repair and
final-confirmation rounds.

## Review Scope

This review covers only the P3-B authority-envelope foundation:

- the shared `authority_envelope.v1` and `authority_payloads.v1` schemas;
- Python semantic owner and one-way legacy resolved-manifest adapter;
- Cordis canonical parser/digest and release-shell lane;
- native strict envelope validator and its dependency boundary;
- checked-in canonical bytes/digest vectors and negative tests for plan,
  release, rollout, and checkpoint authorities.

It does not accept P3-C durable ledger/reader sequencing, P4 host freshness,
lease, tombstone or state-transfer implementation, P5 package/SDK/caller
cutover, Linux qualification, or overall program acceptance.

## Evidence

- Python authority/schema suite: `14 passed` after final repairs.
- Full composition architecture suite: `81 passed, 4 skipped` before the final
  three focused repair guards; the focused final suite then passed independently.
- Cordis authority lane: `4 passed`.
- Fresh Windows/MSVC native build via `VsDevCmd.bat`; authority and boundary
  CTest: `2/2 passed`.
- Cross-language vectors cover exact canonical payload bytes and detached
  digests for plan, release, rollout, and checkpoint; the checked-in generator
  freshness gate passed, and Python, Cordis, and native consume the same valid
  plan bytes instead of reconstructing them.
- `ruff check` and `git diff --check` passed; the latter reports only the
  repository's existing LF/CRLF conversion warnings.

## Acceptance Conditions

P3-B can be accepted only if the independent reviewer finds no unresolved
Critical or High finding, no second writer/parallel truth path, and no
short-term scope substitution. Passing tests alone are not sufficient evidence
for host publication or durable storage.

## Residual Boundaries

The native validator consumes the bounded, typed authority schema and checked-in
canonical bytes. General-purpose arbitrary JSON serialization, durable storage,
N/N-1 reader admission, and signature-key lifecycle remain explicitly owned by
later phases and must not be inferred from this shell foundation.

## Initial Findings And Repair Disposition

The initial review returned `fail`. Its Critical/High findings and later
repair-review findings were closed as follows:

- removed arbitrary nested/generic authoring and limited current-plan entry to
  the one-way validated legacy adapter;
- aligned schema, Python, Cordis, and native owner/version/identifier/hash/
  generation-window checks, including `prepared`, typed rollback policy and
  media/domain pairing;
- bound source request, requested manifest, legacy artifact, rollout, release,
  plan, and checkpoint identities through explicit detached hashes;
- added strict UTF-8/surrogate/BOM handling, UTF-16 key/set ordering, bounded
  numeric admission and non-empty typed signature context;
- replaced reconstructed native fixtures with generator-owned exact canonical
  bytes and added positive valid-plan, release, rollout and checkpoint
  cross-language lanes plus fail-closed negative cases;
- closed the final three High findings: rollout-to-plan chain mismatch, Cordis
  empty `supported_rows`, and missing valid plan conformance/freshness evidence.

The final reviewer independently observed Python contract `9 passed`, Cordis
`4 passed`, native `5 cases / 26 assertions`, and vector-generator freshness
exit `0`. Its optional combined Python run used an environment without
`jsonschema` and therefore did not collect; the main worktree's focused suite
had already passed `14` tests, so this is recorded as an environment gap rather
than a product assertion failure.

## Verdict

`pass`

No unresolved Critical or High finding remains. The reviewer found no
short-term scope substitution. This verdict accepts only P3-B authority shells
and their cross-language conformance; every later-phase boundary above remains
open.
