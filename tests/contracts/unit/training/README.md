# Leader Training Contracts

Maintained frozen-baseline acceptance specs now live under [frozen](/home/void0312/CMO/tests/contracts/unit/training/frozen/README.md).

- Use `frozen/` for the current authoritative leader acceptance/generalization matrix.
- Historical weak baselines and alternate task-chain variants have been moved to [tests/contracts/Archive/unit/training/leader_legacy](/home/void0312/CMO/tests/contracts/Archive/unit/training/leader_legacy/README.md).
- Historical pre-freeze root-level leader contracts have been moved to [tests/contracts/Archive/unit/training/leader_pre_frozen](/home/void0312/CMO/tests/contracts/Archive/unit/training/leader_pre_frozen/README.md).

The active leader acceptance entry point is now `frozen/`. Root-level files in this directory are no longer used for leader gating.
