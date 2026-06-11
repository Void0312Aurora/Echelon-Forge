# A2 MLF-3A Inventory Acceptance Record

Status: `2026-06-09` accepted for MLF-3A. This record only accepts the read-only inventory; it does not mark all of MLF-3 complete.

Chinese main text: [missile_lethality_warhead_effects_inventory_20260609.zh.md](missile_lethality_warhead_effects_inventory_20260609.zh.md)

## Conclusion

MLF-3A passed. The code already has standard event structures and bindings for warhead mechanism, spatial coverage, and component load, but live writers were missing before this round. The old `EffectsEvent` already carries reusable load fields, so the next work should project those facts into standard events instead of redefining kill or crash rules.

## Confirmed Locations

- Event structures: `src/runtime/contracts/engagement_contracts.h`
- Recent-event containers: `src/core/engine/engagement_event_types.h`
- Facade export containers: `src/runtime/facade/runtime_facade_types.h`
- Python bindings: `src/interfaces/python/bindings_runtime.cpp`, `src/interfaces/python/bindings_core.cpp`
- Runtime gaps: `src/core/interfaces/engagement_event_recorder.h`, `src/core/engine/simulation_kernel_engagement_event_store.*`
- Legacy field source: `src/core/interfaces/effects_model.h`, `src/core/interfaces/engagement_effects_event_builder.h`
- Effects model entry: `src/models/weapons/default_effects_model.cpp`, `src/models/weapons/detail/default_effects_warhead_detail.inc`
- Diagnostics entry: `tools/diagnostics/air_combat_weapon_employment_process_probe.py`

## Retained Boundaries

- Do not add type-specific AIM-120C, MQ-9, or other real parameters.
- Do not write CMO-DB, public webpages, historical tests, or engineering assumptions as type-level authority.
- Do not let no-detonation paths emit warhead, spatial coverage, or component-load events.
- Do not convert load facts directly into kill, crash, or entity deletion.

## Follow-On Entry Points

1. `MLF-3B`: add recorder/event-store writers and project existing `EffectsEvent` fields into standard events.
2. `MLF-3B` focused tests: prove detonation exports warhead, spatial, and component-load standard events.
3. `MLF-3E`: make diagnostics prefer standard events, with old `EffectsEvent` only as transitional fallback.
