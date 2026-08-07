# WP Closure Lane Policy

Language:

- English canonical: `wp_closure_lane_policy.md`
- Chinese companion: [wp_closure_lane_policy.zh.md](wp_closure_lane_policy.zh.md)

Status: `2026-05-20` authoritative for reducing WP documentation synchronization
work on the main implementation path.

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/engineering/automation/standards/wp_closure_lane_policy.md`
Owner: `engineering/automation`
Last verified: `2026-08-07`

This policy separates implementation progress from publication closure. It is
intended to keep architecture and code work moving while preserving traceable WP
records.

## State Model

- `Mergeable`: code, focused tests, English canonical task notes, and named
  residuals are complete enough for the implementation stream to continue.
- `Blocked`: the stream has reached its declared round or risk budget and
  cannot safely delete, migrate, or complete a surface without a replacement,
  owner decision, or public API change. `Blocked` must include owner, reason,
  replacement condition, validation gap, and forced review trigger.
- `Closed`: the mergeable stream has also completed acceptance review,
  README/index synchronization, required bilingual companions, archive decisions,
  and traceable residual ownership.

Documentation closure must not reopen implementation scope. If closure discovers
a technical gap, it records a blocked residual or sends the item back to a new
implementation stream rather than silently rewriting the verdict.

`Blocked` is a valid close-out record, not an acceptance result. It should be
preferred over repeated partial waves when the remaining work is unsafe or
underspecified.

## Main Implementation Lane

The main lane owns:

- WP scope and non-goals.
- Code and focused tests.
- English canonical task or cluster notes needed by the active implementation.
- Exact validation commands and outcomes.
- Residual IDs with owner, reason, and next step.

The main lane should avoid editing README indexes, review indexes, archive
trees, and broad bilingual surfaces during active implementation unless those
edits are required to unblock the current code or test change.

The main lane should also keep an explicit documentation budget. Creating more
planning files is not neutral: if the budget is exceeded, the stream should stop
for re-baseline instead of producing another queue or ledger.

## Closure Lane

The closure lane owns:

- Acceptance review publication.
- Simulation architecture README and review README synchronization.
- Required bilingual companions for Tier A or WP acceptance surfaces.
- Archive or superseded-review placement.
- Cross-reference cleanup and broken-link repair.
- Final `Closed` status updates.

The closure lane should run as a serial integration pass after parallel clusters
return handoff packets. It may be assigned to a subagent because its work is
bounded, mostly mechanical, and easy to verify with audit tooling.

## Worker Handoff Packet

Each implementation worker should return:

```md
Stream: WPx-A / WPx-B / ...
Scope: one-sentence scope
Status: pass | fail | blocked
Touched files:
Commands run:
- <exact command> -> passed | failed | blocked
Evidence:
- implementation/test/doc evidence
Residuals:
- ID / owner / reason / next WP or stream
Integration notes:
- shared files left for closure lane
Closure impact:
- README/index update needed?
- required zh companion?
- archive or superseded-review action?
```

## Automation

Use the read-only closure audit before assigning or accepting a closure lane:

```bash
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP9
```

Use `--strict` when a WP is expected to have no error-level closure gaps, and
`--json` when passing the checklist to another worker.

The audit is intentionally scoped to WP task/review closure. It does not replace
semantic review, test execution, or bilingual human review.
