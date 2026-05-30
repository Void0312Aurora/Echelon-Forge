from __future__ import annotations

import importlib
import unittest

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


if __name__ == "__main__":
    unittest.main()
