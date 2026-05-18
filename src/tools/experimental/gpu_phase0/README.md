<!-- Machine-translated draft generated on 2026-05-18 from src/tools/experimental/gpu_phase0/README.md. Review before treating this file as authoritative. -->

# `src/tools/experimental/gpu_phase0` Boundaries

`gpu_phase0` holds early GPU phase-0 probes used to verify the feasibility of GPU helpers such as candidate lists, vision, communication, flight shaping, etc.

## Allowed

- Standalone probe executables.
- Temporary validation related to GPU helper parity or performance.
- Experimental code that makes read-only or controlled calls to the runtime packet API.

## Prohibited

- Default runtime backend.
- Being depended upon by Python bindings, facade, or core runtime.
- Altering the CPU truth path without freezing.

## Migration Notes

Maintainable GPU helpers should be migrated to the `src/gpu` main directory; expired probes should be archived or deleted, rather than continuing to extend the phase-0 directory.
