"""I24/I27 architecture gates for the neutral tasking-contracts layer.

Background: `gym_envs` and `python.rl` used to form a real import cycle through
`python.rl.tasking.bridge` / `python.rl.control.mission_defs` (gym_envs consumed
them) and `python.rl.runtime.*` (which imports `gym_envs.scenario_loader`/
`gym_envs.universal_env`). I24 extracted the profile-independent slice of that
consumed surface into `python.tasking_contracts` (zero dependency on either
side) so the dependency direction becomes::

    gym_envs -> python.tasking_contracts <- python.rl

I27 tightened the residual ledger further: package inits are lazy, and every
remaining `python.rl` reference in `gym_envs` must be a *function-body deferred
import* (module-level references are zero-tolerance).

The collector closes the statically checkable blind spots called out by the
I24/I27 reviews:

- relative imports resolved per PEP 328 (``from .bridge import x``);
- ``from python import rl`` (parent-package alias form);
- ``importlib.import_module("python.rl...")`` with constant, *concatenated*
  (``"python." + "rl..."``) or f-string-constant arguments;
- aliased dynamic importers (``from importlib import import_module as load``,
  ``loader = importlib.import_module``, ``loader = getattr(importlib,
  "import_module")``) and ``__import__(...)``;
- execution-context tracking via an AST visitor: function *bodies* are
  ``deferred``; default-argument expressions, decorators, and annotations
  execute at module import time and are classified ``module``;
- a text-level combination alarm for shapes the AST cannot resolve (dynamic
  loader capability anywhere in the file + a quoted ``python.``-prefixed
  string anywhere in the file). Deliberately conservative: false positives
  are acceptable and go through an explicit allowlist; false negatives are not.

This module enforces:

1. `python/tasking_contracts/**` never imports `python.rl` or `gym_envs`
   (unconditional; this is the whole point of a neutral layer).
2. `gym_envs/**` residual `python.rl` imports match an exact
   file + form allowlist (`deferred` only; no module-level or dynamic form).
"""

from __future__ import annotations

import ast
import textwrap
from pathlib import Path

from tests.architecture.helpers import ensure_repo_root_on_sys_path
from tests.support.paths import REPO_ROOT

ensure_repo_root_on_sys_path()

GYM_ENVS_ROOT = REPO_ROOT / "gym_envs"
TASKING_CONTRACTS_ROOT = REPO_ROOT / "python" / "tasking_contracts"

# Forms recognized by the gate.
FORM_MODULE = "module"
FORM_DEFERRED = "deferred"
FORM_DYNAMIC = "dynamic"

# Files allowed to trip the conservative text-level combination alarm.
# Each entry is a reviewed false positive; the AST layer still fully applies.
TEXT_DYNAMIC_ALLOWLIST: set[str] = {
    # I24-designed compatibility quarantine: import_module("python.scenario.runtime")
    # (an allowed neutral-side seam, not python.rl/gym_envs). The bare `"python.`
    # prefix marker matches its target string.
    "python/tasking_contracts/bridge_views.py",
}


def _iter_python_files(root: Path) -> list[Path]:
    excluded_prefixes = ("__pycache__",)
    return [
        path
        for path in sorted(root.rglob("*.py"))
        if not any(part.startswith(excluded_prefixes) for part in path.parts)
    ]


