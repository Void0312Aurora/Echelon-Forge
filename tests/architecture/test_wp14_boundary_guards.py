from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]

SIMULATION_KERNEL_HEADER = REPO_ROOT / "src" / "core" / "engine" / "simulation_kernel.h"
WORLD_BATCH_HEADER = REPO_ROOT / "src" / "core" / "engine" / "world_batch_runtime.h"
WORLD_BATCH_SOURCE = REPO_ROOT / "src" / "core" / "engine" / "world_batch_runtime.cpp"
WORLD_BATCH_CONTRACTS = REPO_ROOT / "src" / "runtime" / "contracts" / "world_batch_contracts.h"
RUNTIME_FACADE_HEADER = REPO_ROOT / "src" / "runtime" / "facade" / "runtime_facade.h"
RUNTIME_FACADE_SOURCE = REPO_ROOT / "src" / "runtime" / "facade" / "runtime_facade.cpp"
RUNTIME_FACADE_TYPES = REPO_ROOT / "src" / "runtime" / "facade" / "runtime_facade_types.h"
BINDINGS_CORE = REPO_ROOT / "src" / "interfaces" / "python" / "bindings_core.cpp"
BINDINGS_RUNTIME = REPO_ROOT / "src" / "interfaces" / "python" / "bindings_runtime.cpp"
SCENARIO_WORLD_SETUP_COMPAT = REPO_ROOT / "python" / "scenario" / "runtime" / "world_setup_compat.py"
RL_WORLD_BATCH_ADAPTER = REPO_ROOT / "python" / "rl" / "runtime" / "world_batch" / "adapter.py"
EXAMPLES_CONFIG = REPO_ROOT / "examples" / "config"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_wp14_boundary_guard_no_public_spawn_platform_surface_exists() -> None:
    for path in (
        SIMULATION_KERNEL_HEADER,
        WORLD_BATCH_HEADER,
        RUNTIME_FACADE_HEADER,
        BINDINGS_CORE,
        BINDINGS_RUNTIME,
        SCENARIO_WORLD_SETUP_COMPAT,
        RL_WORLD_BATCH_ADAPTER,
    ):
        text = _text(path)
        assert "spawn_platform" not in text, (
            "WP14 first slice must not expose a public spawn_platform path; "
            f"found forbidden token in {path.relative_to(REPO_ROOT).as_posix()}"
        )


def test_wp14_boundary_guard_runtime_capabilities_remains_backend_fidelity_only() -> None:
    header = _text(RUNTIME_FACADE_TYPES)
    struct_start = header.index("struct RuntimeCapabilities")
    struct_end = header.index("};", struct_start)
    runtime_capabilities_block = header[struct_start:struct_end]

    for required in (
        "supports_batch_runtime",
        "supports_compiled_episode_controller",
        "supports_gpu_visual",
        "supports_exact_gpu_backend",
        "multi_fidelity_rejection_reason",
    ):
        assert required in runtime_capabilities_block

    for forbidden in (
        "Capability",
        "CapabilityBundle",
        "ResolvedPlatformSpawnPlan",
        "TypedPlatformSpawnRequest",
        "typed_platform_spawn_requests",
        "source_type_name",
        "capability_bundle",
        "resolved_spawn_plan",
        "compatibility_path_preserved",
        "platform capability",
    ):
        assert forbidden not in runtime_capabilities_block, (
            "RuntimeCapabilities must stay reserved for backend/fidelity query fields; "
            f"found platform token {forbidden!r} inside RuntimeCapabilities"
        )

    binding_source = _text(BINDINGS_RUNTIME)
    runtime_caps_binding_start = binding_source.index('nb::class_<RuntimeCapabilities>(m, "RuntimeCapabilities")')
    runtime_batch_config_start = binding_source.index('nb::class_<RuntimeBatchConfig>(m, "RuntimeBatchConfig")')
    runtime_capabilities_binding_block = binding_source[
        runtime_caps_binding_start:runtime_batch_config_start
    ]

    for forbidden in (
        "capability_bundle",
        "resolved_spawn_plan",
        "typed_platform_spawn_requests",
        "source_type_name",
    ):
        assert forbidden not in runtime_capabilities_binding_block, (
            "RuntimeCapabilities Python binding must not grow platform capability fields; "
            f"found {forbidden!r} in RuntimeCapabilities binding block"
        )


def test_wp14_boundary_guard_legacy_type_name_spawn_surfaces_remain_present() -> None:
    kernel_header = _text(SIMULATION_KERNEL_HEADER)
    world_batch_contracts = _text(WORLD_BATCH_CONTRACTS)
    bindings_core = _text(BINDINGS_CORE)
    facade_types = _text(RUNTIME_FACADE_TYPES)

    assert "flecs::entity spawn_unit(Side side, const std::string& unit_name," in kernel_header
    assert "std::string type_name;" in world_batch_contracts
    assert 'nb::arg("side"), nb::arg("type_name")' in bindings_core
    assert "std::vector<WorldSpawnRequest> spawn_requests;" in facade_types


