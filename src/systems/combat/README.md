# `src/systems/combat` Boundary

`systems/combat` stores the combat system tick logic, including damage handling and guidance system scheduling.

The maintained implementation covers generic combat-state progression, missile
guidance scheduling, pilot weapon release, and the bridge into shared weapon
release services. Naval mission-command weapon release is registered under
`systems/naval`; engagement evidence is exported through runtime contracts and
facade packets. This directory does not make ground fires or ground damage a
maintained runtime.

## Allowed

- Damage system.
- Guidance system.
- Pilot weapon-release system.
- Combined calls to `components/combat`, `models/weapons`, and weapon-release interfaces.

## Prohibited

- Combat component definitions.
- Mission reward/termination rules.
- Python bindings or facades.
- Ground fires, ground damage, or land-domain combat runtime ownership.

## Migration Notes

Rewards and mission results belong to `core/mission`; this directory only handles the progression of combat state within the world.
