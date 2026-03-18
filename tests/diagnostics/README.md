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

Examples in this folder now include:

- physics trace scripts such as drop/takeoff state tracing
- aero-state debug dumps
- gear-damage inspection scripts
