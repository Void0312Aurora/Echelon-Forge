<!-- Machine-translated draft generated on 2026-05-18 from docs/plan/runtime_facade/README.zh.md. Review before treating this file as authoritative. -->

<!-- Machine-translated draft generated on 2026-05-18 from docs/plan/runtime_facade/README.md. Review before treating this file as authoritative. -->

# `runtime_facade/`

This directory contains contracts, execution records, and follow-up cleanup plans for the runtime facade mainline.

Recommended reading order:

1. [runtime_facade_contract_plan.zh.md](runtime_facade_contract_plan.zh.md)
2. [runtime_facade_task_bootstrap_plan.zh.md](runtime_facade_task_bootstrap_plan.zh.md)
3. [runtime_facade_layering_cleanup_freeze.zh.md](runtime_facade_layering_cleanup_freeze.zh.md)

Usage rules:

- Contract documents define boundaries, but are not automatically effective execution freezes.
- `task_bootstrap` now contains the execution records for the first batch of `WP1-WP6`.
- If subsequent implementation continues along the runtime facade mainline, it should be scoped by a new freeze task list.
