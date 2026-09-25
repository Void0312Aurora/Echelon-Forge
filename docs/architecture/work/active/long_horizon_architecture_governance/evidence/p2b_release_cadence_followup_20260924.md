# P2-B Release Cadence Follow-up Evidence

Status: `2026-09-25` — three local package batches were observed on the
supported Windows CPython 3.12 row, representing two distinct package pairs;
representative release cadence remains open.

## Observation

The follow-up reused the accepted P5-A plan digest
`505df883b8cb08dcbbedbcb2fb2a2cffb3c27eb386e76476cbc1efc7f99a3b18` and ran
two separate two-cycle child-process replacement/backout batches. Each batch
had a consistent current/rollback pair and passed the initial P1-C SLOs:

| Batch | Cycles | Current binding SHA-256 | Rollback binding SHA-256 | SLO |
| --- | ---: | --- | --- | --- |
| `p5d-cadence-20260924-a` | 2 | `d699fbccfebc8d51ab22bbb4e50504f744a4836c8b99c707482dfaca24909e37` | `46ef11afe9687a865bd3e0a02e51ba7fa03b0c2d42215b8aff7e70f2e8db96cf` | pass |
| `p5d-cadence-20260924-b` | 2 | `d699fbccfebc8d51ab22bbb4e50504f744a4836c8b99c707482dfaca24909e37` | `6c6391b779f248eadce1fb31a43f1d0b044a5bfc1e38e0f8419ff729a2e2a3fd` | pass |
| `p2b-cadence-20260925-c` | 2 | `d699fbccfebc8d51ab22bbb4e50504f744a4836c8b99c707482dfaca24909e37` | `6c6391b779f248eadce1fb31a43f1d0b044a5bfc1e38e0f8419ff729a2e2a3fd` | pass |

The third batch repeated the second batch's package pair while independently
starting and backing out two child processes. The cadence classifier therefore
reports:

```text
status=distinct_package_batches_observed
distinct_release_id_count=2
distinct_plan_sha256_count=1
distinct_package_pair_count=2
representative_release_cadence=open
```

The samples are real local process observations, not synthetic digest rows.
The third batch's maximum replacement startup was 1.4601902 s and maximum
backout recovery was 1.4587390 s; both cycles adopted the caller and passed
artifact retrieval.
They do not establish a long-term release interval, owner-approved cadence, or
representative workload/change distribution.

## Verification command

The measurements were executed from the isolated
`codex/long-horizon-governance-architecture` worktree with
`tools.maintenance.p5d_measure_supported_row.measure_supported_row` and
`tools.maintenance.p2b_sustainability_baseline._summarize_release_cadence`.
The state directories were temporary directories outside the worktree.

## Boundary

This packet upgrades the local observation from `local_repeat_only` to
`distinct_package_batches_observed`; it does not close the P2-B representative
cadence gate or authorize production publication. A future admitted cadence
sample still needs release-owner timing, changed plan/package provenance, and
representative workload coverage.

Document kind: `evidence`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/long_horizon_architecture_governance/evidence/p2b_release_cadence_followup_20260924.md`
Owner: `cross-domain architecture`
Last verified: `2026-09-25`
