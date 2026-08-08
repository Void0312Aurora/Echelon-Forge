# Kill-Chain Calibration Harness Plan

Status: `2026-06-23` P4 pass harness plan for
[Kill-Chain Expectation Standardization](README.md). This is a docs-only plan
and artifact contract; it does not run batch simulation, retune runtime
parameters, edit descriptors, or claim real AIM-120C/F-16C/Pk authority.

Chinese companion:
[kill_chain_calibration_harness_plan_20260623.zh.md](kill_chain_calibration_harness_plan_20260623.zh.md)

Schema label: `a2.kill_chain_calibration_harness_plan.v0`

## Inputs

- P2 scenario matrix:
  [kill_chain_scenario_expectation_matrix_20260622.md](kill_chain_scenario_expectation_matrix_20260622.md)
- P3 metric mapping:
  [kill_chain_metric_mapping_20260623.md](kill_chain_metric_mapping_20260623.md)
- P6 calibration admission gate:
  [../kill_chain_calibration_admission_gate_20260621.zh.md](../../../../systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/kill_chain_calibration_admission_gate_20260621.zh.md)
- Current decoupled probe:
  [kill_chain_decoupling_probe.py](../../../../../tools/diagnostics/kill_chain_decoupling_probe.py)

## P4 Boundary

P4 only binds the P3 field contract to an executable harness shape. It does not
allow:

- runtime, C++/Python behavior, descriptor, or test-expectation changes;
- full calibration execution or promotion of dry-run output into accepted
  behavior;
- choosing meter values for `R_fuze_m` or `R_effect_m`, probability thresholds,
  or integrity thresholds;
- using warhead / component response to compensate for a guidance miss outside
  `R_fuze`;
- real weapon, real target, deterministic-fuze, Pk, reward, or calibration
  authority claims.

`guidance_approach` is a read-only diagnostic layer in this P4 harness. If an
`N` cell does not enter `R_fuze`, the harness must emit
`guidance_or_model_residual` and stop downstream lethality calibration pressure
for that case.

## Harness Artifacts

P4 plans this artifact family. The paths are proposed locations for future P4
execution or review packets; this P4 document does not create runtime artifacts.

| Artifact | Proposed path | Schema / content |
| --- | --- | --- |
| case grid | `docs/task/air_combat/a2_high_fidelity_damage_model/review_packets/kill_chain_expectation_standardization_p4/case_grid_*.jsonl` | One row per P3 `identity` and `launch_window` field set. |
| before report | `.../before/<batch_id>.json` or `.jsonl` | Heatmap report rows before parameter changes. |
| after report | `.../after/<layer_id>/<batch_id>.json` or `.jsonl` | Heatmap report rows after a single-layer candidate change; not produced by default in P4. |
| delta guard | `.../guard/<layer_id>/<batch_id>.json` | P6 `a2.kill_chain_calibration_delta_guard.v1` output. |
| batch summary | `.../summary/<batch_id>.md` | Worker count, case count, seed count, timing, failed cases, and guard status. |

Each heatmap report row must implement at least these P3 field groups:

- `identity`
- `launch_window`
- `guidance_approach`
- `fuze_decision`
- `warhead_load_field`
- `component_response`
- `consequence_projection`
- `guards`

Missing fields must be explicit, such as `missing_<field>` or
`unclassified_missing_R_effect`; they must not be disguised as observed facts by
zero defaults.

## Case Grid Plan

| Batch id | Grid | Cases / seed | Seeds | Workers | Purpose | P4 status |
| --- | --- | --- | --- | --- | --- | --- |
| `KCES-P4-SMOKE-ANCHOR` | `anchor-grid` signed | `93` | `1` | `<=32` | Validate schema, grouping, `rho_*` derivation, and guard fields. | planned |
| `KCES-P4-PILOT-MAIN` | `recommended-main-grid` signed + maneuver sparse | `572` | `1` | `32` | First main heatmap pilot; collect per-case time, memory, and output-contention data. | planned |
| `KCES-P4-MAIN-3SEED` | same | `572` | `3` | `48-64` after pilot pass | First stable heatmap, about `1716` cases. | gated by pilot |
| `KCES-P4-BOUNDARY` | `boundary-refinement` add-on | `+200-400` | `1-3` | `48-64` after boundary selection | Refine `N/M` and `M/O` boundaries. | gated by main |
| `KCES-P4-MANEUVER-FULL` | `expanded-maneuver-grid` | `962` | `1-3` | held | Expand once the maneuver layer matures. | held |

Worker policy:

- Start with `32` workers; do not immediately occupy all `88` logical CPUs.
- Pilot pass requires no systematic output-write conflicts, retryable failed
  cases, controlled memory peaks, complete report-row fields, and serializable
  guard fields.
