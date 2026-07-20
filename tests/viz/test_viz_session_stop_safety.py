"""Thread-safety contract for VizSession stop/reload under the threading
async model: stop is a signal the worker honors; the worker owns cleanup."""

from __future__ import annotations

import time
from argparse import Namespace
from types import SimpleNamespace

from examples.viz.runtime.viz_session import VizSession


def _make_session() -> VizSession:
    socketio = SimpleNamespace(
        emit=lambda *args, **kwargs: None,
        sleep=time.sleep,
        start_background_task=lambda fn, *a, **k: None,
    )
    args = Namespace(scenario="", model=None, train_config=None, fixed_action=None)
    return VizSession(args, socketio)


def test_stop_before_start_is_not_lost() -> None:
    # A stop arriving before the worker starts must persist: the run loop no
    # longer resets the stop flag at startup, so the worker exits promptly.
    session = _make_session()
    session.stop()
    assert session.stop_requested is True
    # Source-level guarantee that the loop cannot clear a pending stop.
    src = (
        __import__("pathlib").Path("examples/viz/runtime/viz_session.py").read_text(encoding="utf-8")
    )
    assert "self.stop_requested = False" not in src
    assert "self._stop_event.set()" in src


def test_stop_leaves_env_cleanup_to_worker() -> None:
    # stop() must not close/clear the env from the request thread while the
    # worker may be mid-step; the worker's finally block owns cleanup.
    session = _make_session()
    sentinel = object()
    session.env = sentinel
    session.stop()
    assert session.env is sentinel


def test_worker_finally_releases_resources() -> None:
    # run_loop releases resources in its finally block even when the inner
    # loop raises immediately.
    session = _make_session()

    released = []
    session._release_runtime_resources = lambda: released.append(True)  # type: ignore[method-assign]

    def _boom() -> None:
        raise RuntimeError("startup failure")

    session._run_loop_inner = _boom  # type: ignore[method-assign]
    session.run_loop()
    assert released == [True]
    assert session.ready is False


def test_status_payload_reflects_stop_event() -> None:
    session = _make_session()
    assert session.status_payload()["stopped"] is False
    session.stop()
    assert session.status_payload()["stopped"] is True
