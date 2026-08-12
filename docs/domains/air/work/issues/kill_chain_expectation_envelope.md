# Air-To-Air Kill-Chain Expectation Envelope

Language:
- English canonical: `kill_chain_expectation_envelope.md`
- Chinese companion: not maintained (English-only work surface).

Document kind: `plan`
Lifecycle: `draft`
Canonical: `docs/domains/air/work/issues/kill_chain_expectation_envelope.md`
Owner: `domains/air`
Last verified: `2026-08-08`

Status: draft planning issue for air-to-air kill-chain expectation envelopes;
not a current runtime or test contract.

This draft records candidate review vocabulary and an envelope shape for
air-to-air kill-chain expectation checks. It does not claim real AIM-120C, real
F-16C, deterministic-fuze, Pk, or runtime calibration authority.

## Authorization Boundary

This draft does not authorize implementation, runtime retuning, descriptor
edits, harness or schema changes, calibration, reward changes, or training
acceptance. Any such work requires a separately authorized owner-local work
package with its own scope, tests, review, and acceptance evidence.

## Scope

This draft records a candidate envelope for reviewing whether air-to-air
kill-chain diagnostic distributions fall inside an engineering-proxy
expectation range. It remains an owner-local issue plan because the current
harness can produce before-report facts but does not emit this envelope object
as a maintained runtime/test contract.

In scope:

- expected stage vocabulary for launch window, guidance approach, fuze decision,
  warhead load field, component response, and consequence projection
- required human-defined inputs for an expectation envelope
- derived report fields used by envelope checks
- effect-to-response floors, ceilings, and review-pressure labels
- distribution tolerances for anchor-grid reports
- continuity rules and owner-stage attribution for deviations

Out of scope:

- runtime parameter values
- descriptor edits
- weapon- or target-specific real-world truth
- probability-of-kill authority
- calibration approval
- reward or training acceptance

## Source Evidence

The current task evidence lives under:

- [KCES task entry](../../reviews/kill_chain_expectation_standardization_20260706/README.md)
- [KCES idealized expectation contract](../../reviews/kill_chain_expectation_standardization_20260706/kill_chain_idealized_expectation_contract_20260621.md)
- [KCES scenario expectation matrix](../../reviews/kill_chain_expectation_standardization_20260706/kill_chain_scenario_expectation_matrix_20260622.md)
- [KCES metric mapping](../../reviews/kill_chain_expectation_standardization_20260706/kill_chain_metric_mapping_20260623.md)
- [KCES component-response quantization addendum](../../reviews/kill_chain_expectation_standardization_20260706/kill_chain_component_response_quantization_20260705.md)

Current schema label:

```text
a2.kill_chain_expectation_envelope.v0
```

## Human-Defined Inputs

The following fields are policy inputs. They must be declared before judging a
report:

| Field group | Required definition | Current source |
| --- | --- | --- |
| `profile` | `profile_id`, authority level, weapon proxy, target proxy, forbidden claims | KCES seed profile |
| `grid` | `grid_tier`, range axis, signed/unsigned offset axis, target-motion layer, seed plan | KCES scenario matrix |
| `launch_class` | `N`, `M`, or `O` for each heatmap cell | KCES heatmap |
| `R_fuze_m` | profile-declared fuze-radius source | harness metadata |
| `R_effect_variant` | selected effective-load radius policy | KCES variant list |
| `R_effect_m` | variant-specific effective-load radius | derived or harness-declared |
| `effect_band_thresholds` | `rho_effect` to effect-band mapping | KCES contract/metric mapping |
| `response_band_thresholds` | `p_max` and `delta_abs` to response-band mapping | KCES quantization addendum |
| `distribution_tolerance` | candidate satisfied share and negative-control tolerance | this draft |
| `owner_rules` | deviation type to review-stage mapping | this draft |

Changing any of these proposed policy inputs changes the candidate envelope and
must be recorded as a new draft version or addendum.

## Derived Report Fields

Reports derive these fields from measured facts and the declared inputs:

```text
rho_fuze = nearest_distance_m / R_fuze_m
entered_R_fuze = rho_fuze <= 1.0

rho_effect_case = nearest_distance_m / R_effect_m
rho_effect_component = component_loads[].distance_m / R_effect_m

p_max = component_response.max_failure_probability
delta_abs = max(0, -component_response.min_integrity_delta)
sampled_failure_observed = component_response.sampled_failure_count > 0
```

The envelope labels are:

- `guidance_expectation_status`
- `effect_band`
- `component_response_quantized_band`
- `component_response_expectation_status`
- `envelope_cell_status`
- `envelope_owner_stage`

## Launch / Guidance Envelope

| `launch_class` | Expected result | Review pressure | Owner stage |
| --- | --- | --- | --- |
| `N` | `entered_R_fuze=true` | clustered or repeated `entered_R_fuze=false` | `launch_window -> guidance_approach` |
| `M` | fuze entry is plausible but not required | systematic discontinuity against neighboring cells | `launch_window` / boundary review |
| `O` | `entered_R_fuze=false` and no load/response pressure | strong load or `nontrivial_response` or stronger | negative-control review |

## Effect-To-Response Envelope

Response band order:

