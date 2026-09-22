# P5-C Facade-Only Package Qualification

Document kind: `evidence`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/long_horizon_architecture_governance/evidence/p5c_facade_only_package_qualification_20260922.md`
Owner: `cross-domain architecture`
Last verified: `2026-09-22`

## Scope

This evidence qualifies the P5-C production Python package boundary for the
current Windows/MSVC, CPython 3.12, local single-process CPU-canonical
topology. It does not authorize P5-D caller cutover, production truth
publication, package rollback, multi-process failover, CUDA promotion, or P8
provider/topology expansion.

## Boundary Implemented

- `EF_PRODUCTION_FACADE_ONLY=ON` is the maintained wheel default.
- `ef_py` registers command contracts, maintained core DTOs/enums, episode
  contracts, CPU-canonical observation helpers, runtime DTOs, and
  `RuntimeFacade`.
- `SimulationKernel`, `WorldBatchRuntime`, raw engine binding slices, GPU
  probes/device views, and the diagnostics-only module are absent from the
  production Python surface.
- `EF_BUILD_DIAGNOSTICS_BINDINGS` is explicit opt-in and names the separate
  `ef_py_diagnostics` target/module.
- The P4-C candidate adapter remains excluded from the wheel.
- The production extension compiles only maintained mission/geometry and
  visual/execution observation helpers. The private `ef_facade_backend.dll`
  owns the raw engine/world implementation behind `RuntimeFacade`; it exports
  only `RuntimeFacade` methods and is not a public binding target.

## Verification

### Native production facade build

Configured and built with:

```powershell
cmake -S . -B build-long-horizon-p5c-shared -G "Visual Studio 17 2022" -A x64 `
  -DEF_PRODUCTION_FACADE_ONLY=ON `
  -DEF_BUILD_DIAGNOSTICS_BINDINGS=OFF `
  -DBUILD_TESTING=OFF `
  -DEF_FETCHCONTENT_REVALIDATE_PINS=OFF
cmake --build build-long-horizon-p5c-shared --config Debug --target ef_py -- /m:2
```

Result: `ef_py.cp312-win_amd64.pyd` and the private
`ef_facade_backend.dll` built successfully. `dumpbin /exports` on the DLL
showed only `RuntimeFacade` methods; no `SimulationKernel`,
`WorldBatchRuntime`, or GPU-helper exports were present. The pyd import table
contained `ef_facade_backend.dll` and no `ef_core` or `ef_gpu_experiments`.
Existing MSVC STL deprecation and source-encoding warnings remained non-fatal.

The explicit diagnostics configuration was also built with
`-DEF_BUILD_DIAGNOSTICS_BINDINGS=ON`; `ef_py_diagnostics.cp312-win_amd64.pyd`
imported successfully and exposed `SimulationKernel`, `WorldBatchRuntime`,
and `probe_gpu_device` as the intended opt-in diagnostics surface.

### Isolated wheel

Built with `python -m pip wheel . --no-deps` using the facade-only CMake
defaults. The resulting Windows CPython 3.12 wheel is
`artifacts/p5c-wheel-final3/cmo-0.2.0-cp312-cp312-win_amd64.whl` (SHA-256
`4BC32143E2CC9D2EE880A30A4B534F96D8DB6C3186252C5DA98FAF8928D81D67`). It
contains one `ef_py` extension, the private `ef_facade_backend.dll`, and no
`ef_py_diagnostics` or candidate adapter.

In a fresh virtual environment, installed with `pip install --no-deps` and
then installed the smoke dependencies `numpy` and `gymnasium`. The following
checks passed:

- required maintained names included `RuntimeFacade`, `RuntimeBatchConfig`,
  `Side`, `AgentObservation`, `InstrumentState`, `SafetyRuntimeInputs`, and
  `compute_execution_observation_batch_numpy`;
- forbidden names did not include `SimulationKernel`, `WorldBatchRuntime`,
  `probe_gpu_device`, `GpuTensorView`, or `ef_py_diagnostics`;
- `RuntimeFacade(RuntimeBatchConfig()).world_count()` returned `0`;
- `WorldBatchVecEnv` loaded `scenarios/test/test_free_fall.json`, completed
  `reset()`, completed one `step()`, and returned the four-element vector-env
  result;
- the same isolated environment ran `WorldBatchVecEnv(include_visual=True,
  visual_downsample=2)`, with visual tensors shaped `(1, 24, 48, 10)` on both
  reset and step.
- `dumpbin /dependents`-equivalent wheel import resolution loaded the bundled
  `ef_facade_backend.dll`; the fresh venv imported the extension from its own
  `site-packages` directory, not from the source build tree.

### Automated gates

- `tests/architecture/build_system/test_production_facade_package_boundary.py`:
  **4 passed**.
- Existing facade/structural binding gates with
  `CMO_BUILD_DIR=build-long-horizon-p5c-shared`: **20 passed**; visual VecEnv
  reset/step gates: **2 passed**.
- Diagnostics opt-in build/import: `ef_py_diagnostics` built successfully and
  exposed `SimulationKernel`, `WorldBatchRuntime`, and `probe_gpu_device`.
- `ruff check` passed for the new Python architecture test. C++ files are not
  Ruff inputs; native compilation above is the syntax/link verification.

## Residuals

The package still contains maintained helper implementation needed by the
facade observation/episode path. The raw engine/world implementation remains
private to `ef_facade_backend.dll` under the P1-A private-backend-behind-facade
interpretation and is not exported to Python. P5-D still owns production caller
activation, cutover/backout, and removal or retirement of compatibility
authority. P8 still owns cross-platform/package matrix, provider/topology
expansion, and final long-horizon acceptance.
