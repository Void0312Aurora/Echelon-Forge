# Ground Platoon Starter Capability Note

This directory is the first source-controlled `ground` fixture root under
`examples/config/database/`.

`ground_platoon_starter.seed` is a platoon-centered semantic seed for G2
contract usability and G3 planning. It intentionally stops at:

- normalized `ground` specialization and `Army` service-profile alignment
- platoon ownership and command/support relationship anchors
- starter task coverage for `TASK_MOVE`, `TASK_OCCUPY`, and `TASK_SUPPORT`
- construction intent pointing toward capability-bundle lowering

The `.seed` suffix is intentional. The current runtime database loader
recursively consumes `.json` files under `examples/config/database/` as concrete
unit definitions, while this file is not yet a maintained runtime unit schema.
Keeping JSON-shaped content in a non-auto-loaded seed file prevents spurious
runtime loader warnings without weakening the G2 content-root evidence.

It does not claim maintained runtime behavior for movement, terrain, sensing,
fires, weapons, damage, or combat.

Canonical construction direction:

- prefer capability-bundle or additive public-platform lowering
- keep `PlatformFamily = dismounted_unit` and `DoctrineFamily = land_tactics`
  as the first declared ground-aligned families here
- treat `spawn_unit(type_name)` only as compatibility glue when broader spawn
  resolution work needs it
- do not use this fixture to justify a private ground runtime path or legacy
  type-name dispatch as the long-term canonical surface

If later work needs mobility, sensing, launcher, effects, or terrain details,
those should land through accepted capability-bundle/public-platform seams and
their own stage-scoped contracts rather than being implied by this starter
fixture.
