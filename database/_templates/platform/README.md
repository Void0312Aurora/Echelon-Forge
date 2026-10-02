# platform

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/_templates/platform/README.md`
Owner: `database/equipment-data`
Last verified: `not established`
Content status: provisional navigation scaffold; the final data contract is not established.

## Responsibility

Provides one provisional template per platform type represented by the current repository examples: aircraft, ship, submarine, ground, and facility. The templates contain no concrete equipment data.

## Templates

- `aircraft.template.json`: derived from `examples/config/database/aircraft/units/mq9_reaper.json` and the aircraft fields used by `f16c_block50.json`.
- `ship.template.json`: derived from `examples/config/database/ships/units/red_surface_combatant_minimal.json` and `ddg51_flight_i_uss_arleigh_burke.json`.
- `submarine.template.json`: derived from `examples/config/database/ships/units/kilo_class_mvp.json`.
- `ground.template.json`: derived from `examples/config/database/ground/units/ground_platoon_mvp.json`.
- `facility.template.json`: derived from `examples/config/database/facilities/generic_airbase.json`.

Each template has a matching schema: `aircraft.schema.json`, `ship.schema.json`, `submarine.schema.json`, `ground.schema.json`, and `facility.schema.json`. Shared definitions are in `../common.schema.json`.

## Not Responsible For

This directory does not define runtime behavior, source authority, or the final equipment-data schema.

## Hierarchy

- Parent: `_templates/`
- Children: None

## Maintenance Trigger

Update this index when its responsibility, child structure, or governing data contract changes.
