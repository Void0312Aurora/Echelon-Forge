# `src/gpu` Boundary

`gpu/` holds GPU helpers, batch packet runtime, and explicit experimental probes. Currently the default truth path remains the CPU `SimulationKernel::step()`; GPU code must not silently alter the canonical world-step semantics.

## Allowed

- Helper runtime for observation, visual, interaction broadphase, flight shaping, etc.
- CUDA kernels and CPU fallback wrappers.
- Packet extraction, computation, and backfill helpers interfacing with the `WorldBatchRuntime` boundary.
- Explicitly labeled experimental probes.

## Forbidden

- Unfrozen replacements of the exact world-step mainline.
- Owning a mission/episode state machine.
- Python binding implementations.
- Modifying CPU truth state semantics without passing plan freeze and parity verification.

## Subdirectory Conventions

- `experimental/`: Probes and verification code that have not entered the maintenance mainline.

## Migration Notes

If later renamed to `accelerators/gpu`, the migration plan should be frozen first and include/CMake compatibility maintained. GPU helpers may accelerate runtime packets, but they do not own simulation truth.
