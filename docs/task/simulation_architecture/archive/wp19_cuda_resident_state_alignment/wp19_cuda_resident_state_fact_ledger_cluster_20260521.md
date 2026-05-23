# WP19-A CUDA / Resident-State Fact Ledger

Status: `2026-05-21` verified / authoritative facts ledger.

Language:

- English canonical: `wp19_cuda_resident_state_fact_ledger_cluster_20260521.md`
- Chinese companion:
  [wp19_cuda_resident_state_fact_ledger_cluster_20260521.zh.md](wp19_cuda_resident_state_fact_ledger_cluster_20260521.zh.md)

Inputs:

- [WP19 main plan](cuda_resident_state_alignment_wp19_20260521.md)
- [WP18 acceptance review](../../review/wp18_runtime_ownership_cxx_hot_path_consolidation_acceptance_review_20260521.md)
- [Architecture and performance follow-up](../../../plan/architecture/architecture_and_performance_research_followup.md)
- [Simulation system architecture design](../../../plan/architecture/simulation_system_architecture_design.md)
- [WP6 resident-state boundary rules](../wp6_backend_profile_policy/wp6_resident_state_boundary_rules_20260519.md)
- [WP18 ownership fact ledger](../wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_ownership_fact_ledger_hot_path_map_cluster_20260521.md)

## Purpose

Freeze the current CUDA / resident-state facts before any contract or runtime
change lands. This ledger is source-backed only: it records what the current
code and tests already say, and keeps WP19-E in preflight until a safe slice is
proven.

## Evidence Window

- `src/runtime/contracts/backend_profile_contracts.h:13-20, 24-46, 98-130,
  186-205, 256-339, 391-723`
- `src/runtime/facade/runtime_facade_types.h:17-41`
- `src/runtime/facade/runtime_facade.cpp:1044-1065`
- `src/core/engine/world_batch_runtime.cpp:115-180, 703-900`
- `src/gpu/gpu_visual_runtime.{h,cpp}`
- `src/gpu/gpu_execution_observation_runtime.{h,cpp}`
- `src/gpu/gpu_flight_shaping_runtime.{h,cpp}`
- `src/gpu/gpu_interaction_broadphase_runtime.{h,cpp}`
- `src/gpu/*_cuda.cu`
- `src/tools/experimental/gpu_phase0/README.md`
- `src/tools/experimental/gpu_phase0/*.cpp`
- `tests/test_gpu_runtime_bindings.py:20-260, 543-590`
- `tests/runtime/facade/test_runtime_facade.py:524-554`
- `tests/architecture/test_runtime_facade_layering.py:436-494`
- `tests/world_batch/test_world_batch_runtime.py:1131-1320`
- `tests/world_batch/test_world_batch_vec_env.py:681-728`

## Classification Legend

- `maintained owner`: current maintained truth or capability projection owner.
- `host-owned helper`: host-side helper or orchestration path that remains the
  semantic owner while using accelerator-backed helpers.
- `diagnostics-export-only`: report-only, probe-only, or DLPack/export-only
  surface that must not authorise maintained support.
- `candidate`: accelerator path exercised behind an explicit opt-in or
  fallback boundary, but not a maintained truth path.
- `blocked-unknown`: not yet justified for maintained promotion from the
  evidence gathered here.

## Surface Ledger

