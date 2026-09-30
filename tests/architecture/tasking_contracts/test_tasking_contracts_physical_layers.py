from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACT_ROOT = REPO_ROOT / "python" / "tasking_contracts"


def _py_names(path: Path) -> set[str]:
    return {item.name for item in path.glob("*.py")}


def test_tasking_contracts_has_explicit_common_and_domain_packages() -> None:
    assert {item.name for item in CONTRACT_ROOT.iterdir() if item.is_dir()} >= {
        "air",
        "common",
        "joint",
        "naval",
    }
    assert (CONTRACT_ROOT / "common" / "__init__.py").is_file()
    assert (CONTRACT_ROOT / "air" / "__init__.py").is_file()
    assert (CONTRACT_ROOT / "naval" / "__init__.py").is_file()
    assert (CONTRACT_ROOT / "joint" / "__init__.py").is_file()


def test_tasking_contract_root_has_no_implementation_or_compatibility_shims() -> None:
    assert _py_names(CONTRACT_ROOT) == {"__init__.py"}


def test_domain_packages_have_role_specific_subdirectories() -> None:
    assert _py_names(CONTRACT_ROOT / "air") == {"__init__.py", "registry.py"}
    assert _py_names(CONTRACT_ROOT / "air" / "execution") >= {"__init__.py", "model.py"}
    assert _py_names(CONTRACT_ROOT / "air" / "engagement") == {"__init__.py", "model.py"}
    assert _py_names(CONTRACT_ROOT / "air" / "ew") == {"__init__.py", "model.py"}
    assert _py_names(CONTRACT_ROOT / "air" / "strategy") >= {
        "__init__.py",
        "assessment.py",
        "contracts.py",
        "planning.py",
        "weapons.py",
    }
    assert _py_names(CONTRACT_ROOT / "naval") == {"__init__.py", "execution.py"}
    assert _py_names(CONTRACT_ROOT / "joint") == {
        "__init__.py",
        "command_link.py",
        "coordination.py",
        "projection.py",
        "runtime.py",
    }


def test_canonical_packages_do_not_import_legacy_flat_implementation_paths() -> None:
    canonical_roots = (
        CONTRACT_ROOT / "common",
        CONTRACT_ROOT / "air",
        CONTRACT_ROOT / "naval",
        CONTRACT_ROOT / "joint",
    )
    for root in canonical_roots:
        for source in root.rglob("*.py"):
            text = source.read_text(encoding="utf-8")
            assert "from .air_scripted_" not in text, source
            assert "python.tasking_contracts.air_scripted_" not in text, source
