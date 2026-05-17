# Examples

`examples/` now primarily serves as a maintained input/config surface plus a
small set of lightweight fixtures and visualization assets.

This directory is no longer a catch-all for demos, legacy experiments, or
alternate training entrypoints.

## Structure

- `config/`
  - Maintained JSON config inputs for training, diagnostics, prefabs, and unit
    databases.
- `scenarios/`
  - Example-only scenario fixtures. Canonical maintained scenarios live under
    the repository-level [scenarios/README.md](../scenarios/README.md).
- `viz/`
  - Visualization assets and example visualization entrypoints when present.

## Current Entry Surfaces

- [config/training/README.md](config/training/README.md)
  - Maintained training config entrypoints and status taxonomy.
- `config/database/`
  - Unit, aircraft, and module database inputs used by the runtime/content loader.
- `config/diagnostics/`
  - Maintained benchmark and diagnostics config inputs.
- `config/prefabs/`
  - Shared prefab/config fragments used by scenario and content inputs.
- [scenarios/README.md](scenarios/README.md)
  - Scope note for example-only scenario fixtures.

## Usage Notes

- Prefer repo-relative `scenarios/...` paths for maintained configs, tests, and tools.
- Treat `examples/scenarios/` as fixtures or compatibility examples, not as the
  canonical source of maintained training/eval scenarios.
