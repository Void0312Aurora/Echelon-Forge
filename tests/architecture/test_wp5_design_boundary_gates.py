from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_CONTRACTS = REPO_ROOT / "src" / "runtime" / "contracts"
RUNTIME_FACADE = REPO_ROOT / "src" / "runtime" / "facade"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _strip_line_comment(line: str) -> str:
    return line.split("//", 1)[0].strip()


def test_maintained_facade_request_result_headers_do_not_include_engine_owners() -> None:
    headers = [
        *RUNTIME_CONTRACTS.glob("*.h"),
        RUNTIME_FACADE / "runtime_facade_types.h",
    ]
    violations: list[tuple[str, int, str]] = []

    for path in headers:
        for lineno, line in enumerate(_read(path).splitlines(), start=1):
            stripped = _strip_line_comment(line)
            if not stripped.startswith("#include"):
                continue
            if '"core/engine/' in stripped or "world_batch_runtime" in stripped:
                violations.append((str(path.relative_to(REPO_ROOT)), lineno, stripped))

    assert not violations, f"maintained request/result headers include engine owners: {violations}"


def test_facade_contract_and_types_headers_do_not_name_runtime_owner_types() -> None:
    headers = [
        *RUNTIME_CONTRACTS.glob("*.h"),
        RUNTIME_FACADE / "runtime_facade_types.h",
    ]
    forbidden = ("WorldBatchRuntime", "SimulationKernel")
    violations: list[tuple[str, int, str]] = []

    for path in headers:
        for lineno, line in enumerate(_read(path).splitlines(), start=1):
            stripped = _strip_line_comment(line)
            if any(token in stripped for token in forbidden):
                violations.append((str(path.relative_to(REPO_ROOT)), lineno, stripped))

    assert not violations, f"facade contract/type headers expose runtime owner types: {violations}"


def test_runtime_facade_header_limits_world_batch_runtime_to_escape_hatch_and_private_owner() -> None:
    header = _read(RUNTIME_FACADE / "runtime_facade.h")

    assert '#include "core/engine/world_batch_runtime.h"' not in header
    assert "class WorldBatchRuntime;" in header
    assert "Compatibility escape hatch for diagnostics and legacy adapters only." in header
    assert "Maintained frontends should use facade-level request/result APIs instead." in header

    public_section = header.split("public:", 1)[1].split("private:", 1)[0]
    public_owner_lines = [
        _strip_line_comment(line)
        for line in public_section.splitlines()
        if "WorldBatchRuntime" in _strip_line_comment(line)
    ]
    assert public_owner_lines == [
        "WorldBatchRuntime& runtime_compatibility_quarantine() noexcept;",
        "const WorldBatchRuntime& runtime_compatibility_quarantine() const noexcept;",
    ]

    private_section = header.split("private:", 1)[1]
    assert "std::unique_ptr<WorldBatchRuntime> runtime_;" in private_section


def test_runtime_facade_docs_do_not_describe_raw_runtime_as_maintained_path() -> None:
    readme_en = _read(RUNTIME_FACADE / "README.md")
    readme_zh = _read(RUNTIME_FACADE / "README.zh.md")

    assert "compatibility/diagnostics escape hatch" in readme_en
    assert "new mainline code should not depend on it" in readme_en
    assert "must centralize access in an explicit adapter" in readme_en
    assert "must not call `RuntimeFacade.runtime_compatibility_quarantine()` directly" in readme_en
    assert "should also not cache the raw `WorldBatchRuntime`" in readme_en

    assert "compatibility / diagnostics 逃逸口" in readme_zh
    assert "新主线代码不应依赖它" in readme_zh
    assert "必须把访问集中在一个显式 adapter" in readme_zh
    assert "不得直接调用 `RuntimeFacade.runtime_compatibility_quarantine()`" in readme_zh
    assert "不应缓存 raw `WorldBatchRuntime`" in readme_zh


def test_no_broad_direct_sim_ban_is_encoded_in_architecture_tests() -> None:
    current_file = Path(__file__).resolve()
    architecture_tests = "\n".join(
        _read(path)
        for path in sorted((REPO_ROOT / "tests" / "architecture").glob("test_*.py"))
        if path.resolve() != current_file
    )

    broad_patterns = [
        r"sim\.\*",
        r"direct\s+sim\.\*",
        r"forbid(?:s|den)?\s+.*sim\.",
        r"ban(?:s|ned)?\s+.*sim\.",
    ]
    offenders = [
        pattern
        for pattern in broad_patterns
        if re.search(pattern, architecture_tests, flags=re.IGNORECASE)
    ]

    assert not offenders, f"broad direct sim.* ban should wait for allowlists: {offenders}"
