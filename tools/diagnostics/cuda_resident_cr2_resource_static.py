from __future__ import annotations

import re
from dataclasses import dataclass


class EvidenceError(ValueError):
    pass


@dataclass(frozen=True)
class KernelSpec:
    kernel_id: str
    symbol_fragment: str
    launch_count: int


KERNELS = (
    KernelSpec("apply_barrier", "apply_barrier_kernel", 3),
    KernelSpec("phase_a_controls", "prepare_phase_a_controls_kernel", 1),
    KernelSpec("phase_b_forces", "phase_b_forces_kernel", 1),
    KernelSpec("phase_b_aerodynamics", "phase_b_aerodynamics_kernel", 1),
    KernelSpec("phase_b_integrate", "phase_b_integrate_kernel", 1),
    KernelSpec("phase_d_instruments", "phase_d_instruments_kernel", 1),
    KernelSpec("phase_d_configuration", "phase_d_configuration_kernel", 1),
    KernelSpec("phase_d_projection", "phase_d_episode_kernel", 1),
    KernelSpec("phase_d_pack", "phase_d_pack_observation_kernel", 1),
    KernelSpec("phase_d_consumer", "phase_d_consumer_smoke_kernel", 1),
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise EvidenceError(message)


def kernel_id(symbol: str) -> str:
    matches = [spec.kernel_id for spec in KERNELS if spec.symbol_fragment in symbol]
    require(len(matches) == 1, f"kernel symbol is unknown or ambiguous: {symbol}")
    return matches[0]


def parse_ptxas(text: str) -> dict[str, dict[str, int]]:
    cap_values = {int(value) for value in re.findall(r"-maxrregcount(?:=|\s+)(\d+)", text)}
    require(cap_values == {0}, "ptxas build must contain only the explicit no-cap argument")
    entries = list(re.finditer(r"Compiling entry function '([^']+)' for '([^']+)'", text))
    parsed: dict[str, dict[str, int]] = {}
    for index, match in enumerate(entries):
        symbol = match.group(1)
        matching = [spec for spec in KERNELS if spec.symbol_fragment in symbol]
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
    require(set(parsed) == {spec.kernel_id for spec in KERNELS}, "ptxas kernel set incomplete")
    return parsed


def parse_cuobjdump_resources(text: str) -> dict[str, dict[str, int]]:
    pattern = re.compile(
        r"Function\s+(\S+):\s+REG:(\d+) STACK:(\d+) SHARED:(\d+) LOCAL:(\d+)",
        re.MULTILINE,
    )
    parsed: dict[str, dict[str, int]] = {}
    for match in pattern.finditer(text):
        symbol = match.group(1)
        if not any(spec.symbol_fragment in symbol for spec in KERNELS):
            continue
        identifier = kernel_id(symbol)
        row = {
            "registers_per_thread": int(match.group(2)),
            "stack_frame_bytes": int(match.group(3)),
            "static_shared_bytes": int(match.group(4)),
            "local_bytes": int(match.group(5)),
        }
        previous = parsed.setdefault(identifier, row)
        require(previous == row, f"conflicting cuobjdump records for {identifier}")
    require(set(parsed) == {spec.kernel_id for spec in KERNELS}, "cuobjdump kernel set incomplete")
    return parsed


def parse_sass(text: str) -> dict[str, dict[str, int]]:
    headers = list(re.finditer(r"Function\s+:\s+(\S+)", text))
    parsed: dict[str, dict[str, int]] = {}
    for index, match in enumerate(headers):
        symbol = match.group(1)
        if not any(spec.symbol_fragment in symbol for spec in KERNELS):
            continue
        end = headers[index + 1].start() if index + 1 < len(headers) else len(text)
        block = text[match.end() : end]
        row = {
            "ldl_instruction_count": len(re.findall(r"\bLDL(?:\.\w+)?\b", block)),
            "stl_instruction_count": len(re.findall(r"\bSTL(?:\.\w+)?\b", block)),
        }
        identifier = kernel_id(symbol)
        previous = parsed.setdefault(identifier, row)
        require(previous == row, f"conflicting SASS records for {identifier}")
    require(set(parsed) == {spec.kernel_id for spec in KERNELS}, "SASS kernel set incomplete")
    return parsed
