from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


class EvidenceError(ValueError):
    pass


@dataclass(frozen=True)
class KernelSpec:
    kernel_id: str
    symbol_fragment: str
    launch_count: int


CONTRACT_PATH = (
    Path(__file__).resolve().parents[2]
    / "src/runtime/contracts/cuda_resident_resource_evidence_contract.h"
)

_KERNEL_ENTRY_RE = re.compile(r'\{"([a-z0-9_]+)",\s*"([a-z0-9_]+)",\s*(\d+)\}')
_LAUNCH_ENTRY_RE = re.compile(r'\{(\d+),\s*"([a-z0-9_]+)",\s*"([a-z0-9_]+)"\}')


def _contract_text() -> str:
    try:
        return CONTRACT_PATH.read_text(encoding="utf-8")
    except OSError as error:  # pragma: no cover - environment fault
        raise EvidenceError(f"kernel resource contract is unreadable: {error}") from error


def _contract_array(array_name: str, element_type: str) -> str:
    text = _contract_text()
    marker = f"inline constexpr auto {array_name} = std::to_array<{element_type}>({{"
    start = text.find(marker)
    if start < 0:
        raise EvidenceError(f"kernel resource contract does not declare {array_name}")
    end = text.find("});", start)
    if end < 0:
        raise EvidenceError(f"{array_name} in the resource contract is unterminated")
    return text[start:end]


def _parse_catalog(array_name: str) -> tuple[KernelSpec, ...]:
    """Read one kernel catalog out of the C++ evidence contract.

    The contract is the single owner of the kernel catalog. This module used to
    keep its own copy, which is precisely how it went stale when the semantic
    stage migration renamed the kernels: the C++ side moved and nothing forced
    the Python side to follow. Parsing keeps one owner instead of two.
    """
    specs = tuple(
        KernelSpec(kernel_id, symbol_fragment, int(launch_count))
        for kernel_id, symbol_fragment, launch_count in _KERNEL_ENTRY_RE.findall(
            _contract_array(array_name, "KernelSpec")
        )
    )
    if not specs:
        raise EvidenceError(f"{array_name} in the resource contract parsed to no kernels")
    if len({spec.kernel_id for spec in specs}) != len(specs):
        raise EvidenceError(f"{array_name} in the resource contract has duplicate kernel ids")
    return specs


def _parse_launch_sequence(array_name: str) -> tuple[tuple[str, str], ...]:
    """Read one launch sequence out of the contract, ordered by launch index."""
    rows = [
        (int(index), kernel_id, stage)
        for index, kernel_id, stage in _LAUNCH_ENTRY_RE.findall(
            _contract_array(array_name, "LaunchSpec")
        )
    ]
    if not rows:
        raise EvidenceError(f"{array_name} in the resource contract parsed to no launches")
    rows.sort()
    if [index for index, _, _ in rows] != list(range(len(rows))):
        raise EvidenceError(f"{array_name} in the resource contract has non-contiguous indices")
    return tuple((kernel_id, stage) for _, kernel_id, stage in rows)


@lru_cache(maxsize=None)
def kernel_catalog(schema_version: int) -> tuple[KernelSpec, ...]:
    """Kernel catalog for a capture schema version.

    v1 describes the pre-rename binary and stays available so the retained
    static-capture evidence remains verifiable. v2 is the current catalog.
    """
    if schema_version == 1:
        return _parse_catalog("kKernelSpecs")
    if schema_version == 2:
        return _parse_catalog("kKernelSpecsV2")
    raise EvidenceError(f"unknown kernel catalog schema version: {schema_version}")


@lru_cache(maxsize=None)
def launch_sequence(schema_version: int) -> tuple[tuple[str, str], ...]:
    """Expected (kernel_id, semantic_stage) launch order for a schema version."""
    if schema_version == 1:
        return _parse_launch_sequence("kLaunchSequence")
    if schema_version == 2:
        return _parse_launch_sequence("kLaunchSequenceV2")
    raise EvidenceError(f"unknown launch sequence schema version: {schema_version}")


