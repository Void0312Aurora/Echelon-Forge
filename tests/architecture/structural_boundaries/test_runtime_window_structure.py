from __future__ import annotations

from tests.architecture.structural_boundaries.helpers import *


def test_wp22_runtime_window_coordinator_split_advances_with_named_helper_owners() -> None:
  header_text = _text(WINDOW_COORDINATOR)
  helper_text = _text(WINDOW_COORDINATOR_HELPERS)
  selection_text = _text(WINDOW_COORDINATOR_SELECTION_HELPERS)
  callback_text = _text(WINDOW_COORDINATOR_CALLBACK_HELPERS)
  cadence_text = _text(WINDOW_COORDINATOR_CADENCE_TRACE_HELPERS)
  execution_text = _text(WINDOW_COORDINATOR_EXECUTION_HELPERS)

  assert '#include "runtime/facade/runtime_window_coordinator_helpers.h"' in header_text
  assert '#include "runtime/facade/runtime_window_coordinator_selection_helpers.h"' in header_text
  assert '#include "runtime/facade/runtime_window_coordinator_callback_helpers.h"' in header_text
  assert '#include "runtime/facade/runtime_window_coordinator_cadence_trace_helpers.h"' in header_text
  assert '#include "runtime/facade/runtime_window_coordinator_execution_helpers.h"' in header_text
  for marker in WINDOW_COORDINATOR_MAIN_MARKERS:
    assert marker in header_text
  for marker in WINDOW_COORDINATOR_HELPER_MARKERS:
    assert marker in helper_text
  for marker in WINDOW_COORDINATOR_SELECTION_HELPER_MARKERS:
    assert marker in selection_text
    function_name = marker.split("(")[0]
    assert _has_inline_definition(selection_text, function_name)
    assert not _has_inline_definition(header_text, function_name)
  for marker in WINDOW_COORDINATOR_CALLBACK_HELPER_MARKERS:
    assert marker in callback_text
    function_name = marker.split("(")[0]
    assert _has_inline_definition(callback_text, function_name)
    assert not _has_inline_definition(header_text, function_name)
  for marker in WINDOW_COORDINATOR_CADENCE_TRACE_HELPER_MARKERS:
    assert marker in cadence_text
    function_name = marker.split("(")[0]
    assert _has_inline_definition(cadence_text, function_name)
    assert not _has_inline_definition(header_text, function_name)
  for marker in WINDOW_COORDINATOR_EXECUTION_HELPER_MARKERS:
    assert marker in execution_text
    function_name = marker.split("(")[0]
    assert _has_inline_definition(execution_text, function_name)
    assert not _has_inline_definition(header_text, function_name)

  assert "runtime_window_requests_conflict(" in header_text
  assert "runtime_window_requests_conflict(" not in helper_text
  assert "execute_runtime_window(" in header_text
  assert "execute_runtime_window(" not in helper_text
  assert "execute_runtime_window(" not in selection_text
  assert "execute_runtime_window(" not in callback_text
  assert "execute_runtime_window(" not in cadence_text
  assert "execute_runtime_window(" not in execution_text

def test_wp22_runtime_window_coordinator_header_drops_below_closure_threshold() -> None:
  line_count = _line_count(WINDOW_COORDINATOR)
  assert line_count < WINDOW_COORDINATOR_CLOSURE_BLOCKING_MAX_LINES, (
    "WP22-E runtime-window structural split is not complete until the coordinator header "
    "falls below the post-helper closure threshold"
  )
