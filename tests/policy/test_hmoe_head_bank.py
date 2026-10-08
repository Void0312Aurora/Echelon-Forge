from __future__ import annotations

from copy import deepcopy

import pytest
import torch as th

from python.rl.policy_algo.hmoe_routing import DEFAULT_FAMILY_SUBEXPERT_COUNTS
from python.rl.policy_algo.policies import _HMoEHeadBank
from tools.diagnostics.hmoe_head_bank_benchmark import reference_forward


@pytest.mark.parametrize("device", ["cpu", pytest.param("cuda", marks=pytest.mark.skipif(
    not th.cuda.is_available(), reason="CUDA device unavailable"))])
@pytest.mark.parametrize("routing", ["empty_batch", "single_family", "mixed", "empty_subexperts"])
def test_hmoe_output_gradients_and_optimizer_parity(device, routing):
    th.manual_seed(41)
    current = _HMoEHeadBank(8, 4, family_subexpert_counts=DEFAULT_FAMILY_SUBEXPERT_COUNTS).to(device)
    for parameter in current.parameters():
        th.nn.init.normal_(parameter, std=0.2)
    original = deepcopy(current)
    # Existing checkpoint keys/shapes still load without a migration.
    current.load_state_dict(original.state_dict(), strict=True)
    current_optimizer = th.optim.Adam(current.parameters(), lr=1e-3, weight_decay=0.01)
    original_optimizer = th.optim.Adam(original.parameters(), lr=1e-3, weight_decay=0.01)
    batch = 0 if routing == "empty_batch" else 17
    for iteration in range(2):
        latent = th.randn(batch, 8, device=device, requires_grad=True)
        reference_latent = latent.detach().clone().requires_grad_(True)
        indices = th.arange(batch, device=device)
        family = indices % 5 if routing in ("mixed", "empty_subexperts") else th.full_like(indices, iteration)
        subexpert = th.zeros_like(indices) if routing == "empty_subexperts" else indices % 4 - 1
        observed = current(latent, family, subexpert)
        expected = reference_forward(original, reference_latent, family, subexpert)
        th.testing.assert_close(observed, expected, rtol=1e-6, atol=1e-6)
        assert observed.shape == (batch, 4) and observed.device == latent.device
        assert observed.dtype == latent.dtype
        if batch == 0:
            assert observed.requires_grad == expected.requires_grad
            continue
        observed.square().sum().backward()
        expected.square().sum().backward()
        th.testing.assert_close(latent.grad, reference_latent.grad, rtol=1e-5, atol=1e-6)
        for actual_parameter, expected_parameter in zip(current.parameters(), original.parameters()):
            assert (actual_parameter.grad is None) == (expected_parameter.grad is None)
            if actual_parameter.grad is not None:
                th.testing.assert_close(actual_parameter.grad, expected_parameter.grad, rtol=1e-5, atol=1e-6)
        current_optimizer.step()
        original_optimizer.step()
        for actual_parameter, expected_parameter in zip(current.parameters(), original.parameters()):
            th.testing.assert_close(actual_parameter, expected_parameter, rtol=1e-6, atol=1e-6)
        current_optimizer.zero_grad(set_to_none=True)
        original_optimizer.zero_grad(set_to_none=True)


def test_hmoe_occupancy_has_no_scalar_extraction_events():
    bank = _HMoEHeadBank(8, 4, family_subexpert_counts=DEFAULT_FAMILY_SUBEXPERT_COUNTS)
    latent = th.randn(17, 8)
    indices = th.arange(17)
    with th.profiler.profile(activities=[th.profiler.ProfilerActivity.CPU]) as profile:
        bank(latent, indices % 5, indices % 3)
    assert "aten::item" not in {event.key for event in profile.key_averages()}
