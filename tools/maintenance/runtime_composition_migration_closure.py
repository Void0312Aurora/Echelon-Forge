#!/usr/bin/env python3
"""Generate and validate the bounded P8-A runtime composition closure record."""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import jsonschema


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
FIXTURES = ROOT / "tests/architecture/composition/fixtures"
SCHEMA_PATH = (
    ROOT / "src/runtime/contracts/composition/runtime_composition_migration_closure.v1.schema.json"
)
DEFAULT_OUTPUT = FIXTURES / "default_runtime_composition_migration_closure.v1.json"
SCHEMA_VERSION = "echelon_forge.runtime_composition_migration_closure.v1"
CANONICALIZATION = "echelon_forge.sorted_utf8_json.v1"

RETIRED_SETTERS = (
    "set_environment_model",
    "set_unit_factory",
    "set_effects_model",
    "set_sensor_model",
    "set_acoustic_model",
    "set_control_model",
    "set_guidance_model",
)

CALLER_SUFFIXES = {".py", ".yml", ".yaml"}
CPP_CALLER_SUFFIXES = {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx", ".inl", ".ipp"}
SKIPPED_CALLER_DIRECTORIES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "archive",
    "node_modules",
    "tests",
}


class ClosureError(ValueError):
    """Raised when the P8-A closure record is stale or invalid."""


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_json(value: Any) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _blank_lexeme(value: str) -> str:
    return "".join("\n" if char == "\n" else " " for char in value)


def sanitize_cpp_source(source: str, *, strip_literals: bool = True) -> str:
    """Remove comments and optionally literals while preserving source layout."""
    result: list[str] = []
    index = 0
    length = len(source)
    raw_prefixes = ('u8R"', 'uR"', 'UR"', 'LR"', 'R"')
    while index < length:
        if source.startswith("//", index):
            end = source.find("\n", index)
            end = length if end < 0 else end
            result.append(_blank_lexeme(source[index:end]))
            index = end
            continue
        if source.startswith("/*", index):
            end = source.find("*/", index + 2)
            end = length if end < 0 else end + 2
            result.append(_blank_lexeme(source[index:end]))
            index = end
            continue

        raw_prefix = next(
            (prefix for prefix in raw_prefixes if source.startswith(prefix, index)), None
        )
        if raw_prefix is not None:
            delimiter_start = index + len(raw_prefix)
            open_paren = source.find("(", delimiter_start, delimiter_start + 17)
            if open_paren >= 0:
                delimiter = source[delimiter_start:open_paren]
                terminator = ")" + delimiter + '"'
                end = source.find(terminator, open_paren + 1)
                end = length if end < 0 else end + len(terminator)
                lexeme = source[index:end]
                result.append(_blank_lexeme(lexeme) if strip_literals else lexeme)
                index = end
                continue

        if source[index] in {'"', "'"}:
            quote = source[index]
            end = index + 1
            while end < length:
                if source[end] == "\\":
                    end += 2
                    continue
                end += 1
                if source[end - 1] == quote:
                    break
            lexeme = source[index:end]
            result.append(_blank_lexeme(lexeme) if strip_literals else lexeme)
            index = end
            continue

        result.append(source[index])
        index += 1
    return "".join(result)


def cpp_has_implicit_manifest_fallback(source: str) -> bool:
    code = sanitize_cpp_source(source)
    return bool(
        re.search(
            r"\bresolved_manifest_json\s*\.\s*(?:empty|size|length)\s*\(",
            code,
        )
    )


def cpp_has_default_manifest_alias(source: str) -> bool:
    code = sanitize_cpp_source(source)
    return bool(
        re.search(
            r"SimulationKernel::SimulationKernel\s*\(\s*\)\s*:\s*SimulationKernel\s*\(\s*"
            r"runtime::providers::default_compatibility_resolved_manifest_json\s*\(\s*\)\s*"
            r"\)\s*\{\s*\}",
            code,
        )
    )


def python_source_calls_ef_py_symbol(source: str, symbol: str) -> bool:
    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        raise ClosureError(f"cannot parse Python caller source: {error}") from error

    module_aliases: set[str] = set()
    symbol_aliases: set[str] = set()
    importlib_aliases: set[str] = set()
    import_module_aliases: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for imported in node.names:
                if imported.name == "ef_py":
                    module_aliases.add(imported.asname or "ef_py")
                elif imported.name == "importlib":
                    importlib_aliases.add(imported.asname or "importlib")
        elif isinstance(node, ast.ImportFrom) and node.module == "ef_py":
            for imported in node.names:
                if imported.name in {symbol, "*"}:
                    symbol_aliases.add(imported.asname or symbol)
        elif isinstance(node, ast.ImportFrom) and node.module == "importlib":
            for imported in node.names:
                if imported.name == "import_module":
                    import_module_aliases.add(imported.asname or "import_module")

    def is_module_reference(node: ast.AST) -> bool:
        if isinstance(node, ast.Name) and node.id in module_aliases:
            return True
        if not isinstance(node, ast.Call) or not node.args:
            return False
        imports_module = (
            isinstance(node.func, ast.Name)
            and node.func.id in {"__import__", *import_module_aliases}
        ) or (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "import_module"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in importlib_aliases
        )
        return (
            imports_module
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value == "ef_py"
        )

    def is_symbol_reference(node: ast.AST) -> bool:
        return (
            isinstance(node, ast.Attribute)
            and node.attr == symbol
            and is_module_reference(node.value)
        ) or (isinstance(node, ast.Name) and node.id in symbol_aliases)

    def is_dynamic_symbol_reference(node: ast.AST) -> bool:
        return (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "getattr"
            and len(node.args) >= 2
            and is_module_reference(node.args[0])
            and isinstance(node.args[1], ast.Constant)
            and node.args[1].value == symbol
        )

    changed = True
    while changed:
        changed = False
        for node in ast.walk(tree):
            value: ast.AST | None = None
            targets: list[ast.expr] = []
            if isinstance(node, ast.Assign):
                value = node.value
                targets = node.targets
            elif isinstance(node, ast.AnnAssign):
                value = node.value
                targets = [node.target]
            if value is not None and is_module_reference(value):
                for target in targets:
                    if isinstance(target, ast.Name) and target.id not in module_aliases:
                        module_aliases.add(target.id)
                        changed = True
            elif value is not None and (
                is_symbol_reference(value) or is_dynamic_symbol_reference(value)
            ):
                for target in targets:
                    if isinstance(target, ast.Name) and target.id not in symbol_aliases:
                        symbol_aliases.add(target.id)
                        changed = True
    return any(
        isinstance(node, ast.Call)
        and (is_symbol_reference(node.func) or is_dynamic_symbol_reference(node.func))
        for node in ast.walk(tree)
    )


