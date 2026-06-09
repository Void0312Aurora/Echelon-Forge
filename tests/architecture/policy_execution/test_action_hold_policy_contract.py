from __future__ import annotations

import textwrap

from tests.architecture.helpers import REPO_ROOT, compile_cpp_snippet

POLICY_HEADER = REPO_ROOT / "src" / "runtime" / "contracts" / "policy_contracts.h"


def _compile_and_run(source: str):
    return compile_cpp_snippet(source, binary_prefix="policy_action_hold_contract")


def test_action_hold_policy_contract_is_explicitly_declarative_not_runtime_scheduler_logic() -> None:
    header = POLICY_HEADER.read_text(encoding="utf-8")

    assert "declarative_only_contract_runtime_cadence_not_implemented" in header
    assert "scheduler" not in header.lower()
    assert "step_batch(" not in header
    assert "ecs.progress" not in header
    assert "multi-rate" not in header.lower()


def test_action_hold_policy_normalizer_fails_closed_for_invalid_mode() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include "runtime/contracts/policy_contracts.h"

        int main() {
            ActionHoldPolicy policy{};
            policy.hold_mode = "wild_guess";
            policy.expiry_behavior = "linger_forever";
            policy.interpolation_mode = "bezier";
            policy.validity_duration_s = -3.0;
            policy.refresh_cadence_s = -2.0;
            policy.target_control_cadence_s = -1.0;
            policy.credit_assignment_latency_s = -4.0;
            policy.diagnostics_reason.clear();

            const ActionHoldPolicy normalized = normalize_action_hold_policy(policy);
            if (normalized.hold_mode != "drop") {
                std::cerr << "hold_mode_not_fail_closed\n";
                return 1;
            }
            if (normalized.expiry_behavior != "drop") {
                std::cerr << "expiry_behavior_not_fail_closed\n";
                return 1;
            }
            if (normalized.interpolation_mode != "none") {
                std::cerr << "interpolation_mode_not_reset\n";
                return 1;
            }
            if (normalized.validity_duration_s != 0.0 ||
                normalized.refresh_cadence_s != 0.0 ||
                normalized.target_control_cadence_s != 0.0 ||
                normalized.credit_assignment_latency_s != 0.0) {
                std::cerr << "negative_durations_not_clamped\n";
                return 1;
            }
            if (normalized.diagnostics_reason != "unsupported_action_hold_mode_fail_closed_to_drop") {
                std::cerr << "diagnostics_reason_unexpected\n";
                return 1;
            }
            return 0;
        }
        """
    )

    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_action_hold_policy_supported_interpolate_mode_preserves_linear_setting() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include "runtime/contracts/policy_contracts.h"

        int main() {
            ActionHoldPolicy policy{};
            policy.hold_mode = "interpolate";
            policy.expiry_behavior = "expire";
            policy.interpolation_mode = "linear";
            policy.validity_duration_s = 0.15;
            policy.refresh_cadence_s = 0.1;
            policy.target_control_cadence_s = 0.05;
            policy.credit_assignment_latency_s = 0.2;

            const ActionHoldPolicy normalized = normalize_action_hold_policy(policy);
            if (normalized.hold_mode != "interpolate") {
                std::cerr << "hold_mode_changed\n";
                return 1;
            }
            if (normalized.expiry_behavior != "expire") {
                std::cerr << "expiry_behavior_changed\n";
                return 1;
            }
            if (normalized.interpolation_mode != "linear") {
                std::cerr << "interpolation_mode_changed\n";
                return 1;
            }
            return 0;
        }
        """
    )

    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout
