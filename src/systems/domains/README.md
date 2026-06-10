# `src/systems/domains` Boundary

`systems/domains` owns per-tick ECS runtime systems that are specific to a
concrete execution domain. It keeps new domain runtime owners out of the
`systems/` root while preserving the system-layer rule: files here register or
run ECS systems, but they do not own world lifecycle, facades, bindings, or
scenario orchestration.

## Layout

- `air/`: air-domain flight control, aero state, aerodynamic force/moment, and
  propulsion systems.
- `naval/`: naval ship/submarine motion, embarked-air token runtime, naval
  logistics, and naval weapon-release bridge systems.

There is no `ground/` runtime owner yet. Ground-contact primitives remain in
`systems/physics` until land movement, sensing, fires, damage, and terrain
runtime ownership is accepted.

## Dependency Direction

Domain systems may consume shared `components/`, domain components under
`components/domains`, model interfaces, and replaceable `models/`. They must not
depend on sibling domains as a shortcut, nor on `runtime/facade`,
`interfaces/python`, or training/scenario glue.