def yaml_source_may_call_ef_py_symbol(source: str, symbol: str) -> bool:
    uncommented = "\n".join(line.split("#", 1)[0] for line in source.splitlines())
    return "ef_py" in uncommented and symbol in uncommented


def scan_python_callers(symbol: str) -> list[str]:
    callers: list[str] = []
    for directory, child_directories, filenames in os.walk(ROOT):
        child_directories[:] = [
            name
            for name in child_directories
            if name not in SKIPPED_CALLER_DIRECTORIES
            and not name.startswith("build-")
            and not name.startswith(".basetemp")
        ]
        directory_path = Path(directory)
        for filename in filenames:
            path = directory_path / filename
            if path.suffix not in CALLER_SUFFIXES:
                continue
            source = path.read_text(encoding="utf-8", errors="ignore")
            if "ef_py" not in source or symbol not in source:
                continue
            calls_symbol = (
                python_source_calls_ef_py_symbol(source, symbol)
                if path.suffix == ".py"
                else yaml_source_may_call_ef_py_symbol(source, symbol)
            )
            if calls_symbol:
                callers.append(relative(path))
    return sorted(set(callers))


def _balanced_argument_payload(code: str, opening_index: int) -> tuple[str, int]:
    opening = code[opening_index]
    closing = ")" if opening == "(" else "}"
    depth = 0
    for index in range(opening_index, len(code)):
        if code[index] == opening:
            depth += 1
        elif code[index] == closing:
            depth -= 1
            if depth == 0:
                return code[opening_index + 1 : index], index + 1
    return code[opening_index + 1 :], len(code)


def _balanced_argument_kind(code: str, opening_index: int) -> tuple[str, int]:
    payload, end = _balanced_argument_payload(code, opening_index)
    return ("default" if not payload.strip() else "explicit"), end


def _construct_at_argument_kind(code: str, opening_index: int) -> str:
    payload, _ = _balanced_argument_payload(code, opening_index)
    depths = {"(": 0, "{": 0, "[": 0}
    closings = {")": "(", "}": "{", "]": "["}
    for index, char in enumerate(payload):
        if char in depths:
            depths[char] += 1
        elif char in closings:
            depths[closings[char]] = max(0, depths[closings[char]] - 1)
        elif char == "," and not any(depths.values()):
            return "explicit" if payload[index + 1 :].strip() else "default"
    return "default"


def cpp_constructor_kinds(source: str, canonical_type: str) -> set[str]:
    """Classify live C++ constructions as default or explicit-argument calls."""
    code = sanitize_cpp_source(source)
    escaped_canonical = re.escape(canonical_type)
    aliases = {
        match.group(1)
        for match in re.finditer(
            rf"\busing\s+([A-Za-z_]\w*)\s*=\s*"
            rf"(?:(?:[A-Za-z_]\w*)\s*::\s*)*{escaped_canonical}\s*;",
            code,
        )
    }
    aliases.update(
        match.group(1)
        for match in re.finditer(
            rf"\btypedef\s+(?:(?:[A-Za-z_]\w*)\s*::\s*)*{escaped_canonical}\s+"
            r"([A-Za-z_]\w*)\s*;",
            code,
        )
    )
    kinds: set[str] = set()
    for type_name in {canonical_type, *aliases}:
        escaped = re.escape(type_name)
        qualified_type = rf"(?:(?:[A-Za-z_]\w*)\s*::\s*)*{escaped}"

        for match in re.finditer(
            rf"\b(?:make_unique|make_shared|make_optional)\s*<\s*{qualified_type}\s*>\s*"
            rf"([({{])",
            code,
        ):
            kind, _ = _balanced_argument_kind(code, match.start(1))
            kinds.add(kind)

        for match in re.finditer(
            rf"\ballocate_shared\s*<\s*{qualified_type}\s*>\s*([({{])",
            code,
        ):
            kinds.add(_construct_at_argument_kind(code, match.start(1)))

        for match in re.finditer(
            rf"\bconstruct_at\s*<\s*{qualified_type}\s*>\s*([({{])",
            code,
        ):
            kinds.add(_construct_at_argument_kind(code, match.start(1)))

        for holder in re.finditer(
            rf"\b(?:std\s*::\s*)?"
            rf"(optional|variant|vector|deque|list|forward_list|array|tuple|pair|map|unordered_map)"
            rf"\s*<"
            rf"[^;{{}}]*?\b{qualified_type}\b[^;{{}}]*?>\s+([A-Za-z_]\w*)",
            code,
        ):
            holder_kind = holder.group(1)
            variable = holder.group(2)
            tail = holder.end()
            while tail < len(code) and code[tail].isspace():
                tail += 1
            if tail < len(code) and code[tail] in "({":
                kind, _ = _balanced_argument_kind(code, tail)
                if kind == "explicit" or holder_kind in {"variant", "array", "tuple", "pair"}:
                    kinds.add(kind)
            elif (
                tail < len(code)
                and code[tail] == ";"
                and holder_kind
                in {
                    "variant",
                    "array",
                    "tuple",
                    "pair",
                }
            ):
                kinds.add("default")
            for emplace in re.finditer(
                rf"\b{re.escape(variable)}\s*\.\s*"
                rf"(?:emplace|emplace_back|emplace_front|try_emplace)"
                rf"(?:\s*<[^>]+>)?\s*([({{])",
                code[holder.end() :],
            ):
                opening_index = holder.end() + emplace.start(1)
                if holder_kind in {"map", "unordered_map"}:
                    kind = _construct_at_argument_kind(code, opening_index)
                else:
                    kind, _ = _balanced_argument_kind(code, opening_index)
                kinds.add(kind)

        for match in re.finditer(rf"\bnew\s+{qualified_type}\b", code):
            tail = match.end()
            while tail < len(code) and code[tail].isspace():
                tail += 1
            if tail < len(code) and code[tail] in "({":
                kind, _ = _balanced_argument_kind(code, tail)
                kinds.add(kind)
            else:
                kinds.add("default")

        for match in re.finditer(
            rf"\bnew\s*\([^)]*\)\s*{qualified_type}\b",
            code,
        ):
            tail = match.end()
            while tail < len(code) and code[tail].isspace():
                tail += 1
            if tail < len(code) and code[tail] in "({":
                kind, _ = _balanced_argument_kind(code, tail)
                kinds.add(kind)
            else:
                kinds.add("default")

        for match in re.finditer(rf"(?<![A-Za-z0-9_])(?:::)?{qualified_type}\b", code):
            prefix = code[max(0, match.start() - 5) : match.start()]
            if re.search(r"\bnew\s*$", prefix) or re.search(r"<\s*$", prefix):
                continue
            tail = match.end()
            while tail < len(code) and code[tail].isspace():
                tail += 1
            if tail < len(code) and code[tail] in "({":
                kind, _ = _balanced_argument_kind(code, tail)
                kinds.add(kind)
                continue
            identifier = re.match(r"[A-Za-z_]\w*", code[tail:])
            if identifier is None:
                continue
            tail += identifier.end()
            while tail < len(code) and code[tail].isspace():
                tail += 1
            if tail < len(code) and code[tail] == ";":
                kinds.add("default")
            elif tail < len(code) and code[tail] == "[":
                closing = code.find("]", tail + 1)
                if closing >= 0:
                    kinds.add("default")
            elif tail < len(code) and code[tail] in "({":
                kind, _ = _balanced_argument_kind(code, tail)
                kinds.add(kind)
            elif tail < len(code) and code[tail] == "=":
                tail += 1
                while tail < len(code) and code[tail].isspace():
                    tail += 1
                if tail < len(code) and code[tail] == "{":
                    kind, _ = _balanced_argument_kind(code, tail)
                    kinds.add(kind)
    return kinds


