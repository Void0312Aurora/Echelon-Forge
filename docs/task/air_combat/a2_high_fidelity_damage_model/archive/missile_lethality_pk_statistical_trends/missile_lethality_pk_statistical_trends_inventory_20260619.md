# MLF-9 Evidence Inventory

Status: `2026-06-19` P1 inventory pass for MLF-9 Pk/statistical trend inputs.

Chinese companion:
[missile_lethality_pk_statistical_trends_inventory_20260619.zh.md](missile_lethality_pk_statistical_trends_inventory_20260619.zh.md).

## Inventory Decision

MLF-9 can start from existing chain-linked simulation facts, but it must treat
them as replay/trend inputs, not calibrated Pk data. The immediate usable path
is the diagnostics process probe's `lethality_chain_rows`, because it already
joins per-episode/step context, chain/event identifiers, evidence labels, and
stage-specific fields.

The only P1 blocker found in the unified row surface was structural breakup:
C++ contracts, event storage, bindings, and facade packets already expose
`StructuralBreakupEvent`, but the Python diagnostics row contract did not
project `structural_breakup` rows. This branch adds that row projection so MLF-9
can later define structural-outcome denominators without bypassing the common
diagnostics table.

## Input Surfaces

| Surface | Status | Reusable fields | MLF-9 use | Boundary |
| --- | --- | --- | --- | --- |
| Lethality header | accepted input | `chain_id`, `event_id`, `parent_event_id`, `stage`, `source_time_s`, `target`, `evidence_level`, `observation_mode`, `consumer_visibility` in [engagement_contracts.h](../../../../../../src/runtime/contracts/engagement_contracts.h) | Join rows into one replayable chain and preserve evidence labels | Header ordering is not probability calibration |
| Geometry/fuze rows | accepted input | miss distance, local detonation vector, closure, aspect, fuze armed/triggered/sample/reliability, trigger radius | Trend bins such as near/far, direct/proximity, trigger/non-trigger | Synthetic fuze probabilities are not real fuze reliability |
| Warhead/spatial rows | accepted input | mechanism family, fragment/blast/rod values, spatial hit estimate/fraction, pattern/energy scale | Exposure and mechanism grouping | Generic research loads are not weapon-specific truth |
| MLF-5 component damage | accepted input | component name/system, integrity before/after, failure mode/severity, failure probability/sample | Component-damage outcome and component-family grouping | Component probability remains generic and uncalibrated |
| MLF-6 structural breakup | row-surface pass in this branch | breakup state, break mode, detached part ref/count, airframe breakup, cause event id | Structural outcome bucket and bridge between component damage and terminal outcomes | Structural facts are not direct crash or Pk rules |
| MLF-7 platform consequence | accepted input | mission/mobility/sensor/survivability before/after, deltas, kill flags, loss-state transition | Functional outcome bucket | Consequence facts do not imply real-world kill probability |
| MLF-8 lifecycle | accepted input | lifecycle from/to, ground lifecycle, debris count, terminal flag, terminal projection id, diagnostics-only visibility | Terminal wreck / detached-part lifecycle bucket | Lifecycle facts remain diagnostics-only and non-reward by default |
| Window-position sweep | candidate reference | release/effects/component/consequence/mission-kill rates, confidence intervals, variance flags | Reference implementation for rate/uncertainty math | It is a training diagnostic, not MLF-9 authority by itself |

## Current Row Surface

This branch aligns Python diagnostics with the C++ stage list by adding
`structural_breakup` to:

- [tools/diagnostics/lethality_chain_contract.py](../../../../../../tools/diagnostics/lethality_chain_contract.py)
- [tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/schema.py](../../../../../../tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/schema.py)
- [tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/lethality_chain.py](../../../../../../tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/lethality_chain.py)
- [tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/lethality_snapshot.py](../../../../../../tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/lethality_snapshot.py)
- [tests/runtime/air_combat/test_diagnostics_process_probe_lethality.py](../../../../../../tests/runtime/air_combat/test_diagnostics_process_probe_lethality.py)

The row fields added for MLF-9 are:

- `breakup_state`
- `break_mode`
- `detached_part_ref`
- `detached_part_count`
- `airframe_breakup`
- `cause_event_id`

Snapshot fields added for downstream trend summaries are:

- `lethality_chain_structural_breakup_count`
- `lethality_chain_breakup_state`
- `lethality_chain_break_mode`
- `lethality_chain_detached_part_ref`
- `lethality_chain_detached_part_count`
- `lethality_chain_airframe_breakup`
- `lethality_chain_structural_cause_event_id`

Rows are now sorted by chain id, canonical stage order, event id, and source
event id so structural rows appear between component-damage and
platform-consequence stages regardless of which producer loop saw them first.

## Missing Or Held Inputs

| Gap | Effect on MLF-9 | Proposed handling |
| --- | --- | --- |
| No accepted MLF-9 denominator yet | Rates such as "given launch", "given detonation", or "given component damage" would be ambiguous | Define denominators in P2 contract before trend extraction |
| No calibrated sample population | Any reported rate is a simulation replay rate, not real Pk | Label every report as synthetic simulation trend |
| No public-outcome admission | Cannot fit or validate against real events | Hold for MLF-10 |
| No first-class debris entity | Cannot count fragment interactions or debris-caused secondary damage | Use lifecycle terminal/detached facts only |
| DCR controlled nonzero consequence fixture still partial | Reward/consequence training evidence cannot be used as MLF-9 acceptance | Keep reward work adjacent, not authoritative |

## Safe Implementation Write Sets

Allowed for the initial MLF-9 implementation slices:

- MLF-9 docs under this directory.
- Diagnostics row contract and process-probe tests when they expose already
  accepted event facts.
- Test-only fixtures that build explicit rows without changing runtime physics.

Held until a later contract:

- Runtime damage physics, probability parameters, weapon profiles, reward
  shaping, entity lifecycle, or archived MLF evidence packages.

## Validation

Commands run for this inventory/row-surface pass:

```bash
python3 -m py_compile \
  tools/diagnostics/air_combat_weapon_employment_process_probe.py \
  tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/lethality_chain.py \
  tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/lethality_rows.py \
  tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/lethality_snapshot.py \
  tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/schema.py \
  tools/diagnostics/lethality_chain_contract.py

PYTHONPATH=build-workshop:. pytest -q \
  tests/runtime/air_combat/test_diagnostics_process_probe_lethality.py \
  tests/runtime/air_combat/test_diagnostics_process_probe_summary.py \
  tests/training/test_fire_timing_fault_localization_contracts.py
```

Result: `47 passed`; py-compile passed.
