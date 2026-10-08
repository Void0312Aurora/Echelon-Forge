from __future__ import annotations

import os
from pathlib import Path
import signal
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize("fault, diagnostic", [
    ("stamp", "stable identity invariant violated: stamp_stable_serial: already_stamped"),
    ("draw", "stochastic draw invariant violated: site 5: participant carries no StableEntitySerial"),
])
def test_internal_invariant_terminates_only_the_child(fault: str, diagnostic: str) -> None:
    build = Path(os.environ.get("CMO_BUILD_DIR", ROOT / "build"))
    binary = build / ("ef_test.exe" if os.name == "nt" else "ef_test")
    if not binary.is_file():
        pytest.skip("native ef_test binary is required for the fatal process probe")
    env = os.environ.copy()
    env["EF_TEST_INVARIANT_FAULT"] = fault
    child = subprocess.run(
        [str(binary), "--test-case=process invariant fault probe", "--no-skip"],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=30, check=False,
    )
    expected_codes = {3, 0x40000015, -1073740791} if os.name == "nt" else {-signal.SIGABRT}
    assert child.returncode in expected_codes, (child.returncode, child.stdout, child.stderr)
    assert diagnostic in child.stderr
    # A fresh training worker can start after the parent observes the fatal receipt.
    replacement = subprocess.run(
        [sys.executable, "-c", "from python.runtime_bootstrap import ensure_repo_imports; "
         "ensure_repo_imports(); import ef_py; k=ef_py.SimulationKernel(); k.reset(17); "
         "k.step(); print('WORKER_READY')"],
        cwd=ROOT, env=os.environ.copy(), capture_output=True, text=True, timeout=30, check=False,
    )
    assert replacement.returncode == 0, replacement.stderr
    assert "WORKER_READY" in replacement.stdout


def test_python_clock_refusal_is_catchable_and_worker_remains_usable() -> None:
    from python.runtime_bootstrap import ensure_repo_imports
    ensure_repo_imports()
    import ef_py

    kernel = ef_py.SimulationKernel()
    original_dt = kernel.get_time_step()
    for dt in [float("nan"), float("inf"), -1.0, 0.0, 1e100, 1e-100]:
        with pytest.raises(ValueError, match="time step"):
            kernel.set_time_step(dt)
    kernel.step()
    assert kernel.get_time_step() == pytest.approx(original_dt)
