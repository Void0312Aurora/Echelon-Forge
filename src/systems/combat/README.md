<!-- Machine-translated draft generated on 2026-05-18 from src/systems/combat/README.md. Review before treating this file as authoritative. -->

# `src/systems/combat` Boundary

`systems/combat` stores the combat system tick logic, including damage handling and guidance system scheduling.

## Allowed

- damage system
- guidance system
- Combined calls to `components/combat` and `models/weapons`

## Prohibited

- combat component definitions
- mission reward/termination rules
- Python bindings or facades

## Migration Notes

Rewards and mission results belong to `core/mission`; this directory only handles the progression of combat state within the world.
