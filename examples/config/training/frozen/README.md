# Frozen Leader Baseline

This directory contains the maintained leader-layer training entry points for the frozen common-core substrate.

Status for everything linked from here is `Frozen Baseline` unless a note explicitly calls out lineage into `Archived` history.

## Baseline Configs

- [leader_task_only_frozen_v1.json](/home/void0312/CMO/examples/config/training/frozen/leader_task_only_frozen_v1.json)
  - Preserves the inherited task-only baseline after the substrate freeze.
- [leader_c2_frozen_v1.json](/home/void0312/CMO/examples/config/training/frozen/leader_c2_frozen_v1.json)
  - Preserves the inherited reporting/full-chain baseline after the substrate freeze.

## Execution Curriculum

- [execution/README.md](/home/void0312/CMO/examples/config/training/frozen/execution/README.md)
  - Post-freeze execution-layer `p2 -> p3 -> p4 -> p4b -> p5` curriculum.

## Retrain Configs

- [leader_task_only_retrain_v1.json](/home/void0312/CMO/examples/config/training/frozen/leader_task_only_retrain_v1.json)
  - Main task-only retrain config for producing a native post-freeze leader model.
- [leader_task_only_retrain_smoke_v1.json](/home/void0312/CMO/examples/config/training/frozen/leader_task_only_retrain_smoke_v1.json)
  - Short smoke run for task-only launch validation.
- [leader_c2_retrain_v1.json](/home/void0312/CMO/examples/config/training/frozen/leader_c2_retrain_v1.json)
  - Main reporting/full-chain retrain config for the frozen substrate.
- [leader_c2_retrain_smoke_v1.json](/home/void0312/CMO/examples/config/training/frozen/leader_c2_retrain_smoke_v1.json)
  - Short smoke run for reporting/full-chain launch validation.

## Lineage

- `leader_task_only_retrain_*`
  - derived from [p6_leader_layer_frozen_exec_generalization_v1.json](/home/void0312/CMO/examples/config/Archive/training/leader_legacy/p6_leader_layer_frozen_exec_generalization_v1.json)
  - adjusted to run directly on the frozen common-core substrate and target the current randomized task-only gap
- `leader_c2_retrain_*`
  - derived from [p7_leader_layer_c2_reporting_generalization_v1.json](/home/void0312/CMO/examples/config/Archive/training/leader_legacy/p7_leader_layer_c2_reporting_generalization_v1.json) and [p7_leader_layer_c2_reporting_generalization_fast_v2.json](/home/void0312/CMO/examples/config/Archive/training/leader_legacy/p7_leader_layer_c2_reporting_generalization_fast_v2.json)
  - adjusted to use the frozen execution artifact and the current frozen acceptance set

## Acceptance Targets

- `leader_task_only_retrain_*`
  - [leader_task_only_generalization_frozen_v1.json](/home/void0312/CMO/tests/contracts/unit/training/frozen/leader_task_only_generalization_frozen_v1.json)
  - [leader_task_only_randomized_frozen_v1.json](/home/void0312/CMO/tests/contracts/unit/training/frozen/leader_task_only_randomized_frozen_v1.json)
- `leader_c2_retrain_*`
  - [leader_full_chain_demo_frozen_v1.json](/home/void0312/CMO/tests/contracts/unit/training/frozen/leader_full_chain_demo_frozen_v1.json)
  - [leader_full_chain_randomized_frozen_v1.json](/home/void0312/CMO/tests/contracts/unit/training/frozen/leader_full_chain_randomized_frozen_v1.json)

## Recommended Scenario Pairing

- `leader_task_only_retrain_*`
  - smoke/main scenario: `scenarios/combined/takeoff_to_landing_c2_task_only_train_v1.json`
- `leader_c2_retrain_*`
  - smoke scenario: `scenarios/combined/takeoff_to_landing_c2_task_demo_fasttrain_v1.json`
  - main scenario: `scenarios/combined/takeoff_to_landing_c2_task_demo_v1.json`

## Verified Smoke Commands

```bash
./.venv/bin/python train.py \
  --scenario scenarios/combined/takeoff_to_landing_c2_task_only_train_v1.json \
  --train_config examples/config/training/frozen/leader_task_only_retrain_smoke_v1.json \
  --run_name leader_task_only_retrain_smoke_verify_20260323 \
  --output_base /tmp/cmo_frozen_smoke
```

```bash
./.venv/bin/python train.py \
  --scenario scenarios/combined/takeoff_to_landing_c2_task_demo_fasttrain_v1.json \
  --train_config examples/config/training/frozen/leader_c2_retrain_smoke_v1.json \
  --run_name leader_c2_retrain_smoke_verify_20260323 \
  --output_base /tmp/cmo_frozen_smoke
```

## Artifact Policy

- Frozen execution model:
  - `experiments/_archive_20260322_test_results/root_level/experiments_tmp/20260318_p5_takeoff_to_landing_continuous_v3_retrain_v1/final_model.zip`
- Maintained execution train config lineage:
  - [execution/p5_continuous_retrain_v1.json](/home/void0312/CMO/examples/config/training/frozen/execution/p5_continuous_retrain_v1.json)
- Archived historical leader configs:
  - [examples/config/Archive/training/leader_legacy](/home/void0312/CMO/examples/config/Archive/training/leader_legacy/README.md)

Use this directory, not `examples/config/Archive/**`, when a maintained contract, bridge, or smoke recipe needs the frozen leader/execution baseline.
