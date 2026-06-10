# `src/components/domains` Boundary

`components/domains` owns component slices that are specific to a concrete
execution domain. It keeps domain growth out of the `components/` root while
preserving the component-layer rule: files here are data and DTOs, not runtime
or system logic.

## Layout

- `air/`: air-domain platform, combat, command, and tasking components.
- `naval/`: naval-domain platform, combat, command, and tasking components.
- `ground/`: ground-domain combat, command, and tasking owner slices. This is
  still bounded to the accepted bootstrap/static-tasking surface.

Inside a domain, prefer capability subdirectories such as `platform/`,
`combat/`, `command/`, and `tasking/`. New domains should follow the same shape
instead of adding more top-level component directories.

## Dependency Direction

Domain component slices may depend on shared component foundations such as
`components/basic`, `components/combat/common`, `components/command/common`, and
`components/tasking/common`. They must not depend on sibling domains, `systems/`,
`models/`, `core/`, `runtime/`, or `interfaces/`.
