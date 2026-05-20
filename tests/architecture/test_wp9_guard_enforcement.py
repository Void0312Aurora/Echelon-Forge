from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ALLOWLIST_EVIDENCE_DOC = (
    REPO_ROOT
    / "docs"
    / "task"
    / "simulation_architecture"
    / "wp9_contract_infrastructure_closure"
    / "wp9_guard_allowlist_evidence_20260520.md"
)

# The allowlist stays explicit and label-driven so the guard can distinguish
# compatibility-only bridges, diagnostics-only evidence, and test-only fixtures.
SIM_DIRECT_ACCESS_ALLOWLIST = {
    "compatibility_only": {
        "files": {
            "python/rl/control/wrappers.py",
            "python/rl/runtime/cooperative_world_batch_vec_env.py",
            "python/rl/runtime/leader_world_batch_runtime.py",
            "python/rl/runtime/single_world_batch_runtime.py",
            "python/rl/runtime/world_batch/cooperative_director.py",
            "python/rl/runtime/world_batch/runtime_access.py",
            "python/rl/runtime/world_batch_vec_env.py",
            "python/rl/tasking/leader_tasking.py",
            "python/scenario/runtime/kernel_apply.py",
            "game/backend/app.py",
        },
        "prefixes": {
            "gym_envs/",
            "game/backend/",
        },
    },
    "diagnostics_only": {
        "prefixes": {
            "python/testing/contracts/",
            "examples/viz/runtime/",
            "tools/diagnostics/",
            "tools/eval/",
        },
        "files": {
            "world_model_train.py",
        },
    },
    "test_only": {
        "prefixes": {
            "tests/",
        },
    },
}


def _iter_python_files() -> list[Path]:
    excluded_prefixes = (".git", ".venv", "__pycache__", "build", "dist", "node_modules", "archive", "temp")
    return [
        path
        for path in sorted(REPO_ROOT.rglob("*.py"))
        if not any(part.startswith(excluded_prefixes) for part in path.parts)
    ]


def _attribute_chain(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Attribute):
        return _attribute_chain(node.value) + [node.attr]
    if isinstance(node, ast.Call):
        return _attribute_chain(node.func)
    if isinstance(node, ast.Name):
        return [node.id]
    return []


def _sim_access_lines(path: Path) -> list[int]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    lines: list[int] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            chain = _attribute_chain(node)
            if len(chain) > 1 and "sim" in chain:
                lines.append(int(getattr(node, "lineno", 0) or 0))
    return sorted(set(line for line in lines if line > 0))


def _label_for_path(relative_path: str) -> str | None:
    for label, spec in SIM_DIRECT_ACCESS_ALLOWLIST.items():
        if relative_path in spec.get("files", set()):
            return label
    for label, spec in SIM_DIRECT_ACCESS_ALLOWLIST.items():
        for prefix in spec.get("prefixes", set()):
            if relative_path.startswith(prefix):
                return label
    return None


def test_direct_sim_access_is_limited_to_explicitly_labeled_allowlists() -> None:
    hits: dict[str, tuple[str, list[int]]] = {}

    for path in _iter_python_files():
        lines = _sim_access_lines(path)
        if not lines:
            continue

        relative_path = str(path.relative_to(REPO_ROOT))
        label = _label_for_path(relative_path)
        if label is None:
            hits[relative_path] = ("unlabeled", lines)
            continue

        hits[relative_path] = (label, lines)

    violations = {
        path: lines
        for path, (label, lines) in hits.items()
        if label == "unlabeled"
    }
    assert not violations, f"direct sim access without allowlist labels: {violations}"

    used_labels = {label for label, _ in hits.values() if label != "unlabeled"}
    assert used_labels == set(SIM_DIRECT_ACCESS_ALLOWLIST), (
        "allowlist labels should be exercised by live direct sim access files; "
        f"got {sorted(used_labels)}"
    )

    for label, spec in SIM_DIRECT_ACCESS_ALLOWLIST.items():
        assert spec.get("files", set()) or spec.get("prefixes", set()), f"empty allowlist for {label}"


def test_wp9_guard_allowlist_evidence_doc_matches_the_explicit_labels() -> None:
    text = ALLOWLIST_EVIDENCE_DOC.read_text(encoding="utf-8")

    for label in ("compatibility_only", "diagnostics_only", "test_only"):
        assert label in text

    for path in (
        "python/rl/runtime/world_batch/runtime_access.py",
        "python/testing/contracts/",
        "tests/",
    ):
        assert path in text