def test_wp14_boundary_guard_examples_and_scenario_python_schema_stay_on_legacy_spawn_requests() -> None:
    scenario_world_setup = _text(SCENARIO_WORLD_SETUP_COMPAT)
    adapter = _text(RL_WORLD_BATCH_ADAPTER)

    assert "typed_platform_spawn_requests" not in scenario_world_setup, (
        "Scenario Python compatibility layer must not migrate to typed_platform_spawn_requests "
        "in the first WP14 slice"
    )
    assert "TypedPlatformSpawnRequest" not in scenario_world_setup
    assert "CapabilityBundle" not in scenario_world_setup
    assert "ResolvedPlatformSpawnPlan" not in scenario_world_setup

    assert "typed_platform_spawn_requests" not in adapter, (
        "RL world-batch adapter must not migrate to typed platform spawn schema "
        "in the first WP14 slice"
    )
    assert "spawn_platform" not in adapter

    for path in EXAMPLES_CONFIG.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".json", ".yaml", ".yml", ".md"}:
            continue
        text = _text(path)
        assert "typed_platform_spawn_requests" not in text, (
            "examples/config must stay on the legacy scenario schema in the first WP14 slice; "
            f"found typed platform token in {path.relative_to(REPO_ROOT).as_posix()}"
        )
        assert "spawn_platform" not in text, (
            "examples/config must not introduce spawn_platform schema in the first WP14 slice; "
            f"found forbidden token in {path.relative_to(REPO_ROOT).as_posix()}"
        )


def test_wp14_boundary_guard_typed_platform_spawn_requests_are_additive_not_auto_materialized() -> None:
    facade_header = _text(RUNTIME_FACADE_HEADER)
    facade_source = _text(RUNTIME_FACADE_SOURCE)
    world_batch_header = _text(WORLD_BATCH_HEADER)
    world_batch_source = _text(WORLD_BATCH_SOURCE)

    assert "std::vector<uint64_t> apply_world_setup_batch(" in facade_header
    assert "const std::vector<WorldSpawnRequest>& requests," in facade_header
    assert "typed_platform_spawn_requests" not in facade_header, (
        "RuntimeFacade public apply_world_setup_batch surface must remain on WorldSpawnRequest "
        "for the first WP14 slice"
    )

    apply_world_setup_block = facade_source[
        facade_source.index("BatchWorldSetupResult RuntimeFacade::apply_world_setup("):
        facade_source.index("void RuntimeFacade::set_pilot_actions_batch(")
    ]
    assert "request.spawn_requests" in apply_world_setup_block
    assert "typed_platform_spawn_requests" not in apply_world_setup_block, (
        "RuntimeFacade::apply_world_setup must not automatically materialize "
        "typed_platform_spawn_requests without an explicit gate"
    )
    assert "ResolvedPlatformSpawnPlan" not in apply_world_setup_block
    assert "CapabilityBundle" not in apply_world_setup_block

    assert "spawn_units_batch(const std::vector<WorldSpawnRequest>& requests)" in world_batch_source
    assert "TypedPlatformSpawnRequest" not in world_batch_header, (
        "WorldBatchRuntime public mainline API must not materialize typed platform requests "
        "in the first WP14 slice"
    )
    assert "typed_platform_spawn_requests" not in world_batch_source, (
        "WorldBatchRuntime implementation must not auto-materialize typed platform requests "
        "in the first WP14 slice"
    )


def test_wp14_boundary_guard_additive_dto_validation_stays_fail_closed_without_runtime_gate() -> None:
    world_batch_contracts = _text(WORLD_BATCH_CONTRACTS)

    for token in (
        "validate_typed_platform_spawn_request",
        "typed_platform_spawn_requires_resolved_spawn_plan",
        "typed_platform_spawn_requires_type_name_compatibility_path",
        "typed_platform_spawn_resolved_plan_invalid",
    ):
        assert token in world_batch_contracts

    validate_block = world_batch_contracts[
        world_batch_contracts.index("validate_typed_platform_spawn_request("):
        world_batch_contracts.index("struct WorldPilotActionAssignment")
    ]
    for forbidden in (
        "spawn_unit(",
        "spawn_units_batch(",
        "apply_world_setup_batch(",
        "SimulationKernel",
        "WorldBatchRuntime",
        "RuntimeFacade",
    ):
        assert forbidden not in validate_block, (
            "Typed platform spawn request validation must stay declarative/fail-closed "
            f"and not materialize runtime behavior; found {forbidden!r}"
        )
