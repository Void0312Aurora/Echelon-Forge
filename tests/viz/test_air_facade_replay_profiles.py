from __future__ import annotations

from argparse import Namespace

from python.runtime_bootstrap import resolve_repo_path
from python.simulation import create_scenario_backend
from python.simulation.air import AirFacadeScenarioRuntime
from examples.viz.runtime.viz_session import VizSession


DATABASE = resolve_repo_path("examples", "config", "database")
SCENARIO = resolve_repo_path(
    "scenarios", "air_combat", "air_combat_1v1_headon_sensor_smoke_v1.json"
)


class _ReplaySocket:
    def __init__(self) -> None:
        self.events: list[tuple[str, object]] = []
        self.session: VizSession | None = None

    def emit(self, event: str, payload=None, **_kwargs) -> None:
        self.events.append((event, payload))
        if event == "state_update" and isinstance(payload, dict):
            replay = payload.get("replay", {})
            if replay.get("status") == "completed":
                assert self.session is not None
                self.session.stop()

    def sleep(self, _seconds: float) -> None:
        return None


def _write_receipt(path) -> None:
    backend = create_scenario_backend(
        backend_id="facade_batch",
        database_path=DATABASE,
        scenario_path=SCENARIO,
    )
    runtime = AirFacadeScenarioRuntime(backend)
    try:
        runtime.run(seed=37, steps=3).replay_receipt().write_json(path)
    finally:
        runtime.close()


def test_air_facade_replay_is_consumed_by_the_visualization_lifecycle(tmp_path) -> None:
    receipt_path = tmp_path / "air-facade-replay.json"
    _write_receipt(receipt_path)
    socket = _ReplaySocket()
    args = Namespace(
        scenario=SCENARIO,
        mode="replay",
        replay=str(receipt_path),
        seed=None,
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
    assert len(states) == 3
    assert states[-1]["replay"]["schema"] == "air.facade.replay.v1"
    assert states[-1]["replay"]["status"] == "completed"
    assert states[-1]["replay"]["frame"] == 2
    assert states[-1]["replay"]["frame_count"] == 3
    assert len(states[-1]["units"]) == 2
    assert session.last_error == ""
