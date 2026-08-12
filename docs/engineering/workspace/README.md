# Workspace Engineering

Language:
- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/engineering/workspace/README.md`
Owner: `engineering`
Last verified: `2026-08-13`

This owner covers the shape of a checkout rather than its contents: where linked
worktrees live, which account owns their files, and how long a path may get
before host tooling stops being able to open it. Build configuration, CI lanes,
and test organization belong to other engineering owners.

## Current Authority

- [Worktree and Path Policy](worktree_and_path_policy.md): worktree placement
  and lifecycle, the elevated-shell ownership trap, the 200-character
  repository-relative path budget, and the repair runbooks for both.

## Enforcement

| Surface | What it holds |
| --- | --- |
| [`tools/maintenance/audit_worktrees.py`](../../../tools/maintenance/audit_worktrees.py) | Read-only audit: worktree placement, `git status` reachability, untracked residue. Exits non-zero on any finding. |
| [`tests/architecture/governance/test_path_length_budget.py`](../../../tests/architecture/governance/test_path_length_budget.py) | Ratchet gate on the relative-path budget, baselined in `path_length_baseline.json`. |
| [`tests/architecture/governance/test_worktree_audit_contract.py`](../../../tests/architecture/governance/test_worktree_audit_contract.py) | Classification contract for the audit script, run against synthetic inventories only. |

The audit script is deliberately not wired into a test. The repository's live
worktree inventory is developer-local state that no commit can fix, so a gate
asserting it is clean would fail on machines whose checkout is fine. Run the
audit when a worktree misbehaves, and before handing a machine to someone else.

## Routing Boundary

- This owner defines where a checkout may sit and how long its paths may be.
- Content owners still decide what files exist; the path budget only constrains
  how deeply they may be nested.
- Host-level configuration (registry long-path support, account ownership) is
  documented here as diagnosis material, not owned here.

## Reverification Triggers

Update this index when the worktree layout policy changes, when the path-length
budget or its baseline is regenerated, or when an enforcement surface listed
above moves or is retired.
