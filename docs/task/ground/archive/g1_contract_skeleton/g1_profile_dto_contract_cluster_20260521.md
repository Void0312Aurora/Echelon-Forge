# G1 Profile And DTO Contract Cluster

Status: `2026-05-21` G1-A preflight and G1-B Python-profile implementation
accepted.

Inputs:

- [G1 README](README.md)
- [G1 profile and DTO preflight](g1_profile_dto_preflight_20260521.md)
- [Ground standards overview](../../../standards/ground/README.md)
- [Ground minimal task structure](../../../standards/ground/minimal_task_structure.md)
- [Subagent Usage Policy](../../../standards/governance/subagent_usage_policy.md)

## Purpose

Add the first ground contract skeleton while preserving the existing
`common + specialization + profile bridge` pattern.

## Task Items

| ID | Item | Acceptance |
|----|------|------------|
| `G1-A1` | Profile resolver | `tasking_profile` accepts `army`, `ground`, and `land`, and normalizes to `ground`. |
| `G1-A2` | Ground profile shell | A `ground_profile` and adapter expose the same narrow interface expected by the tasking bridge. |
| `G1-A3` | Starter task defaults | `TASK_MOVE`, `TASK_OCCUPY`, and `TASK_SUPPORT` map to common-core fields without air/naval vocabulary leakage. |
| `G1-A4` | DTO landing decision | Decide whether G1 needs empty/minimal `components/tasking/ground` and `components/command/ground` headers or should remain Python-profile-only. |
| `G1-A5` | Focused tests | Tests prove profile resolution and starter defaults while existing air/naval tests keep passing. |

## Write Scope

Likely allowed after G0 closure:

- `python/rl/tasking/bridge.py`
- `python/rl/tasking/common_core_profile.py`
- `python/rl/tasking/ground_adapter.py`
- `python/rl/profile/ground_profile.py`
- focused `tests/leader` or `tests/runtime/mission` profile tests
- optional `src/components/tasking/ground/**` and `src/components/command/ground/**`

Do not edit:

- movement, physics, sensor, weapon, damage, or facade runtime behavior
- air/naval profile semantics except for compatibility-preserving resolver hooks
- broad scenario-loader behavior

## Suggested Validation

```bash
git diff --check
python -m pytest -q tests/leader/test_tasking_profile_contracts.py
python -m pytest -q tests/leader/test_tasking_profile_contracts.py
python -m pytest -q tests/runtime/mission/test_naval_mission_command_mapping.py
```

Add a focused ground profile test once implementation starts.

## Handoff

Return:

- touched files
- profile aliases accepted
- task default mapping table
- tests run
- residuals for G2/G3

Preflight result:

- [G1 profile and DTO preflight](g1_profile_dto_preflight_20260521.md) recommends a narrow Python-profile-only implementation release and records the DTO decision as `not needed in G1`.

Implementation result:

- `G1-B` edited only Python resolver/profile/adapter files and focused
  `tests/leader` coverage.
- `army`, `ground`, `land`, and `ServiceProfile.Army` now normalize to
  `ground`.
- DTO-shell decision remains `not needed in G1`.
- C++ DTO shells, bindings, runtime behavior, command delivery, scenario
  loading, and G2/G3/G4 scope remain held.
