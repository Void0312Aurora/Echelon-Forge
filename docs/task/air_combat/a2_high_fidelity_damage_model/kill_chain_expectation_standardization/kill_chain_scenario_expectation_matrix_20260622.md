# Kill-Chain Scenario Expectation Matrix

Status: `2026-06-23` P2 pass matrix for
[Kill-Chain Expectation Standardization](README.md). This is a docs-only
scenario matrix; it does not run simulation, retune parameters, or claim real
AIM-120C/F-16C/Pk authority.

Chinese companion:
[kill_chain_scenario_expectation_matrix_20260622.zh.md](kill_chain_scenario_expectation_matrix_20260622.zh.md)

## Matrix Policy

The P1 contract closed the radius-policy ambiguity as:

```text
R_effect_policy = independent_review_variable
```

Therefore this matrix classifies guidance/fuze expectations without silently
equating `R_effect` and `R_fuze`. A row can be evaluated under one or more
declared `R_effect_variant` values later, but the launch-window and fuze
expectation remains separate from the effective-load expectation.

## Shared Seed Profile

| Field | Value |
| --- | --- |
| profile_id | `KCES-AIM120C-LIKE-FIGHTER-V0` |
| authority_level | `engineering_proxy_expectation` |
| weapon_proxy | AIM-120C-like active-radar, blast-fragmentation engineering proxy |
| target_proxy | fighter-size synthetic target; repository F-16C-like vulnerability shape only |
| R_fuze | profile-declared; may map to repository trigger-radius proxy in later metric rows |
| R_effect | independent review variable |
| forbidden claims | real AIM-120C warhead/fuze/fragment truth, real F-16C vulnerability, deterministic fuze, Pk, reward authority |

## Launch-Window Classes

| Class | Definition | Guidance expectation |
| --- | --- | --- |
| `nominal_in_envelope` | Nonmaneuvering or mild target motion, geometry inside the declared test envelope, and no sensor/data simplification intended to prevent terminal guidance. | Nearest approach should enter `R_fuze`; repeated misses outside `R_fuze` indicate guidance/kinematic/model classification work. |
| `marginal_in_envelope` | Geometry stresses turn rate, closure, seeker handoff, or timing but is still a plausible shot. | Fuze entry is plausible but not guaranteed; misses may be acceptable if stage facts explain them. |
| `outside_envelope` | Geometry or target motion is outside the declared proxy envelope. | No fuze-entry or lethality expectation. |

## Heatmap Matrix Policy

The P2 calibration constraint is not a single 8 km / 30 deg row. It is the
range x offset-angle heatmap. Individual rows are anchors or diagnostic examples
for heatmap cells. P3/P4 must not treat a single passing cell as envelope
calibration.

The first heatmap anchor grid uses these axes:

| Axis | Samples | Note |
| --- | --- | --- |
| Initial range `range_km` | `4`, `6`, `8`, `10`, `12`, `16` | Engineering-proxy anchor grid, not a real AIM-120C range table or final sampling density. |
| Offset angle `offset_deg` | `0`, `15`, `30`, `45`, `60`, `75`, `90` | Launch-geometry offset / bearing-angle stress; P3 maps this to concrete stage-report fields; not the final angular step. |
| Target-motion layer | `nonmaneuvering_constant_velocity` full grid; `mild_maneuver` sparse grid; `hard_maneuver` held | Constrain the constant-velocity heatmap first, then use maneuver layers for generality checks. |

Symbols:

| Symbol | Meaning | P3 expectation |
| --- | --- | --- |
| `N` | `nominal_in_envelope` | Should enter `R_fuze`; repeated misses need guidance/kinematic explanation. |
| `M` | `marginal_in_envelope` | Fuze entry is plausible but not guaranteed; P3 must record stage facts. |
| `O` | `outside_envelope` | No fuze/load/response calibration pressure. |

First constant-velocity target heatmap:

| range_km \ offset_deg | `0` | `15` | `30` | `45` | `60` | `75` | `90` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `4` | N | N | N | N | M | M | O |
| `6` | N | N | N | N | M | O | O |
| `8` | N | N | N | M | M | O | O |
| `10` | N | N | M | M | O | O | O |
| `12` | N | M | M | O | O | O | O |
| `16` | M | M | O | O | O | O | O |

This heatmap is an engineering-proxy expectation, not a real weapon envelope.
It constrains topology:

- At fixed offset angle, increasing range should not improve the expectation
  class unless P3 declares a seeker/handoff mechanism reason.
