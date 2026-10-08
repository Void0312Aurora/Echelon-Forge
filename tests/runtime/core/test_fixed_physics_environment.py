from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
OVERRIDES = (
    "CMO_ROT_MAX_RATE_CROSS_RAD_S", "CMO_ROT_MAX_TORQUE_NM", "CMO_ROT_MAX_ANG_ACCEL_RAD_S2",
    "CMO_ROT_MAX_RATE_RAD_S", "CMO_ROT_SINGULARITY_MIN_PITCH_DEG", "CMO_ROT_PITCH_LIMIT_DEG",
    "CMO_FBW_PROTECTION_MODE",
)
BOOTSTRAP = "from python.runtime_bootstrap import ensure_repo_imports; ensure_repo_imports(); import ef_py\n"
PROBE = BOOTSTRAP + '''
import json
def state(kernel):
    kernel.reset(17)
    kernel.set_wind(0,0,0)
    entity=kernel.spawn_unit(ef_py.Side.Blue,"Aircraft",0,0,1000,0,88,0,0,200,0)
    kernel.step()
    inst=kernel.get_instrument_state(entity)
    return [inst.pitch, inst.roll, inst.heading, inst.p, inst.q, inst.r]
kernel=ef_py.SimulationKernel()
first=state(kernel)
replay=state(kernel)
second=state(ef_py.SimulationKernel())
graph=ef_py.RuntimeFacade(1).export_composition_evidence().evidence.executable_graph_sha256
print("RESULT="+json.dumps({"first":first,"replay":replay,"second":second,"graph":graph}))
'''


def _run(code: str, overrides: dict[str, str] | None = None):
    env = os.environ.copy()
    for name in OVERRIDES:
        env.pop(name, None)
    env.update(overrides or {})
    return subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=env,
                          capture_output=True, text=True, timeout=30, check=False)


def _result(process):
    assert process.returncode == 0, process.stderr
    return json.loads(next(line[7:] for line in process.stdout.splitlines() if line.startswith("RESULT=")))


def test_fixed_defaults_replay_in_fresh_processes_reset_and_multiple_worlds():
    a, b = _result(_run(PROBE)), _result(_run(PROBE))
    assert a == b
    assert a["first"] == a["replay"] == a["second"]
    assert 80 < a["first"][0] <= 89  # eligible attitude; old 70-degree override changed it
    assert len(a["graph"]) == 64


@pytest.mark.parametrize("name", OVERRIDES)
@pytest.mark.parametrize("constructor", ["ef_py.SimulationKernel()", "ef_py.RuntimeFacade(1)"])
def test_native_entrypoints_reject_every_defined_override_in_fresh_process(name, constructor):
    process = _run(BOOTSTRAP + constructor, {name: "off" if "FBW" in name else "70"})
    assert process.returncode != 0
    expected_type = "RuntimeError" if "RuntimeFacade" in constructor else "ValueError"
    assert expected_type in process.stderr
    assert "builtin.default_physics.v1" in process.stderr
    assert name in process.stderr


@pytest.mark.parametrize("value", ["", "nan", "not-a-number"])
def test_even_empty_or_invalid_values_are_explicitly_refused(value):
    process = _run(BOOTSTRAP + "ef_py.SimulationKernel()", {OVERRIDES[0]: value})
    assert process.returncode != 0 and OVERRIDES[0] in process.stderr


def test_late_environment_change_does_not_change_existing_world_truth():
    code = PROBE + '''
import os
os.environ["CMO_ROT_PITCH_LIMIT_DEG"]="70"
assert state(kernel)==first
try:
    ef_py.SimulationKernel()
except ValueError as error:
    assert "CMO_ROT_PITCH_LIMIT_DEG" in str(error)
else:
    raise AssertionError("another world admitted a forbidden override")
'''
    _result(_run(code))
