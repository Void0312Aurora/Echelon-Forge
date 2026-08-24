"""Focused I87 C3/C20 typed-observation pilot gates.

The pilot's spec data source is the pure Python static declaration in
``python/rl/runtime/world_batch/typed_observation_view.py``
(``maintained_observation_view_spec``); the retired C++
``RuntimeFacade.describe_maintained_observation_view`` export only mirrored
those constants, so these gates now exercise the static declaration plus the
fail-closed admission seam directly.
"""

from __future__ import annotations

import ast
import dataclasses
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from python.runtime_bootstrap import ensure_repo_imports


ensure_repo_imports()

import python.rl.runtime.world_batch.adapter as adapter_module  # noqa: E402
import python.rl.runtime.world_batch._vec_env_support as vec_env_support  # noqa: E402
import python.rl.runtime.world_batch.observation_batching as observation_batching  # noqa: E402
from python.rl.runtime.world_batch.adapter import RuntimeFacadeAdapter  # noqa: E402
from python.rl.runtime.world_batch.typed_observation_view import (  # noqa: E402
    maintained_observation_view_spec,
)
from tests.support._world_batch_vec_env_test_support import (  # noqa: E402
    _inline_vec_env_scenario,
)

try:  # The real parity test is optional when the RL environment extras are absent.
    from python.rl.runtime.world_batch.vec_env import WorldBatchVecEnv  # noqa: E402
except ModuleNotFoundError:  # pragma: no cover - exercised by minimal CI envs
    WorldBatchVecEnv = None


_REPO_ROOT = Path(__file__).resolve().parents[2]
_C3_PATH = _REPO_ROOT / "python" / "rl" / "runtime" / "world_batch" / "observation_batching.py"
_C20_PATH = _REPO_ROOT / "python" / "rl" / "runtime" / "world_batch" / "_vec_env_support.py"


def _valid_spec():
    return maintained_observation_view_spec()


def test_default_off_leaves_spec_unset_and_has_no_post_construction_enable() -> None:
    adapter = RuntimeFacadeAdapter(1)

    assert adapter.typed_observation_view_spec is None
    assert not hasattr(adapter, "enable_typed_observation_view")


def test_opt_in_admits_the_static_declaration_exactly_once() -> None:
    adapter = RuntimeFacadeAdapter(1, use_typed_observation_view=True)

    spec = adapter.typed_observation_view_spec
    assert spec is not None
    assert spec == _valid_spec()
    assert adapter.typed_observation_view_spec is spec


