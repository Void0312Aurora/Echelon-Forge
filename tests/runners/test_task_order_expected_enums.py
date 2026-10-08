import copy
import json
from pathlib import Path

import pytest

from python.testing.contracts.unit.comm import _check_task_order_common_core


def fixture():
    path = Path(__file__).resolve().parents[2] / 'tests/contracts/unit/comm/task_order_common_core_defaults.json'
    return json.loads(path.read_text(encoding='utf-8'))


@pytest.mark.parametrize('value', ['DELIBERATELY_WRONG_VALUE', '', 999999, None, True, 1.5])
def test_invalid_explicit_expectation_fails(value):
    spec = fixture()
    spec['expected_common_core']['coordination_mode'] = value
    ok, reason = _check_task_order_common_core(spec)
    assert not ok
    assert 'invalid expected enum coordination_mode' in reason


def test_independent_expected_values_and_omitted_defaults():
    spec = fixture()
    assert _check_task_order_common_core(spec)[0]
    for name, value in [('coordination_mode', 'Independent'), ('coordination_mode', 'Unspecified'),
                        ('recovery_site_id', 999999)]:
        mutant = copy.deepcopy(spec)
        mutant['expected_common_core'][name] = value
        assert not _check_task_order_common_core(mutant)[0]
    del spec['expected_common_core']['coordination_mode']
    assert _check_task_order_common_core(spec)[0]
