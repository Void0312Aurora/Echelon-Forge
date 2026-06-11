from __future__ import annotations

from tests.architecture.structural_boundaries.helpers import *


def test_wp22_counterfactual_structural_split_promotes_types_and_validation_owners() -> None:
  header_text = _text(COUNTERFACTUAL_HEADER)
  constants_text = _text(COUNTERFACTUAL_CONSTANTS)
  types_text = _text(COUNTERFACTUAL_TYPES)
  validation_text = _text(COUNTERFACTUAL_VALIDATION)
  helper_text = _text(COUNTERFACTUAL_VALIDATION_HELPERS)
  replay_validation_text = _text(COUNTERFACTUAL_REPLAY_VALIDATION)
  counterfactual_validation_text = _text(COUNTERFACTUAL_COUNTERFACTUAL_VALIDATION)
  experiment_validation_text = _text(COUNTERFACTUAL_EXPERIMENT_VALIDATION)

  assert '#include "runtime/contracts/counterfactual_replay_contract_constants.h"' in header_text
  assert '#include "runtime/contracts/counterfactual_replay_contract_types.h"' in header_text
  assert '#include "runtime/contracts/counterfactual_replay_contract_validation.h"' in header_text
  assert '#include "runtime/contracts/counterfactual_replay_counterfactual_validation.h"' in validation_text
  assert '#include "runtime/contracts/counterfactual_replay_experiment_validation.h"' in validation_text
  assert "struct ReplayEnvelope;" in header_text
  assert "validate_replay_envelope(" in header_text
  assert "struct ReplayEnvelope" not in constants_text
  assert "validate_replay_envelope(" not in constants_text
  assert "struct ReplayEnvelope {" in types_text
  assert "validate_replay_envelope(" not in types_text
  assert "replay_contract_is_blank(" in helper_text
  assert "validate_replay_envelope(" in replay_validation_text
  assert "validate_counterfactual_experiment_request(" in counterfactual_validation_text
  assert "make_experiment_evidence_bridge_record(" in experiment_validation_text
  assert "struct ReplayEnvelope {" not in replay_validation_text
  assert "struct ReplayEnvelope {" not in counterfactual_validation_text
  assert "struct ReplayEnvelope {" not in experiment_validation_text

  for marker in COUNTERFACTUAL_CONSTANT_ALLOWLIST:
    assert marker in constants_text, f"missing structural constant marker: {marker}"

  assert COUNTERFACTUAL_HEADER.stat().st_size < COUNTERFACTUAL_TYPES.stat().st_size
  assert COUNTERFACTUAL_HEADER.stat().st_size < COUNTERFACTUAL_REPLAY_VALIDATION.stat().st_size
  assert (
    COUNTERFACTUAL_HEADER.stat().st_size <
    COUNTERFACTUAL_COUNTERFACTUAL_VALIDATION.stat().st_size
  )
  assert (
    COUNTERFACTUAL_HEADER.stat().st_size <
    COUNTERFACTUAL_EXPERIMENT_VALIDATION.stat().st_size
  )

def test_wp22_counterfactual_validation_umbrella_stays_below_split_threshold() -> None:
  line_count = _line_count(COUNTERFACTUAL_VALIDATION)
  assert line_count < 300, (
    "WP22-E counterfactual validation umbrella should stay focused once family helpers "
    "are split into named companion headers"
  )

def test_wp22_counterfactual_contract_header_drops_below_closure_threshold() -> None:
  line_count = _line_count(COUNTERFACTUAL_HEADER)
  assert line_count < COUNTERFACTUAL_CLOSURE_BLOCKING_MAX_LINES, (
    "WP22-E counterfactual structural split is not complete until the public umbrella "
    "header falls below the 1500-line closure threshold"
  )
