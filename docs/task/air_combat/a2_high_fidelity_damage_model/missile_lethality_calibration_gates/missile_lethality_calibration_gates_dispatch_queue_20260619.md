# MLF-10 Calibration Gates Dispatch Queue

Status: `2026-06-19` initial queue for
[MLF-10 Calibration Gates](README.md). Only `MLF10-P0` is active in this
opening slice.

## Active Queue

| Date | Packet | Cluster | Owner | Write set | Goal | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `2026-06-19` | `MLF10-Q0` | `MLF10-P0` | main thread | MLF-10 docs and parent A2 README files | Create the subproject surface and parent live entry | active |

## Planned Queue

| Packet | Cluster | Owner | Trigger | Output |
| --- | --- | --- | --- | --- |
| `MLF10-Q1` | `MLF10-P1` | read-only diagnostics worker or main thread | After Q0 link/diff check passes | Calibration-like evidence inventory |
| `MLF10-Q2` | `MLF10-P2` | main thread | After Q1 inventory | Admission contract and report schema |
| `MLF10-Q3` | `MLF10-P3` | implementation worker | After Q2 contract | Deterministic audit tooling and focused tests |
| `MLF10-Q4` | `MLF10-P4` | integration worker | After Q3 tooling | Retained report integration |
| `MLF10-Q5` | `MLF10-P5` | main thread | After Q4 report integration | Focused validation and residual record |
| `MLF10-Q6` | `MLF10-P6` | main thread | After Q5 validation | Acceptance, hold, or re-scope decision |

## Hold Conditions

- Stop if a request asks for direct parameter tuning before the admission
  contract exists.
- Stop if a report would imply real-world Pk, weapon-specific lethality,
  target-specific lethality, or deterministic fuze truth before admission.
- Stop if a source needs ingestion but lacks source-rights and provenance
  review.
- Stop if implementation would require rewriting archived MLF evidence instead
  of consuming accepted outputs.

## Validation For Q0

- Local Markdown links over parent A2 README files and MLF-10 docs.
- `git diff --check -- docs/task/air_combat/a2_high_fidelity_damage_model`.
