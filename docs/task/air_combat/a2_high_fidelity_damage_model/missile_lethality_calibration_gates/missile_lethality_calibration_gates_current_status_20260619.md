# MLF-10 Current Status

Status: `2026-06-19` active P0 boundary surface. MLF-10 is open as the
calibration-gate follow-on after MLF-9, but no calibration authority is accepted
yet.

## Decision

Existing A2/MLF work contains calibrated-looking engineering proxies and
retained source-admission artifacts. MLF-10 treats those as audit inputs. It
does not treat them as already released real-world calibration.

## Current Evidence Map

| Evidence | Current reading | MLF-10 handling |
| --- | --- | --- |
| MLF-6 near-field structural thresholds and cumulative wing-loss behavior | Engineering proxy with tests and diagnostics | Inventory as model-calibration candidate input; do not promote without gate |
| MLF-7 platform consequences | Bounded consequence projection from accepted breakup facts | Inventory as chain outcome evidence; no Pk or target-specific truth |
| MLF-8 lifecycle facts | Diagnostics-only detached-part and terminal-wreck lifecycle evidence | Inventory as terminal outcome labels; no debris physics calibration |
| MLF-9 statistical trends | Deterministic synthetic trend reports over explicit rows | Candidate report input only; real-world Pk remains refused |
| A2 residual register `RES-013/014` | Pk and deterministic-fuze boundaries deferred | Must remain blockers unless independent evidence chain exists |
| A2 source-admission packets | Mixed retained pass/fail-closed gates | Gate state must be read explicitly; fail-closed remains fail-closed |

## Active Boundary

- No runtime parameter retuning in P0.
- No claim that current engineering proxies are real AIM-120C/F-16C/MQ-9 truth.
- No admission of public-output data without source-rights and provenance review.
- No edits inside archived MLF packages except link-only maintenance.

## Next Packet

Run `MLF10-P1` inventory. The first useful output is a table that classifies
each calibration-like value or artifact as:

- `engineering_proxy`
- `retained_non_authoritative`
- `calibration_candidate`
- `admitted`
- `rejected`
- `blocked`

No code implementation should start until that inventory is written.
