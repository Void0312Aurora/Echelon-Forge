from __future__ import annotations

import argparse
import os
import threading
import time
from typing import Iterable

from examples.viz.app.asset_registry import list_asset_registries, load_asset_registry
from examples.viz.app.profile_loader import list_viz_profiles, load_viz_profile
from examples.viz.runtime.scene_geometry import load_scene_geometry_payload
from examples.viz.runtime.viz_session import VizSession


class SessionManager:
    def __init__(self, socketio, *, default_args: argparse.Namespace | None = None) -> None:
        self.socketio = socketio
        self.default_args = default_args
        self.session: VizSession | None = None
        self.current_profile: dict | None = None
        self.asset_registry = load_asset_registry()
        self.scene_geometry: dict | None = None
        # Bumped on every scene-geometry (re)load; part of the cache key so
        # frontends refetch even across bundles with colliding declared ids.
        self._scene_geometry_generation = 0
        self._tasks: list = []
        # Serializes session transitions (load/stop/shutdown): concurrent
        # threaded socket handlers must never race two replacements.
        self._transition_lock = threading.Lock()

    def list_scenarios(self, roots: Iterable[str] | None = None) -> list[str]:
        search_roots = list(roots or ["scenarios"])
        found: list[str] = []
        for root in search_roots:
            abs_root = os.path.abspath(root)
            if not os.path.isdir(abs_root):
                continue
            for current_root, _dirs, files in os.walk(abs_root):
                for filename in sorted(files):
                    if not filename.endswith(".json"):
                        continue
                    abs_path = os.path.join(current_root, filename)
                    found.append(os.path.relpath(abs_path, os.getcwd()))
        found.sort()
        return found

    def list_profiles(self) -> list[dict]:
        return list_viz_profiles()

    def list_asset_registries(self) -> list[dict]:
        return list_asset_registries()

    def current(self) -> VizSession | None:
        return self.session

    def _scene_geometry_status(self) -> dict:
        payload = self.scene_geometry
        if not isinstance(payload, dict):
            return {"available": False}
        bundle = payload.get("bundle", {})
        return {
            "available": True,
            "bundle_id": str(bundle.get("bundle_id", "")),
            # Backend-authoritative cache key: a monotonically increasing
            # load generation combined with the declared digest. Frontends
            # must key their caches on this, never on the bundle's
            # self-declared id (which is unvalidated and could collide).
            "cache_key": (
                f"{int(self._scene_geometry_generation)}:"
                f"{bundle.get('content_digest_sha256', '')}"
            ),
            "summary": payload.get("summary", {}),
            "held_total": int(payload.get("held", {}).get("total", 0)),
        }

    def status_payload(self) -> dict:
        session = self.session
        if session is None:
            return {
                "loaded": False,
                "session": None,
                "scenarios": self.list_scenarios(),
                "profiles": self.list_profiles(),
                "asset_registries": self.list_asset_registries(),
                "profile": self.current_profile["summary"] if isinstance(self.current_profile, dict) else None,
                "asset_registry": self.asset_registry,
                "scene_geometry": self._scene_geometry_status(),
            }
        return {
            "loaded": True,
            "session": session.status_payload(),
            "scenarios": self.list_scenarios(),
            "profiles": self.list_profiles(),
            "asset_registries": self.list_asset_registries(),
            "profile": self.current_profile["summary"] if isinstance(self.current_profile, dict) else None,
            "asset_registry": self.asset_registry,
            "scene_geometry": self._scene_geometry_status(),
        }

    def emit_status(self) -> None:
        self.socketio.emit("viz_app_status", self.status_payload())
        session = self.session
        if session is not None:
            self.socketio.emit("viz_session_status", session.status_payload())

    def load_session(self, scenario: str, overrides: dict | None = None) -> VizSession:
        with self._transition_lock:
            return self._load_session_locked(scenario, overrides)

    def _load_session_locked(self, scenario: str, overrides: dict | None = None) -> VizSession:
        base = argparse.Namespace(**vars(self.default_args)) if self.default_args is not None else argparse.Namespace()
        setattr(base, "scenario", str(scenario))
        if overrides:
            for key, value in overrides.items():
                setattr(base, key, value)

        old_session = self.session
        if old_session is not None:
            old_session.stop()
        # Every live worker must be gone before a replacement starts -- not
        # just the one referenced by self.session: stop_current() clears the
        # reference while its worker may still be draining. Two live workers
        # would interleave unscoped state_update streams. Startup can be
        # slow (env build, model load), so the session's stop checkpoints
        # bound the wait; if a worker still will not die, refuse the
        # replacement instead of abandoning it.
        if self._tasks:
            self._drain_tasks(timeout_s=15.0)
        if self._tasks:
            raise RuntimeError(
                "a previous viz session worker has not terminated; "
                "retry once it stops instead of running two sessions"
            )

        session = VizSession(base, self.socketio, status_callback=self.emit_status)
        self.session = session
        task = self.socketio.start_background_task(session.run_loop)
        self._tasks.append(task)
        self.emit_status()
        return session

    def load_profile(self, profile_ref: str) -> VizSession:
        # Stage everything outside the lock (pure loads, no manager state),
        # then commit metadata and start the session atomically under the
        # transition lock: a refused replacement or a concurrent load must
        # never leave one profile's metadata paired with another scenario.
        profile = load_viz_profile(profile_ref)
        registry_ref = str(profile.get("asset_registry") or "").strip()
        staged_registry = load_asset_registry(registry_ref or None)
        bundle_ref = str(profile.get("environment_bundle") or "").strip()
        staged_geometry = load_scene_geometry_payload(bundle_ref) if bundle_ref else None

        with self._transition_lock:
            session = self._load_session_locked(
                profile["scenario"], overrides=profile.get("session_overrides")
            )
            # The session started; commit the staged metadata with it.
            self.current_profile = profile
            self.asset_registry = staged_registry
            self.scene_geometry = staged_geometry
            self._scene_geometry_generation += 1

        startup = profile.get("startup", {}) if isinstance(profile, dict) else {}
        try:
            speed = float(startup.get("speed", 1.0))
        except Exception:
            speed = 1.0
        session.set_speed({"value": speed})
        if bool(startup.get("auto_start", False)):
            session.start()
        self.emit_status()
        return session

    def clear_profile_selection(self) -> None:
        self.current_profile = None
        self.asset_registry = load_asset_registry()
        self.scene_geometry = None

    def load_asset_registry_only(self, registry_ref: str) -> None:
        self.asset_registry = load_asset_registry(registry_ref)
        self.emit_status()

    def start_current(self) -> None:
        if self.session is None:
            return
        self.session.start()
        self.emit_status()

    def pause_current(self) -> None:
        if self.session is None:
            return
        self.session.pause()
        self.emit_status()

    def resume_current(self) -> None:
        if self.session is None:
            return
        self.session.resume()
        self.emit_status()

    def stop_current(self) -> None:
        with self._transition_lock:
            if self.session is None:
                return
            self.session.stop()
            self.session = None
            self._drain_tasks(timeout_s=5.0)
            self.emit_status()

    @staticmethod
    def _task_finished(task) -> bool:
        # threading.Thread exposes is_alive(); eventlet/gevent greenlets
        # expose .dead. Support both so the async model stays swappable.
        is_alive = getattr(task, "is_alive", None)
        if callable(is_alive):
            return not bool(is_alive())
        return bool(getattr(task, "dead", True))

    def _drain_tasks(self, *, timeout_s: float) -> None:
        deadline = time.monotonic() + max(0.0, float(timeout_s))
        for task in list(self._tasks):
            while not self._task_finished(task) and time.monotonic() < deadline:
                self.socketio.sleep(0.05)
            if not self._task_finished(task):
                # Greenlets can be killed; threads exit via the session's
                # stop flag and are daemonized by flask-socketio, so an
                # overrunning thread is abandoned rather than force-killed.
                kill_fn = getattr(task, "kill", None)
                if callable(kill_fn):
                    try:
                        kill_fn()
                    except Exception:
                        pass
        self._tasks = [task for task in self._tasks if not self._task_finished(task)]

    def shutdown(self, *, timeout_s: float = 5.0) -> None:
        with self._transition_lock:
            session = self.session
            self.session = None
            if session is not None:
                session.stop()
            self._drain_tasks(timeout_s=timeout_s)
            self.emit_status()

    def set_speed(self, data) -> None:
        if self.session is None:
            return
        self.session.set_speed(data)
        self.emit_status()
