# Kill-Chain Idealized Expectation Contract

Status: `2026-06-21` draft contract for
[Kill-Chain Expectation Standardization](README.md). This document is a
repository engineering-proxy expectation contract. It is not real AIM-120C,
F-16C, deterministic-fuze, or Pk authority.

Schema label: `a2.kill_chain_idealized_expectation_contract.v0`

## Contract Boundary

The contract defines expected behavior for a declared proxy profile. It must not
be read backwards from current runtime output. Current runtime output is evidence
about implementation behavior; this contract is the upstream target used to
judge whether that behavior should be calibrated, held, or reclassified.

The contract has three authority levels:

| Level | Meaning | Runtime use |
| --- | --- | --- |
| `engineering_proxy_expectation` | Project-owned idealized expectation for simplified but credible behavior. | May drive docs, diagnostics, and guarded calibration plans. |
| `research_candidate_expectation` | Derived from reviewable methods or candidate data but not admitted as runtime truth. | May drive benchmark design and residual tracking. |
| `admitted_authority_expectation` | Passed a future task-specific authority gate. | May drive runtime authority only for the admitted field and scope. |

The current document only uses `engineering_proxy_expectation`.

## Stage Contract

The kill chain is evaluated as ordered stage contracts:

| Stage | Question answered | Primary expected output | Must not decide |
| --- | --- | --- | --- |
| `launch_window` | Was the shot categorized as nominal, marginal, or outside the declared launch envelope? | scenario class, target motion class, launch-envelope label | damage strength |
| `guidance_approach` | Did the missile approach to the declared fuze/effect region? | nearest approach, time-to-nearest, remaining energy or kinematic margin | component damage |
| `fuze_decision` | Should the fuze trigger for the nearest-approach geometry? | trigger yes/no, trigger point, fuze quality or confidence | warhead load strength beyond declared fuze effects |
| `warhead_load_field` | What load field reaches the target proxy? | normalized spatial/load band and mechanism-specific load facts | target consequence |
| `component_response` | How should the target proxy respond to the load field? | component response band, integrity delta band, failure-probability band | mission outcome by itself |
| `consequence_projection` | What observable mission or platform consequences follow? | mission, mobility, sensor, structural, lifecycle, or loss-state consequence band | back-propagated guidance/fuze success |

Calibration must target one stage at a time. If a proposed metric crosses
stages, the metric must declare itself as cross-stage and cannot be used as a
single-layer calibration objective.

## Normalized Distance Vocabulary

Fixed distances such as "10 m" are not meaningful without a declared profile.
The contract uses:

```text
rho_fuze = miss_distance / R_fuze
rho_effect = miss_distance / R_effect
```

where:

- `R_fuze` is the declared proximity-fuze trigger radius for the proxy profile.
- `R_effect` is the declared effective warhead-load radius for the proxy
  expectation. It is an independent review variable by default, not an alias for
  `R_fuze` and not a value inferred from current runtime response. It may later
  be set equal to, smaller than, or larger than a descriptor/runtime projection
  radius, but that choice must be declared before interpreting a case.

The initial ordinal expectation bands are:

| Band | Normalized distance | Idealized expectation |
| --- | --- | --- |
| `core` | `rho_effect <= 0.25` | Strong load field and strong component response are expected. |
| `effective` | `0.25 < rho_effect <= 0.50` | Significant load and non-trivial component response are expected. |
| `outer_effective` | `0.50 < rho_effect <= 0.80` | Moderate or edge-significant response is expected; near-zero response needs explanation. |
| `edge` | `0.80 < rho_effect <= 1.00` | Weak, intermittent, or highly geometry-dependent response is acceptable. |
| `outside_effect` | `rho_effect > 1.00` | No effective warhead-load response is the default unless another declared mechanism applies. |

These are ordinal bands, not probability numbers. Quantitative thresholds are a
future P3/P4 decision.

## AIM-120C-Like Seed Profile

Profile id: `KCES-AIM120C-LIKE-FIGHTER-V0`

Authority: `engineering_proxy_expectation`

Purpose: provide a first discussion target for medium-range active-radar
air-to-air missile behavior against a fighter-size synthetic target.

Declared proxy assumptions:

| Field | Seed value | Authority note |
| --- | --- | --- |
| weapon family label | `AIM-120C-like active-radar missile` | Family label only; not a variant-specific performance claim. |
| warhead mechanism | `blast_fragmentation` | Repository engineering proxy. |
| target class | `fighter_size_synthetic_target` | Uses repository F-16C-like synthetic vulnerability shape as a proxy, not real F-16C truth. |
| target motion class | `nonmaneuvering_constant_velocity` for the first matrix | Future matrices must add maneuvering cases. |
| launch-window class | `nominal_in_envelope` must be declared case by case | The contract does not automatically classify every launch as nominal. |
| `R_fuze` | profile-declared, initially mapped to the repository trigger-radius proxy when needed | Not real deterministic-fuze authority. |
| `R_effect` | `independent_review_variable` | Not derived from `R_fuze`, not inferred from current weak response, and not a real warhead-effect truth. |

Policy decision:

```text
R_effect_policy = independent_review_variable
```

The seed profile therefore treats fuze-trigger range and effective-load range as
separate concepts. Scenario rows may carry `R_effect_variant` labels such as
`effect_radius_equals_fuze_radius`, `effect_radius_smaller_than_fuze_radius`, or
`effect_radius_larger_than_runtime_projection`, but those are review variants,
not hidden defaults.

Interpretation rule:

- If a case is declared `nominal_in_envelope`, nonmaneuvering, and sensor/truth
  gated for an idealized test, guidance is expected to place the nearest
  approach inside `R_fuze`.
- If the same case enters `R_fuze` but has `rho_effect` in `core`,
  `effective`, or `outer_effective`, the downstream load/response stages should
  not collapse to a near-zero response without a declared target-resistance or
  warhead-effect reason.
- If profile review chooses `R_effect` smaller than the miss distance, weak
  response can be consistent with the expectation contract; the case then
  belongs to `outside_effect`, not to an unexplained failed near-fuze lethality
  expectation.

This is the answer to the "10 m" ambiguity: the contract does not say 10 m must
or must not kill. It says 10 m cannot be interpreted until `R_fuze`, `R_effect`,
target proxy, and consequence metric are declared.

## Launch-Window Expectations

For a proxy case to be called `nominal_in_envelope`, it should explicitly state:

- initial range, altitude, ownship and target speeds;
- target aspect, offset angle, and closure geometry;
- target maneuver class;
- seeker/data/track simplification used by the test;
- missile kinematic constraints used by the profile;
- whether the test is idealized truth-guided, sensor-limited, or full runtime.

Expected stage result:

| Launch-window class | Guidance expectation | Failure interpretation |
| --- | --- | --- |
| `nominal_in_envelope` | nearest approach should normally enter `R_fuze` for nonmaneuvering targets | miss outside `R_fuze` is a guidance/kinematic/modeling issue until reclassified. |
| `marginal_in_envelope` | fuze entry is plausible but not guaranteed | repeated misses may be acceptable if documented. |
| `outside_envelope` | no fuze entry expectation | no calibration pressure on lethality. |

The 8 km / 30 deg case should not be used as a calibration oracle until it is
explicitly classified under this table.

## General Air-To-Air Template

Every future expectation row should declare:

| Field | Required content |
| --- | --- |
| `profile_id` | Stable id for the proxy expectation. |
| `authority_level` | One of the authority levels above. |
| `weapon_proxy` | Family, guidance class, warhead mechanism, and declared proxy parameters. |
| `target_proxy` | Size class, vulnerability profile, component map, and synthetic/authority status. |
| `geometry_class` | Range, aspect, offset, closure, altitude band, and target maneuver class. |
| `R_fuze` and `R_effect` | Declared radii and their source/authority. |
| `expected_stage_bands` | Expected launch, guidance, fuze, load, response, and consequence bands. |
| `measurement_fields` | Stage-report fields used to evaluate the row. |
| `forbidden_claims` | Real-weapon, real-target, deterministic-fuze, Pk, or reward claims that remain refused. |

## Open Decisions

- Whether ordinal component-response bands should be defined by integrity delta,
  component failure probability, sampled failures, or mission consequence.
- Whether launch-window classes should be maintained in task-local docs first or
  promoted into a broader air/weapon standard after review.

Until those decisions close, this contract is a standardization target, not a
runtime calibration instruction.

Closed P1 decision:

- `R_effect` remains an independent review variable for the AIM-120C-like seed.
  This closes the P1 radius-policy ambiguity while preserving later sensitivity
  rows in the scenario matrix.