def cpp_source_constructs_default_kernel(source: str) -> bool:
    return "default" in cpp_constructor_kinds(source, "SimulationKernel")


def cpp_source_constructs_explicit_kernel(source: str) -> bool:
    return "explicit" in cpp_constructor_kinds(source, "SimulationKernel")


def cpp_source_constructs_runtime_facade(source: str) -> bool:
    return bool(cpp_constructor_kinds(source, "RuntimeFacade"))


def iter_cpp_source_files():
    for path in (ROOT / "src").rglob("*"):
        if path.is_file() and path.suffix.lower() in CPP_CALLER_SUFFIXES:
            yield path


def scan_cpp_default_kernel_callers() -> list[str]:
    callers: list[str] = []
    for path in iter_cpp_source_files():
        relative_path = path.relative_to(ROOT)
        if (
            "tests" in relative_path.parts
            or "experimental" in relative_path.parts
            or relative_path.as_posix()
            in {"src/core/engine/simulation_kernel.cpp", "src/core/engine/simulation_kernel.h"}
        ):
            continue
        source = path.read_text(encoding="utf-8", errors="ignore")
        if cpp_source_constructs_default_kernel(source):
            callers.append(relative(path))
    return sorted(set(callers))


def scan_cpp_explicit_kernel_callers() -> list[str]:
    callers: list[str] = []
    for path in iter_cpp_source_files():
        relative_path = path.relative_to(ROOT)
        if (
            "tests" in relative_path.parts
            or "experimental" in relative_path.parts
            or relative_path.as_posix()
            in {"src/core/engine/simulation_kernel.cpp", "src/core/engine/simulation_kernel.h"}
        ):
            continue
        source = path.read_text(encoding="utf-8", errors="ignore")
        if cpp_source_constructs_explicit_kernel(source):
            callers.append(relative(path))
    return sorted(set(callers))


def scan_cpp_runtime_facade_callers() -> list[str]:
    callers: list[str] = []
    for path in iter_cpp_source_files():
        relative_path = path.relative_to(ROOT)
        if (
            "tests" in relative_path.parts
            or "experimental" in relative_path.parts
            or relative_path.as_posix()
            in {"src/runtime/facade/runtime_facade.cpp", "src/runtime/facade/runtime_facade.h"}
        ):
            continue
        source = path.read_text(encoding="utf-8", errors="ignore")
        if cpp_source_constructs_runtime_facade(source):
            callers.append(relative(path))
    return sorted(set(callers))


def cpp_source_references_symbol(source: str, symbol: str) -> bool:
    code = sanitize_cpp_source(source)
    return bool(re.search(rf"\b{re.escape(symbol)}\b", code))


def scan_cpp_symbol_callers(symbol: str, *, excluded_paths: set[str] | None = None) -> list[str]:
    callers: list[str] = []
    excluded = excluded_paths or set()
    for path in iter_cpp_source_files():
        relative_path = relative(path)
        if relative_path in excluded:
            continue
        source = path.read_text(encoding="utf-8", errors="ignore")
        if cpp_source_references_symbol(source, symbol):
            callers.append(relative_path)
    return sorted(set(callers))


def source_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _require_no_issues(label: str, issues: list[Any]) -> None:
    if issues:
        rendered = "; ".join(
            f"{getattr(issue, 'code', 'invalid')}@{getattr(issue, 'path', '$')}" for issue in issues
        )
        raise ClosureError(f"{label} rejected: {rendered}")


