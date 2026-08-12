"""The damage-model router must resolve producers lazily.

Importing ``tools/maintenance/damage_model.py`` used to import all ~47 producer
modules (~14s per interpreter), a cost paid by every ``--help``, every
sub-command and every pytest session regardless of which domain it needed.
These tests pin the laziness itself plus the two properties the eager imports
used to give away for free: every registered command names a module that really
exists, and that module exposes a top-level ``main``.
"""

from __future__ import annotations

import ast
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

from tools.maintenance import damage_model


ROUTER_PATH = Path(damage_model.__file__).resolve()
REPO_ROOT = ROUTER_PATH.parents[2]
PRODUCER_PREFIX = "tools.maintenance."


def _producer_modules() -> list[str]:
    return sorted(
        {command_main.producer_module for _, command_main in damage_model.COMMANDS.values()}
    )


def _module_scope_imports(tree: ast.Module) -> list[ast.Import | ast.ImportFrom]:
    """Imports that run at module import, including those inside ``try`` blocks."""
    found: list[ast.Import | ast.ImportFrom] = []

    def walk(nodes: list[ast.stmt]) -> None:
        for node in nodes:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                found.append(node)
                continue
            walk([child for child in ast.iter_child_nodes(node) if isinstance(child, ast.stmt)])

    walk(tree.body)
    return found


def _imported_names(node: ast.Import | ast.ImportFrom) -> list[str]:
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if node.level:  # relative: cannot name an absolute producer path
        return []
    base = node.module or ""
    return [f"{base}.{alias.name}" if base else alias.name for alias in node.names]


def test_every_command_is_bound_through_the_lazy_producer_shim() -> None:
    unbound = sorted(
        command
        for command, (_, command_main) in damage_model.COMMANDS.items()
        if not getattr(command_main, "producer_module", "").startswith(PRODUCER_PREFIX)
    )
    assert not unbound, (
        "every sub-command must route through _producer() so the router stays "
        f"importable without its producers: {unbound}"
    )

    undescribed = sorted(
        command for command, (description, _) in damage_model.COMMANDS.items() if not description
    )
    assert not undescribed, f"commands without a --help description: {undescribed}"


def test_every_producer_module_exists_and_defines_main() -> None:
    """Deferred imports move typos from import time to dispatch time.

    ``find_spec`` plus an AST scan keeps the old crash-early coverage without
    executing (or paying for) a single producer.
    """
    missing: list[str] = []
    without_main: list[str] = []
    for module_path in _producer_modules():
        try:
            spec = importlib.util.find_spec(module_path)
        except ModuleNotFoundError:
            spec = None
        if spec is None or not spec.origin:
            missing.append(module_path)
            continue
        tree = ast.parse(Path(spec.origin).read_text(encoding="utf-8"))
        if not any(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "main"
            for node in tree.body
        ):
            without_main.append(module_path)

    assert not missing, f"registered commands name modules that do not exist: {missing}"
    assert not without_main, f"registered producers expose no top-level main(): {without_main}"


def test_router_source_imports_no_producer_at_module_scope() -> None:
    tree = ast.parse(ROUTER_PATH.read_text(encoding="utf-8"))
    eager = sorted(
        name
        for node in _module_scope_imports(tree)
        for name in _imported_names(node)
        if name.startswith(PRODUCER_PREFIX)
    )
    assert not eager, (
        "producer imports must stay inside the dispatch path; module-scope "
        f"imports found: {eager}"
    )


def test_dispatch_loads_only_the_invoked_producer(monkeypatch: pytest.MonkeyPatch) -> None:
    loaded: list[str] = []

    class _Producer:
        @staticmethod
        def main(argv: list[str] | None) -> object:
            return ("ran", tuple(argv or ()))

    def fake_import_module(name: str) -> object:
        loaded.append(name)
        return _Producer

    monkeypatch.setattr(damage_model, "import_module", fake_import_module)

    result = damage_model.main(["source-governance", "admission-audit", "--dry-run"])

    assert loaded == ["tools.maintenance.source_governance.admission_audit"]
    assert result == ("ran", ("--dry-run",))


@pytest.mark.parametrize("argv", [[], ["--help"], ["-h"], ["not-a-domain", "not-a-command"]])
def test_help_and_unknown_commands_load_no_producer(
    monkeypatch: pytest.MonkeyPatch, argv: list[str]
) -> None:
    def refuse(name: str) -> object:
        raise AssertionError(f"{argv} must not import {name}")

    monkeypatch.setattr(damage_model, "import_module", refuse)

    assert damage_model.main(argv) in (0, 2)


def test_a_fresh_interpreter_imports_the_router_without_its_producers() -> None:
    probe = (
        "import sys, tools.maintenance.damage_model\n"
        "print('\\n'.join(sorted(n for n in sys.modules if n.startswith('tools.maintenance'))))"
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    result = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    loaded = set(result.stdout.split())
    assert "tools.maintenance.damage_model" in loaded, result.stdout
    assert not loaded.intersection(_producer_modules()), (
        "importing the router must not pull in producer modules: "
        f"{sorted(loaded.intersection(_producer_modules()))}"
    )
