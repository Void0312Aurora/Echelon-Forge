# Component-Response Quantization Thresholds

Status: `2026-07-15` post-P5 task-local docs-only threshold addendum, refreshed
against the corrected runtime spatial projection radius. This
document fills the probability / integrity threshold gap left by
[kill_chain_metric_mapping_20260623.md](kill_chain_metric_mapping_20260623.md)
for `component_response`. It does not run calibration, retune runtime
parameters, edit descriptors, or claim real AIM-120C, F-16C, Pk, or
deterministic-fuze authority.

Chinese companion:
[kill_chain_component_response_quantization_20260705.zh.md](kill_chain_component_response_quantization_20260705.zh.md)

Schema label: `a2.kill_chain_component_response_quantization.v0`

## Input Boundary

This addendum consumes only KCES before/after report fields that already exist
or can be derived from current report rows:

- `component_response_row_count`
- `max_failure_probability`
- `sampled_failure_count`
- `min_integrity_delta`
- `primary_failure_mode`
- `component_response_band`
- `component_detail.component_rows[].failure_probability`
- `component_detail.component_rows[].integrity_delta`
- `component_detail.component_rows[].sampled_failure`

Derived fields:

```text
p_max = component_response.max_failure_probability
delta_abs = max(0, -component_response.min_integrity_delta)
n_sampled = component_response.sampled_failure_count
n_rows = component_response.component_response_row_count
```

`n_sampled` is a single-seed observation, not the threshold itself. The
quantized band is driven by `p_max` and `delta_abs`; `n_sampled > 0` is attached
as a separate `sampled_failure_observed` flag.

## Quantized Bands

| band | Condition | Meaning |
| --- | --- | --- |
| `no_component_response` | `n_rows = 0` | No evaluable component response rows. |
| `trace_response` | `n_rows > 0`, `p_max < 0.02`, and `delta_abs < 0.02` | Probability trace and tiny integrity change only. |
| `weak_response` | `0.02 <= p_max < 0.10` or `0.02 <= delta_abs < 0.05` | Visible but weak component response. |
| `nontrivial_response` | `0.10 <= p_max < 0.30` or `0.05 <= delta_abs < 0.15` | Non-trivial component response. |
| `material_response` | `0.30 <= p_max < 0.70` or `0.15 <= delta_abs < 0.35` | Material component response. |
| `severe_response` | `p_max >= 0.70` or `delta_abs >= 0.35` | Strong component response; not a mission-kill or Pk claim. |

If multiple predicates match, use the strongest matching band. Sampling remains
orthogonal:

```text
sampled_failure_observed = n_sampled > 0
```

## Review Pressure By Effect Band

These thresholds are not calibration targets. They define review pressure
between `warhead_load_field.effect_band` and `component_response`:

| `effect_band` | Expected floor | Handling below the floor |
| --- | --- | --- |
| `core` | `material_response` | `trace_response` / `weak_response` must enter factor decomposition; do not retune fuze or guidance. |
| `effective` | `nontrivial_response` | `trace_response` requires explanation in warhead load, receiver exposure / armor / threshold, or response curve. |
| `outer_effective` | `weak_response` | `trace_response` creates review pressure, not automatic calibration authority. |
| `edge` | `trace_response` | Trace or weak response is acceptable; material or stronger response needs geometry/load review. |
| `outside_effect` | `no_component_response` or `trace_response` | `nontrivial_response` or stronger creates negative-control pressure. |
| `unclassified_missing_R_effect` | none | Declare `R_effect_m` or a concrete `R_effect_variant` first. |

## Current Before-Report Check

For the constant-velocity anchor before report under `REV-RUNTIME-PROJECTION`:

[kces_anchor_cv_before_report_20260623.json](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_before_report_20260623.json)

| `effect_band` | count | Quantized response distribution | Addendum interpretation |
| --- | ---: | --- | --- |
| `core` | 6 | `severe_response=6` | Consistent with the strong-load region. |
| `effective` | 12 | `severe_response=8`, `material_response=4` | Reaches the effective-region floor. |
| `outside_effect` | 60 | `trace_response=10`, `no_component_response=50` | Satisfies the outside-effect negative-control ceiling. |

`REV-RUNTIME-PROJECTION` now reads the launch-time runtime projection snapshot:
`lethal_radius_m=15`, `projection_radius_fraction=0.60`, and
`resolved_projection_radius_m=9`. The six `4/6/8 km +/-30 deg` rows therefore
have `rho_effect_case=1.05..1.22` and are `outside_effect`; their
`trace_response` is permitted by this addendum and does not create a current
component-response residual. `REV-EQ-FUZE` remains a separate 15 m sensitivity
variant and must not be substituted for the runtime projection radius.

## Suggested Report Fields

Future harness summaries can add read-only derived fields under
`component_response`:

```json
{
  "component_response_quantized_band": "trace_response",
  "component_response_sampled_failure_observed": false,
  "component_response_expectation_status": "below_outer_effective_floor",
  "component_response_quantization_schema": "a2.kill_chain_component_response_quantization.v0"
}
```

Suggested `component_response_expectation_status` values:

| Status | Condition |
| --- | --- |
| `not_applicable_no_effect_band` | `effect_band=unclassified_missing_R_effect` |
| `not_applicable_no_rows` | `n_rows=0` and the `effect_band` does not require response |
| `satisfied` | The quantized band reaches the expected floor for the `effect_band` |
| `below_expected_floor` | Below the `core` / `effective` expected floor |
| `below_outer_effective_floor` | `outer_effective` has only `trace_response` |
| `negative_control_pressure` | `outside_effect` has `nontrivial_response` or stronger |

## Acceptance

This document accepts only the standard addendum, not calibration success:

- Thresholds are based on existing KCES report fields and can be reused for
  before/after reports.
- `sampled_failure_count` is an observation flag, not a standalone threshold.
- `mission_kill`, `mobility_kill`, and `destroyed` remain owned by
  `consequence_projection`.
- Review pressure does not grant `component_failure_probability_authority`,
  `effect_scale_authority`, `pk_authority`, or `deterministic_fuze_authority`.
- Any future after-report improvement must name one target layer under the P6
  guard and prove that `guidance_approach`, `fuze_decision`, and non-target
  layers did not move unexpectedly.