```text
no_component_response < trace_response < weak_response <
nontrivial_response < material_response < severe_response
```

| `effect_band` | Expected floor | Normal allowed range | Review pressure | Negative-control pressure |
| --- | --- | --- | --- | --- |
| `core` | `material_response` | `material_response..severe_response` | `nontrivial_response` or weaker | n/a |
| `effective` | `nontrivial_response` | `nontrivial_response..severe_response` | `trace_response` or `weak_response` | n/a |
| `outer_effective` | `weak_response` | `weak_response..material_response` | `trace_response` | `severe_response` |
| `edge` | `trace_response` | `trace_response..weak_response` | `no_component_response` | `material_response` or stronger |
| `outside_effect` | `no_component_response` | `no_component_response..trace_response` | n/a | `nontrivial_response` or stronger |
| `unclassified_missing_R_effect` | none | none | cannot judge | cannot judge |

`sampled_failure_observed` is an observation flag. It must not be used alone to
satisfy or fail the envelope.

## Distribution Tolerances

The following v0 cell-count values are candidate review thresholds until
repeated seeds provide confidence metadata. They do not pass or fail a runtime
release and do not authorize parameter changes:

| Group | v0 tolerance |
| --- | --- |
| non-boundary `N` cells | `>= 90%` should enter `R_fuze` |
| immediate `N/M` boundary `N` cells | `>= 75%` should enter `R_fuze` |
| `M` cells | no pass/fail share; preserve stage facts and continuity |
| `O` cells | `0` cells should show `nontrivial_response` or stronger |
| `core/effective` effect cells | `>= 90%` should satisfy the expected response floor |
| `outer_effective` effect cells | `>= 70%` should reach `weak_response` or stronger |
| `edge` effect cells | `trace_response` or `weak_response` is acceptable |
| `outside_effect` cells | `no_component_response` or `trace_response` is acceptable |

## Continuity Rules

- At fixed offset angle, increasing range must not systematically improve
  launch class, fuze entry, effect band, or response band unless a declared
  mechanism explains it.
- At fixed range, increasing absolute offset angle must not systematically
  improve launch class, fuze entry, effect band, or response band unless a
  declared mechanism explains it.
- `M` cells absorb boundary ambiguity.
- `O` cells are negative controls. Improving target cells by making `O` cells
  respond strongly fails the envelope.

## Cell Status

| Status | Condition |
| --- | --- |
| `satisfied` | Expected floors are reached and negative-control ceilings are not exceeded. |
| `boundary_observation` | Result is in an `M` cell or immediate boundary band without negative-control pressure. |
| `below_expected_floor` | `core` or `effective` response falls below its floor. |
| `below_outer_effective_floor` | `outer_effective` maps only to `trace_response`. |
| `guidance_or_model_residual` | `N` cell does not enter `R_fuze`. |
| `negative_control_pressure` | `O` / `outside_effect` produces `nontrivial_response` or stronger, or `edge` produces material/severe response. |
| `not_judged_missing_metadata` | required radius, variant, or report field is missing. |

## Owner Rules

| Deviation | Owner stage |
| --- | --- |
| `N` cell misses `R_fuze` | `launch_window -> guidance_approach` |
| entered `R_fuze` but no fuze trigger | `fuze_decision` |
| triggered but effect band is weaker than the selected variant implies | `warhead_load_field` |
| load is `core/effective/outer_effective` but response is below floor | `warhead_load_field -> component_response` |
| response satisfies floor but consequence remains weak | `consequence_projection` |
| `O/outside_effect` produces strong response | negative-control review, usually `warhead_load_field` first |
| missing radii or variant metadata | `harness_metadata` |

## Minimal Envelope Object

After separately authorized implementation, a future harness summary may emit:

```json
{
  "schema_version": "a2.kill_chain_expectation_envelope.v0",
  "profile_id": "KCES-AIM120C-LIKE-FIGHTER-V0",
  "grid_tier": "anchor-grid",
  "case_id": "KCES-S1-8KM-30DEG-CV",
  "launch_class": "N",
  "R_effect_variant": "REV-RUNTIME-PROJECTION",
  "R_effect_m": 9.0,
  "R_effect_source": "missile_runtime_projection.resolved_projection_radius_m",
  "guidance_expectation_status": "satisfied",
  "effect_band": "outside_effect",
  "component_response_quantized_band": "trace_response",
  "component_response_expectation_status": "satisfied",
  "envelope_cell_status": "satisfied",
  "envelope_owner_stage": "no_review_pressure"
}
```

This object is a proposed planning/review label, not a calibration result or an
implemented schema commitment.

## Current Held Boundary

The corrected current KCES runtime-projection slice resolves `R_effect_m=9.0`
from the launch-time runtime snapshot. Its `4/6/8 km +/-30 deg` trace-response
rows are therefore `outside_effect` and satisfy the negative-control ceiling;
they are not a current `outer_effective -> trace_response` residual. The
envelope still retains that residual label for other declared variants, such as
`REV-EQ-FUZE`, but this plan remains draft until a maintained harness emits the
object and focused tests pin the schema through separately authorized work.
Runtime retuning remains held behind the KCES P6 single-layer admission gate.
