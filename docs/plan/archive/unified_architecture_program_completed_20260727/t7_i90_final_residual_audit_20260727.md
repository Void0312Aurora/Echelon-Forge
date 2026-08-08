# T7 I90 Final Residual Audit (2026-07-27)

Language:
- English canonical: `t7_i90_final_residual_audit_20260727.md`
- Chinese companion: [t7_i90_final_residual_audit_20260727.zh.md](t7_i90_final_residual_audit_20260727.zh.md)

Document kind: `report`
Lifecycle: `maintained`
Canonical: `docs/plan/archive/unified_architecture_program_completed_20260727/t7_i90_final_residual_audit_20260727.md`
Owner: `unified architecture program workline`
Last verified: `2026-07-27`
Baseline/source landing head: `5a2c75f7`
Landing commit: `5b728ac2`

Status: **I90 accepted — final residual audit clean pass 2.**

This report is the final T7 evidence record after the I89 narrow repair pack.
It records the two post-repair clean passes and retained survivor
classifications; it does not authorize deletion, normalize user worktrees,
or reopen held work.

## 1. Scope and two-pass evidence

The material I89 repair landed at `a272fc04`; `5a2c75f7` is the subsequent
ledger/hash settlement and I90's audit source head. The I90 report/ledger
closure landed at `5b728ac2`. Both clean passes used that source tree and a
matching `EF-landing\build-local-win` runtime build:

| Pass | Checkout | Evidence | Independent review |
|---|---|---|---|
| Post-repair confirmation | `EF-landing` at `5a2c75f7` | maintained smoke `753 passed, 4 skipped, 45 subtests`; `ef_test` 143 / 19,147; CTest 8/8; focused content 26, I87 13, T8/T9 99; generators fresh; Ruff clean | `i89_landing_review`: PASS |
| I90 fresh pass | fresh `codex/i90-final-residual-audit` at `5a2c75f7` | maintained smoke `753 passed, 4 skipped, 45 subtests`; `ef_test` 143 / 19,147; CTest 8/8; registry 90/90; links 182 documents / 2,802 links / 0 issues; no exact duplicate >= 0.1 MB; test-system inventory complete | `i90_bounded_review`: PASS/CLEAN |

The only environment noise was inability to read the user-level global Git
ignore file in the sandbox; worktree porcelain, source status, and project
gates remained readable and clean.

After this report and its bilingual/index registrations were added, the
docs-only closure gate also passed: registry 91/91 synchronized and link audit
184 documents / 2,820 links / 0 issues. No source or test files changed during
that closure step.

## 2. Final survivor classification

Every survivor is classified below. Detailed evidence and owner-gated next
steps remain in [I89 Residual Disposition](t7_i89_residual_disposition_20260727.md).

| ID | Classification | Final reason / retained boundary |
|---|---|---|
| D-01 | `held` | GPU packed/SoA helper layouts lack an accepted maintained GPU ABI/projection owner; exact-runtime/GPU evidence is required. |
| D-02 | `held` | I83 extracted the measured WorldBatchCore seam; mode-specific ownership awaits WP4 parity and performance evidence. |
| D-03 | `held` | Three active naval N4 configs lack a typed Experiment owner; domain protocol and byte-preserving freshness gate are prerequisites. |
| D-04 | `intentional` / `uneconomic` | Distinct MATRIX_DIR extension contracts are freshness-pinned; consolidation adds churn without reducing drift risk. |
| D-05 | `intentional` governance / product expectations `held` | T6 xfails and conditional skips are per-node and reasoned until calibration or product authority changes. |
| D-06 | fixed text / remaining semantics `held` | I87 wording is accepted/landed; declared-but-open readers retain their semantic owner boundary. |
| D-07 | fixed evidence pointers / behavior `held` | T9 adapter references are current; no-mapping remains the evidence-backed verdict. |
| D-08 | `fixed` | I96 flags and I89 sensor_refs parity match the C++ loader for empty/non-array/non-string/non-empty shapes. |
| D-09 | `held` | Rollback scan scope excludes scripts/root entrypoints pending caller taxonomy and positive inventory. |
| D-10 | `held` | Logistics fuel-blocked command semantics lack an owner and typed rejection/hold contract. |
| D-11 | `held` | Loadout replenishment semantics and int-keyed codec boundary lack an accepted typed contract. |
| D-12 | `held` | Jettison drag has no authoritative aero/model owner or validated transition. |
| D-13 | `held` | Main worktree retains 857 untracked entries in 58 temp dirs (11,745 files / 198.93 MiB); retention authority is absent. |
| D-14 | `held` | Six dirty non-target worktrees remain user/agent-owned until provenance and cleanup decisions are explicit. |
| D-15 | `held` | Empty `.git/worktrees/EF-w24-i88/refs` was reported as garbage, but the linked worktree is live; no metadata mutation is authorized. |

## 3. Stop-condition verdict

- Maintained entry navigation is clean at the audit snapshot: 182 documents and 2,802 links, zero issues; bilingual registry 90/90. The subsequent docs-only closure is 91/91 and 184/2,820 (zero issues), as recorded above.
- No unreachable production body or unowned compatibility path was found in the active audit surface. The three logistics TODOs and external workspace residues have named owners and next gates.
- Remaining duplicate schemas/helpers are owner-backed, intentional, or held behind exact-runtime, domain, performance, or cleanup authority.
- No archive/evidence or user-owned workspace was deleted.
- Two consecutive post-repair clean passes completed with independent review.

**T7 is complete. I90 is accepted and is the final queue item.** Future held-item reopening requires a new, separately numbered evidence slice; it must not be appended to I90 or rewrite this clean-pass result.

## Related

- [I89 Residual Disposition](t7_i89_residual_disposition_20260727.md)
- [I72+ Iteration Queue](iteration_queue_i72_plus_20260726.md)
- [Repository Consolidation Plan](../repository_consolidation_completed_20260729/README.md)
- [T6 Residual Ledger](t6_residual_ledger.md)