- At fixed range, increasing offset angle should not improve the expectation
  class unless P3 declares a geometry or target-motion reason.
- The 8 km / 30 deg constant-velocity cell is `N`, but it is not the only
  calibration target. Adjacent cells must preserve reasonable continuity.
- `O` cells are negative controls. They should not gain load/component-response
  expectation through lethality retuning.

First maneuvering-target sparse heatmap:

| range_km \ offset_deg | `0` | `30` | `60` |
| --- | --- | --- | --- |
| `6` | N | M | O |
| `8` | M | M | O |
| `10` | M | O | O |

The `mild_maneuver` sparse heatmap checks generality, but it must not weaken the
constant-velocity full heatmap. `hard_maneuver` remains outside P2 pass until
maneuver severity, target acceleration, and guidance-model metrics are declared.

## Heatmap Acceptance Constraints

Future P3/P4 work should map each heatmap cell to these layers:

| Heatmap layer | Fields | Use |
| --- | --- | --- |
| `launch_class` | `N/M/O` | P2 expectation class. |
| `guidance_fuze` | `rho_fuze`, nearest approach, fuze trigger | Judge whether the cell satisfies guidance/fuze expectation. |
| `runtime_projection_effect` | `rho_effect` and load band under `REV-RUNTIME-PROJECTION` | Compare current implementation. |
| `eq_fuze_effect` | `rho_effect` and load band under `REV-EQ-FUZE` | Sensitivity upper bound. |
| `smaller_load_effect` | `rho_effect` and load band under `REV-SMALLER-LOAD` | "Triggered but smaller effective load" explanation path. |
| `component_response` | failure-probability band, integrity-delta band, sampled failure | Evaluate only after fuze/load success. |

P2 does not require every cell to have an immediate runtime sample. It requires
P3/P4 sampling and reports to be heatmap-shaped. If compute is limited,
prioritize `N` cells, cells adjacent to `N/M` boundaries, and `O` negative
controls.

## Sampling Density Estimate

The `4/6/8/10/12/16 km` and `0/15/30/45/60/75/90 deg` axes above are P2
anchor points for expectation topology. They should not be the only sampling
density used by the follow-on calibration harness. P3/P4 should explicitly
separate unsigned heatmap cells, signed bearing cases, and repeat/seed count.

| Sampling tier | Range axis | Offset-angle axis | Target-motion layer | Single-seed case estimate | Use |
| --- | --- | --- | --- | --- | --- |
| `anchor-grid` | `4,6,8,10,12,16` km | unsigned `0,15,30,45,60,75,90` deg; signed is `0, +/-15, +/-30, +/-45, +/-60, +/-75, +/-90` | constant-velocity full; maneuver sparse | unsigned: `42 + 9 = 51`; signed: `78 + 15 = 93` | Documentation anchors, smoke runs, and quick topology checks. |
| `recommended-main-grid` | `4..16 km`, `1 km` step, `13` points | unsigned `0..90 deg`, `5 deg` step, `19` points; signed has `37` bearings | constant-velocity full; maneuver sparse uses `4/6/8/10/12/14/16 km` x signed `0/15/30/45/60/75/90 deg` | constant-velocity signed `13 x 37 = 481`; maneuver sparse signed `7 x 13 = 91`; total `572` | Recommended first calibration heatmap for a stable range x bearing surface. |
| `boundary-refinement` | add local `+/-0.5 km` points near `N/M` and `M/O` boundaries | add local `+/-2.5 deg` points near boundaries | constant velocity first; maneuver only where anomalies appear | expected add-on `200-400` cases, controlled by measured P3 boundary count | Check boundary continuity and avoid coarse-grid misclassification. |
| `expanded-maneuver-grid` | same as `recommended-main-grid` | same as `recommended-main-grid` | mild maneuver also runs full grid | constant velocity `481` + mild full `481` = `962` | Use only after maneuver-model metrics stabilize; not the default P2/P3 entry point. |

Repeat / seed budget:

| Grid | 1 seed | 3 seeds | 5 seeds | Recommendation |
| --- | --- | --- | --- | --- |
| `anchor-grid` signed | `93` | `279` | `465` | Smoke and regression entry point. |
| `recommended-main-grid` signed + maneuver sparse | `572` | `1716` | `2860` | Preferred P3/P4 plan; run 1 seed first, then repeat boundary and anomalous cells. |
| `expanded-maneuver-grid` | `962` | `2886` | `4810` | Run after the maneuver layer matures. |
| `boundary-refinement` add-on | `+200-400` | `+600-1200` | `+1000-2000` | Append after the first P3 heatmap selects measured boundaries. |

