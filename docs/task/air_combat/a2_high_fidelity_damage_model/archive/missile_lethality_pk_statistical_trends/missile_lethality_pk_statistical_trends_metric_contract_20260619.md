# MLF-9 Metric Contract

Status: `2026-06-19` P2 initial contract pass. This contract defines the first
bounded statistical trend surface and keeps calibrated Pk held.

Chinese companion:
[missile_lethality_pk_statistical_trends_metric_contract_20260619.zh.md](missile_lethality_pk_statistical_trends_metric_contract_20260619.zh.md).

## Contract Boundary

MLF-9 reports simulation trends over replayable chain rows. It does not report
real probability of kill. Every rate produced under this contract must be read
as:

```text
within this synthetic scenario / fixture population, among rows that satisfy
this explicit denominator, this fraction reached this simulated outcome bucket
```

It must not be read as:

```text
this real weapon has this Pk against this real target
```

## Required Row Source

The initial implementation must use `lethality_chain_rows` or an equivalent
test fixture with the same fields. Rows must carry:

- `episode`, `step`, `sim_time_s`
- `chain_id`, `event_id`, `parent_event_id`
- `stage`, `source_event_kind`, `source_event_id`
- `munition_id`, `target_id`
- `evidence_level`, `observation_mode`, `consumer_visibility`

For MLF-9 v1, the accepted stage set is:

1. `nearest_approach`
2. `fuze`
3. `warhead_mechanism`
4. `spatial_coverage`
5. `component_load`
6. `component_damage`
7. `structural_breakup`
8. `platform_consequence`
9. `lifecycle`

`training_projection` remains outside the MLF-9 v1 row source because reward
or training consumers would blur statistical trend evidence with training
feedback.

## Denominators

| Denominator | Definition | Allowed use | Not allowed |
| --- | --- | --- | --- |
| `chain_count` | Distinct `chain_id` values in the report population | Overall sample size | Claiming independent real-world trials unless fixture generation proves independence |
| `released_chain_count` | Chains with a launch/effects source row or explicit fixture release marker | Given-release rates | Using it as real shot count |
| `detonated_chain_count` | Chains with effective warhead/spatial/component-load rows and no terminal negative fuze reason | Given-effective-detonation rates | Treating synthetic fuze outcome as real fuze reliability |
| `component_damage_chain_count` | Chains with at least one `component_damage` row | Structural or consequence rates conditional on component damage | Claiming component damage probability is calibrated |
| `structural_breakup_chain_count` | Chains with at least one `structural_breakup` row | Consequence/lifecycle rates conditional on structural breakup | Treating breakup as direct crash/deletion |
| `platform_consequence_chain_count` | Chains with a `platform_consequence` row | Functional outcome distribution | Treating consequence rows as real mission kill probability |

Every report must print the denominator name, count, and filter expression used.

## Outcome Buckets

| Bucket | Row fields | Meaning | Boundary |
| --- | --- | --- | --- |
| `fuze_negative` | `fuze_triggered == 0` or terminal negative reason | Chain did not reach effective detonation | Negative reason is a simulation fact, not a real miss statistic |
| `effective_component_damage` | `component_damage` row count > 0 | At least one component-damage fact was sampled | Generic component damage only |
| `structural_breakup` | `structural_breakup` row count > 0 | At least one named structural breakup fact exists | Not a crash rule |
| `airframe_breakup` | any structural row has `airframe_breakup == 1` | Airframe-level breakup fact exists | Not debris physics |
| `functional_kill` | mission/mobility/sensor/survivability kill fields | Platform consequence reached a functional bucket | Not real-world mission outcome probability |
| `terminal_lifecycle` | lifecycle row has `lifecycle_terminal == 1` or terminal ground lifecycle | Terminal lifecycle fact exists | Diagnostics-only rows stay out of reward |

## Grouping Fields

Initial trend reports may group by:

- miss-distance bucket;
- direct-hit vs proximity evidence;
- mechanism family;
- component system;
- component failure mode;
- structural break mode;
- terminal lifecycle class.

Reports must avoid weapon or target labels that imply calibration. If a scenario
name contains a platform label, the report title must still state "simulation
trend" or "fixture trend".

## Uncertainty Labels

Initial MLF-9 rates may use Wilson-style binomial intervals or an equivalent
explicit interval method already used by diagnostics tooling. The report must
state:

- sample count;
- confidence level;
- interval method;
- whether high-variance flags were triggered;
- whether samples came from deterministic fixtures, seed sweeps, or live probe
  episodes.

## P3 Implementation Gate

The next implementation package may build a trend harness only if it:

- consumes explicit rows and does not read hidden runtime state;
- exposes denominators and filters in output;
- has deterministic controlled-fixture tests;
- refuses real Pk, calibration, reward, and entity-deletion claims.

## Validation

P2 row-surface validation already passed:

```bash
PYTHONPATH=build-workshop:. pytest -q \
  tests/runtime/air_combat/test_diagnostics_process_probe_lethality.py \
  tests/runtime/air_combat/test_diagnostics_process_probe_summary.py \
  tests/training/test_fire_timing_fault_localization_contracts.py
```

Result: `47 passed`.