def _validate_sealed_artifact(value: dict[str, Any], identity_key: str, label: str) -> None:
    payload = {
        key: item for key, item in value.items() if key not in {"canonical_json", identity_key}
    }
    expected_canonical = canonical_json(payload)
    if value.get("canonical_json") != expected_canonical:
        raise ClosureError(f"{label} canonical payload mismatch")
    if value.get(identity_key) != sha256_text(expected_canonical):
        raise ClosureError(f"{label} identity mismatch")


def _runtime_package_expectations() -> dict[str, Any]:
    package_root = ROOT / "packages/cordis-runtime"
    descriptor_path = package_root / "packages/default-compatibility.package.json"
    descriptor = load_json(descriptor_path)
    package_metadata = load_json(package_root / "package.json")
    package_lock_path = package_root / "package-lock.json"

    nodes: list[dict[str, Any]] = []
    for dependency in descriptor["dependencies"]:
        node = {
            "node_id": dependency["dependency_id"],
            "kind": dependency["kind"],
            "requires": sorted(dependency["requires"], key=lambda value: value.encode("utf-8")),
        }
        if dependency["kind"] == "npm_package":
            node.update(
                package_name=dependency["package_name"],
                version=dependency["version"],
            )
        else:
            node.update(path=dependency["path"], sha256=dependency["sha256"])
        nodes.append(node)
    for overlay in descriptor["overlays"]:
        nodes.append(
            {
                "node_id": overlay["overlay_id"],
                "kind": "configuration_overlay",
                "path": overlay["path"],
                "sha256": overlay["sha256"],
                "requires": sorted(overlay["requires"], key=lambda value: value.encode("utf-8")),
            }
        )
    nodes.sort(key=lambda row: row["node_id"].encode("utf-8"))
    node_ids = {row["node_id"] for row in nodes}
    indegree = {row["node_id"]: len(row["requires"]) for row in nodes}
    dependents = {node_id: [] for node_id in node_ids}
    for node in nodes:
        for requirement in node["requires"]:
            if requirement not in node_ids:
                raise ClosureError(
                    f"runtime package dependency missing: {node['node_id']} requires {requirement}"
                )
            dependents[requirement].append(node["node_id"])
    for values in dependents.values():
        values.sort(key=lambda value: value.encode("utf-8"))
    ready = sorted(
        (node_id for node_id, degree in indegree.items() if degree == 0),
        key=lambda value: value.encode("utf-8"),
    )
    order: list[str] = []
    while ready:
        current = ready.pop(0)
        order.append(current)
        for dependent in dependents[current]:
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                ready.append(dependent)
                ready.sort(key=lambda value: value.encode("utf-8"))
    if len(order) != len(nodes):
        raise ClosureError("runtime package dependency graph contains a cycle")

    dependency_by_id = {
        dependency["dependency_id"]: dependency for dependency in descriptor["dependencies"]
    }
    profile = descriptor["profile"]
    module_dependency = dependency_by_id[profile["module_dependency_id"]]
    bundle_dependency = dependency_by_id[profile["bundle_dependency_id"]]
    cordis_dependency = dependency_by_id[descriptor["cordis_dependency_id"]]
    module_path = package_root / module_dependency["path"]
    bundle_path = package_root / bundle_dependency["path"]
    if sha256_bytes(module_path.read_bytes()) != module_dependency["sha256"]:
        raise ClosureError("runtime package profile module bytes drifted from its descriptor")
    if sha256_bytes(bundle_path.read_bytes()) != bundle_dependency["sha256"]:
        raise ClosureError("runtime package profile bundle bytes drifted from its descriptor")

    overlays: list[dict[str, Any]] = []
    for overlay in descriptor["overlays"]:
        overlay_path = package_root / overlay["path"]
        if sha256_bytes(overlay_path.read_bytes()) != overlay["sha256"]:
            raise ClosureError(f"runtime package overlay bytes drifted: {overlay['overlay_id']}")
        overlay_value = load_json(overlay_path)
        overlays.append(
            {
                "overlay_id": overlay["overlay_id"],
                "overlay_version": overlay_value["overlay_version"],
                "precedence": overlay_value["precedence"],
                "sha256": overlay["sha256"],
            }
        )
    return {
        "package": {
            "package_id": descriptor["package_id"],
            "package_version": descriptor["package_version"],
            "descriptor_sha256": sha256_bytes(descriptor_path.read_bytes()),
        },
        "profile": {
            "profile_id": profile["profile_id"],
            "profile_version": profile["profile_version"],
            "module_sha256": module_dependency["sha256"],
            "bundle_sha256": bundle_dependency["sha256"],
        },
        "dependency_resolution": {
            "order": order,
            "graph_sha256": sha256_text(canonical_json({"nodes": nodes})),
        },
        "configuration_overlays": overlays,
        "producer": {
            "package_name": package_metadata["name"],
            "package_version": package_metadata["version"],
            "cordis_version": cordis_dependency["version"],
            "package_lock_sha256": sha256_bytes(package_lock_path.read_bytes()),
        },
    }


def validate_runtime_package_provenance(
    provenance: dict[str, Any],
    request_sha256: str,
    lock_sha256: str,
    projection_sha256: str,
) -> None:
    schema_path = (
        ROOT / "packages/cordis-runtime/contracts/cordis_runtime_package_provenance.v1.schema.json"
    )
    jsonschema.Draft202012Validator(load_json(schema_path)).validate(provenance)
    _validate_sealed_artifact(provenance, "provenance_sha256", "runtime package provenance")
    expected = _runtime_package_expectations()
    for field, value in expected.items():
        if provenance.get(field) != value:
            raise ClosureError(
                f"runtime package provenance {field} does not match live package bytes"
            )
    if provenance["runtime_artifacts"] != {
        "request_sha256": request_sha256,
        "lock_sha256": lock_sha256,
        "profile_projection_sha256": projection_sha256,
    }:
        raise ClosureError("runtime package provenance does not bind the live runtime artifacts")