The current development host exposes `88` logical CPUs. The P4 harness plan can
start with a `32` worker pilot batch, then increase to `48-64` workers after
checking per-case time, memory, and output contention. `R_effect_variant` should
normally be an offline evaluation dimension over recorded miss/load facts; unless
the implementation truly requires runtime re-execution, `REV-RUNTIME-PROJECTION`,
`REV-EQ-FUZE`, and `REV-SMALLER-LOAD` should not multiply the simulation case
count.

## Initial Scenario Rows

The following rows are heatmap anchors, not the complete calibration set.

| Row id | Heatmap cell | Geometry class | Target motion | Launch-window class | Guidance expectation | Fuze expectation | Warhead-load expectation | Component-response expectation | Consequence expectation | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `KCES-S1-8KM-30DEG-CV` | CV heatmap `8 km x 30 deg = N` | 8 km initial range, 30 deg offset, fighter-size target | `nonmaneuvering_constant_velocity` | `nominal_in_envelope` | nearest approach should enter `R_fuze` | trigger expected if nearest approach is inside `R_fuze` | depends on declared `R_effect_variant`; cannot infer from meters alone | non-near-zero response expected only for `core/effective/outer_effective` variants | consequence not asserted until component-response metric is declared | Primary cell for the current concern. It is a guidance/fuze expectation row first, not a kill-probability row. |
| `KCES-S2-HEADON-CV` | CV heatmap low-offset `N` cells | head-on, moderate range, low offset | `nonmaneuvering_constant_velocity` | `nominal_in_envelope` | nearest approach should enter `R_fuze` with lower lateral-demand stress than S1 | trigger expected if inside `R_fuze` | evaluate through `rho_effect` | response band follows declared `rho_effect` | consequence held | Baseline simple intercept row. |
| `KCES-S3-TAILCHASE-CV` | CV heatmap distance-stress `M` cells | tail-chase, moderate range, positive closure margin required | `nonmaneuvering_constant_velocity` | `marginal_in_envelope` | fuze entry depends on closure/energy margin | trigger only if nearest approach enters `R_fuze` | evaluate through `rho_effect`; no extra lethality pressure if guidance fails | held unless fuze/load succeeds | held | Separates energy/closure limits from warhead calibration. |
| `KCES-S4-BEAM-CV` | CV heatmap offset-stress `M` cells | beam crossing target, moderate range | `nonmaneuvering_constant_velocity` | `marginal_in_envelope` | nearest approach may stress lead/PN/autopilot response | trigger expected only for successful approach | evaluate through `rho_effect` | response should not compensate for guidance miss outside `R_fuze` | held | Useful for terminal-lead and lateral-acceleration checks. |
| `KCES-S5-HIGH-OFFBORESIGHT-CV` | CV heatmap high-offset `M/O` cells | high offset / high bearing angle | `nonmaneuvering_constant_velocity` | `marginal_in_envelope` or `outside_envelope` | no nominal fuze-entry guarantee until constraints are declared | trigger not guaranteed | no load expectation if outside `R_fuze` | no response expectation if no fuze/load | held | Prevents treating every launch as a calibration oracle. |
| `KCES-S6-8KM-30DEG-MANEUVER` | mild-maneuver sparse heatmap `8 km x 30 deg = M` | 8 km initial range, 30 deg offset | `mild_maneuver` | `marginal_in_envelope` | fuze entry may fail depending on maneuver severity and guidance model | trigger not guaranteed | evaluate only if fuze succeeds | response follows declared `rho_effect` | held | Adds target maneuver without changing the nonmaneuvering S1 expectation. |
| `KCES-S7-OUTSIDE-RANGE-CV` | CV heatmap `O` cells | range or geometry outside declared proxy envelope | `nonmaneuvering_constant_velocity` | `outside_envelope` | no fuze-entry expectation | trigger not expected | no load expectation | no response expectation | no consequence expectation | Negative-control row. |

## R Effect Variants

These variants are not runtime parameters. They are labels for later sensitivity
or metric-mapping rows. P2 only selects the first evaluation labels; it does not
declare meter radii or probability thresholds.

