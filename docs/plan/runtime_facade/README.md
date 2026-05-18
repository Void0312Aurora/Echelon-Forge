<!-- Machine-translated draft generated on 2026-05-18 from docs/plan/runtime_facade/README.zh.md. Review before treating this file as authoritative. -->

# `runtime_facade/`

This directory contains contracts and follow-up cleanup plans for the runtime facade mainline. The execution records have been moved to `../archive/runtime_facade/`.

Recommended reading order:

1. [runtime_facade_contract_plan.zh.md](runtime_facade_contract_plan.zh.md)
2. [archive/runtime_facade/README.md](../archive/runtime_facade/README.md)
3. [archive/runtime_facade/runtime_facade_task_bootstrap_plan.md](../archive/runtime_facade/runtime_facade_task_bootstrap_plan.md)
4. [archive/runtime_facade/runtime_facade_layering_cleanup_freeze.md](../archive/runtime_facade/runtime_facade_layering_cleanup_freeze.md)

Usage rules:

- Contract documents define boundaries, but are not automatically effective execution freezes.
- The first batch of `WP1-WP6` execution records now lives in `../archive/runtime_facade/`.
- If subsequent implementation continues along the runtime facade mainline, it should be scoped by a new freeze task list.
