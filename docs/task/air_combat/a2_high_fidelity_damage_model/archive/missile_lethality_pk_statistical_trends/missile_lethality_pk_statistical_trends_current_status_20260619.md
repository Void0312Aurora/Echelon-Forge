# MLF-9 Current Status

Status: `2026-06-19` accepted / archived. MLF-9 closes the bounded
Pk/statistical trend simulation-report slice after MLF-8 acceptance.

Chinese companion:
[missile_lethality_pk_statistical_trends_current_status_20260619.zh.md](missile_lethality_pk_statistical_trends_current_status_20260619.zh.md).

## Summary

The accepted slice creates the durable MLF-9 work surface, inventories accepted
inputs, defines the metric contract, aligns diagnostics rows so
`structural_breakup` is visible beside component damage, consequence, and
lifecycle stages, adds a deterministic row-level trend harness, exposes the
trend payload through the process probe as a retained diagnostics artifact, and
records focused validation and acceptance. The output remains a simulation
trend report over replayable chain facts, not calibrated real-world probability
of kill.

## Maturity Matrix

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| Subproject surface | P0 pass | README, task clusters, dispatch queue, current status, archive placeholder; docs diff and link checks passed | Setup alone does not prove a runtime trend harness |
| Upstream facts | accepted inputs | MLF-5 component failure, MLF-6 structural failure, MLF-7 consequences, MLF-8 lifecycle | Inputs are accepted simulation facts, not Pk calibration |
| Evidence inventory | P1 pass | Inventory doc names reusable rows, gaps, and safe write sets | Inventory is not trend evidence by itself |
| Metric contract | P2 initial pass | Metric contract defines row source, denominators, buckets, grouping fields, and uncertainty labels | Contract still refuses calibrated Pk |
| Structural row surface | P2 initial pass | Process probe row contract now exposes `structural_breakup`; focused diagnostics tests pass | Row exposure does not change damage physics |
| Trend extraction | P3 initial pass | `tools/diagnostics/mlf9_statistical_trends.py`, `tests/tools/test_mlf9_statistical_trends.py`, trend harness result doc | Row summarization only; no runtime physics or calibration promotion |
| Report integration | P4 initial pass | Process probe embeds `mlf9_statistical_trends` and can write `--mlf9_report_json_out`; report integration result doc | Diagnostics/report artifact only; no reward/training/calibration consumer |
| Validation | P5 pass | Focused validation reports `50 passed`, clean `git diff --check`, and 0 missing local Markdown links | Validation covers simulation/report behavior only, not real Pk |
| Closeout | P6 pass | Acceptance record and parent indexes mark the slice accepted / archived | Old active path is a compatibility pointer |
| Calibration | held | MLF-10 reserved | No real weapon or target-specific probability |

## Recommended Action Order

1. Use the archived evidence packet as the canonical MLF-9 record.
2. Open MLF-10 only for calibration gates, public-source outcome admission, or
   weapon/target-specific probability discussion.
3. Keep Pk calibration, public-outcome fitting, reward shaping, and entity
   deletion held.

## Refused Claims

- Real AIM-120C, F-16, MQ-9, or stock platform Pk.
- Public-outcome calibration or validation.
- Reward shaping or training success.
- Entity deletion, direct crash rules, or debris physics.
