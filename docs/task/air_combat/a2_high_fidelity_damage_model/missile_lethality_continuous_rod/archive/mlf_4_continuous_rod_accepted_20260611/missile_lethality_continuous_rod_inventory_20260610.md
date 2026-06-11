# A2 MLF-4A Continuous-Rod Read-Only Inventory Packet

Status: `2026-06-10` accepted inventory packet. The original `MLF-4A-X1` worker did not return an acceptable packet, so the main thread completed recovery review over the same read-only scope.

Chinese main text: [missile_lethality_continuous_rod_inventory_20260610.zh.md](missile_lethality_continuous_rod_inventory_20260610.zh.md)

## Worker Packet

status: pass

touched files:

- No runtime source edits.
- This inventory packet and MLF-4 status/queue docs were updated by the main thread.

commands/outcomes:

- `wait_agent 019eb210-9e5e-7b80-bc77-335b98d5796c`: no completion packet was available.
- `resume_agent 019eb210-9e5e-7b80-bc77-335b98d5796c`: returned `pending_init`.
- `close_agent 019eb210-9e5e-7b80-bc77-335b98d5796c`: worker still had `pending_init` status when closed.
- `rg -n "rod_cut_margin|continuous_rod|rod_cut|cut_margin" src/runtime src/models src/components tools tests/runtime/air_combat`: confirmed field, model-branch, diagnostics, and historical-test entry points.
- `rg -n "warhead_mechanism_events|component_load_events|mechanism_rod|rod_cut|LETHALITY_CHAIN_STAGES" tools/diagnostics tests/runtime/air_combat`: confirmed diagnostics paths and existing guard tests.

remaining paths:

- `MLF-4B-W1`: stabilize the standard rod/cut event surface and focused tests.
- `MLF-4C-W1`: revalidate generic continuous-rod geometry as current MLF-4 accepted tests instead of promoting historical Phase 3 tests directly.
- `MLF-4D-W1`: project component cut exposure to standard component-load facts without emitting failure.
- `MLF-4E-W1`: diagnostics and no-detonation/non-rod guards.

behavior risks:

- Existing continuous-rod logic already influences component damage and historical component-failure tests; later MLF-4 work must isolate cutting facts from component failure or structural consequences.
- Existing constants are generic research assumptions, not AIM-120C or any real weapon-specific rod parameters.
- Historical Phase 3 tests cover useful phenomena, but they are not this phase's accepted evidence.

integration notes:

- The existing `WarheadMechanismEvent::rod_cut_margin` and `ComponentLoadEvent::rod_cut_margin` appear sufficient for MLF-4B's standard event surface. A dedicated rod/cut event is not recommended unless 4B finds a need for more cut-specific fields.
- No-detonation gate evidence exists: no-detonation paths emit no standard warhead/spatial/component load events, and effects rod values remain zero.
- Non-rod gate evidence exists historically: blast paths keep rod values at zero. MLF-4B/4E should still add focused MLF-4 tests that pin this to standard events and diagnostics.

## Read-Only Findings

### Event And Export Fields

- Standard warhead events already expose `rod_cut_margin`: [engagement_contracts.h](../../../../../../../src/runtime/contracts/engagement_contracts.h).
- Standard component-load events already expose `rod_cut_margin`: [engagement_contracts.h](../../../../../../../src/runtime/contracts/engagement_contracts.h).
- Legacy effects and component rows also keep rod fields: `mechanism_rod_cut_margin`, `component_primary_mechanism_rod_cut_margin`, and `ComponentMechanismLoadRow::mechanism_rod_cut_margin`.
- Python bindings expose those fields: [bindings_runtime.cpp](../../../../../../../src/interfaces/python/bindings_runtime.cpp).
- The event store extracts rod values from `EffectsEvent` into standard `WarheadMechanismEvent` and `ComponentLoadEvent`: [simulation_kernel_engagement_event_store.cpp](../../../../../../../src/core/engine/simulation_kernel_engagement_event_store.cpp).

### Continuous-Rod Cut-In Points

- `continuous_rod` already has family weights, spatial projection, penetration/cut estimation, orientation weighting, and vulnerability filter entry points in the default effects model: [default_effects_warhead_detail.inc](../../../../../../../src/models/weapons/detail/default_effects_warhead_detail.inc).
- The current `rod_cut_margin` calculation uses generic rod count, rod segment mass, closure speed, range quality, orientation weights, spatial hit estimate, and target armor thickness. These values should remain labeled as generic assumptions.
- Spatial projection already records `mechanism_load` into component rows: [default_effects_spatial_projection_detail.inc](../../../../../../../src/models/weapons/detail/default_effects_spatial_projection_detail.inc).
- The scratch/result/builder chain already moves sampled rod values into `EffectsEvent`: [default_effects_state_detail.inc](../../../../../../../src/models/weapons/detail/default_effects_state_detail.inc), [default_effects_result_detail.inc](../../../../../../../src/models/weapons/detail/default_effects_result_detail.inc), [engagement_effects_event_builder.h](../../../../../../../src/core/interfaces/engagement_effects_event_builder.h).

### Diagnostics Path

- Diagnostics rows already include `rod_cut_margin`: [air_combat_weapon_employment_process_probe.py](../../../../../../../tools/diagnostics/air_combat_weapon_employment_process_probe.py).
- Diagnostics prefer standard `warhead_mechanism_events` and `component_load_events`, with `EffectsEvent` as fallback.
- Existing diagnostics contract tests mainly lock field shape and standard-event precedence; they do not yet provide MLF-4-specific continuous-rod positive/negative cases.

### Test Isolation

- `tests/runtime/air_combat/weapon_guidance_realism/warhead_effects.py` contains historical Phase 3 tests for orientation axis, attitude, positive rod values, non-rod zero values, and component-row rod values.
- `component_damage.py` and `aircraft_damage.py` contain historical continuous-rod tests that reach component failure or structural effects. These must not be used as MLF-4 acceptance evidence because MLF-4 does not accept failure or structural outcomes.
- 4B/4C/4D/4E should add or split focused MLF-4 tests that only check cutting facts, standard events, and diagnostics, not component failure, crash, or structural breakup.

## Acceptance Conclusion

`MLF-4A-X1` is accepted. It completed the read-only inventory of existing fields, branches, historical tests, and gaps, and it is sufficient to unlock `MLF-4B-W1 Standard Rod Event Surface`.

This acceptance does not mean MLF-4 runtime is complete and does not mean the continuous-rod lethality model is high-fidelity. It only means the next step can safely enter standard rod/cut event-surface implementation and test design.
