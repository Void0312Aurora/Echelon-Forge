from __future__ import annotations

import pytest
import torch

from _world_model_train_impl.checkpoint import _checkpoint_tensor, _load_actor_checkpoint


class _FakeActor:
  def __init__(self, input_dim: int) -> None:
    self._state = {
      "net.net.0.weight": torch.zeros((2, input_dim), dtype=torch.float32),
      "net.net.0.bias": torch.zeros((2,), dtype=torch.float32),
    }

  def state_dict(self) -> dict[str, torch.Tensor]:
    return {key: value.clone() for key, value in self._state.items()}

  def load_state_dict(self, state: dict[str, torch.Tensor]) -> None:
    for key, current in self._state.items():
      if key not in state or state[key].shape != current.shape:
        raise RuntimeError(f"shape mismatch for {key}")
    self._state = {key: value.clone() for key, value in state.items()}


def test_actor_checkpoint_supported_migration_pads_new_inputs_with_zeros() -> None:
  actor = _FakeActor(input_dim=4)
  source = {
    "net.net.0.weight": torch.full((2, 2), 3.0, dtype=torch.float32),
    "net.net.0.bias": torch.full((2,), 4.0, dtype=torch.float32),
  }

  _load_actor_checkpoint(
    actor,
    source,
    source_input="embed",
    target_input="embed_sincos",
  )

  loaded = actor.state_dict()
  assert torch.equal(loaded["net.net.0.weight"][:, :2], source["net.net.0.weight"])
  assert torch.count_nonzero(loaded["net.net.0.weight"][:, 2:]) == 0
  assert torch.equal(loaded["net.net.0.bias"], source["net.net.0.bias"])


def test_actor_checkpoint_unsupported_migration_fails_closed() -> None:
  actor = _FakeActor(input_dim=4)
  source = actor.state_dict()

  with pytest.raises(RuntimeError, match="Unsupported actor checkpoint input migration"):
    _load_actor_checkpoint(
      actor,
      source,
      source_input="rssm",
      target_input="embed_sincos",
    )


def test_actor_checkpoint_supported_migration_rejects_partial_non_input_state() -> None:
  actor = _FakeActor(input_dim=4)
  source = {
    "net.net.0.weight": torch.full((2, 2), 3.0, dtype=torch.float32),
  }

  with pytest.raises(RuntimeError, match="non-input parameter keys differ"):
    _load_actor_checkpoint(
      actor,
      source,
      source_input="embed",
      target_input="embed_sincos",
    )


def test_actor_checkpoint_same_input_rejects_shape_padding() -> None:
  actor = _FakeActor(input_dim=6)
  source = {
    "net.net.0.weight": torch.full((2, 4), 3.0, dtype=torch.float32),
    "net.net.0.bias": torch.full((2,), 4.0, dtype=torch.float32),
  }

  with pytest.raises(RuntimeError, match="same actor_input.*reset_actor"):
    _load_actor_checkpoint(
      actor,
      source,
      source_input="embed_sincos",
      target_input="embed_sincos",
      source_angle_deg_indices=(9, 30),
      target_angle_deg_indices=(9, 30),
    )


@pytest.mark.parametrize(
  ("source_input", "target_input"),
  [
    ("embed_sincos", "embed_sincos"),
    ("embed_sincos", "embed_sincos_track"),
  ],
)
def test_actor_checkpoint_rejects_changed_sincos_feature_identity(
  source_input: str,
  target_input: str,
) -> None:
  actor = _FakeActor(input_dim=8)
  source = {
    "net.net.0.weight": torch.full((2, 6), 3.0, dtype=torch.float32),
    "net.net.0.bias": torch.full((2,), 4.0, dtype=torch.float32),
  }

  with pytest.raises(RuntimeError, match="angle_deg_indices do not match"):
    _load_actor_checkpoint(
      actor,
      source,
      source_input=source_input,
      target_input=target_input,
      source_angle_deg_indices=(9, 30),
      target_angle_deg_indices=(9, 30, 32),
    )


def test_checkpoint_normalization_tensor_requires_presence_and_matching_shape() -> None:
  current = torch.zeros((3,), dtype=torch.float32)

  with pytest.raises(RuntimeError, match="missing required normalization tensor"):
    _checkpoint_tensor({}, "obs_mean", current, device=torch.device("cpu"))

  with pytest.raises(RuntimeError, match="has shape"):
    _checkpoint_tensor(
      {"obs_mean": torch.zeros((2,), dtype=torch.float32)},
      "obs_mean",
      current,
      device=torch.device("cpu"),
    )


def test_checkpoint_std_tensor_applies_minimum_floor() -> None:
  restored = _checkpoint_tensor(
    {"obs_std": torch.tensor([0.0, 0.5], dtype=torch.float32)},
    "obs_std",
    torch.ones((2,), dtype=torch.float32),
    device=torch.device("cpu"),
    minimum=0.1,
  )

  assert restored is not None
  assert torch.allclose(restored, torch.tensor([0.1, 0.5], dtype=torch.float32))


def test_checkpoint_normalization_tensor_rejects_non_finite_values() -> None:
  current = torch.zeros((2,), dtype=torch.float32)

  with pytest.raises(RuntimeError, match="contains non-finite values"):
    _checkpoint_tensor(
      {"obs_mean": torch.tensor([0.0, float("nan")], dtype=torch.float32)},
      "obs_mean",
      current,
      device=torch.device("cpu"),
    )
