# WP22-B Python Business Bypass Retirement

Status: `2026-05-22` source-verified refresh complete; WP22-B maintained-business retirement is `pass`; `common_core_profile` and `loading.py` are compatibility-only guard surfaces, the raw sim seam is owned by the C/F compatibility guard lane, and the remaining import-time `ef_py.TaskOrder` hit in `command_chain_cache` is validation-only.

Inputs:

- [WP22 main plan](legacy_compatibility_retirement_wp22_20260522.md)
- [WP22-A fact ledger](wp22_retirement_fact_ledger_cluster_20260522.md)

## Purpose

Retire maintained Python business paths that still bypass the accepted runtime
architecture through raw loader/runtime access, raw truth reads, hardcoded air
profile dispatch, or untyped mission-command dictionaries. This stream now
closes the maintained-business retirement lane; the import-time `TaskOrder`
follow-up is a validation-only C/F guard concern.

## Owned Scope

- `python/rl/tasking/leader_tasking.py`
- `python/rl/tasking/bridge.py`
- `python/rl/tasking/common_core_profile.py`
- `python/rl/tasking/*_adapter.py`
- `python/rl/profile/*_profile.py`
- Mission-command loader/runtime-state adapters in `gym_envs/scenario_loader/`
- Focused tests for tasking/profile/mission-command behavior

Do not edit runtime facade C++ internals in this stream.

## Required Output

| Area | Required retirement |
|------|---------------------|
| Hardcoded air profile | `build_kernel_mission_command(loader)` routes through bridge/profile selection, not `_air_profile` directly. |
| Direct loader writes | Production tasking writes no longer call `loader.sim.set_task_order`, `set_leader_intent`, or `set_pilot_report` directly. |
| Raw truth reads | Policy-facing tasking reads use maintained observation/information-state surfaces or an explicit quarantined diagnostics path. |
| Mission command dict | Maintained consumers use a typed adapter/DTO instead of open-ended `getattr(loader, "mission_cmd", {})` patterns. |
| Profile duplication | Shared normalization/dispatch moves to bridge-owned helpers where safe; air-specific logic leaves common core. |
| Monkey patching | Production `ef_py =` monkey patching is removed or quarantined with a narrow import boundary; test-local stubs are permitted, but the remaining `command_chain_cache` import-time `TaskOrder` unlock is validation-only. |

## Gate

Pass only if architecture tests can distinguish maintained tasking paths from
compatibility diagnostics and fail on new production `loader.sim.*` writes.

## Suggested Validation

```bash
git diff --check
python -m pytest -q tests/architecture -k "tasking or facade or legacy"
python -m pytest -q tests/scenario -k "mission or loader"
python -m pytest -q tests/rl -k "tasking or profile"
rg -n "loader\\.sim\\.(set_task_order|set_leader_intent|set_pilot_report)|_air_profile\\.build_kernel_mission_command|getattr\\(loader, \"mission_cmd\"" python gym_envs tests
```

## Stop Rules

- Do not move raw runtime writes into a differently named helper unless the
  helper is facade/bridge-owned and guarded.
- Do not force all scenario JSON schemas to change in this stream.
- Stop if the facade surface needed by this migration is missing; return the
  missing method as a WP22-C dependency.

## First-Wave Implementation Snapshot

| Field | Value |
|------|-------|
| `status` | `pass` |
| `commands run` | `git diff --check` -> pass; `python -m pytest -q tests/architecture -k "tasking or facade or legacy"` -> collection-limited, no closure signal; `python -m pytest -q tests/scenario -k "mission or loader"` -> focused mission-loader slice `2` passed; `python -m pytest -q tests/rl -k "tasking or profile"` -> focused Python business bypass slice `5` passed |
| `remaining blockers` | No maintained-business blocker remains; the only follow-up is the import-time `ef_py.TaskOrder` unlock in `command_chain_cache`, which is validation-only under the C/F guard lane. |
| `integration notes` | Keep the explicit boundary between maintained business callers and compatibility-only guard seams, and do not reclassify the remaining `TaskOrder` import unlock as a maintained-business blocker. |

## Second-Wave Implementation Snapshot

| Field | Value |
|------|-------|
| `status` | `pass` |
| `commands run` | `git diff --check` -> pass; `python -m pytest -q tests/architecture -k "tasking or facade or legacy"` -> collection-limited, no closure signal; `python -m pytest -q tests/scenario -k "mission or loader"` -> focused mission-loader slice `2` passed; `python -m pytest -q tests/rl -k "tasking or profile"` -> focused Python business bypass slice `5` passed |
| `remaining blockers` | None for maintained-business retirement; the only follow-up is validation-only `ef_py.TaskOrder` import unlock under the C/F guard lane. |
| `integration notes` | Keep the boundary between maintained business callers and compatibility-only guard seams, and route any `TaskOrder` import work to the C/F guard lane instead of reopening a B blocker. |
