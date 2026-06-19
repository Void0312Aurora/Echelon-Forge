# MLF-10 Current Status

Status: `2026-06-19` P0-P6 complete. Gate infrastructure is accepted / retained;
no calibration authority is accepted.

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

- No runtime parameter retuning before a contract admits a narrower claim.
- No claim that current engineering proxies are real AIM-120C/F-16C/MQ-9 truth.
- No admission of public-output data without source-rights and provenance review.
- No edits inside archived MLF packages except link-only maintenance.

## P1 Result

The
[calibration-like evidence inventory](missile_lethality_calibration_gates_inventory_20260619.md)
classifies the current evidence families. No evidence is admitted. Stage B is a
contract-ready candidate; Stage C, TP-21, BEC-O, Pk, and deterministic fuze
remain blocked.

## P2 Result

The
[calibration admission contract](missile_lethality_calibration_admission_contract_20260619.md)
defines the evidence manifest, evidence record, field-specific authority
decision, and retained report schemas. Pk, deterministic fuze, reward, and
entity deletion are fixed blocked fields in v1.

## P3/P4 Result

The audit tool and focused tests are implemented. The retained repository
manifest produces seven decisions: one engineering proxy, one retained
non-authoritative report, four blocked candidates/evidence records, one
rejected source category, and zero admitted records.

## P5/P6 Result

Focused validation passed with `18 passed`, deterministic report regeneration,
clean diff whitespace, and zero missing local Markdown links. The gate
infrastructure is accepted / retained. Calibration authority remains held.

## Reopen Condition

Reopen only for new evidence, a replacement signoff packet, or an explicit
authority-promotion request.
