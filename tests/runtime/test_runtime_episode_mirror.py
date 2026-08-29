from __future__ import annotations

from copy import deepcopy

import pytest

from tests.runtime.shadow_runtime_episode_mirror import (
    EpisodeMirrorError,
    EpisodeMirrorState,
    NativeEpisodeMirror,
    episode_transition_intent_sha256,
    episode_transition_receipt_sha256,
)


HASH = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
HASH2 = "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"


def identity(high: int, low: int) -> dict[str, int]:
  return {"high": high, "low": low}


def episode(
  generation: int = 1,
  episode_low: int = 7,
  world_generation: int = 1,
) -> dict[str, object]:
  return {
    "world": {
      "incarnation": {
        "host": {"host_id": identity(1, 2), "boot_id": identity(3, 4)},
        "incarnation_epoch": 1,
      },
      "world_slot": 0,
      "world_generation": world_generation,
    },
    "episode_id": identity(5, episode_low),
    "episode_generation": generation,
  }


def receipt(
  *,
  kind: str = "action",
  before: dict[str, object] | None = None,
  after: dict[str, object] | None = None,
  previous: int = 0,
  resulting: int = 1,
  phase: str = "running",
  terminal: bool = False,
  reset_applied: bool = False,
  barrier: int = 0,
) -> dict[str, object]:
  before = deepcopy(before or episode())
  after = deepcopy(after or before)
  value: dict[str, object] = {
    "protocol_generation": 1,
    "kind": kind,
    "idempotency_key": identity(8, 9 if kind == "action" else 10),
    "episode_before": before,
    "episode_after": after,
    "previous_step_sequence": previous,
    "resulting_step_sequence": resulting,
    "resulting_phase": phase,
    "terminal": terminal,
    "reset_applied": reset_applied,
    "snapshot_id": identity(11, 12),
    "snapshot_sha256": HASH2,
    "barrier_sequence": barrier,
    "receipt_sha256": "0" * 64,
  }
  value["receipt_sha256"] = episode_transition_receipt_sha256(value)
  return value


def mirror() -> NativeEpisodeMirror:
  return NativeEpisodeMirror(EpisodeMirrorState(
    episode=episode(),
    phase="running",
    step_sequence=0,
    barrier_sequence=0,
    snapshot_id=identity(13, 14),
    snapshot_sha256=HASH,
  ))


def test_action_receipt_updates_mirror_and_replay_is_idempotent() -> None:
  state = mirror()
  action = receipt()
  assert action["receipt_sha256"] == "280f80bf64d46f9b2746f5d450dc8456e8fff4a1fe6180dd5c3e8b6a608370fe"
  first = state.apply_receipt(action)
  assert not first.replayed
  assert first.state.step_sequence == 1
  assert first.state.phase == "running"
  second = state.apply_receipt(action)
  assert second.replayed
  assert second.state == first.state
  state.acknowledge_receipt(action)
  with pytest.raises(EpisodeMirrorError, match="local guessing is forbidden"):
    state.apply_receipt(action)


def test_intent_canonical_vector_includes_authority_bit() -> None:
  intent = {
    "protocol_generation": 1,
    "kind": "action",
    "expected_episode": episode(),
    "expected_step_sequence": 0,
    "idempotency_key": identity(8, 9),
    "payload_sha256": HASH,
    "production_authorized": False,
  }
  assert episode_transition_intent_sha256(intent) == "7a9b047d12c941acf2153bb69d4bb20b0fba6feec9f9b2b92d845df503ab1c71"


def test_terminal_then_native_reset_receipt_advances_episode() -> None:
  state = mirror()
  terminal = receipt(phase="terminal", terminal=True)
  state.apply_receipt(terminal)
  reset = receipt(
    kind="reset",
    before=episode(),
    after=episode(2, 15, 2),
    previous=1,
    resulting=0,
    phase="running",
    reset_applied=True,
    barrier=1,
  )
  applied = state.apply_receipt(reset)
  assert applied.state.episode["episode_generation"] == 2
  assert applied.state.step_sequence == 0
  assert applied.state.barrier_sequence == 1


def test_gap_digest_and_python_authored_reset_fail_closed() -> None:
  state = mirror()
  gap = receipt(previous=1, resulting=2)
  with pytest.raises(EpisodeMirrorError, match="local guessing is forbidden") as gap_error:
    state.apply_receipt(gap)
  assert gap_error.value.code == "mirror.resync_required"

  tampered = receipt()
  tampered["snapshot_sha256"] = HASH
  with pytest.raises(EpisodeMirrorError, match="digest mismatch") as digest_error:
    state.apply_receipt(tampered)
  assert digest_error.value.code == "receipt.digest"

  unauthorized_reset = receipt(
    kind="reset",
    before=episode(),
    after=episode(2, 16, 2),
    previous=0,
    resulting=0,
    phase="running",
    reset_applied=True,
    barrier=1,
  )
  with pytest.raises(EpisodeMirrorError, match="reset receipt violates native authority"):
    state.apply_receipt(unauthorized_reset)


def test_unknown_fields_and_old_protocol_generation_are_rejected() -> None:
  state = mirror()
  unknown = receipt()
  unknown["python_autoreset"] = True
  with pytest.raises(EpisodeMirrorError, match="unknown or missing fields"):
    state.apply_receipt(unknown)

  old = receipt()
  old["protocol_generation"] = 0
  with pytest.raises(EpisodeMirrorError, match="unsupported episode handshake generation"):
    state.apply_receipt(old)