- Increase to `48-64` workers only after pilot pass.
- `R_effect_variant` is an offline evaluation dimension by default and does not
  multiply simulation case count.

## Layer Guard Plan

P6 already defines calibratable layers. P4 only binds those layers to the P3
report row schema and delta guard; it does not open real authority.

| Layer id | Target stage | Allowed to change | Frozen / reject-if-changed stages | P4 use |
| --- | --- | --- | --- | --- |
| `guidance_diagnostic_readonly` | none | none | `approach`, `fuze_decision`, `warhead_load_field`, `component_response`, `consequence_projection` | Read-only check of whether `N/M/O` cells enter `R_fuze`; no calibration. |
| `fuze_data` | `fuze_decision` | fuze reliability / detection / delay / detonation-probability candidate fields, only after evidence admission | `approach`, `warhead_load_field`, `component_response`, `consequence_projection` | Future single-layer candidate if `entered_R_fuze=true` but fuze does not trigger. |
| `warhead_data` | `warhead_load_field` | projection radius, fragment/blast load-field candidate fields, only after evidence admission | `approach`, `fuze_decision`, `component_response`, `consequence_projection` | Future single-layer candidate if fuze succeeds but load bands are anomalous. |
| `target_response_data` | `component_response` | component threshold / failure probability candidate fields, only after evidence admission | `approach`, `fuze_decision`, `warhead_load_field`, `consequence_projection` | Future single-layer candidate if load is plausible but response is near-zero. |
| `consequence_data` | `consequence_projection` | component-failure to platform-consequence mapping, only after evidence admission | `approach`, `fuze_decision`, `warhead_load_field`, `component_response` | Evaluate consequence only after component response is explicit. |

Every mutable layer must satisfy:

```text
mutation_scope = single_layer_only
dry_run_only = true
runtime_parameter_retuning = false
default_database_modified = false
before_after_stage_report_required = true
delta_guard_required = true
```

## Before / After And Delta Guard

Future P4 execution must generate a before report first, then a single-layer
after report, then run the P6 delta guard. The delta-guard CLI shape is:

```bash
python tools/diagnostics/kill_chain_decoupling_probe.py \
  --delta-guard-before <before_report.json> \
  --delta-guard-after <after_report.json> \
  --delta-guard-layer <layer_id> \
  --output <guard_report.json>
```

Guard pass conditions:

| Condition | Requirement |
| --- | --- |
| case overlap | before / after share at least one `case_id` set. |
| target stage delta | `target_stage_id` must change; otherwise emit `target_stage_delta_missing`. |
| frozen stages | any change to `reject_if_changed_stage_ids` must fail. |
| authority boundary | `runtime_parameter_retuning=false`, `default_database_modified=false`, `real_world_pk=false`, `deterministic_fuze_authority=false`, `calibration_authority=false`. |
| negative controls | `O` cells must not become strong load / response evidence through downstream calibration. |

## Batch Interpretation Rules

| Situation | P4 class | Follow-up |
| --- | --- | --- |
| `N` cell does not enter `R_fuze` | `guidance_or_model_residual` | Do not enter fuze/load/response calibration; record guidance / model residual. |
| `N` cell enters `R_fuze` but fuze does not trigger | `fuze_layer_candidate` | Single-layer dry run only after future `fuze_data` admission. |
| fuze succeeds but `REV-EQ-FUZE` is still `outside_effect` or load is near-zero | `warhead_load_mapping_residual` | Inspect load-field mapping; do not alter component response. |
| load is plausible but response is near-zero | `component_response_candidate` | Single-layer dry run only after future `target_response_data` admission. |
| response is plausible but consequence is anomalous | `consequence_projection_candidate` | Evaluate consequence layer only; do not back-infer upstream stages. |
| `O` cell shows strong trigger/load/response | `negative_control_alert` | Check launch classification, case generation, and stage facts first. |

## P4 Closure

P4 is pass. It has:

- bound the P3 heatmap report row schema to a harness artifact family;
- turned the `anchor-grid`, `recommended-main-grid`, boundary refinement, and
  maneuver expansion into a batch plan;
- defined the `32` worker pilot, `48-64` worker escalation criteria, and seed
  budget;
- bound the P6 single-layer calibration plan / delta guard to the four
  calibratable layers;
- made `guidance_approach` read-only in this harness;
- named frozen / reject-if-changed stages;
- kept runtime calibration, descriptor edits, real authority, and full batch
  execution held.

P4 does not resolve:

- actual heatmap runtime report generation;
- actual before / after dry-runs;
- parameter values, probability thresholds, or integrity thresholds;
- standards promotion;
- authority admission.

Those move to P5 decisions, future harness implementation, or evidence/admission
work.
