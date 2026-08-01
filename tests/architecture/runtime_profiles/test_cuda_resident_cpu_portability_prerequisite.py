from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_cr2_cpu_prerequisite_uses_portable_bit_scan() -> None:
    source = _read("src/core/engine/world_batch_runtime.cpp")

    assert "#include <bit>" in source
    assert "std::countr_zero(mask)" in source
    assert "__builtin_ctz" not in source


def test_cr2_cpu_prerequisite_keeps_environment_model_global() -> None:
    contract = _read("src/core/interfaces/control_model.h")
    implementation = _read("src/models/domains/air/default_control_model.cpp")

    include_position = contract.index('#include "core/interfaces/environment_model.h"')
    class_position = contract.index("class IControlModel")
    assert include_position < class_position
    assert "IControlModel::IEnvironmentModel" not in contract
    assert "IControlModel::IEnvironmentModel" not in implementation
    assert "IEnvironmentModel::SurfaceType" in implementation


def test_cr2_cpu_prerequisite_enables_legacy_pi_only_for_msvc_core() -> None:
    cmake = _read("CMakeLists.txt")
    marker = "target_compile_definitions(ef_core PRIVATE _USE_MATH_DEFINES)"

    assert "if (MSVC)" in cmake
    assert marker in cmake
    assert cmake.index("if (MSVC)") < cmake.index(marker)
