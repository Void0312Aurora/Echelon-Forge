# Example Scenario Fixtures

This directory is for small example-only scenario fixtures.

Canonical training, evaluation, diagnostic, and contract scenarios currently live under the repository-level [scenarios](../../scenarios/README.md) directory. Keep using repo-relative `scenarios/...` paths for maintained configs, tests, and tools.

Do not move canonical scenarios here until path compatibility has been added and all maintained references have been updated. A safe migration would first teach loaders, contract runners, and tools to accept both `scenarios/...` and `examples/scenarios/...`, then update references in a measured pass.
