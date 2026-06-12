# Archived JSON Contracts

This directory contains JSON contract specs removed from the maintained
`tests/contracts/` root.

Archived specs are retained for provenance and comparison only. They should not
be counted as active contract coverage, and contract batch runners should not
select them by glob.

Current archived contract surfaces:

- `env_regression/`: retired raw `UniversalEnv` reset/step/reward/observation specs.
- `scripted_bridge/`: retired scripted wrapper bridge specs that depended on the raw env executor.
- `unit/`: historical unit-regression baselines retained for comparison.
