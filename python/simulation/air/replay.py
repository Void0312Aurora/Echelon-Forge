"""Provider-independent replay consumption for semantic Air frames.

The replay consumer deliberately has no native or RL dependency.  It owns the
small lifecycle needed by visualizers and diagnostics so they can consume a
validated receipt without re-running the provider or reconstructing entity IDs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

from .scenario_runtime import AirFacadeFrame, AirFacadeReplayReceipt


class AirFacadeReplaySession:
    """Consume one validated Air replay receipt through a closed lifecycle."""

    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    STOPPED = "stopped"

    def __init__(self, receipt: AirFacadeReplayReceipt) -> None:
        if not isinstance(receipt, AirFacadeReplayReceipt):
            raise TypeError("Air replay session requires an AirFacadeReplayReceipt")
        receipt.verify()
        self.receipt = receipt
        self._status = self.READY
        self._cursor = -1

    @classmethod
    def from_json(cls, path: str | Path) -> "AirFacadeReplaySession":
        return cls(AirFacadeReplayReceipt.load_json(path))

    @property
    def status(self) -> str:
        return self._status

    @property
    def frame_index(self) -> int:
        """Zero-based consumed frame index, or -1 before the first frame."""

        return self._cursor

    @property
    def current_frame(self) -> AirFacadeFrame | None:
        if self._cursor < 0:
            return None
        return self.receipt.frames[self._cursor]

    def start(self) -> None:
        if self._status != self.READY:
            raise RuntimeError(f"Air replay session cannot start from {self._status!r}")
        self._status = self.RUNNING

    def pause(self) -> None:
        if self._status != self.RUNNING:
            raise RuntimeError(f"Air replay session cannot pause from {self._status!r}")
        self._status = self.PAUSED

    def resume(self) -> None:
        if self._status != self.PAUSED:
            raise RuntimeError(f"Air replay session cannot resume from {self._status!r}")
        self._status = self.RUNNING

    def stop(self) -> None:
        if self._status not in {self.COMPLETED, self.STOPPED}:
            self._status = self.STOPPED

    def close(self) -> None:
        """Close the consumer so generic visualization cleanup can own it."""

        self.stop()

    def reset(self) -> None:
        if self._status == self.RUNNING:
            raise RuntimeError("Air replay session must be paused or stopped before reset")
        self._cursor = -1
        self._status = self.READY

    def step(self) -> AirFacadeFrame | None:
        """Consume one frame; the final frame closes the session as completed."""

        if self._status != self.RUNNING:
            if self._status == self.COMPLETED:
                return None
            raise RuntimeError(f"Air replay session cannot step from {self._status!r}")
        next_index = self._cursor + 1
        if next_index >= len(self.receipt.frames):
            self._status = self.COMPLETED
            return None
        self._cursor = next_index
        frame = self.receipt.frames[next_index]
        if next_index == len(self.receipt.frames) - 1:
            self._status = self.COMPLETED
        return frame

    def iter_frames(self) -> Iterator[AirFacadeFrame]:
        """Yield all remaining frames while preserving lifecycle state."""

        if self._status == self.READY:
            self.start()
        while self._status == self.RUNNING:
            frame = self.step()
            if frame is None:
                break
            yield frame

    def status_payload(self) -> dict[str, int | str]:
        return {
            "status": self._status,
            "frame_index": int(self._cursor),
            "frame_count": len(self.receipt.frames),
            "seed": int(self.receipt.seed),
            "steps": int(self.receipt.steps),
            "digest": self.receipt.digest,
        }


__all__ = ["AirFacadeReplaySession"]