def _module_qualname_for_path(path: Path, *, package_root: Path, package_name: str) -> str:
    rel = path.relative_to(package_root)
    parts = list(rel.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join((package_name, *parts)) if parts else package_name


def _resolve_import_from_module(
    node: ast.ImportFrom,
    *,
    file_module: str,
    is_package_init: bool = False,
) -> str | None:
    """Resolve ImportFrom.module, including relative imports (level > 0)."""
    if node.level <= 0:
        return node.module
    parts = [part for part in file_module.split(".") if part]
    # Containing package: package ``__init__`` qualname *is* the package; ordinary
    # modules drop the leaf name (``gym_envs.foo.bar`` -> ``gym_envs.foo``).
    package_parts = list(parts) if is_package_init else parts[:-1]
    # ``level`` leading dots: level=1 keeps package_parts; level=2 drops one; …
    drop = node.level - 1
    if drop > len(package_parts):
        return None
    base = package_parts[: len(package_parts) - drop]
    if node.module:
        return ".".join((*base, *node.module.split("."))) if base else node.module
    return ".".join(base) if base else None


def _is_target_package(module: str | None, packages: tuple[str, ...]) -> bool:
    if not module:
        return False
    return module in packages or any(module.startswith(f"{pkg}.") for pkg in packages)


def _const_str(node: ast.AST) -> str | None:
    """Conservatively fold string-constant expressions (Constant, +, f-string)."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _const_str(node.left)
        right = _const_str(node.right)
        if left is not None and right is not None:
            return left + right
        return None
    if isinstance(node, ast.JoinedStr):
        pieces: list[str] = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                pieces.append(value.value)
            else:
                return None
        return "".join(pieces)
    return None


def _dynamic_import_aliases(tree: ast.AST) -> set[str]:
    """Names bound to ``importlib.import_module`` anywhere in the file.

    Covers ``from importlib import import_module [as alias]``,
    ``alias = importlib.import_module`` and
    ``alias = getattr(importlib, "import_module")``.
    """
    aliases: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "importlib" and node.level == 0:
            for alias in node.names:
                if alias.name == "import_module":
                    aliases.add(alias.asname or alias.name)
        elif isinstance(node, ast.Assign):
            value = node.value
            binds_import_module = (
                isinstance(value, ast.Attribute) and value.attr == "import_module"
            ) or (
                isinstance(value, ast.Call)
                and isinstance(value.func, ast.Name)
                and value.func.id == "getattr"
                and len(value.args) >= 2
                and isinstance(value.args[1], ast.Constant)
                and value.args[1].value == "import_module"
            )
            if binds_import_module:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        aliases.add(target.id)
    return aliases


class _PackageRefCollector(ast.NodeVisitor):
    """AST collector with execution-context tracking.

    ``deferred`` strictly means "executes inside a function body". Default
    arguments, decorators, and annotations run at definition time, i.e. in the
    *enclosing* context — for a top-level ``def`` that is module import time.
    """

    def __init__(
        self,
        *,
        packages: tuple[str, ...],
        file_module: str,
        is_package_init: bool,
        aliases: set[str],
    ) -> None:
        self.packages = packages
        self.file_module = file_module
        self.is_package_init = is_package_init
        self.aliases = aliases
        self.body_depth = 0
        self.refs: set[tuple[str, str, int, str]] = set()

    def _form(self) -> str:
        return FORM_DEFERRED if self.body_depth > 0 else FORM_MODULE

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            if _is_target_package(alias.name, self.packages):
                self.refs.add((alias.name, "<module>", int(node.lineno), self._form()))

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        resolved = _resolve_import_from_module(
            node,
            file_module=self.file_module,
            is_package_init=self.is_package_init,
        )
        if resolved is None:
            return
        form = self._form()
        # Parent-package alias form: `from python import rl [as x]`.
        for pkg in self.packages:
            if "." not in pkg:
                continue
            parent, leaf = pkg.rsplit(".", 1)
            if resolved != parent:
                continue
            for alias in node.names:
                if alias.name == leaf or alias.name.startswith(f"{leaf}."):
                    module = pkg if alias.name == leaf else f"{parent}.{alias.name}"
                    self.refs.add((module, "<module>", int(node.lineno), form))
        if _is_target_package(resolved, self.packages):
            for alias in node.names:
                self.refs.add((resolved, alias.name, int(node.lineno), form))

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        is_dynamic_import = (
            isinstance(func, ast.Name)
            and (func.id in self.aliases or func.id in ("import_module", "__import__"))
        ) or (isinstance(func, ast.Attribute) and func.attr == "import_module")
        if is_dynamic_import and node.args:
            target = _const_str(node.args[0])
            if target is not None and _is_target_package(target, self.packages):
                self.refs.add((target, "<module>", int(node.lineno), self._form()))
        self.generic_visit(node)

    def _visit_definition_time_parts(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        args = node.args
        for default in (*args.defaults, *args.kw_defaults):
            if default is not None:
                self.visit(default)
        for arg in (*args.posonlyargs, *args.args, *args.kwonlyargs):
            if arg.annotation is not None:
                self.visit(arg.annotation)
        for special in (args.vararg, args.kwarg):
            if special is not None and special.annotation is not None:
                self.visit(special.annotation)
        for decorator in node.decorator_list:
            self.visit(decorator)
        if node.returns is not None:
            self.visit(node.returns)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_definition_time_parts(node)
        self.body_depth += 1
        for stmt in node.body:
            self.visit(stmt)
        self.body_depth -= 1

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_definition_time_parts(node)
        self.body_depth += 1
        for stmt in node.body:
            self.visit(stmt)
        self.body_depth -= 1

    def visit_Lambda(self, node: ast.Lambda) -> None:
        for default in (*node.args.defaults, *node.args.kw_defaults):
            if default is not None:
                self.visit(default)
        self.body_depth += 1
        self.visit(node.body)
        self.body_depth -= 1


def _collect_ast_package_refs(
    path: Path,
    *,
    packages: tuple[str, ...],
    file_module: str,
) -> set[tuple[str, str, int, str]]:
    """Return {(module, name, lineno, form)} for package references found via AST."""
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    collector = _PackageRefCollector(
        packages=packages,
        file_module=file_module,
        is_package_init=path.name == "__init__.py",
        aliases=_dynamic_import_aliases(tree),
    )
    collector.visit(tree)
    return collector.refs


# Dynamic-loader capability markers for the text-level combination alarm.
_DYNAMIC_CAPABILITY_MARKERS = ("getattr(importlib", "__import__(", "import_module")


def _quoted_prefix_markers(packages: tuple[str, ...]) -> tuple[str, ...]:
    """Quoted-string markers that could name (a concatenation piece of) a package."""
    markers: list[str] = []
    for pkg in packages:
        root = pkg.split(".", 1)[0]
        for quote in ('"', "'"):
            markers.append(f"{quote}{pkg}")
            # Conservative: `"python." + "rl..."` style concatenation pieces.
            markers.append(f"{quote}{root}.")
    return tuple(dict.fromkeys(markers))


def _collect_dynamic_text_refs(path: Path, *, packages: tuple[str, ...]) -> set[tuple[str, str, int, str]]:
    """Text-level combination alarm for dynamic shapes AST cannot resolve.

    Fires when the file contains BOTH (a) any dynamic-loader capability marker
    (``getattr(importlib`` / ``__import__(`` / any ``import_module`` mention,
    which covers aliased assignments and cross-line variable calls) and (b) a
    quoted string that could be — or could concatenate into — a target package
    path (``"python.rl...``, or a bare ``"python."`` piece). Deliberately
    conservative; reviewed false positives go to TEXT_DYNAMIC_ALLOWLIST.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    capability_lines = [
        lineno
        for lineno, line in enumerate(lines, start=1)
        if any(marker in line for marker in _DYNAMIC_CAPABILITY_MARKERS)
    ]
    if not capability_lines:
        return set()
    markers = _quoted_prefix_markers(packages)
    refs: set[tuple[str, str, int, str]] = set()
    for lineno, line in enumerate(lines, start=1):
        for marker in markers:
            if marker not in line:
                continue
            # Best-effort extraction of the quoted module string for reporting.
            quote = marker[0]
            start = line.index(marker) + 1
            end = line.find(quote, start)
            module = line[start:end] if end > start else marker[1:]
            refs.add((module, "<dynamic>", lineno, FORM_DYNAMIC))
    return refs


def _foreign_package_refs(
    path: Path,
    *,
    packages: tuple[str, ...],
    package_root: Path,
    package_name: str,
) -> set[tuple[str, str, int, str]]:
    file_module = _module_qualname_for_path(path, package_root=package_root, package_name=package_name)
    refs = _collect_ast_package_refs(path, packages=packages, file_module=file_module)
    rel = path.relative_to(REPO_ROOT).as_posix() if path.is_relative_to(REPO_ROOT) else path.as_posix()
    if rel not in TEXT_DYNAMIC_ALLOWLIST:
        refs |= _collect_dynamic_text_refs(path, packages=packages)
    return refs


# Governance ledger (I27): file -> {(module, imported_name, form)}.
# Only FORM_DEFERRED is permitted. Module-level python.rl references are forbidden.
GYM_ENVS_PYTHON_RL_RESIDUAL_ALLOWLIST: dict[str, set[tuple[str, str, str]]] = {
    "gym_envs/leader_env.py": {
        ("python.rl.tasking.bridge", "make_rule_based_leader_phase_manager", FORM_DEFERRED),
        ("python.rl.tasking.bridge", "make_scripted_c2_task_manager", FORM_DEFERRED),
    },
    "gym_envs/leader_env_parts/decision_runtime/commands.py": {
        ("python.rl.tasking.bridge", "infer_recovery_approach_type", FORM_DEFERRED),
        ("python.rl.tasking.bridge", "infer_recovery_base_id", FORM_DEFERRED),
        ("python.rl.tasking.bridge", "infer_recovery_runway_id", FORM_DEFERRED),
        ("python.rl.tasking.bridge", "infer_route_ref_id", FORM_DEFERRED),
        ("python.rl.tasking.bridge", "is_patrol_task", FORM_DEFERRED),
        ("python.rl.tasking.bridge", "is_recover_task", FORM_DEFERRED),
    },
    "gym_envs/leader_env_parts/decision_runtime/observations.py": {
        ("python.rl.tasking.bridge", "task_observation_codes", FORM_DEFERRED),
    },
    "gym_envs/leader_env_parts/execution_runtime/policy_runtime.py": {
        ("python.rl.runtime.single_world_batch_runtime", "build_single_world_batch_execution_runtime", FORM_DEFERRED),
        ("python.rl.control.wrappers", "get_action_wrapper_spec", FORM_DEFERRED),
    },
    "gym_envs/leader_env_parts/policy.py": {
        ("python.rl.policy_algo.ppo_adaptive_kl", "AdaptiveKLPPO", FORM_DEFERRED),
    },
    "gym_envs/leader_env_parts/runtime_facade.py": {
        ("python.rl.runtime.leader_window_runtime", "LocalLeaderWindowRuntime", FORM_DEFERRED),
        ("python.rl.runtime.leader_window_runtime", "WorldBatchLeaderWindowRuntime", FORM_DEFERRED),
    },
    "gym_envs/scenario_loader/behavior_runtime/command_chain.py": {
        ("python.rl.tasking.bridge", "build_kernel_mission_command", FORM_DEFERRED),
    },
    "gym_envs/scenario_loader/behavior_runtime/command_chain_owner.py": {
        ("python.rl.tasking.bridge", "make_rule_based_leader_phase_manager", FORM_DEFERRED),
    },
    "gym_envs/scenario_loader/loading.py": {
        ("python.rl.tasking.bridge", "normalize_task_order_spec", FORM_DEFERRED),
    },
    "gym_envs/scenario_loader/runtime_state.py": {
        ("python.rl.tasking.bridge", "build_kernel_mission_command", FORM_DEFERRED),
    },
    "gym_envs/scenario_loader/step_evaluation.py": {
        ("python.rl.tasking.bridge", "resolve_tasking_profile", FORM_DEFERRED),
        ("python.rl.tasking.bridge", "tasking_profile_for_loader", FORM_DEFERRED),
    },
    "gym_envs/universal_env_parts/info.py": {
        ("python.rl.tasking.bridge", "resolve_tasking_profile", FORM_DEFERRED),
        ("python.rl.tasking.bridge", "tasking_profile_for_loader", FORM_DEFERRED),
    },
    "gym_envs/universal_env_parts/naval_actions.py": {
        ("python.rl.tasking.bridge", "resolve_tasking_profile", FORM_DEFERRED),
        ("python.rl.tasking.bridge", "tasking_profile_for_loader", FORM_DEFERRED),
    },
    "gym_envs/universal_env_parts/observations.py": {
        ("python.rl.tasking.bridge", "resolve_tasking_profile", FORM_DEFERRED),
        ("python.rl.tasking.bridge", "tasking_profile_for_loader", FORM_DEFERRED),
    },
}


def test_tasking_contracts_package_never_imports_python_rl_or_gym_envs() -> None:
    offenders: dict[str, list[str]] = {}
    for path in _iter_python_files(TASKING_CONTRACTS_ROOT):
        refs = _foreign_package_refs(
            path,
            packages=("python.rl", "gym_envs"),
            package_root=TASKING_CONTRACTS_ROOT,
            package_name="python.tasking_contracts",
        )
        if refs:
            rel = path.relative_to(REPO_ROOT).as_posix()
            offenders[rel] = sorted(
                f"L{lineno}: {form} {module}.{name}" for module, name, lineno, form in refs
            )
    assert not offenders, (
        "python/tasking_contracts/** must stay neutral (stdlib + ef_py-style native "
        f"lazy imports only); found python.rl/gym_envs references: {offenders}"
    )


def test_gym_envs_python_rl_imports_are_limited_to_the_documented_residual_allowlist() -> None:
    found: dict[str, set[tuple[str, str, str]]] = {}
    for path in _iter_python_files(GYM_ENVS_ROOT):
        refs = _foreign_package_refs(
            path,
            packages=("python.rl",),
            package_root=GYM_ENVS_ROOT,
            package_name="gym_envs",
        )
        if refs:
            rel = path.relative_to(REPO_ROOT).as_posix()
            found.setdefault(rel, set()).update(
                (module, name, form) for module, name, _lineno, form in refs
            )
    # Zero tolerance for module-level / dynamic forms outside the deferred ledger.
    module_level = {
        rel: sorted(item for item in items if item[2] != FORM_DEFERRED)
        for rel, items in found.items()
        if any(item[2] != FORM_DEFERRED for item in items)
    }
    assert not module_level, (
        "gym_envs module-level (or dynamic) python.rl references are forbidden after I27; "
        "move them into function-body deferred imports or justify a new reviewed form: "
        f"{module_level}"
    )
    expected_files = set(GYM_ENVS_PYTHON_RL_RESIDUAL_ALLOWLIST)
    found_files = set(found)
    new_files = found_files - expected_files
    assert not new_files, (
        "gym_envs file(s) import python.rl without a governance-ledger allowlist entry "
        f"(I24/I27 broke this cycle; new python.rl imports need an explicit, reviewed entry "
        f"or must go through python.tasking_contracts instead): {sorted(new_files)}"
    )
    for relative_path, expected_refs in GYM_ENVS_PYTHON_RL_RESIDUAL_ALLOWLIST.items():
        actual_refs = found.get(relative_path, set())
        assert actual_refs == expected_refs, (
            f"{relative_path}: residual python.rl import set drifted from the I27 governance "
            f"ledger. expected={sorted(expected_refs)} actual={sorted(actual_refs)}. "
            "If this file's residual shrank, narrow the allowlist entry (progress); if it "
            "grew, that is a new entanglement that needs its own reviewed justification."
        )
    stale_files = expected_files - found_files
    assert not stale_files, (
        "governance ledger allowlist entries no longer match any real python.rl import in "
        f"gym_envs; remove the stale entries to keep this gate honest: {sorted(stale_files)}"
    )


# --- Blind-spot fixture tests (tmp trees; every reviewed bypass construction) --


def _write_tmp_module(tmp_path: Path, relative: str, source: str) -> Path:
    path = tmp_path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(source), encoding="utf-8")
    return path


def test_gate_detects_relative_import_of_python_rl(tmp_path: Path) -> None:
    # Simulate a package where `from .bridge import x` resolves to python.rl.tasking.bridge.
    package_root = tmp_path / "python" / "rl"
    path = _write_tmp_module(
        package_root,
        "tasking/consumer.py",
        """
        def load():
            from .bridge import resolve_tasking_profile
            return resolve_tasking_profile
        """,
    )
    refs = _collect_ast_package_refs(
        path,
        packages=("python.rl",),
        file_module="python.rl.tasking.consumer",
    )
    assert any(
        module == "python.rl.tasking.bridge" and name == "resolve_tasking_profile"
        for module, name, _lineno, _form in refs
    ), refs


def test_gate_detects_from_python_import_rl(tmp_path: Path) -> None:
    path = _write_tmp_module(
        tmp_path,
        "sample.py",
        """
        from python import rl
        """,
    )
    refs = _collect_ast_package_refs(
        path,
        packages=("python.rl",),
        file_module="sample",
    )
    assert any(module == "python.rl" for module, _name, _lineno, _form in refs), refs


def test_gate_detects_importlib_import_module_string(tmp_path: Path) -> None:
    path = _write_tmp_module(
        tmp_path,
        "sample.py",
        """
        import importlib

        def load():
            return importlib.import_module("python.rl.tasking.bridge")
        """,
    )
    refs = _collect_ast_package_refs(
        path,
        packages=("python.rl",),
        file_module="sample",
    )
    assert any(
        module == "python.rl.tasking.bridge" and form == FORM_DEFERRED
        for module, _name, _lineno, form in refs
    ), refs


def test_gate_detects_concatenated_import_module_string(tmp_path: Path) -> None:
    # Reviewed bypass (a): constant concatenation must be folded by the AST layer.
    path = _write_tmp_module(
        tmp_path,
        "sample.py",
        """
        from importlib import import_module

        bridge = import_module("python." + "rl.tasking.bridge")
        """,
    )
    refs = _collect_ast_package_refs(
        path,
        packages=("python.rl",),
        file_module="sample",
    )
    assert any(
        module == "python.rl.tasking.bridge" and name == "<module>" and form == FORM_MODULE
        for module, name, _lineno, form in refs
    ), refs


def test_gate_detects_aliased_import_module_calls(tmp_path: Path) -> None:
    # Reviewed bypass (b): `from importlib import import_module as load` plus
    # a getattr-bound alias must both be tracked by the AST layer.
    path = _write_tmp_module(
        tmp_path,
        "sample.py",
        """
        import importlib
        from importlib import import_module as load

        loader = getattr(importlib, "import_module")
        wrappers = loader("python.rl.control.wrappers")

        def use():
            return load("python.rl.tasking.bridge")
        """,
    )
    refs = _collect_ast_package_refs(
        path,
        packages=("python.rl",),
        file_module="sample",
    )
    assert any(
        module == "python.rl.control.wrappers" and form == FORM_MODULE
        for module, _name, _lineno, form in refs
    ), refs
    assert any(
        module == "python.rl.tasking.bridge" and form == FORM_DEFERRED
        for module, _name, _lineno, form in refs
    ), refs


def test_gate_default_argument_import_module_is_module_level(tmp_path: Path) -> None:
    # Reviewed bypass (c): default-argument expressions execute at module load
    # time; they must NOT be classified as deferred.
    path = _write_tmp_module(
        tmp_path,
        "sample.py",
        """
        from importlib import import_module

        def f(bridge=import_module("python.rl.tasking.bridge")):
            return bridge
        """,
    )
    refs = _collect_ast_package_refs(
        path,
        packages=("python.rl",),
        file_module="sample",
    )
    assert any(
        module == "python.rl.tasking.bridge" and form == FORM_MODULE
        for module, _name, _lineno, form in refs
    ), refs
    assert not any(form == FORM_DEFERRED for _m, _n, _l, form in refs), (
        "default-argument import_module must not be classified deferred",
        refs,
    )


def test_gate_text_fallback_detects_cross_line_getattr_dynamic(tmp_path: Path) -> None:
    # Cross-line shape: the loader alias is bound on one line, the target string
    # appears several lines later. The combination alarm is file-scoped.
    path = _write_tmp_module(
        tmp_path,
        "sample.py",
        """
        import importlib

        loader = getattr(importlib, "import_module")

        def indirection():
            name = "python.rl.tasking.bridge"
            return loader(name)
        """,
    )
    refs = _collect_dynamic_text_refs(path, packages=("python.rl",))
    assert refs, "expected file-scoped combination alarm to flag getattr(importlib, ...)"
    assert any(
        "python.rl" in module for module, _name, _lineno, form in refs if form == FORM_DYNAMIC
    ), refs


def test_gate_text_fallback_detects_variable_concatenation(tmp_path: Path) -> None:
    # Variable concatenation defeats AST folding; the `"python."` piece plus the
    # import_module capability marker must still trip the combination alarm.
    path = _write_tmp_module(
        tmp_path,
        "sample.py",
        """
        from importlib import import_module

        prefix = "python."

        def load():
            return import_module(prefix + "rl.tasking.bridge")
        """,
    )
    refs = _collect_dynamic_text_refs(path, packages=("python.rl",))
    assert any(form == FORM_DYNAMIC for _module, _name, _lineno, form in refs), refs


def test_gate_classifies_module_level_vs_deferred(tmp_path: Path) -> None:
    path = _write_tmp_module(
        tmp_path,
        "sample.py",
        """
        from python.rl.tasking.bridge import resolve_tasking_profile

        def use():
            from python.rl.tasking.bridge import tasking_profile_for_loader
            return tasking_profile_for_loader
        """,
    )
    refs = _collect_ast_package_refs(
        path,
        packages=("python.rl",),
        file_module="sample",
    )
    forms = {(name, form) for _module, name, _lineno, form in refs}
    assert ("resolve_tasking_profile", FORM_MODULE) in forms
    assert ("tasking_profile_for_loader", FORM_DEFERRED) in forms
