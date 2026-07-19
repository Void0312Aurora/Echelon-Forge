# Leader Training Contracts

Maintained frozen-baseline acceptance specs now live under [frozen](frozen/README.md).

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
- Historical weak baselines, alternate task-chain variants, and pre-freeze root-level leader contracts were retired from the tree during test-system consolidation; recover them from git history if needed.

The active leader acceptance entry point is now `frozen/`. Root-level files in this directory are no longer used for leader gating.
If a maintained bridge or wrapper check needs an older behavioral shape, keep the contract itself in the maintained tree but point it at a maintained `Frozen Baseline` config rather than a raw `Archive` config path.
