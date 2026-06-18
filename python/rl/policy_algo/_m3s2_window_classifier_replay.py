"""Balanced replay buffer for the M3-S2 window classifier head.

Extracted from ``ppo_adaptive_kl.py`` as a subdomain helper. The replay
supports both latent-vector and observation-dict storage and is self-contained:
it holds no reference to the surrounding algorithm and is exercised directly by
the auxiliary-update tests.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch as th


@dataclass
class _M3S2WindowClassifierReplay:
    capacity: int
    storage: str = "latent"
    positives: th.Tensor | None = None
    negatives: th.Tensor | None = None
    positive_observations: dict[str, th.Tensor] | None = None
    negative_observations: dict[str, th.Tensor] | None = None

    @property
    def positive_count(self) -> int:
        if self.storage == "observation":
            return self._observation_count(self.positive_observations)
        return 0 if self.positives is None else int(self.positives.shape[0])

    @property
    def negative_count(self) -> int:
        if self.storage == "observation":
            return self._observation_count(self.negative_observations)
        return 0 if self.negatives is None else int(self.negatives.shape[0])

    def append(
        self,
        latents: th.Tensor,
        labels: th.Tensor,
        *,
        observations: dict[str, th.Tensor] | None = None,
    ) -> None:
        if int(latents.numel()) <= 0 or int(labels.numel()) <= 0:
            return
        flat_labels = labels.detach().reshape(-1).to(device="cpu") > 0.5
        if self.storage == "observation":
            if observations is None:
                raise ValueError("M3-S2 window classifier observation replay requires observations")
            self._append_observations(observations, flat_labels)
            return

        flat_latents = (
            latents.detach().reshape(int(latents.shape[0]), -1).to(device="cpu", dtype=th.float32)
        )
        if int(flat_labels.numel()) != int(flat_latents.shape[0]):
            raise ValueError(
                "M3-S2 window classifier replay latents and labels must have matching rows"
            )
        self.positives = self._append_rows(self.positives, flat_latents[flat_labels])
        self.negatives = self._append_rows(self.negatives, flat_latents[~flat_labels])

    def can_sample(self, *, min_positive: int = 1, min_negative: int = 1) -> bool:
        return bool(
            self.positive_count >= max(1, int(min_positive))
            and self.negative_count >= max(1, int(min_negative))
        )

    def sample_balanced(
        self,
        *,
        batch_size: int,
        device: th.device,
        dtype: th.dtype,
    ) -> tuple[th.Tensor | dict[str, th.Tensor], th.Tensor] | None:
        if self.storage == "observation":
            return self._sample_observations_balanced(
                batch_size=batch_size, device=device, dtype=dtype
            )
        if self.positives is None or self.negatives is None:
            return None
        if self.positive_count <= 0 or self.negative_count <= 0:
            return None
        per_class = max(1, int(batch_size) // 2)
        pos_idx = th.randint(self.positive_count, (per_class,), device=th.device("cpu"))
        neg_idx = th.randint(self.negative_count, (per_class,), device=th.device("cpu"))
        pos_latents = self.positives[pos_idx]
        neg_latents = self.negatives[neg_idx]
        latents = th.cat((pos_latents, neg_latents), dim=0).to(device=device, dtype=dtype)
        labels = th.cat(
            (
                th.ones((per_class,), dtype=dtype),
                th.zeros((per_class,), dtype=dtype),
            ),
            dim=0,
        ).to(device=device)
        order = th.randperm(int(labels.numel()), device=device)
        return latents[order], labels[order]

    def _append_rows(self, current: th.Tensor | None, new_rows: th.Tensor) -> th.Tensor | None:
        if int(new_rows.numel()) <= 0:
            return current
        rows = (
            new_rows.detach().reshape(int(new_rows.shape[0]), -1).to(device="cpu", dtype=th.float32)
        )
        if current is None:
            combined = rows
        else:
            combined = th.cat((current, rows), dim=0)
        capacity = max(1, int(self.capacity))
        if int(combined.shape[0]) > capacity:
            combined = combined[-capacity:]
        return combined.contiguous()

    @staticmethod
    def _observation_count(observations: dict[str, th.Tensor] | None) -> int:
        if not observations:
            return 0
        for value in observations.values():
            return int(value.shape[0])
        return 0

    def _append_observations(self, observations: dict[str, th.Tensor], labels: th.Tensor) -> None:
        if not observations:
            return
        flat_labels = labels.reshape(-1).to(device="cpu", dtype=th.bool)
        row_count = int(flat_labels.numel())
        cpu_observations: dict[str, th.Tensor] = {}
        for key, value in observations.items():
            tensor = value.detach().to(device="cpu")
            if int(tensor.shape[0]) != row_count:
                raise ValueError(
                    "M3-S2 window classifier replay observations and labels must match rows"
                )
            cpu_observations[str(key)] = tensor
        positive_rows = {key: value[flat_labels] for key, value in cpu_observations.items()}
        negative_rows = {key: value[~flat_labels] for key, value in cpu_observations.items()}
        self.positive_observations = self._append_observation_rows(
            self.positive_observations, positive_rows
        )
        self.negative_observations = self._append_observation_rows(
            self.negative_observations, negative_rows
        )

    def _append_observation_rows(
        self,
        current: dict[str, th.Tensor] | None,
        new_rows: dict[str, th.Tensor],
    ) -> dict[str, th.Tensor] | None:
        row_count = self._observation_count(new_rows)
        if row_count <= 0:
            return current
        if current is None:
            combined = {key: value.contiguous() for key, value in new_rows.items()}
        else:
            if set(current.keys()) != set(new_rows.keys()):
                raise ValueError("M3-S2 window classifier replay observation keys changed")
            combined = {key: th.cat((current[key], new_rows[key]), dim=0) for key in current.keys()}
        capacity = max(1, int(self.capacity))
        if self._observation_count(combined) > capacity:
            combined = {key: value[-capacity:].contiguous() for key, value in combined.items()}
        return combined

    def _sample_observations_balanced(
        self,
        *,
        batch_size: int,
        device: th.device,
        dtype: th.dtype,
    ) -> tuple[dict[str, th.Tensor], th.Tensor] | None:
        if self.positive_observations is None or self.negative_observations is None:
            return None
        if self.positive_count <= 0 or self.negative_count <= 0:
            return None
        if set(self.positive_observations.keys()) != set(self.negative_observations.keys()):
            raise ValueError("M3-S2 window classifier replay observation keys differ by class")
        per_class = max(1, int(batch_size) // 2)
        pos_idx = th.randint(self.positive_count, (per_class,), device=th.device("cpu"))
        neg_idx = th.randint(self.negative_count, (per_class,), device=th.device("cpu"))
        observations = {
            key: th.cat(
                (
                    self.positive_observations[key][pos_idx],
                    self.negative_observations[key][neg_idx],
                ),
                dim=0,
            ).to(device=device)
            for key in self.positive_observations.keys()
        }
        labels = th.cat(
            (
                th.ones((per_class,), dtype=dtype),
                th.zeros((per_class,), dtype=dtype),
            ),
            dim=0,
        ).to(device=device)
        order = th.randperm(int(labels.numel()), device=device)
        observations = {key: value[order] for key, value in observations.items()}
        return observations, labels[order]

    def calibration_balanced(
        self,
        *,
        max_rows: int,
        device: th.device,
        dtype: th.dtype,
    ) -> tuple[th.Tensor | dict[str, th.Tensor], th.Tensor] | None:
        if self.positive_count <= 0 or self.negative_count <= 0:
            return None
        max_rows = int(max_rows)
        if max_rows <= 0:
            max_rows = self.positive_count + self.negative_count
        per_class = max(1, min(self.positive_count, self.negative_count, max_rows // 2))
        if self.storage == "observation":
            if self.positive_observations is None or self.negative_observations is None:
                return None
            if set(self.positive_observations.keys()) != set(self.negative_observations.keys()):
                raise ValueError("M3-S2 window classifier replay observation keys differ by class")
            observations = {
                key: th.cat(
                    (
                        self.positive_observations[key][-per_class:],
                        self.negative_observations[key][-per_class:],
                    ),
                    dim=0,
                ).to(device=device)
                for key in self.positive_observations.keys()
            }
            labels = th.cat(
                (
                    th.ones((per_class,), dtype=dtype),
                    th.zeros((per_class,), dtype=dtype),
                ),
                dim=0,
            ).to(device=device)
            return observations, labels
        if self.positives is None or self.negatives is None:
            return None
        latents = th.cat((self.positives[-per_class:], self.negatives[-per_class:]), dim=0).to(
            device=device,
            dtype=dtype,
        )
        labels = th.cat(
            (
                th.ones((per_class,), dtype=dtype),
                th.zeros((per_class,), dtype=dtype),
            ),
            dim=0,
        ).to(device=device)
        return latents, labels