| Surface | Classification | Current fact | Evidence |
|---|---|---|---|
| `src/runtime/contracts/backend_profile_contracts.h` + `src/runtime/facade/runtime_facade.{h,cpp}` | maintained owner | The maintained capability projection is fail-closed. `cpu_exact.reference` is the sole maintained profile, `gpu_helpers.diagnostics_only` is report-only, and `supports_resident_state`, `supports_exact_gpu_backend`, `supports_shadow_compare`, and `supports_device_observation_view` stay `false`. | `src/runtime/contracts/backend_profile_contracts.h:13-20, 24-46, 98-130, 186-205, 256-339, 391-723`; `src/runtime/facade/runtime_facade.cpp:1044-1065`; `src/runtime/facade/runtime_facade_types.h:17-41` |
| `src/gpu/gpu_visual_runtime.{h,cpp}` reference helpers (`render_visual_reference_cpu*`, `estimate_visual_tensor_footprint`) | host-owned helper | These functions build host-side reference outputs or size estimates. They support parity checks and host orchestration, but they do not own maintained world truth. | `src/gpu/gpu_visual_runtime.cpp:47-179` |
| `src/gpu/gpu_visual_runtime.{h,cpp}` experiment / device-resident helpers (`render_visual_experiment*`, `render_visual_experiment_batch_device_resident`) | candidate | The GPU path is explicitly optional behind `EF_ENABLE_CUDA_EXPERIMENTS`, falls back to CPU when needed, and is exercised as an accelerator/parity candidate rather than a maintained semantic owner. | `src/gpu/gpu_visual_runtime.cpp:12-43, 185-288`; `src/gpu/gpu_visual_runtime_cuda.cu` |
| `src/gpu/gpu_visual_runtime.{h,cpp}` diagnostics hooks (`last_visual_experiment_stats`, `last_visual_output_device_ptr`, `last_visual_output_float_count`, `probe_device`) | diagnostics-export-only | These hooks expose availability, timing, and device pointers for reports or DLPack export. They never flip support flags. | `src/gpu/gpu_visual_runtime.cpp:115-133` |
| `src/gpu/gpu_execution_observation_runtime.{h,cpp}` reference helpers (`compute_execution_observation_reference_cpu_batch`, `execution_observation_output_float_count`) | host-owned helper | The host reference path owns the observable output shape and parity baseline. | `src/gpu/gpu_execution_observation_runtime.cpp:139-291` |
| `src/gpu/gpu_execution_observation_runtime.{h,cpp}` experiment / device-resident helpers (`compute_execution_observation_experiment_batch*`) | candidate | The CUDA path is optional, compare-by-reference, and can fall back to CPU. It does not claim maintained device-observation support. | `src/gpu/gpu_execution_observation_runtime.cpp:12-31, 270-307`; `src/gpu/gpu_execution_observation_runtime_cuda.cu` |
| `src/gpu/gpu_execution_observation_runtime.{h,cpp}` diagnostics hooks (`last_execution_observation_stats`, `last_execution_observation_output_device_ptr`, `last_execution_observation_output_float_count`) | diagnostics-export-only | These hooks are report-only and only surface device state for diagnostics or export. | `src/gpu/gpu_execution_observation_runtime.cpp:167-185` |
| `src/gpu/gpu_flight_shaping_runtime.{h,cpp}` reference helpers (`compute_flight_shaping_reference_cpu_batch`) | host-owned helper | The CPU reference helper remains the host baseline for flight-shaping terms. | `src/gpu/gpu_flight_shaping_runtime.cpp:87-110` |
| `src/gpu/gpu_flight_shaping_runtime.{h,cpp}` experiment / device-resident helpers (`compute_flight_shaping_experiment_batch*`) | candidate | The GPU path is optional and falls back to the CPU reference path when the experiment path is unavailable or empty. | `src/gpu/gpu_flight_shaping_runtime.cpp:8-19, 101-123`; `src/gpu/gpu_flight_shaping_runtime_cuda.cu` |
| `src/gpu/gpu_flight_shaping_runtime.{h,cpp}` diagnostics hooks (`last_flight_shaping_stats`, `last_flight_shaping_output_device_ptr`, `last_flight_shaping_output_float_count`) | diagnostics-export-only | These hooks report timing and device pointer state for validation only. | `src/gpu/gpu_flight_shaping_runtime.cpp:63-81` |
| `src/gpu/gpu_interaction_broadphase_runtime.{h,cpp}` reference helpers (`build_interaction_broadphase_reference_cpu_batch`, `interaction_broadphase_word_count`) | host-owned helper | The host reference path owns bitset semantics and validation. | `src/gpu/gpu_interaction_broadphase_runtime.cpp:33-112` |
| `src/gpu/gpu_interaction_broadphase_runtime.{h,cpp}` experiment / device-resident helpers (`build_interaction_broadphase_experiment_batch*`) | candidate | The GPU path is explicitly optional and falls back to the host reference when needed. | `src/gpu/gpu_interaction_broadphase_runtime.cpp:7-25, 118-140`; `src/gpu/gpu_interaction_broadphase_runtime_cuda.cu` |
| `src/gpu/gpu_interaction_broadphase_runtime.{h,cpp}` diagnostics hooks (`last_interaction_broadphase_stats`, `last_interaction_broadphase_output_device_ptr`, `last_interaction_broadphase_output_word_count`) | diagnostics-export-only | These hooks expose performance and output placement facts only. | `src/gpu/gpu_interaction_broadphase_runtime.cpp:58-76` |
| `src/tools/experimental/gpu_phase0/*` | diagnostics-export-only | Phase-0 probes are standalone binaries for measurement and parity reporting. The README forbids them from becoming the default runtime backend or from being depended on by facade/core runtime. | `src/tools/experimental/gpu_phase0/README.md:3-21`; `src/tools/experimental/gpu_phase0/*.cpp` |
| `WorldBatchRuntime` GPU candidate-ID call sites (`get_sensor_candidate_ids_batch`, `get_visual_candidate_ids_batch`, `get_comm_candidate_ids_batch`) | host-owned helper | The runtime owns the final filtering and sorting. GPU broadphase only supplies candidate bitsets under an explicit `use_gpu` flag. | `src/core/engine/world_batch_runtime.cpp:703-900` |
| `src/gpu/*_cuda.cu` device kernels | blocked-unknown | Kernel internals are only reachable through guarded experimental wrappers. They are not yet a maintained surface, and there is no evidence here that would justify promotion. | `src/gpu/*_cuda.cu` |
| `tests/test_gpu_runtime_bindings.py`, `tests/runtime/facade/test_runtime_facade.py`, `tests/architecture/test_runtime_facade_layering.py` | diagnostics-export-only | These tests lock the capability flags to `false`, verify helper bindings exist, and prevent `RuntimeFacade` or core runtime from depending on GPU helper implementation details. | `tests/test_gpu_runtime_bindings.py:20-260, 543-590`; `tests/runtime/facade/test_runtime_facade.py:524-554`; `tests/architecture/test_runtime_facade_layering.py:436-494` |