def artifact_identities() -> dict[str, str]:
    from tools.maintenance import runtime_composition_evidence_contract as evidence_contract
    from tools.maintenance import runtime_composition_projection_contract as projection_contract
    from tools.maintenance import runtime_host_batch_parity_contract as parity_contract
    from tools.maintenance import runtime_profile_projection_contract as profile_contract
    from tools.maintenance import simulation_composition_contract as manifest_contract

    request = load_json(FIXTURES / "default_runtime_composition_request.v1.json")
    lock = load_json(FIXTURES / "default_admitted_catalog_lock.v1.json")
    projection = load_json(FIXTURES / "default_runtime_profile_projection.v1.json")
    requested = load_json(FIXTURES / "default_compatibility_manifest.requested.json")
    resolved = load_json(FIXTURES / "default_compatibility_manifest.resolved.json")
    provenance = load_json(FIXTURES / "default_runtime_package_provenance.v1.json")
    evidence = load_json(FIXTURES / "default_runtime_composition_evidence.v1.json")
    parity = load_json(FIXTURES / "default_runtime_host_batch_parity.windows_msvc.v1.json")
    backend_request = load_json(FIXTURES / "default_backend_provider_request.v1.json")

    request_sha256 = projection_contract.request_identity(request)
    _require_no_issues(
        "catalog lock",
        projection_contract.validate_catalog_lock(lock, request=request),
    )
    lock_sha256 = projection_contract.catalog_lock_identity(lock)
    if lock["lock_sha256"] != lock_sha256:
        raise ClosureError("catalog lock identity does not match its canonical payload")

    _require_no_issues("requested manifest", manifest_contract.validate_manifest(requested))
    expected_resolved = manifest_contract.resolve_manifest(requested)
    if resolved != expected_resolved:
        raise ClosureError("resolved manifest is not the live resolution of the requested manifest")
    requested_sha256 = expected_resolved["requested_manifest_sha256"]
    resolved_sha256 = expected_resolved["resolved_manifest_sha256"]

    _require_no_issues(
        "profile projection",
        profile_contract.validate_profile_projection(
            projection, request, lock, requested, resolved
        ),
    )
    projection_sha256 = projection["projection_sha256"]
    backend_schema = load_json(
        ROOT / "src/runtime/contracts/composition/runtime_backend_provider_request.v1.schema.json"
    )
    jsonschema.Draft202012Validator(backend_schema).validate(backend_request)
    _require_no_issues(
        "composition evidence",
        evidence_contract.validate_evidence(
            evidence, request, lock, projection, backend_request, resolved
        ),
    )
    validate_runtime_package_provenance(provenance, request_sha256, lock_sha256, projection_sha256)
    try:
        parity_contract.validate_evidence(parity)
    except parity_contract.ParityError as error:
        raise ClosureError(f"host/batch parity evidence rejected: {error}") from error

    request_hashes = {
        request_sha256,
        lock["request_sha256"],
        projection["request_sha256"],
        provenance["runtime_artifacts"]["request_sha256"],
        evidence["runtime_request_sha256"],
        parity["producer"]["request_sha256"],
    }
    lock_hashes = {
        lock["lock_sha256"],
        projection["lock_sha256"],
        provenance["runtime_artifacts"]["lock_sha256"],
        evidence["catalog_lock_sha256"],
        parity["producer"]["lock_sha256"],
    }
    projection_hashes = {
        projection["projection_sha256"],
        provenance["runtime_artifacts"]["profile_projection_sha256"],
        evidence["profile_projection_sha256"],
        parity["producer"]["profile_projection_sha256"],
    }
    requested_hashes = {
        requested_sha256,
        resolved["requested_manifest_sha256"],
        evidence["requested_manifest_sha256"],
        parity["producer"]["requested_manifest_sha256"],
    }
    resolved_hashes = {
        resolved_sha256,
        resolved["resolved_manifest_sha256"],
        evidence["resolved_manifest_sha256"],
        parity["producer"]["resolved_manifest_sha256"],
    }
    if any(
        len(values) != 1
        for values in (
            request_hashes,
            lock_hashes,
            projection_hashes,
            requested_hashes,
            resolved_hashes,
        )
    ):
        raise ClosureError(
            "accepted request/lock/projection/manifest authority chain does not join"
        )
    if (
        parity["producer"]["package_provenance_sha256"] != provenance["provenance_sha256"]
        or parity["producer"]["dependency_graph_sha256"]
        != provenance["dependency_resolution"]["graph_sha256"]
        or parity["producer"]["native_admission_status"] != "validated"
        or parity["budget_evaluation"]["status"] != "pass"
        or parity["semantic_comparison"]["status"] != "exact_within_budget"
        or parity["semantic_comparison"]["mismatches"]
        or parity["node_host_status"] != "conditional_held_p6b_not_admitted"
    ):
        raise ClosureError("accepted Cordis/provenance/parity chain is not closed and fail-closed")
    security_entries = [
        entry
        for entry in lock["entries"]
        if entry["category"] == "security" and entry["owner_id"] == "owner.security"
    ]
    if len(security_entries) != 1 or security_entries[0]["provenance"]["artifact_kind"] != (
        "repository_builtin"
    ):
        raise ClosureError("bounded security admission is not repository-built and owner-owned")
    return {
        "request_sha256": request_sha256,
        "catalog_lock_sha256": lock_sha256,
        "profile_projection_sha256": projection_sha256,
        "requested_manifest_sha256": requested_sha256,
        "resolved_manifest_sha256": resolved_sha256,
        "composition_evidence_sha256": evidence["evidence_sha256"],
        "cordis_package_provenance_sha256": provenance["provenance_sha256"],
        "cordis_dependency_graph_sha256": provenance["dependency_resolution"]["graph_sha256"],
        "host_batch_budget_sha256": parity["budget"]["budget_sha256"],
        "host_batch_semantic_reference_sha256": parity["semantic_reference_sha256"],
        "host_batch_evidence_sha256": parity["evidence_sha256"],
        "request_schema_version": request["schema_version"],
        "manifest_schema_version": requested["schema_version"],
    }


