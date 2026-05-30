from __future__ import annotations

import importlib
import unittest
from unittest import mock

from python.testing.runtime import ensure_repo_imports


HOST_FRAME_PAYLOAD = (
    '[1,"Altis",12.5,0.2,36.0,[1000.0,2000.0,1000.0],[0.0,0.0,0.0],'
    "[0.0,1.0,0.0],[0.0,0.0,1.0]]"
)


class ArmaProxyBackendEchelonEnvTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        ensure_repo_imports()
        cls.mod = importlib.import_module("tools.diagnostics.arma_proxy_backend_echelon_env")

    def test_heading_pitch_roll_to_dir_up_level_heading_north(self) -> None:
        direction, up = self.mod.heading_pitch_roll_to_dir_up(
            heading_deg=0.0,
            pitch_deg=0.0,
            roll_deg=0.0,
        )

        self.assertAlmostEqual(direction[0], 0.0, places=6)
        self.assertAlmostEqual(direction[1], 1.0, places=6)
        self.assertAlmostEqual(direction[2], 0.0, places=6)
        self.assertAlmostEqual(up[2], 1.0, places=6)

    def test_backend_emits_proxy_state_from_real_env(self) -> None:
        backend = self.mod.ArmaProxyEchelonEnvBackend(
            self.mod.EchelonEnvConfig(
                scenario="scenarios/stable_flight/stable_flight.json",
                action_mode="full",
                mission_obs_mode="basic",
                seed=123,
            )
        )
        try:
            self.assertEqual(
                backend.handle_line("begin_session\talpha\tAltis\tB_Plane_Fighter_01_F"),
                "ack\tbegin_session",
            )
            response = backend.handle_line(
                f"host_frame\talpha\tmission|tick\t{HOST_FRAME_PAYLOAD}"
            )
            self.assertTrue(response.startswith("proxy_state\t"))
            payload = response.split("\t", 1)[1]
            proxy_state = self.mod.ProxyState.to_sqf_payload  # type: ignore[attr-defined]
            self.assertIsNotNone(proxy_state)

            values = importlib.import_module("tools.diagnostics.arma_proxy_backend_stub").parse_sqf_simple_array(payload)
            self.assertGreaterEqual(int(values[0]), 1)
            self.assertEqual(len(values), 9)
            self.assertAlmostEqual(float(values[1][0]), 1000.0, delta=200.0)
            self.assertAlmostEqual(float(values[1][1]), 2000.0, delta=200.0)
        finally:
            backend.handle_line("shutdown\talpha")

    def test_sb3_policy_adapter_uses_model_predict(self) -> None:
        model = mock.Mock()
        model.predict.return_value = ([0.1, 0.2, 0.3], None)
        adapter = self.mod.SB3PolicyAdapter(model, deterministic=False)

        action = adapter.act({"obs": [1.0]})

        self.assertEqual(action, [0.1, 0.2, 0.3])
        model.predict.assert_called_once_with({"obs": [1.0]}, deterministic=False)

    def test_backend_bootstraps_model_backed_env_from_train_config(self) -> None:
        train_config = {
            "env": {
                "include_visual": True,
                "include_proprio": True,
                "action_mode": "full",
                "mission_obs_mode": "nav_v2",
                "execution_step_runtime_mode": "compiled",
                "step_info_mode": "terminal",
                "visual_downsample": 2,
                "visual_update_interval": 2,
            },
            "wrappers": {
                "multi_timescale_action": {
                    "enabled": True,
                    "hold_steps": 4,
                }
            },
        }
        raw_env = mock.Mock()
        wrapped_env = mock.Mock()
        wrapped_env.reset.return_value = ({"mission": [0.0], "instruments": [0.0, 0.0, 0.0, 0.0]}, {})
        model = mock.Mock()
        wrapper_factory = mock.Mock(return_value=wrapped_env)

        with mock.patch.object(self.mod, "load_json_config", return_value=train_config) as load_json, \
            mock.patch.object(self.mod, "load_sb3_policy", return_value=model) as load_model, \
            mock.patch.object(self.mod, "UniversalEnv", return_value=raw_env) as universal_env, \
            mock.patch.object(
                self.mod,
                "get_action_wrapper_spec",
                return_value=(wrapper_factory, {"hold_steps": 4}),
            ):
            backend = self.mod.ArmaProxyEchelonEnvBackend(
                self.mod.EchelonEnvConfig(
                    scenario="scenarios/stable_flight/stable_flight.json",
                    train_config="train.json",
                    model_path="model.zip",
                    algo="AdaptiveKLPPO",
                    device="cpu",
                )
            )

            self.assertEqual(
                backend.handle_line("begin_session\talpha\tAltis\tB_Plane_Fighter_01_F"),
                "ack\tbegin_session",
            )

        load_json.assert_called_once()
        load_model.assert_called_once()
        universal_env.assert_called_once()
        env_call = universal_env.call_args
        self.assertEqual(env_call.args[0], "scenarios/stable_flight/stable_flight.json")
        self.assertTrue(env_call.kwargs["include_visual"])
        self.assertTrue(env_call.kwargs["include_proprio"])
        self.assertEqual(env_call.kwargs["action_mode"], "full")
        self.assertEqual(env_call.kwargs["mission_obs_mode"], "nav_v2")
        self.assertEqual(env_call.kwargs["execution_step_runtime_mode"], "compiled")
        self.assertEqual(env_call.kwargs["step_info_mode"], "terminal")
        self.assertEqual(env_call.kwargs["visual_downsample"], 2)
        self.assertEqual(env_call.kwargs["visual_update_interval"], 2)
        self.assertTrue(env_call.kwargs["runtime_compatibility_enabled"])
        wrapper_factory.assert_called_once_with(raw_env, hold_steps=4)
        session = backend._sessions["alpha"]
        self.assertIs(session.env, wrapped_env)
        self.assertIsInstance(session.policy, self.mod.SB3PolicyAdapter)

    def test_backend_rejects_partial_model_bootstrap(self) -> None:
        with self.assertRaisesRegex(ValueError, "train_config and model_path"):
            self.mod.ArmaProxyEchelonEnvBackend(
                self.mod.EchelonEnvConfig(
                    scenario="scenarios/stable_flight/stable_flight.json",
                    train_config="train.json",
                )
            )


if __name__ == "__main__":
    unittest.main()
