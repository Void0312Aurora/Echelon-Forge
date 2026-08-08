# RB11 CUDA-Resident Program Closure

Language versions:

- English canonical: `cuda_resident_rb11_closure_20260731.md`
- Chinese companion: [cuda_resident_rb11_closure_20260731.zh.md](cuda_resident_rb11_closure_20260731.zh.md)
- Machine-readable record: [cuda_resident_rb11_closure_20260731.json](cuda_resident_rb11_closure_20260731.json)

- Closure id: `rb11.closed_without_promotion.cuda_resident.20260731`
- Date: `2026-07-31`
- Branch: `codex/cuda-resident-backend`
- Pre-closure head: `e5ea624fc1688d6e9d8b00ae64670ddcc2e3bd02`
- Baseline/main head: `395e02b7dfeaa87baedb2611ec503d14ab137ce3`

## Disposition

The branch-local CUDA-resident program is **closed without promotion**. The
implemented backend remains an unmaintained research candidate. It is not
selected by RuntimeFacade, is not advertised by maintained support projection,
and does not replace the maintained CPU backend.

RB11 makes no runtime, CUDA kernel, support, ABI, manifest, fallback, tuning,
or semantic change. It records the closure boundary and guards it. A future
implementation cycle requires a new explicit program; this branch does not
silently reopen itself.

The documentation/test write set is limited to this machine-readable record
and bilingual closure pair, the bilingual program terminal status, both
exact-runtime and parent-plan README pairs, the iteration ledger, a new closure
guard, and the terminal-state assertions in the existing RB10 continuation
guard.

The two `.gitattributes` rules added in this iteration are part of the closure
write set: they mark the RB10 decision JSON and this closure JSON as `-text` so
their committed bytes, and therefore their hashes, do not drift under
`core.autocrlf` on another checkout.

## Repository and publication snapshot

Immediately before RB11, the candidate branch contains eleven reviewed commits
above baseline and has merge-base `395e02b7...` with local `main`. Local
`main` remains exactly at that baseline; the candidate is not merged into it.
No local remote-tracking ref contains the pre-closure head. That remote
observation is intentionally scoped to the existing local ref snapshot without
a fetch; it is not a claim about unseen server state.

The branch and its independent worktree are retained. RB11 does not delete,
archive, merge, or push them. This preserves the complete RB0-RB11 evidence and
makes later inspection recoverable without altering the maintained worktree.

## Post-closure publication authorization

On `2026-08-05`, the repository owner explicitly authorized publishing the
retained branch and opening a pull request against `main`. This later
authorization changes distribution state only: it does not reopen RB0-RB11,
authorize RuntimeFacade promotion, advertise maintained support, select the
CUDA backend by default, or convert the held measurements into promotion
evidence. Any pull request must describe the implementation as an unmaintained,
fail-closed research candidate and preserve the CPU backend as the maintained
default.

The repository and publication snapshot above remains the historical RB11
snapshot. Its executable guard therefore reconstructs the frozen baseline,
RB10 ancestry, commit count, and absence of pre-closure merge commits from
immutable commit ids. It no longer asserts the current `main`, worktree, or
remote-ref state, because those operational refs are expected to change after
the separately authorized publication.

## Accepted chain before the closure commit

| Iteration | Commit | Outcome |
| --- | --- | --- |
| RB0 | `e7f3b144` | Program frozen |
| RB1 | `91195ea8` | CPU backend seam |
| RB2 | `6df115c0` | Admission/parity contract |
| RB3 | `6e1a3b67` | CUDA lifecycle shell |
| RB4 | `939f962a` | Resident state barriers |
| RB5 | `f287a4f8` | Phase A controls |
| RB6 | `3e4f4f44` | Phase B dynamics |
| RB7 | `4fe0f15c` | Phase D projection/device view |
| RB8 | `1304d050` | Replay/shadow harness |
| RB9 | `c2175790` | Held performance evidence |
| RB10 | `e5ea624f` | Hold decision |

The RB11 commit is represented as `this_commit` in the machine-readable record
because a commit cannot embed its own hash. Branch history remains the source
of truth for the final identity.

## Retention and rollback boundary

- Maintained recovery requires no rollback: local `main` was never advanced by
  this program and remains at the baseline commit.
- Candidate recovery is the retained branch, worktree, and reviewed commit
  chain. Compact RB9 evidence and the RB10 hold decision remain tracked.
- No destructive cleanup is performed. Future worktree/branch deletion needs
  explicit user authorization after a fresh worktree/ref audit.
- If this work is reconsidered, it must start from a new authorization and
  remeasure a full facade-equivalent window, learner consumption, required
  counters, parity release, and small-batch policy. The world-4 provisional
  private threshold cannot be reused as promotion authority.

## Maintained boundary at closure

- `compiled_experimental_backend=false`;
- `supports_resident_state=false`;
- `supports_device_observation_view=false`;
- CPU remains the maintained default;
- no public ABI promotion is claimed.

RB9 already supplied the accepted runtime validation for the last runtime
write set. RB10-RB11 are documentation/architecture-guard iterations only, so
RB11 reuses that accepted CPU/CUDA evidence and runs fresh read-only closure,
decision, performance, bilingual-link, and Git-boundary guards plus independent
review.
