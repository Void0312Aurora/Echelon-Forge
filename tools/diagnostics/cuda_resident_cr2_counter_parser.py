from __future__ import annotations

import csv
import hashlib
import io
import math
import re
import subprocess
from pathlib import Path
from typing import Any

if __package__:
    from .cuda_resident_cr2_resource_static import (
        kernel_catalog as _kernel_catalog,
        launch_sequence as _launch_sequence,
    )
else:
    from cuda_resident_cr2_resource_static import (  # type: ignore[no-redef]
        kernel_catalog as _kernel_catalog,
        launch_sequence as _launch_sequence,
    )


COUNTER_FAMILIES = {
    "achieved_occupancy": "ratio",
    "branch_divergence": "ratio",
    "global_memory_traffic": "bytes",
    "local_memory_traffic": "bytes",
    "shared_memory_traffic": "bytes",
}
# The frozen v1 evidence records `bytes` for the three memory families, from a
# capture that never produced a value. A real capture records the unit Nsight
# Compute itself declares for the metrics collected, which is `sector` for the
# global/local sector counters and `wavefront` for shared. The sector-to-byte
# conversion is deliberately NOT applied: it would require asserting a sector
# width this collector cannot read back from the report, and a derived byte
# figure would be an inference presented as a measurement.
#
# v1 stays exactly as frozen; only a capture that actually carries values
# declares the measured units. Keyed by resource-evidence generation.
COUNTER_FAMILY_UNITS = {
    1: dict(COUNTER_FAMILIES),
    2: {
        "achieved_occupancy": "ratio",
        "branch_divergence": "ratio",
        "global_memory_traffic": "sector",
        "local_memory_traffic": "sector",
        "shared_memory_traffic": "wavefront",
    },
    # The CP-5 fused window graph collects the same metric set as v2; only the
    # launch topology changed, and that is derived from the contract below.
    3: {
        "achieved_occupancy": "ratio",
        "branch_divergence": "ratio",
        "global_memory_traffic": "sector",
        "local_memory_traffic": "sector",
        "shared_memory_traffic": "wavefront",
    },
}


def required_launch_count(schema_version: int) -> int:
    """Every launch of the generation's captured window graph.

    Derived from the contract launch sequence rather than pinned, so a new
    execution-graph generation never re-pins launch counts anywhere in the
    counter chain -- the drift class CP-4c paid for. A new generation still
    registers its identity in the schema module and its measured-unit map in
    COUNTER_FAMILY_UNITS above, once each.
    """
    return len(_launch_sequence(schema_version))


def command_template(launch_count: int) -> tuple[str, ...]:
    """The frozen capture invocation, parameterized only by launch count.

    A counter capture profiles every launch of its parent generation's window
    graph, so the count follows that generation rather than being pinned here.
    """
    return (
        "ncu",
        "--target-processes=application-only",
        "--profile-from-start=off",
        "--replay-mode=kernel",
        "--kernel-name-base=demangled",
        "--set=full",
        f"--launch-count={launch_count}",
        "--force-overwrite",
        "--export=<raw>/full-window-256",
        "--log-file=<raw>/attempt.log",
        "<resource-probe>",
        "--output=<raw>/probe-output.json",
    )


COUNTER_METRICS: dict[str, tuple[tuple[str, ...], str]] = {
    "achieved_occupancy": (("sm__warps_active.avg.pct_of_peak_sustained_active",), "%"),
    "branch_divergence": (("smsp__thread_inst_executed_per_inst_executed.ratio",), ""),
    "global_memory_traffic": (
        (
            "l1tex__t_sectors_pipe_lsu_mem_global_op_ld.sum",
            "l1tex__t_sectors_pipe_lsu_mem_global_op_st.sum",
        ),
        "sector",
    ),
    "local_memory_traffic": (
        (
            "l1tex__t_sectors_pipe_lsu_mem_local_op_ld.sum",
            "l1tex__t_sectors_pipe_lsu_mem_local_op_st.sum",
        ),
        "sector",
    ),
    "shared_memory_traffic": (
        ("l1tex__data_pipe_lsu_wavefronts_mem_shared.sum",),
        "",
    ),
}
# Warp width on every CUDA architecture this program targets. Used only to turn
# the threads-per-instruction-executed ratio into a 0..1 convergence fraction,
# because the family contract requires a ratio in that range. A value of 32
# threads per executed instruction means full convergence, i.e. 1.0.
WARP_LANES = 32
CSV_IDENTITY_COLUMNS = ("ID", "Kernel Name", "Block Size", "Grid Size")
PERMISSION_CODE = "ERR_NVGPUCTRPERM"


class CounterParseError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CounterParseError(message)


def _csv_number(raw: object, label: str) -> float:
    text = str(raw).strip().replace(",", "")
    _require(bool(text), f"{label} is empty in the Nsight Compute report")
    try:
        value = float(text)
    except ValueError as error:
        raise CounterParseError(f"{label} is not numeric: {text!r}") from error
    _require(math.isfinite(value), f"{label} is not finite")
    return value


