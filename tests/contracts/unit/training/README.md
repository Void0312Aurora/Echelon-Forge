# Leader Training Contracts

Maintained frozen-baseline acceptance specs now live under [frozen](/home/void0312/CMO/tests/contracts/unit/training/frozen/README.md).

Status taxonomy used by this entry surface:

- `Authoritative`
  - The current acceptance matrix we should gate against first.
- `Frozen Baseline`
  - Maintained, intentionally stable acceptance contracts for the frozen leader/execution substrate.
- `Compatibility`
  - Transitional maintained entry points that may validate a maintained frozen config or bridge an older semantic shape without reopening archived contracts.
- `Archived`
  - Historical contracts retained only for traceability and provenance lookup.

- Use `frozen/` for the current authoritative leader acceptance/generalization matrix.
- Historical weak baselines and alternate task-chain variants have been moved to [tests/contracts/Archive/unit/training/leader_legacy](/home/void0312/CMO/tests/contracts/Archive/unit/training/leader_legacy/README.md).
- Historical pre-freeze root-level leader contracts have been moved to [tests/contracts/Archive/unit/training/leader_pre_frozen](/home/void0312/CMO/tests/contracts/Archive/unit/training/leader_pre_frozen/README.md).

The active leader acceptance entry point is now `frozen/`. Root-level files in this directory are no longer used for leader gating.
If a maintained bridge or wrapper check needs an older behavioral shape, keep the contract itself in the maintained tree but point it at a maintained `Frozen Baseline` config rather than a raw `Archive` config path.
