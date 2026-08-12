# KCES Component-Response Local Diagnosis

This report consumes existing before-report rows and inspects the cells
already attributed to `component_response`. It is a report-level local
diagnostic; it does not rerun simulation, edit parameters, or claim real
weapon / target / Pk authority.

Boundary: engineering-proxy diagnostics only.

## Source

- Input: `docs/domains/air/reviews/kill_chain_expectation_standardization_20260706/review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_before_report_20260623.json`
- Variant: `REV-RUNTIME-PROJECTION`
- Target motion layer: `nonmaneuvering_constant_velocity`
- Candidate rows: `0`
- Baseline rows: `13`
- Diagnosis buckets: `{}`
- Detail projection signals: `{}`

## Artifacts

- Manifest JSON: `kces_anchor_cv_response_diagnosis_manifest_20260628.json`
- Detail CSV: `kces_anchor_cv_response_diagnosis_detail_20260628.csv`
- Matrix CSV: `kces_anchor_cv_response_diagnosis_matrix_20260628.csv`
- Probability scatter PNG: `kces_anchor_cv_response_diagnosis_probability_scatter_20260628.png`
- Probability scatter SVG: `kces_anchor_cv_response_diagnosis_probability_scatter_20260628.svg`

## Candidate Rows


## Interpretation

- No rows are currently attributed to `component_response` for the
  selected variant and target-motion layer.
- The empty candidate set is a valid diagnostic result; no local
  load / response residual is asserted by this artifact.