## Capability Facts

- `RuntimeCapabilities` defaults all GPU / resident / shadow flags to `false`.
- `RuntimeFacade::capabilities()` keeps the same flags false and publishes only
  metadata strings for the current candidate profiles.
- `tests/test_gpu_runtime_bindings.py` proves that helper/probe availability
  does not imply maintained support.
- `tests/runtime/facade/test_runtime_facade.py` locks the facade result to
  `supports_resident_state == false`, `supports_exact_gpu_backend == false`,
  and `supports_shadow_compare == false`.
- `tests/architecture/test_runtime_facade_layering.py` forbids
  `RuntimeFacade` from including or calling GPU helper/probe code and forbids
  core runtime from projecting GPU / resident / shadow capability support.

## WorldBatchRuntime Facts

- `WorldBatchRuntime` uses `gpu::build_interaction_broadphase_experiment_batch(...)`
  and `..._device_resident(...)` in the sensor, visual, and comm candidate-ID
  paths.
- Host-side decode, filtering, and sort remain in `WorldBatchRuntime`; GPU
  output is just a candidate bitset.
- `tests/world_batch/test_world_batch_runtime.py` exercises the explicit
  `use_gpu=True` path and checks that the candidate helper results behave as
  expected.
- `tests/world_batch/test_world_batch_vec_env.py` keeps the compiled visual
  batch path matched to the legacy path, which keeps the helper surface in
  parity mode rather than support-promotion mode.

## WP19-E Recommendation

Status: `preflight-only`.

The evidence supports a guarded helper boundary, not a promoted resident-state
slice. If later WP19-B, WP19-C, and WP19-D produce a safe bounded helper slice,
the first implementation candidate should be a single host-owned
`WorldBatchRuntime` candidate-list path with explicit host post-filtering,
likely interaction broadphase first. For now, WP19-E should not change runtime
behavior.
