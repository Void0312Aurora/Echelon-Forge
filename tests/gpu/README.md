# GPU Tests README

`tests/gpu/` holds GPU runtime binding and CUDA integration regression tests.

## Scope

- GPU runtime bindings (`ef_py` capability probing, DLPack tensor export, device properties)
- CUDA import order and runtime environment setup
- Aligned with `src/gpu/` and Python GPU bindings

## Distinction from architecture tests

- `tests/gpu/`: runtime behavior tests (import, binding, capability, DLPack round-trip)
- `tests/architecture/runtime_profiles/test_runtime_profile_contracts.py`: architecture contract guards (GPU truth boundary, parity budget assertions)

## Constraints

- GPU tests are gated behind `EF_ENABLE_CUDA_EXPERIMENTS` by default, consistent with the CPU-truth-first policy defined in `src/gpu/README.md`.
- When CUDA is unavailable, tests should skip gracefully (`pytest.skip` or equivalent) rather than fail.
- Do not add pure diagnostic/exploratory scripts here — they belong in `tools/diagnostics/`.