def parse_attempt_log(text: str) -> dict[str, Any]:
    """Extract process lifecycle and stable error codes from an NCU log."""
    connected = re.findall(r"^==PROF== Connected to process (\d+) ", text, flags=re.MULTILINE)
    disconnected = re.findall(
        r"^==PROF== Disconnected from process (\d+)\s*$", text, flags=re.MULTILINE
    )
    error_lines = re.findall(r"^==ERROR== ([^\r\n]+)$", text, flags=re.MULTILINE)
    error_codes: list[str] = []
    for line in error_lines:
        match = re.match(r"([A-Z][A-Z0-9_]+)\b", line)
        _require(match is not None, "Nsight Compute error line has no stable code")
        error_codes.append(match.group(1))
    permission_lines = [line for line in error_lines if line.startswith(f"{PERMISSION_CODE} ")]
    permission_message = "does not have permission to access NVIDIA GPU Performance Counters"
    permission_denied = (
        len(permission_lines) == 1
        and permission_message in permission_lines[0]
        and error_codes == [PERMISSION_CODE]
    )
    return {
        "connected_pids": [int(value) for value in connected],
        "disconnected_pids": [int(value) for value in disconnected],
        "error_codes": error_codes,
        "permission_denied": permission_denied,
        "permission_line_sha256": (
            hashlib.sha256(permission_lines[0].encode("utf-8")).hexdigest()
            if permission_denied
            else None
        ),
    }


def empty_counter_families(generation: int) -> dict[str, dict[str, Any]]:
    """A valueless capture still declares its generation's measured units, so
    blocked and failed attempts leave self-validating evidence beyond v1."""
    return {
        family: {
            "unit": unit,
            "provenance": None,
            "metric_names": None,
            "values_by_launch": None,
        }
        for family, unit in COUNTER_FAMILY_UNITS[generation].items()
    }


def export_counter_csv(ncu: Path, ncu_report: Path) -> str:
    """Re-export the captured report as raw CSV.

    This reads the already-written `.ncu-rep`; it never re-profiles, so it does
    not need counter permission and cannot change what was measured.
    """
    completed = subprocess.run(
        [str(ncu.resolve()), "--import", str(ncu_report.resolve()), "--page", "raw", "--csv"],
        capture_output=True,
        check=False,
    )
    _require(completed.returncode == 0, "Nsight Compute report import failed")
    text = completed.stdout.decode("utf-8", errors="replace")
    _require(bool(text.strip()), "Nsight Compute report import produced no CSV")
    return text


def parse_counter_csv(text: str, schema_version: int) -> dict[str, Any]:
    """Extract achieved counters per launch from an `--page raw --csv` export.

    Row 0 of the export is a units row; the measured launches follow. Every
    launch is matched against the kernel catalog for `schema_version` so a
    renamed or unexpected kernel fails closed rather than being counted.
    """
    _require(
        schema_version in COUNTER_FAMILY_UNITS,
        f"unknown resource-evidence generation: {schema_version}",
    )
    launch_count = required_launch_count(schema_version)
    rows = list(csv.DictReader(io.StringIO(text)))
    _require(len(rows) >= 2, "Nsight Compute CSV has no measured launches")
    units, launches = rows[0], rows[1:]
    _require(
        len(launches) == launch_count,
        f"expected {launch_count} measured launches, found {len(launches)}",
    )
    for column in CSV_IDENTITY_COLUMNS:
        _require(column in units, f"Nsight Compute CSV is missing the {column} column")
    _require(
        all(not str(units[column]).strip() for column in CSV_IDENTITY_COLUMNS),
        "first Nsight Compute CSV row is not the expected units row",
    )

    catalog = _kernel_catalog(schema_version)
    expected = [kernel_id for kernel_id, _stage in _launch_sequence(schema_version)]

    observed: list[str] = []
    for index, row in enumerate(launches):
        symbol = str(row["Kernel Name"])
        matching = [spec for spec in catalog if spec.symbol_fragment in symbol]
        _require(
            len(matching) == 1,
            f"launch {index} kernel is unknown or ambiguous: {symbol}",
        )
        observed.append(matching[0].kernel_id)
    _require(
        observed == expected,
        f"achieved launch order drifted: {observed} != {expected}",
    )

    families: dict[str, dict[str, Any]] = {}
    family_units = COUNTER_FAMILY_UNITS[schema_version]
    for family, unit in family_units.items():
        metrics, expected_unit = COUNTER_METRICS[family]
        for metric in metrics:
            _require(metric in units, f"{family} metric is absent from the report: {metric}")
            _require(
                str(units[metric]).strip() == expected_unit,
                f"{metric} unit drifted: {units[metric]!r} != {expected_unit!r}",
            )
        values: list[float] = []
        for index, row in enumerate(launches):
            total = sum(
                _csv_number(row[metric], f"{family}[{index}].{metric}") for metric in metrics
            )
            if family == "achieved_occupancy":
                # Reported as a percent of peak sustained active warps.
                _require(0.0 <= total <= 100.0, f"{family}[{index}] percent out of range")
                total = total / 100.0
            elif family == "branch_divergence":
                # The metric is threads-per-instruction-executed, where
                # WARP_LANES means every lane was active. Dividing by WARP_LANES
                # yields a 0..1 *convergence* fraction, so 1.0 is fully
                # converged and lower values mean more divergence. The family
                # key is a frozen schema field name and cannot be renamed, so
                # `divergence_encoding` in the report states this direction
                # explicitly rather than leaving the name to imply it.
                _require(
                    0.0 <= total <= WARP_LANES,
                    f"{family}[{index}] threads-per-instruction out of range",
                )
                total = total / WARP_LANES
            values.append(total)
        families[family] = {
            "unit": unit,
            "provenance": "nsight_compute_hardware_counter",
            "metric_names": list(metrics),
            "values_by_launch": values,
        }
    return {"families": families, "kernel_order": observed}
