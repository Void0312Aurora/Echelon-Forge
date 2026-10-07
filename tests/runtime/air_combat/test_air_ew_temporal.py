"""E3 acceptance for opt-in EW history on maintained environment/policy paths."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import torch
from gymnasium import spaces
from stable_baselines3 import PPO

from gym_envs.universal_env_parts.spaces import (
    EW_STATE_DIM,
    make_action_space,
    make_observation_space,
)
from python.env_config import resolve_env_settings
from python.models.transformer import TemporalTransformerExtractor
from python.rl.runtime.cooperative_world_batch_vec_env import CooperativeWorldBatchVecEnv
from python.rl.runtime.world_batch.vec_env import WorldBatchVecEnv
from python.runtime_bootstrap import resolve_repo_path
from python.training.deps import get_policy_kwargs


_SCENARIO = Path(
    resolve_repo_path("scenarios", "air_combat", "air_combat_1v1_headon_sensor_smoke_v1.json")
)
_SEED = 20260516
_HISTORY_LEN = 4


def _space(*, include_ew_state: bool = True, history_len: int = _HISTORY_LEN):
    return make_observation_space(
        action_space=make_action_space("air_combat_hybrid_v1"),
        mission_obs_mode="basic",
        include_visual=False,
        include_proprio=False,
        arb_height=48,
        arb_width=96,
        arb_channels=10,
        temporal_history_len=history_len,
        include_ew_state=include_ew_state,
    )


def _tensor_history(space, batch_size: int = 2):
    return {
        key: torch.zeros((batch_size, *value.shape), dtype=torch.float32)
        for key, value in space.spaces.items()
    }


def test_default_and_non_ew_temporal_layouts_keep_keys_and_parameters():
    single = _space(history_len=1)
    assert "ew_state_history" not in single.spaces
    assert "temporal_valid_mask" not in single.spaces
    legacy = _space(include_ew_state=False)
    assert set(legacy.spaces) == {
        "instruments",
        "contacts",
        "rwr",
        "mission",
        "instruments_history",
        "contacts_history",
        "rwr_history",
        "mission_history",
        "proprio_history",
    }
    extractor = TemporalTransformerExtractor(legacy, features_dim=32, n_heads=4, n_layers=1)
    assert not extractor.has_ew_state
    assert extractor.type_embed.num_embeddings == 5
    assert not any("ew_state" in key for key in extractor.state_dict())
    restored = TemporalTransformerExtractor(legacy, features_dim=32, n_heads=4, n_layers=1)
    restored.load_state_dict(extractor.state_dict(), strict=True)
    features = restored(_tensor_history(legacy))
    assert torch.isfinite(features).all()


def test_incomplete_or_mismatched_ew_history_is_rejected():
    space = _space()
    for missing in ("ew_state", "ew_state_history", "temporal_valid_mask"):
        incomplete = spaces.Dict(
            {key: value for key, value in space.spaces.items() if key != missing}
        )
        with pytest.raises(ValueError, match="together"):
            TemporalTransformerExtractor(incomplete, features_dim=32)
    for key, shape in (("ew_state_history", (3, EW_STATE_DIM)), ("temporal_valid_mask", (3,))):
        malformed = spaces.Dict(
            {**space.spaces, key: spaces.Box(-1.0, 1.0, shape, dtype=np.float32)}
        )
        with pytest.raises(ValueError, match="history length"):
            TemporalTransformerExtractor(malformed, features_dim=32)


@pytest.mark.parametrize("checkpointing", [False, True])
def test_temporal_policy_ignores_padding_but_consumes_older_valid_ew_frames(checkpointing):
    torch.manual_seed(7)
    space = _space()
    extractor = TemporalTransformerExtractor(
        space,
        features_dim=32,
        n_heads=4,
        n_layers=1,
        temporal_n_layers=2,
        use_checkpointing=checkpointing,
    )
    obs = _tensor_history(space)
    obs["temporal_valid_mask"] = torch.tensor([[0, 0, 1, 1], [0, 0, 0, 1]], dtype=torch.float32)
    obs["ew_state_history"][:, -1, 0] = 30.0
    obs["ew_state_history"][0, -2, 0] = 31.0
    obs["ew_state_history"].requires_grad_(True)
    features = extractor(obs)
    assert torch.isfinite(features).all()
    features[:, 0].sum().backward()
    gradient = obs["ew_state_history"].grad
    assert torch.isfinite(gradient).all()
    assert torch.count_nonzero(gradient[:, :2]) == 0
    assert torch.count_nonzero(gradient[1, -2]) == 0
    assert float(gradient[0, -2].abs().sum()) > 1.0e-8
    assert float(extractor.embed_ew_state.weight.grad.abs().sum()) > 1.0e-8

    # Inference uses Torch's optimized encoder path; padding must remain
    # invisible there as well as in the differentiable training path.
    extractor.eval()
    dirty = {key: value.detach().clone() for key, value in obs.items()}
    for key in dirty:
        if key.endswith("_history"):
            dirty[key][0, :2] = 99999.0
            dirty[key][1, :3] = -99999.0
    with torch.no_grad():
        expected = extractor({key: value.detach() for key, value in obs.items()})
        actual = extractor(dirty)
    assert torch.isfinite(actual).all()
    torch.testing.assert_close(actual, expected, rtol=0.0, atol=0.0)


def test_timeout_reset_preserves_terminal_history_and_clears_the_new_episode(tmp_path):
    scenario = json.loads(_SCENARIO.read_text(encoding="utf-8"))
    scenario["environment"]["max_steps"] = 2
    path = tmp_path / "short_ew_history.json"
    path.write_text(json.dumps(scenario), encoding="utf-8")
    env = WorldBatchVecEnv(
        scenario_path=str(path),
        n_envs=2,
        include_visual=False,
        include_ew_state=True,
        action_mode="air_ew_hybrid_v2",
        temporal_history_len=_HISTORY_LEN,
        worker_threads=1,
    )
    try:
        env.seed(_SEED)
        initial = env.reset()
        np.testing.assert_array_equal(initial["temporal_valid_mask"], [[0, 0, 0, 1]] * 2)
        actions = np.zeros((2, 16), dtype=np.float32)
        actions[:, 3] = 0.7
        actions[0, 14] = 1.0
        first, _, done, _ = env.step(actions)
        assert not done.any()
        assert first["ew_state"][0, 3] == 1.0
        assert first["ew_state"][1, 3] == 0.0
        np.testing.assert_array_equal(first["ew_state_history"][:, -1], first["ew_state"])
        reset, _, done, infos = env.step(actions)
        assert done.all()
        np.testing.assert_array_equal(reset["temporal_valid_mask"], [[0, 0, 0, 1]] * 2)
        np.testing.assert_array_equal(reset["ew_state_history"][:, :-1], 0.0)
        for index, info in enumerate(infos):
            terminal = info["terminal_observation"]
            np.testing.assert_array_equal(terminal["temporal_valid_mask"], [0, 1, 1, 1])
            np.testing.assert_array_equal(
                terminal["ew_state_history"][-2], first["ew_state"][index]
            )
        env.seed(_SEED)
        np.testing.assert_array_equal(env.reset()["ew_state_history"], initial["ew_state_history"])
    finally:
        env.close()


def test_seeded_ew_history_replays_through_transmit_and_standby():
    env = WorldBatchVecEnv(
        scenario_path=str(_SCENARIO),
        n_envs=1,
        include_visual=False,
        include_ew_state=True,
        action_mode="air_ew_hybrid_v2",
        temporal_history_len=_HISTORY_LEN,
        worker_threads=1,
    )
    try:
        traces = []
        for _ in range(2):
            env.seed(_SEED)
            env.reset()
            trace = []
            for step in range(6):
                action = np.zeros((1, 16), dtype=np.float32)
                action[0, 3] = 0.7
                action[0, 14] = float(step in (1, 2, 4))
                action[0, 15] = float(step % 3)
                obs, _, done, _ = env.step(action)
                assert not done.any()
                assert bool(obs["ew_state"][0, 3]) == bool(action[0, 14])
                trace.append(
                    {
                        key: obs[key].copy()
                        for key in ("ew_state_history", "rwr_history", "temporal_valid_mask")
                    }
                )
            traces.append(trace)
        for first, second in zip(*traces, strict=True):
            for key in first:
                np.testing.assert_array_equal(first[key], second[key])
    finally:
        env.close()


def test_cooperative_slots_keep_independent_ew_histories(tmp_path):
    from tests.runtime.multi_agent.test_cooperative_vec_env_tasking import (
        _cooperative_cruise_scenario,
    )

    path = tmp_path / "cooperative_ew_history.json"
    path.write_text(json.dumps(_cooperative_cruise_scenario()), encoding="utf-8")
    env = CooperativeWorldBatchVecEnv(
        scenario_path=str(path),
        n_envs=1,
        include_visual=False,
        include_ew_state=True,
        action_mode="air_ew_hybrid_v1",
        temporal_history_len=_HISTORY_LEN,
        worker_threads=1,
    )
    try:
        env.seed(_SEED)
        initial = env.reset()
        np.testing.assert_array_equal(initial["temporal_valid_mask"], [[0, 0, 0, 1]] * 2)
        actions = np.zeros((2, 14), dtype=np.float32)
        actions[:, 3] = 0.7
        settled, _, _, _ = env.step(actions)
        actions[0, 12] = 1.0
        actions[1, 13] = 1.0
        for _ in range(40):
            obs, _, done, _ = env.step(actions)
            assert not done.any()
            if (
                obs["ew_state"][0, 0] < settled["ew_state"][0, 0]
                and obs["ew_state"][1, 1] < settled["ew_state"][1, 1]
            ):
                break
        assert obs["ew_state"][0, 0] < settled["ew_state"][0, 0]
        assert obs["ew_state"][0, 1] == settled["ew_state"][0, 1]
        assert obs["ew_state"][1, 1] < settled["ew_state"][1, 1]
        assert obs["ew_state"][1, 0] == settled["ew_state"][1, 0]
        np.testing.assert_array_equal(obs["ew_state_history"][:, -1], obs["ew_state"])
        np.testing.assert_array_equal(env.reset()["temporal_valid_mask"], [[0, 0, 0, 1]] * 2)
    finally:
        env.close()


def test_maintained_config_builds_a_temporal_ew_policy_and_checkpoint(tmp_path):
    settings = resolve_env_settings(
        {
            "env": {
                "action_mode": "air_combat_hybrid_v1",
                "include_ew_state": True,
                "temporal_history_len": _HISTORY_LEN,
                "include_visual": False,
            }
        },
        object(),
    )
    env = WorldBatchVecEnv(scenario_path=str(_SCENARIO), n_envs=1, worker_threads=1, **settings)
    try:
        config = {
            "hyperparameters": {
                "policy_kwargs": {
                    "features_extractor_class": "TemporalTransformerExtractor",
                    "features_extractor_kwargs": {
                        "features_dim": 32,
                        "n_heads": 4,
                        "n_layers": 1,
                        "temporal_n_layers": 1,
                        "use_checkpointing": True,
                    },
                    "net_arch": {"pi": [32], "vf": [32]},
                }
            }
        }
        env.seed(_SEED)
        model = PPO(
            "MultiInputPolicy",
            env,
            n_steps=2,
            batch_size=2,
            n_epochs=1,
            device="cpu",
            policy_kwargs=get_policy_kwargs(config),
            seed=7,
            verbose=0,
        )
        model.learn(total_timesteps=4)
        obs = env.reset()
        expected, _ = model.predict(obs, deterministic=True)
        assert expected.shape == (1, 12)
        assert np.isfinite(expected).all()
        path = tmp_path / "temporal_ew_policy"
        model.save(path)
        restored = PPO.load(path, env=env, device="cpu")
        actual, _ = restored.predict(obs, deterministic=True)
        np.testing.assert_array_equal(actual, expected)
        assert restored.policy.features_extractor.has_ew_state
    finally:
        env.close()