| Variant id | P2 decision | Meaning | Use |
| --- | --- | --- | --- |
| `REV-RUNTIME-PROJECTION` | selected | `R_effect` mapped to the current runtime projection radius. | First implementation-comparison row; it explains which `rho_effect` band the current implementation occupies, not the idealized standard. |
| `REV-EQ-FUZE` | selected | `R_effect = R_fuze` for a simple expectation-envelope sensitivity row. | Tests the strongest simple coupling assumption; if response is still near-zero here, P3/P4 should prioritize load/response mapping. |
| `REV-SMALLER-LOAD` | selected | `R_effect < R_fuze` to model a fuze range larger than effective load range. | Expresses the "fuze triggered but effective load is edge/insufficient" explanation path; valid only when the variant is explicit. |
| `REV-DECLARED-EFFECT` | held | `R_effect` declared from a future engineering-proxy review row. | Still the long-term preferred path, but P2 does not fabricate a review row; wait for P3/P4 or external-evidence work. |

## P2 Row Closure

| Row id | P2 status | First-round `R_effect_variant` | P3 priority | P3 handoff |
| --- | --- | --- | --- | --- |
| `KCES-S1-8KM-30DEG-CV` | pass | `REV-RUNTIME-PROJECTION`, `REV-EQ-FUZE`, `REV-SMALLER-LOAD` | high | Primary calibration-planning anchor. P3 must report `rho_fuze`, all three `rho_effect` variants, fuze trigger, load band, and component-response band. |
| `KCES-S2-HEADON-CV` | pass | `REV-RUNTIME-PROJECTION`, `REV-EQ-FUZE` | medium | Simple intercept baseline. P3 uses it to separate low lateral demand from S1's 30 deg offset demand. |
| `KCES-S3-TAILCHASE-CV` | pass | `REV-RUNTIME-PROJECTION`, `REV-SMALLER-LOAD` | medium | Energy/closure pressure row. P3 first confirms `R_fuze` entry; load/response are evaluated only after fuze success. |
| `KCES-S4-BEAM-CV` | pass | `REV-RUNTIME-PROJECTION`, `REV-EQ-FUZE` | medium | Lead/PN/lateral-acceleration row. P3 should separate guidance miss from warhead response. |
| `KCES-S5-HIGH-OFFBORESIGHT-CV` | pass | conditional `REV-RUNTIME-PROJECTION` only after `R_fuze` entry | low | Envelope-classification row first; if it does not enter `R_fuze`, it must not enter load/response calibration. |
| `KCES-S6-8KM-30DEG-MANEUVER` | pass | conditional `REV-RUNTIME-PROJECTION`, `REV-SMALLER-LOAD` only after `R_fuze` entry | medium | Maneuvering target row; it must not weaken the nonmaneuvering S1 nominal expectation. |
| `KCES-S7-OUTSIDE-RANGE-CV` | pass | none | low | Negative-control row; P3 should confirm no fuze/load/response expectation rather than calling it a calibration failure. |

## P3 Input Requirements

P3 does not need to reopen P2 classification. It should add measurable fields on
the rows above:

- `launch_window`: range, offset/aspect, target-motion class, launch-window
  class.
- `guidance_approach`: nearest approach, `rho_fuze`, time-to-nearest, and
  whether `R_fuze` was entered.
- `fuze_decision`: trigger yes/no, trigger point, fuze quality/confidence.
- `warhead_load_field`: selected `R_effect_variant`, `rho_effect`, load band,
  and mechanism-load facts.
- `component_response`: component response band, failure-probability band,
  integrity-delta band, and sampled failure.
- `consequence_projection`: evaluate only after the component-response metric is
  explicit; do not back-infer it from a kill flag.

## P2 Closure State

P2 is pass. This matrix provides the first range x offset-angle heatmap, a
sampling-density estimate, and
classifies the 8 km / 30 deg nonmaneuvering cell as `nominal_in_envelope` under
the AIM-120C-like engineering-proxy expectation. P2 has selected the first
`R_effect_variant` evaluation set: `REV-RUNTIME-PROJECTION`, `REV-EQ-FUZE`, and
`REV-SMALLER-LOAD`; `REV-DECLARED-EFFECT` remains held until a future review row
or admitted evidence exists.

P2 itself does not resolve:

- meter-valued `R_effect`;
- component-response probability thresholds;
- consequence, Pk, or reward authority.

Concrete stage-report metrics have moved into the independent P3 mapping page:
[kill_chain_metric_mapping_20260623.md](kill_chain_metric_mapping_20260623.md).
Remaining parameter values, thresholds, and harness execution design move to P4
or follow-on evidence work and remain inside docs-only / guarded-planning
boundaries.