def verify_source_truth() -> None:
    header = source_text("src/runtime/providers/default_simulation_provider_catalog.h")
    provider = source_text("src/runtime/providers/default_simulation_provider_catalog.cpp")
    kernel = source_text("src/core/engine/simulation_kernel.cpp")
    facade = source_text("src/runtime/facade/runtime_facade.cpp")
    backend_provider = source_text("src/runtime/facade/internal/world_batch_backend_provider.cpp")
    conformance = source_text("src/tests/test_cordis_runtime_conformance.cpp")
    bindings_core = source_text("src/interfaces/python/bindings_core.cpp")
    bindings_runtime = source_text("src/interfaces/python/bindings_runtime.cpp")
    flecs_backend = source_text("src/runtime/facade/internal/flecs_cpu_backend.cpp")
    smoke_test = source_text("src/tests/test_simulation_kernel_smoke.cpp")
    header_code = sanitize_cpp_source(header)
    provider_code = sanitize_cpp_source(provider)
    kernel_code = sanitize_cpp_source(kernel)
    facade_code = sanitize_cpp_source(facade)
    backend_provider_code = sanitize_cpp_source(backend_provider)
    conformance_code = sanitize_cpp_source(conformance)
    bindings_core_code = sanitize_cpp_source(bindings_core)
    bindings_runtime_code = sanitize_cpp_source(bindings_runtime)
    flecs_backend_code = sanitize_cpp_source(flecs_backend)
    smoke_test_code = sanitize_cpp_source(smoke_test)

    if re.search(r"\bresolved_manifest_json\s*=", header_code):
        raise ClosureError(
            "production composition builder still exposes an implicit empty fallback"
        )
    if cpp_has_implicit_manifest_fallback(provider):
        raise ClosureError(
            "production composition builder still treats empty input as fallback authority"
        )
    if len(re.findall(r"\bresolved_manifest_json\b", provider_code)) != 4:
        raise ClosureError(
            "shared native realizer must receive and consume explicit manifest bytes once"
        )
    if not re.search(
        r"\bconst\s+std::string\s+resolved_json\s*\(\s*resolved_manifest_json\s*\)\s*;",
        provider_code,
    ):
        raise ClosureError(
            "production composition builder no longer consumes the explicit manifest bytes"
        )
    if len(re.findall(r"\bSimulationKernel::SimulationKernel\s*\(\s*\)", kernel_code)) != 1:
        raise ClosureError("default kernel constructor definition count is not exactly one")
    if not cpp_has_default_manifest_alias(kernel):
        raise ClosureError(
            "default kernel construction is not an explicit canonical-manifest alias"
        )
    if (
        len(
            re.findall(
                r"\bbuild_default_simulation_composition\s*\(\s*SimulationKernel\s*&\s*kernel",
                provider_code,
            )
        )
        != 1
    ):
        raise ClosureError("production native composition builder count is not exactly one")
    if (
        len(
            re.findall(
                r"\bbuild_default_simulation_composition_impl\s*\(\s*SimulationKernel\s*&\s*kernel",
                provider_code,
            )
        )
        != 1
    ):
        raise ClosureError("shared native composition realizer count is not exactly one")
    if (
        len(re.findall(r"\bparse_resolved_composition_json\s*\(", provider_code)) != 1
        or len(re.findall(r"\bCompositionKernel\s*::\s*realize\s*\(", provider_code)) != 1
    ):
        raise ClosureError("native production and test-only builders no longer share one realizer")
    if not re.search(
        r"\bbuild_default_simulation_composition_impl\s*\(\s*kernel\s*,\s*world\s*,\s*"
        r"missile_tuning\s*,\s*rng\s*,\s*resolved_manifest_json\s*,\s*\{\s*\}\s*\)",
        provider_code,
    ):
        raise ClosureError(
            "production composition builder no longer delegates to the shared realizer"
        )
    if not re.search(
        r"\bbuild_default_simulation_composition_impl\s*\(\s*kernel\s*,\s*world\s*,\s*"
        r"missile_tuning\s*,\s*rng\s*,\s*resolved_json\s*,\s*fail_effect_provider\s*\)",
        provider_code,
    ):
        raise ClosureError("test-only fault injection no longer delegates to the shared realizer")
    searched = "\n".join(
        sanitize_cpp_source(source_text(path))
        for path in (
            "src/core/engine/simulation_kernel.h",
            "src/core/engine/simulation_kernel.cpp",
            "src/runtime/providers/default_simulation_provider_catalog.h",
            "src/runtime/providers/default_simulation_provider_catalog.cpp",
        )
    )
    present = [symbol for symbol in RETIRED_SETTERS if re.search(rf"\b{symbol}\s*\(", searched)]
    if present:
        raise ClosureError(f"retired composition setters returned: {', '.join(present)}")
    direct_factories = re.findall(
        r"\b(?:make_default_(?:environment|effects|sensor|acoustic|control|guidance)_model|"
        r"DefaultUnitFactory|SimulationKernelWeaponReleaseService)\b",
        kernel_code,
    )
    if direct_factories:
        raise ClosureError("SimulationKernel again contains concrete provider construction truth")
    if not re.search(
        r"\bmaterialize_default_world_batch_backend\s*\(\s*world_count\s*\)", facade_code
    ):
        raise ClosureError("RuntimeFacade no longer constructs through backend-provider admission")
    if re.search(r"\bmake_unique\s*<\s*FlecsCpuBackend\s*>", facade_code):
        raise ClosureError("RuntimeFacade again constructs the concrete CPU backend directly")
    if (
        len(
            re.findall(
                r"\bstd\s*::\s*make_unique\s*<\s*FlecsCpuBackend\s*>\s*"
                r"\(\s*world_count\s*\)",
                backend_provider_code,
            )
        )
        != 1
    ):
        raise ClosureError("default backend provider factory count is not exactly one")
    if not re.search(
        r"\bSimulationKernel\s+kernel\s*\(\s*resolved_manifest\s*\)\s*;", conformance_code
    ):
        raise ClosureError(
            "Cordis/native conformance no longer reaches explicit native realization"
        )
    if not scan_cpp_default_kernel_callers():
        raise ClosureError("native default-kernel callers disappeared from the retained inventory")
    explicit_kernel_callers = scan_cpp_explicit_kernel_callers()
    if explicit_kernel_callers:
        raise ClosureError(
            "unadmitted production explicit-manifest callers appeared: "
            + ", ".join(explicit_kernel_callers)
        )
    if not scan_cpp_runtime_facade_callers():
        raise ClosureError("native RuntimeFacade callers disappeared from the retained inventory")
    fault_injection_callers = scan_cpp_symbol_callers(
        "build_default_simulation_composition_for_testing",
        excluded_paths={
            "src/runtime/providers/default_simulation_provider_catalog.cpp",
            "src/runtime/providers/default_simulation_provider_catalog.h",
        },
    )
    if fault_injection_callers != ["src/core/engine/simulation_kernel.cpp"] or (
        len(re.findall(r"\bbuild_default_simulation_composition_for_testing\s*\(", kernel_code))
        != 1
    ) or (
        len(
            re.findall(
                r"\bprobe_default_provider_publication_failure_for_testing\s*\(",
                smoke_test_code,
            )
        )
        != 1
    ):
        raise ClosureError(
            "test-only fault-injection composition caller changed without disposition"
        )
    if not re.search(
        r"\bnb\s*::\s*class_\s*<\s*SimulationKernel\s*>\s+simulation_kernel\s*"
        r"\(\s*m\s*,\s*\)\s*;",
        bindings_core_code,
    ) or not re.search(
        r"\bsimulation_kernel\s*\.\s*def\s*\(\s*nb\s*::\s*init\s*<\s*>\s*"
        r"\(\s*\)\s*\)\s*;",
        bindings_core_code,
    ):
        raise ClosureError(
            "Python default-kernel compatibility exposure changed without disposition"
        )
    if not re.search(
        r"\bnb\s*::\s*class_\s*<\s*WorldBatchRuntime\s*>\s*\(\s*m\s*,\s*\)",
        bindings_runtime_code,
    ):
        raise ClosureError("Python world-batch compatibility exposure changed without disposition")
    if not re.search(
        r"\bnb\s*::\s*class_\s*<\s*RuntimeFacade\s*>\s*\(\s*m\s*,\s*\)",
        bindings_runtime_code,
    ):
        raise ClosureError("Python maintained-facade exposure changed without disposition")
    if not re.search(
        r"\bFlecsCpuBackend\s*::\s*FlecsCpuBackend\s*\(\s*std\s*::\s*size_t\s+"
        r"world_count\s*\)\s*:\s*runtime_\s*\(\s*world_count\s*\)",
        flecs_backend_code,
    ):
        raise ClosureError("admitted CPU backend no longer owns WorldBatchRuntime construction")


