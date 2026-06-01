# Diagnostics README

`tests/diagnostics/` contains exploratory and debugging-oriented scripts.

These are not treated as contract regressions. They are kept separate because they typically:

- run longer exploratory loops
- emit rich human-readable traces
- depend on optional training/runtime packages
- are used to investigate failures rather than assert a single stable invariant

When a diagnostic stabilizes into a deterministic regression, prefer migrating it into:

- `tests/contracts/` plus a thin runner, or
- a small focused test in `tests/` if contracts are not a good fit

This folder is intentionally not the home for general-purpose unit/runtime
tests. If a file starts asserting stable invariants under `pytest`, it should be
moved back into the main `tests/` tree rather than staying here.

At the moment, the active exploratory scripts have been cleaned out of this
folder. The only maintained file currently left here is
`test_diagnostics_import_order.py`, a pytest regression for diagnostics/runtime
import-order behavior. It is stable test evidence, not an exploratory script,
and should move to a main test domain once import-order ownership is settled.

If new diagnostics are added here, they should be temporary and explicitly on a
path toward either:

- promotion into `tools/diagnostics/` as a maintained operator-facing tool, or
- migration into `tests/contracts/` / focused `tests/` once the behavior is stable.
