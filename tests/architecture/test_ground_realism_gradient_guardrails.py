from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
GROUND_SCENARIOS = REPO_ROOT / "scenarios" / "ground"


def _ground_scenario_docs() -> list[tuple[Path, dict]]:
    docs: list[tuple[Path, dict]] = []
    for path in sorted(GROUND_SCENARIOS.glob("*.json")):
        with path.open("r", encoding="utf-8") as handle:
            docs.append((path, json.load(handle)))
    return docs


def test_ground_scenarios_keep_current_spawn_shell_explicitly_compatibility_only() -> None:
    docs = _ground_scenario_docs()
    assert docs, "ground scenarios should exist before this guard can pass"

    for path, scenario in docs:
        boundary = scenario.get("mvp_boundary", {})
        assert boundary.get("compatibility_spawn_type") == "Aircraft", path.relative_to(REPO_ROOT).as_posix()
        assert scenario.get("tasking_profile") == "ground", path.relative_to(REPO_ROOT).as_posix()
        for entity in scenario.get("entities", []):
            assert entity.get("type") == "Aircraft", path.relative_to(REPO_ROOT).as_posix()


def test_ground_g0_g1_scenarios_defer_native_runtime_and_g2_plus_realism() -> None:
    required_deferred_tokens = (
        "runtime-loadable ground unit schema",
        "ground movement dynamics",
        "terrain",
        "ground sensing",
        "damage",
    )

    for path, scenario in _ground_scenario_docs():
        boundary = scenario.get("mvp_boundary", {})
        gradient = boundary.get("realism_gradient", {})
        grade = str(gradient.get("grade", "G0")).strip().upper() or "G0"
        assert grade in {"G0", "G1"}, path.relative_to(REPO_ROOT).as_posix()

        deferred_claims = [
            str(item)
            for item in (
                list(boundary.get("deferred_runtime_claims", []) or [])
                + list(gradient.get("deferred_claims", []) or [])
            )
        ]
        deferred_text = "\n".join(deferred_claims).lower()
        for token in required_deferred_tokens:
            assert token.lower() in deferred_text, (
                path.relative_to(REPO_ROOT).as_posix(),
                token,
                deferred_claims,
            )


def test_ground_runtime_paths_do_not_import_private_ground_profile_directly() -> None:
    runtime_roots = [
        REPO_ROOT / "python" / "rl" / "runtime",
        REPO_ROOT / "gym_envs" / "scenario_loader",
        REPO_ROOT / "python" / "scenario" / "runtime",
    ]
    forbidden = (
        "from python.rl.profile.ground_profile",
        "import python.rl.profile.ground_profile",
        "from python.rl.tasking import ground_adapter",
        "import python.rl.tasking.ground_adapter",
    )
    violations: list[tuple[str, str]] = []

    for root in runtime_roots:
        for path in sorted(root.rglob("*.py")):
            text = path.read_text(encoding="utf-8")
            for token in forbidden:
                if token in text:
                    violations.append((path.relative_to(REPO_ROOT).as_posix(), token))

    assert not violations, f"ground runtime must route through tasking bridge, found {violations}"
