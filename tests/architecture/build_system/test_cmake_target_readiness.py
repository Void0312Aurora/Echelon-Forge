from __future__ import annotations

import re

from tests.architecture.helpers import REPO_ROOT


CMAKE = REPO_ROOT / "CMakeLists.txt"


def _cmake_source() -> str:
    return CMAKE.read_text(encoding="utf-8")


def _command_body(source: str, command: str, first_args: str) -> str:
    match = re.search(
        rf"{re.escape(command)}\s*\(\s*{re.escape(first_args)}(.*?)\n\)",
        source,
        re.DOTALL,
    )
    assert match is not None, f"missing CMake command: {command}({first_args}"
    return match.group(1)


def test_core_source_groups_are_named_for_future_targets() -> None:
    source = _cmake_source()
    required_groups = [
        "EF_CORE_ENGINE_SOURCES",
        "EF_CORE_GEOMETRY_SOURCES",
        "EF_CORE_MISSION_RUNTIME_SOURCES",
        "EF_CORE_MISSION_EPISODE_SOURCES",
        "EF_CORE_MISSION_EPISODE_DETAIL_SOURCES",
        "EF_CORE_MISSION_SOURCES",
        "EF_RUNTIME_FACADE_SOURCES",
        "EF_MODEL_DEFAULT_SOURCES",
        "EF_CONTENT_SOURCES",
        "EF_CORE_SOURCES",
        "EF_PYTHON_BINDING_SOURCES",
        "EF_GPU_MAINTAINED_HELPER_SOURCES",
        "EF_GPU_EXPERIMENT_SOURCES",
    ]
    missing = [name for name in required_groups if f"set({name}" not in source]
    assert not missing, f"missing future target source groups: {missing}"


def test_core_target_uses_source_group_instead_of_flat_file_list() -> None:
    source = _cmake_source()
    body = _command_body(source, "add_library", "ef_core STATIC")
    assert "${EF_CORE_SOURCES}" in body
    assert "src/" not in body, (
        "add_library(ef_core) should consume grouped source variables only"
    )


def test_python_module_uses_binding_source_group_instead_of_flat_file_list() -> None:
    source = _cmake_source()
    body = _command_body(source, "nanobind_add_module", "ef_py")
    assert "${EF_PYTHON_BINDING_SOURCES}" in body
    assert "src/" not in body, (
        "nanobind_add_module(ef_py) should consume grouped binding sources only"
    )


def test_core_mission_root_has_no_flat_runtime_sources() -> None:
    mission_root = REPO_ROOT / "src" / "core" / "mission"
    flat_sources = sorted(
        path.name for path in mission_root.iterdir() if path.suffix in {".cpp", ".h"}
    )
    assert not flat_sources, (
        f"mission sources should live under runtime/ or episode/: {flat_sources}"
    )


def test_core_mission_episode_detail_does_not_escape_controller_domain() -> None:
    allowed_roots = {
        REPO_ROOT / "src" / "core" / "mission" / "episode",
    }
    search_roots = [
        REPO_ROOT / "src",
        REPO_ROOT / "tests",
    ]
    forbidden_include = "core/mission/episode/" + "detail/"
    violations: list[tuple[str, int, str]] = []
    for root in search_roots:
        for path in root.rglob("*"):
            if path.suffix not in {".cpp", ".h", ".py"}:
                continue
            if any(path.is_relative_to(allowed_root) for allowed_root in allowed_roots):
                continue
            for lineno, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if forbidden_include in line:
                    violations.append((str(path.relative_to(REPO_ROOT)), lineno, line.strip()))

    assert not violations, (
        "mission episode detail includes escaped controller domain: "
        f"{violations}"
    )
