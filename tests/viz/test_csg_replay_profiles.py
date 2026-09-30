"""S0 CSG replay profiles exercise the normal visualization wire contract."""

from __future__ import annotations

from argparse import Namespace

from examples.viz.app.profile_loader import load_viz_profile
from examples.viz.runtime.viz_session import VizSession


class _ReplaySocket:
    def __init__(self) -> None:
        self.events: list[tuple[str, object]] = []
        self.session: VizSession | None = None

    def emit(self, event: str, payload=None, **_kwargs) -> None:
        self.events.append((event, payload))
        if event == "state_update" and isinstance(payload, dict):
            replay = payload.get("replay", {})
            spectator = payload.get("spectator", {})
            if ("replay" in payload and int(replay.get("frame", -1)) == int(replay.get("frame_count", 0)) - 1) or (
                bool(spectator.get("native")) and float(payload.get("tick", 0.0)) >= 120.0
            ):
                assert self.session is not None
                self.session.stop()

    def sleep(self, _seconds: float) -> None:
        return None


def test_csg_s0_replay_profiles_stream_all_frames() -> None:
    profiles = [
        "examples/viz/profiles/naval_csg_s0_ford_vs_fujian_replay.json",
        "examples/viz/profiles/naval_csg_s0_ford_mirror_replay.json",
        "examples/viz/profiles/naval_csg_s0_ford_vs_fujian_spectator.json",
        "examples/viz/profiles/naval_csg_s0_ford_mirror_spectator.json",
    ]
    for profile_ref in profiles:
        profile = load_viz_profile(profile_ref)
        socket = _ReplaySocket()
        args = Namespace(
            scenario=profile["scenario"],
            mode=profile["session_overrides"]["mode"],
            replay=profile["session_overrides"].get("replay"),
            seed=profile["session_overrides"].get("seed"),
            model=None,
            train_config=None,
            fixed_action=None,
        )
        session = VizSession(args, socket)
        socket.session = session
        session.start()
        session.run_loop()

        setups = [payload for event, payload in socket.events if event == "map_setup"]
        states = [payload for event, payload in socket.events if event == "state_update"]
        assert len(setups) == 1
        assert len(states) == 241
        assert len(states[0]["units"]) in {22, 24}
        if "replay" in states[-1]:
            assert states[-1]["replay"]["frame"] == 240
        else:
            assert states[-1]["spectator"]["native"] is True
            assert states[-1]["tick"] == 120.0
        assert session.last_error == ""