@pytest.mark.parametrize(
    ("field", "value", "needle"),
    [
        ("view_id", "gym_envs.other_view", "view_id"),
        ("schema_version", "2.0", "schema_version"),
        ("schema_version", "1", "schema_version"),
        ("information_layer_produced", ("Decision Belief",), "information_layer_produced"),
        ("information_layer_consumed", ("World Truth",), "information_layer_consumed"),
        ("semantic_stage", ("P2 TaskingIntent",), "semantic_stage"),
    ],
)
def test_opt_in_structural_admission_fails_closed(
    field: str,
    value: object,
    needle: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tampered = dataclasses.replace(_valid_spec(), **{field: value})
    monkeypatch.setattr(
        adapter_module, "maintained_observation_view_spec", lambda: tampered
    )
    with pytest.raises(RuntimeError, match=needle):
        RuntimeFacadeAdapter(1, use_typed_observation_view=True)


@pytest.mark.parametrize("field", ["required_fields", "optional_fields"])
def test_nonempty_field_catalogue_is_not_a_wildcard_and_fails_closed(
    field: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tampered = dataclasses.replace(_valid_spec(), **{field: ("own_ship.x",)})
    monkeypatch.setattr(
        adapter_module, "maintained_observation_view_spec", lambda: tampered
    )
    with pytest.raises(RuntimeError, match=f"{field}.*structural-only"):
        RuntimeFacadeAdapter(1, use_typed_observation_view=True)


def test_c3_and_c20_pass_opaque_truth_to_compiled_kernels_and_use_reader() -> None:
    truth = object()
    inst = SimpleNamespace(alt_baro=100.0)
    reader_calls: list[tuple[object, str]] = []

    def read_field(value: object, field: str) -> float:
        reader_calls.append((value, field))
        return 12.5 if field == "x" else -3.25

    class _Loader:
        def _build_mission_observation_runtime_inputs(self, _mode, *, truth, inst):
            return {"truth": truth, "inst": inst}

        def get_ils_observation(self, x, y, altitude):
            assert (x, y, altitude) == (12.5, -3.25, 100.0)
            return np.zeros((4,), dtype=np.float32)

    state = SimpleNamespace(loader=_Loader(), last_truth=truth, last_inst=inst)
    captured: dict[str, object] = {}

    def fake_batch_kernel(inst_batch, truth_batch, *_args):
        captured["batch_truth"] = truth_batch[0]
        return (
            np.ones((1, 2), dtype=np.float32),
            np.ones((1, 2), dtype=np.float32),
            np.ones((1, 2), dtype=np.float32),
            np.ones((1, 2), dtype=np.float32),
        )

    original_batch_kernel = observation_batching.ef_py.compute_execution_observation_batch_numpy
    observation_batching.ef_py.compute_execution_observation_batch_numpy = fake_batch_kernel
    try:
        result = observation_batching.compute_execution_observation_batch(
            states=[state],
            mission_obs_mode="basic",
            max_contacts=2,
            max_rwr=2,
            backend="compiled",
            observation_view_spec=_valid_spec(),
            own_ship_field_reader=read_field,
        )
    finally:
        observation_batching.ef_py.compute_execution_observation_batch_numpy = original_batch_kernel

    assert reader_calls == [(truth, "x"), (truth, "y")]
    assert captured["batch_truth"] is truth
    assert result.truth_batch[0] is truth

    captured_runtime: dict[str, object] = {}

    def fake_runtime_kernel(_inst, runtime_truth, *_args):
        captured_runtime["truth"] = runtime_truth
        return np.ones((2,), dtype=np.float32), [], []

    original_runtime_kernel = vec_env_support.ef_py.compute_execution_observation_runtime_numpy
    vec_env_support.ef_py.compute_execution_observation_runtime_numpy = fake_runtime_kernel
    try:
        vector = vec_env_support._execution_instrument_vector(
            _Loader(),
            truth,
            inst,
            max_contacts=2,
            max_rwr=2,
            observation_view_spec=_valid_spec(),
            own_ship_field_reader=read_field,
        )
    finally:
        vec_env_support.ef_py.compute_execution_observation_runtime_numpy = original_runtime_kernel

    assert captured_runtime["truth"] is truth
    assert vector.dtype == np.float32
    assert reader_calls[-2:] == [(truth, "x"), (truth, "y")]


def test_c3_opt_in_and_default_off_observations_are_exactly_equal() -> None:
    if WorldBatchVecEnv is None:
        pytest.skip("optional RL VecEnv dependencies are unavailable")
    with tempfile.TemporaryDirectory() as tmpdir:
        scenario_path = Path(tmpdir) / "inline_scenario.json"
        scenario_path.write_text(json.dumps(_inline_vec_env_scenario()), encoding="utf-8")
        default_env = WorldBatchVecEnv(
            scenario_path=str(scenario_path),
            n_envs=1,
            include_visual=False,
            include_proprio=False,
            use_typed_observation_view=False,
        )
        typed_env = WorldBatchVecEnv(
            scenario_path=str(scenario_path),
            n_envs=1,
            include_visual=False,
            include_proprio=False,
            use_typed_observation_view=True,
        )
        try:
            default_env.seed(123)
            typed_env.seed(123)
            default_obs = default_env.reset()
            typed_obs = typed_env.reset()
            for key in default_obs:
                assert np.array_equal(default_obs[key], typed_obs[key]), key

            action = np.zeros((1, 17), dtype=np.float32)
            default_obs, default_reward, default_done, _ = default_env.step(action)
            typed_obs, typed_reward, typed_done, _ = typed_env.step(action)
            for key in default_obs:
                assert np.array_equal(default_obs[key], typed_obs[key]), key
            assert np.array_equal(default_reward, typed_reward)
            assert np.array_equal(default_done, typed_done)
        finally:
            default_env.close()
            typed_env.close()


def test_i87_lower_consumers_have_no_raw_xy_leaf_reads() -> None:
    for path in (_C3_PATH, _C20_PATH):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        raw = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "truth"
            and node.attr in {"x", "y"}
        ]
        assert not raw, path.as_posix()
        assert "own_ship_field_reader" in path.read_text(encoding="utf-8")
