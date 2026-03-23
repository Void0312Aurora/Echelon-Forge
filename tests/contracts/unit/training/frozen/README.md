# Frozen Leader Acceptance Set

This directory contains the maintained leader-layer acceptance specs for the frozen common-core substrate.

## Gating Baseline Specs

- [leader_task_only_generalization_frozen_v1.json](/home/void0312/CMO/tests/contracts/unit/training/frozen/leader_task_only_generalization_frozen_v1.json)
- [leader_full_chain_demo_frozen_v1.json](/home/void0312/CMO/tests/contracts/unit/training/frozen/leader_full_chain_demo_frozen_v1.json)

## Supplemental Matrix Specs

- [leader_full_chain_randomized_frozen_v1.json](/home/void0312/CMO/tests/contracts/unit/training/frozen/leader_full_chain_randomized_frozen_v1.json)
- [leader_task_only_randomized_frozen_v1.json](/home/void0312/CMO/tests/contracts/unit/training/frozen/leader_task_only_randomized_frozen_v1.json)

The supplemental task-only randomized matrix is retained for follow-up tuning, but it is not promoted to the frozen gating set because it is currently unstable under the present leader/runtime baseline.

## Usage

```bash
./.venv/bin/python tools/runners/run_scenario_contract.py \
  --spec tests/contracts/unit/training/frozen/leader_full_chain_demo_frozen_v1.json
```

```bash
./.venv/bin/python tools/runners/run_scenario_contract.py \
  --spec tests/contracts/unit/training/frozen/leader_task_only_randomized_frozen_v1.json
```
