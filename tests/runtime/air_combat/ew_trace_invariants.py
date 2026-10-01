"""Shared invariants for the maintained scripted Air EW demo traces.

The native MAWS owner keeps a launch warning raised for every frame in which
an active missile is inbound inside the warning envelope, and the native
dispenser admits one release per ``release_interval`` once a warning starts.
These helpers express that contract as properties of a demo trace instead of
pinning scan-cadence artifacts or exact per-step inventories.
"""

from __future__ import annotations

from typing import Any, Sequence

# gen4_standard EW suite (examples/config/database/aircraft/modules/ew_suites)
# and the demo scenarios' environment.time_step.
RELEASE_INTERVAL_STEPS = 10
INITIAL_CHAFF = 60
INITIAL_FLARE = 30


def contiguous_runs(steps: Sequence[int]) -> list[tuple[int, int]]:
    runs: list[tuple[int, int]] = []
    for step in steps:
        if runs and runs[-1][1] == step - 1:
            runs[-1] = (runs[-1][0], step)
        else:
            runs.append((step, step))
    return runs


def assert_continuous_warning(warning_steps: Sequence[int], *, last_step: int) -> int:
    """Warnings form one unbroken run from the first launch to ``last_step``."""

    assert warning_steps, "expected at least one launch warning"
    runs = contiguous_runs(warning_steps)
    assert runs == [(warning_steps[0], last_step)], runs
    return int(warning_steps[0])


def assert_interval_gated_consumption(
    samples: Sequence[dict[str, Any]],
    *,
    first_warning_step: int,
    chaff_requested: bool,
    flare_requested: bool,
) -> None:
    """Each requested store drops by one per release interval, from the first warning."""

    assert samples, "expected countermeasure samples on request steps"
    assert int(samples[0]["step"]) == first_warning_step
    for sample in samples:
        released = 1 + (int(sample["step"]) - first_warning_step) // RELEASE_INTERVAL_STEPS
        expected_chaff = INITIAL_CHAFF - released if chaff_requested else INITIAL_CHAFF
        expected_flare = INITIAL_FLARE - released if flare_requested else INITIAL_FLARE
        assert int(sample["chaff_remaining"]) == expected_chaff, sample
        assert int(sample["flare_remaining"]) == expected_flare, sample