# Retained name for the v1 validators in this module and its callers. New code
# should ask for a version explicitly via kernel_catalog().
KERNELS = kernel_catalog(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise EvidenceError(message)


def kernel_id(symbol: str, schema_version: int = 1) -> str:
    catalog = kernel_catalog(schema_version)
    matches = [spec.kernel_id for spec in catalog if spec.symbol_fragment in symbol]
    require(len(matches) == 1, f"kernel symbol is unknown or ambiguous: {symbol}")
    return matches[0]


def parse_ptxas(text: str, schema_version: int = 1) -> dict[str, dict[str, int]]:
    catalog = kernel_catalog(schema_version)
    cap_values = {int(value) for value in re.findall(r"-maxrregcount(?:=|\s+)(\d+)", text)}
    require(cap_values == {0}, "ptxas build must contain only the explicit no-cap argument")
    entries = list(re.finditer(r"Compiling entry function '([^']+)' for '([^']+)'", text))
    parsed: dict[str, dict[str, int]] = {}
    for index, match in enumerate(entries):
        symbol = match.group(1)
        matching = [spec for spec in catalog if spec.symbol_fragment in symbol]
        if not matching:
            continue
        require(len(matching) == 1, f"ambiguous ptxas kernel symbol: {symbol}")
        require(match.group(2) == "sm_86", f"ptxas architecture drift for {matching[0].kernel_id}")
        block_end = entries[index + 1].start() if index + 1 < len(entries) else len(text)
        block = text[match.end() : block_end]
        properties = re.search(
            r"(\d+) bytes stack frame, (\d+) bytes spill stores, (\d+) bytes spill loads",
            block,
        )
        registers = re.search(r"Used (\d+) registers", block)
        require(properties is not None, f"ptxas properties missing for {matching[0].kernel_id}")
        require(registers is not None, f"ptxas registers missing for {matching[0].kernel_id}")
        row = {
            "registers_per_thread": int(registers.group(1)),
            "stack_frame_bytes": int(properties.group(1)),
            "spill_store_bytes": int(properties.group(2)),
            "spill_load_bytes": int(properties.group(3)),
        }
        previous = parsed.setdefault(matching[0].kernel_id, row)
        require(previous == row, f"conflicting ptxas records for {matching[0].kernel_id}")
    require(set(parsed) == {spec.kernel_id for spec in catalog}, "ptxas kernel set incomplete")
    return parsed


def parse_cuobjdump_resources(text: str, schema_version: int = 1) -> dict[str, dict[str, int]]:
    catalog = kernel_catalog(schema_version)
    pattern = re.compile(
        r"Function\s+(\S+):\s+REG:(\d+) STACK:(\d+) SHARED:(\d+) LOCAL:(\d+)",
        re.MULTILINE,
    )
    parsed: dict[str, dict[str, int]] = {}
    for match in pattern.finditer(text):
        symbol = match.group(1)
        if not any(spec.symbol_fragment in symbol for spec in catalog):
            continue
        identifier = kernel_id(symbol, schema_version)
        row = {
            "registers_per_thread": int(match.group(2)),
            "stack_frame_bytes": int(match.group(3)),
            "static_shared_bytes": int(match.group(4)),
            "local_bytes": int(match.group(5)),
        }
        previous = parsed.setdefault(identifier, row)
        require(previous == row, f"conflicting cuobjdump records for {identifier}")
    require(set(parsed) == {spec.kernel_id for spec in catalog}, "cuobjdump kernel set incomplete")
    return parsed


def parse_sass(text: str, schema_version: int = 1) -> dict[str, dict[str, int]]:
    catalog = kernel_catalog(schema_version)
    headers = list(re.finditer(r"Function\s+:\s+(\S+)", text))
    parsed: dict[str, dict[str, int]] = {}
    for index, match in enumerate(headers):
        symbol = match.group(1)
        if not any(spec.symbol_fragment in symbol for spec in catalog):
            continue
        end = headers[index + 1].start() if index + 1 < len(headers) else len(text)
        block = text[match.end() : end]
        row = {
            "ldl_instruction_count": len(re.findall(r"\bLDL(?:\.\w+)?\b", block)),
            "stl_instruction_count": len(re.findall(r"\bSTL(?:\.\w+)?\b", block)),
        }
        identifier = kernel_id(symbol, schema_version)
        previous = parsed.setdefault(identifier, row)
        require(previous == row, f"conflicting SASS records for {identifier}")
    require(set(parsed) == {spec.kernel_id for spec in catalog}, "SASS kernel set incomplete")
    return parsed
