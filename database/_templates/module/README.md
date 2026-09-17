# module

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/_templates/module/README.md`
Owner: `database/equipment-data`
Last verified: `not established`
Content status: provisional navigation scaffold; the final data contract is not established.

## Responsibility

Provides one provisional template per module type represented by the current repository examples. The templates contain no concrete equipment data.

## Templates

- `engine.template.json`: derived from `examples/config/database/aircraft/modules/engines/f110_ge_129.json`.
- `sensor.template.json`: derived from `examples/config/database/aircraft/modules/sensors/an_apg_68.json`.
- `ew_suite.template.json`: derived from `examples/config/database/aircraft/modules/ew_suites/gen4_standard.json`.
- `rcs_profile.template.json`: derived from `examples/config/database/aircraft/modules/rcs_profiles/fighter_standard.json`.

Each template has a matching schema: `engine.schema.json`, `sensor.schema.json`, `ew_suite.schema.json`, and `rcs_profile.schema.json`. Shared definitions are in `../common.schema.json`.

## Not Responsible For

This directory does not define runtime behavior, source authority, or the final equipment-data schema.

## Hierarchy

- Parent: `_templates/`
- Children: None

## Maintenance Trigger

Update this index when its responsibility, child structure, or governing data contract changes.
