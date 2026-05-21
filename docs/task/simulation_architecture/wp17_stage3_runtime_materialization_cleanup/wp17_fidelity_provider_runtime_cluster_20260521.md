# WP17-D Fidelity Provider Runtime

Status: `2026-05-21` implemented / focused validation passed for reference CPU
facade admission and fail-closed provider rejection.

Inputs:

- [WP17 main plan](stage3_runtime_materialization_cleanup_wp17_20260521.md)
- [WP13 backend fidelity expansion](../wp13_backend_fidelity_expansion/backend_fidelity_expansion_wp13_20260520.md)
- [WP6 backend profile policy](../wp6_backend_profile_policy/backend_profile_policy_wp6_20260519.md)

## Purpose

Move from query-only capability metadata to one runtime fidelity/provider slice.
The first slice must be conservative: CPU exact remains the maintained baseline,
unsupported accelerated/exact profiles reject explicitly, and one provider
family can be selected by runtime evidence.

## Scope

In scope:

- facade-level fidelity profile request/admission with explicit rejection;
- a minimal provider-family enum or equivalent runtime-owned discriminator;
- one stage-node/provider-family proof, preferably physics `P5 PhysicsStep`;
- profile, parity-budget, and fallback evidence visible through facade/bindings.

Out of scope:

- exact GPU promotion;
- resident-state promotion;
- learned model rollout;
- capability composition or spawn schema changes.

## Task Items

| ID | Item | Acceptance |
|----|------|------------|
| `D1` | Fidelity request surface | Request accepted/rejected through facade with `required_profile_class`, `profile_id`, and reason. |
| `D2` | Provider-family discriminator | One runtime-owned provider family can be selected without changing semantic output contracts. |
| `D3` | Conservative fallback | Reference CPU exact remains default; unsupported profiles reject rather than silently fallback unless fallback is explicit evidence. |
| `D4` | Binding/test proof | Python-facing tests can query capabilities and observe request result/rejection metadata. |

## Suggested Validation

```bash
git diff --check
python -m pytest -q tests/runtime/facade/test_runtime_facade.py -k "capabilities or fidelity"
python -m pytest -q tests/test_gpu_runtime_bindings.py -k "capabilities"
python -m pytest -q tests/architecture/test_wp13_*.py
```

## Handoff

Return touched capability/provider files, request/rejection behavior, exact
validation outcomes, and backend profiles that remain blocked.
