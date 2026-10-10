# Timestep fallback and validation contract

Language:
- English canonical contract.
- Chinese companion: `timestep_fallback_contract.zh.md`.
Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/architecture/standards/timestep_fallback_contract.md`
Owner: `architecture/runtime-contracts`
Last verified: `2026-10-10`

## Scope

This contract describes how maintained simulation and mission entry points respond when a per-system timestep is zero, negative, non-finite, or otherwise unsupported. A fallback is a compatibility path for direct Flecs worlds, initialization, and paused stages. It does not change the ordinary positive timestep supplied by `SimulationKernel::step()` or `WorldBatch`.

The contract is intentionally per consumer. A fallback is not evidence that the engine's fixed clock has multiple active cadences during a normal step, and no global replacement is implied.

## Policy inventory

| Surface | Invalid or unsupported input | Maintained response | Reachability / owner |
| --- | --- | --- | --- |
| `SimulationKernel::set_time_step` | non-finite or `<= 0` | reject with `std::invalid_argument`; positive finite values are retained | Public kernel configuration; `src/core/engine/simulation_kernel.cpp` |
| Kernel default | omitted setup value | `SimulationKernel::kDefaultTimeStepS` (`1/60 s`) | Kernel construction/reset; `src/core/engine/simulation_kernel.h` |
| WorldBatch setup | DTO `0` | map the legacy “absent” sentinel to kernel default (`1/60 s`) | `src/core/engine/world_batch_setup_helper.h`; negative/non-finite DTO values are rejected |
| Shared physics integrator | zero, negative, or non-finite | `physics_runtime::kIntegratorFallbackDtS` (`0.05 s`) through `resolve_integrator_dt` | Leapfrog, rotational, ground contact, and air state/actuator/propulsion/control systems; direct Flecs invocation or paused stage |
| Aircraft and naval entity ticks | zero, negative, or non-finite | `physics_runtime::kEntityFallbackDtS` (`1/60 s`) through `resolve_entity_dt` | Aircraft damage, naval damage, ship motion, and submarine motion; direct system invocation |
| Mission off-runway grace conversion | non-finite or `<= 1e-6 s` | `mission_runtime::kTerminationFallbackDtS` (`0.05 s`) through `resolve_termination_dt` | Converts a configured grace duration in seconds to step count; it does not replace the kernel clock |

The shared physics fallback is also used by `actuator_first_order_step` and `first_order_step`. Their positive finite behavior is unchanged; invalid input now follows the same finite-positive predicate as the registered systems.

## Reachability and boundaries

- A normal `SimulationKernel::step()` supplies its validated positive fixed step. The fallback paths are reachable from direct Flecs tests, initialization/paused execution, and compatibility callers that invoke a registered system with an invalid iterator delta.
- Mission `time_step_s` is an input to the termination calculation. The fallback protects the seconds-to-steps conversion; the caller still owns the episode clock.
- WorldBatch's zero sentinel is a transport rule, not a permission for `SimulationKernel::set_time_step(0)`.
- This standard does not authorize changing system-specific model constants, action cadence, sensor cadence, or weapon guidance cadence. Such changes require a separate contract and positive-step regression evidence.

## Required tests

`src/tests/test_timestep_contract.cpp` locks:

- finite-positive preservation and zero/negative/non-finite rejection for the shared physics policy;
- air actuator and propulsion first-order fallback behavior;
- the `1/60 s` entity fallback used by aircraft damage and naval motion/damage;
- mission off-runway grace conversion for zero, negative, `NaN`, and infinite inputs, plus a positive-step control case.

Existing kernel, ground-contact, and WorldBatch tests remain authoritative for kernel rejection, shared contact/integrator behavior, and DTO zero mapping.