def build_record() -> dict[str, Any]:
    verify_source_truth()
    identities = artifact_identities()
    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "closure_id": "default_cpu_exact.runtime_composition.p8a",
        "closure_version": "1.0.0",
        "scope": {
            "profile_id": "builtin.default_compatibility",
            "backend_profile_id": "cpu_exact.reference",
            "execution_owner": "native_cpp",
            "status": "accepted_bounded_default_cpu_exact",
        },
        "authority_chain": identities,
        "truth_path": {
            "cordis_producer": "@echelon-forge/cordis-runtime",
            "native_manifest_constructor": "SimulationKernel(std::string resolved_manifest_json)",
            "native_composition_builder": "runtime::providers::build_default_simulation_composition",
            "native_shared_realizer": (
                "runtime::providers::build_default_simulation_composition_impl"
            ),
            "default_compatibility_artifact": (
                "runtime::providers::default_compatibility_resolved_manifest_json"
            ),
            "backend_materializer": (
                "runtime::backend_provider::materialize_default_world_batch_backend"
            ),
            "native_execution_owner": "SimulationKernel::step",
        },
        "caller_inventory": [
            {
                "surface_id": "runtime_facade.maintained_host",
                "classification": "maintained_host",
                "owner": "runtime/facade",
                "callers": scan_python_callers("RuntimeFacade"),
                "disposition": "retained; routes through admitted backend provider",
            },
            {
                "surface_id": "runtime_facade.native_internal_callers",
                "classification": "maintained_native_internal",
                "owner": "runtime/facade",
                "callers": scan_cpp_runtime_facade_callers(),
                "disposition": (
                    "retained; nested counterfactual worlds re-enter the admitted backend provider"
                ),
            },
            {
                "surface_id": "simulation_kernel.default_compatibility",
                "classification": "compatibility_and_diagnostics",
                "owner": "core/engine",
                "callers": scan_python_callers("SimulationKernel"),
                "disposition": "retained; explicit alias of the generated resolved manifest",
            },
            {
                "surface_id": "simulation_kernel.native_default_callers",
                "classification": "standalone_and_batch_compatibility",
                "owner": "core/engine",
                "callers": scan_cpp_default_kernel_callers(),
                "disposition": "retained; both enter the explicit generated-manifest alias",
            },
            {
                "surface_id": "simulation_kernel.python_binding_exposure",
                "classification": "compatibility_binding",
                "owner": "interfaces/python",
                "callers": ["src/interfaces/python/bindings_core.cpp"],
                "disposition": "retained for established low-level and diagnostics callers",
            },
            {
                "surface_id": "world_batch_runtime.native_backend_owner",
                "classification": "native_backend_internal",
                "owner": "runtime/backend",
                "callers": ["src/runtime/facade/internal/flecs_cpu_backend.cpp"],
                "disposition": "retained behind the admitted Flecs CPU backend provider",
            },
            {
                "surface_id": "world_batch_runtime.python_binding_exposure",
                "classification": "compatibility_binding",
                "owner": "interfaces/python",
                "callers": ["src/interfaces/python/bindings_runtime.cpp"],
                "disposition": "retained for bounded low-level compatibility and diagnostics",
            },
            {
                "surface_id": "runtime_facade.python_binding_exposure",
                "classification": "maintained_binding",
                "owner": "interfaces/python",
                "callers": ["src/interfaces/python/bindings_runtime.cpp"],
                "disposition": "retained maintained Python host entry",
            },
            {
                "surface_id": "simulation_kernel.explicit_manifest",
                "classification": "cordis_native_bridge",
                "owner": "architecture/runtime-composition",
                "callers": ["src/tests/test_cordis_runtime_conformance.cpp"],
                "disposition": "maintained conformance bridge; validates before native realization",
            },
            {
                "surface_id": "simulation_kernel.test_fault_injection",
                "classification": "test_only_fault_injection",
                "owner": "core/engine",
                "callers": scan_cpp_symbol_callers(
                    "probe_default_provider_publication_failure_for_testing",
                    excluded_paths={
                        "src/core/engine/simulation_kernel.cpp",
                        "src/core/engine/simulation_kernel.h",
                    },
                ),
                "disposition": (
                    "retained test-only rollback seam; shares the single native realizer"
                ),
            },
        ],
        "retired_surfaces": [
            {
                "surface_id": "simulation_kernel.model_replacement_setters",
                "status": "absent",
                "symbols": list(RETIRED_SETTERS),
            },
            {
                "surface_id": "simulation_kernel.concrete_provider_construction",
                "status": "absent",
                "symbols": [
                    "make_default_environment_model",
                    "make_default_effects_model",
                    "make_default_sensor_model",
                    "make_default_acoustic_model",
                    "make_default_control_model",
                    "make_default_guidance_model",
                    "DefaultUnitFactory",
                    "SimulationKernelWeaponReleaseService",
                ],
            },
            {
                "surface_id": "runtime_facade.concrete_backend_construction",
                "status": "absent",
                "symbols": ["std::make_unique<FlecsCpuBackend>"],
            },
            {
                "surface_id": "native_builder.empty_manifest_fallback",
                "status": "absent",
                "symbols": ["resolved_manifest_json = {}", "if (resolved_manifest_json.empty())"],
            },
        ],
        "acceptance_matrix": [
            {"cluster": "P0-A", "state": "accepted", "evidence": "authority scaffold"},
            {"cluster": "P1-A", "state": "accepted", "evidence": "composition census"},
            {"cluster": "P1-B", "state": "accepted", "evidence": "manifest and resolver contract"},
            {"cluster": "P2-A", "state": "accepted", "evidence": "native lifecycle substrate"},
            {"cluster": "P2-B", "state": "accepted", "evidence": "default provider migration"},
            {"cluster": "P2-C0", "state": "accepted", "evidence": "request and catalog lock"},
            {
                "cluster": "P2-C1",
                "state": "accepted",
                "evidence": "Cordis/native vertical conformance",
            },
            {"cluster": "P3-A", "state": "accepted", "evidence": "owner-derived system graph"},
            {"cluster": "P3-B", "state": "accepted", "evidence": "default profile projection"},
            {"cluster": "P4-A", "state": "accepted", "evidence": "default backend provider"},
            {"cluster": "P5-A", "state": "accepted", "evidence": "sealed composition evidence"},
            {"cluster": "P6-A", "state": "accepted", "evidence": "repository Cordis package"},
            {"cluster": "P6-B", "state": "held", "evidence": "explicit Node host decision absent"},
            {"cluster": "P7-A", "state": "accepted", "evidence": "host and batch parity"},
            {"cluster": "P8-A", "state": "accepted", "evidence": "migration closure record"},
        ],
        "residuals": [
            {
                "residual_id": "node_host_adapter",
                "state": "held",
                "owner": "interfaces/node",
                "activation_gate": "explicit approved Node host use case and P6-B dispatch",
            },
            {
                "residual_id": "broader_profiles_and_providers",
                "state": "held",
                "owner": "architecture/runtime-composition",
                "activation_gate": "owner admission plus profile/provider parity evidence",
            },
            {
                "residual_id": "cuda_backend_parity",
                "state": "held",
                "owner": "runtime/backend",
                "activation_gate": "separate exact-runtime CUDA admission and parity gate",
            },
            {
                "residual_id": "external_plugin_distribution_and_signing",
                "state": "held",
                "owner": "owner.security",
                "activation_gate": "artifact authenticity, ABI, distribution, and trust policy",
            },
            {
                "residual_id": "complete_state_replay",
                "state": "held",
                "owner": "runtime/evidence",
                "activation_gate": "state-complete replay contract beyond composition compatibility",
            },
        ],
        "canonicalization": CANONICALIZATION,
        "hash_algorithm": "sha256",
    }
    sealed = canonical_json(body)
    return {**body, "canonical_json": sealed, "closure_sha256": sha256_text(sealed)}


def validate_record(record: dict[str, Any]) -> None:
    jsonschema.Draft202012Validator(load_json(SCHEMA_PATH)).validate(record)
    body = copy.deepcopy(record)
    canonical = body.pop("canonical_json")
    digest = body.pop("closure_sha256")
    expected_canonical = canonical_json(body)
    if canonical != expected_canonical:
        raise ClosureError("closure canonical_json is not the canonical record payload")
    if digest != sha256_text(canonical):
        raise ClosureError("closure_sha256 does not seal canonical_json")
    expected = build_record()
    if record != expected:
        raise ClosureError(
            "closure record is stale or does not match the live caller/truth inventory"
        )


def write_record(path: Path) -> dict[str, Any]:
    record = build_record()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    generate = subparsers.add_parser("generate")
    generate.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    validate = subparsers.add_parser("validate")
    validate.add_argument("--closure", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if args.command == "generate":
        record = write_record(args.output)
        print(record["closure_sha256"])
        return 0
    record = load_json(args.closure)
    validate_record(record)
    print(record["closure_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
