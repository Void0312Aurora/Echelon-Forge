# MLF-10 Calibration Gates Task Clusters

Status: `2026-06-19` finite task-cluster plan for
[MLF-10 Calibration Gates](README.md).

## Boundary Decision

MLF-10 may inventory and gate calibration-like evidence. It must not directly
retune runtime damage parameters, declare real Pk, admit deterministic fuze
truth, or promote stock weapon/target lethality before the gate contract exists
and passes.

## Finite Task Cluster List

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `MLF10-P0` | main thread | n/a | Create MLF-10 subproject surface and parent A2 live entry. | MLF-10 docs, parent A2 README files | Runtime code, archive registry entry, calibration claim | Markdown link check and `git diff --check` | README/status/dispatch/task-cluster docs exist and parent links resolve | First; serial | 1 | complete |
| `MLF10-P1` | read-only diagnostics worker or main thread | n/a | Inventory existing calibration-like values, source gates, residuals, and MLF-9 reports. | MLF-10 inventory/current-status docs only | Code edits, parameter tuning, source ingestion | Cited source inventory; no broken links | Every artifact is classified as engineering proxy, retained, candidate, admitted, rejected, or blocked | After P0; can be read-only | 2 | complete |
| `MLF10-P2` | main thread | high | Define calibration-admission contract and report schema. | MLF-10 contract docs; optional schema tests | Runtime physics edits, public data scraping | Contract inspection; focused schema tests if code added | Contract names provenance, source rights, denominator, uncertainty, independence, and authority flags | After P1; serial | 2 | complete |
| `MLF10-P3` | implementation worker | high | Implement deterministic admission-audit tooling over retained evidence manifests and MLF-9 reports. | `tools/diagnostics/**` or `tools/maintenance/**`; focused tests | Changing model parameters, accepting new sources | `py_compile`; focused pytest; fixture pass/fail-closed cases | Tool emits stable audit reports with fail-closed defaults | After P2 | 2 | complete |
| `MLF10-P4` | integration worker | medium | Expose audit reports as retained diagnostics artifacts without runtime authority leakage. | MLF-10 docs; optional probe/report integration paths | Reward authority, entity deletion, training success claim | Focused report-shape tests; link check | Report labels authority and non-claims explicitly | After P3 | 2 | complete |
| `MLF10-P5` | main thread | medium | Run focused validation and record residuals. | MLF-10 validation/status docs; tests if failures reveal scoped issues | Broad unrelated cleanup | Focused tests; `git diff --check`; Markdown link check | Validation records accepted and held boundaries | After P4 | 1 + 1 repair | complete |
| `MLF10-P6` | main thread | n/a | Accept gate infrastructure, hold calibration authority, or re-scope. | MLF-10 acceptance/archive docs; parent index updates | Closing real Pk without admitted evidence | Docs/link inspection; accepted-vs-held review | Parent indexes and archive registry match final decision | Last; serial | 1 | complete |

## Dispatch Rules

- Every packet must map to one cluster above.
- Do not create a new conversation thread.
- Do not edit archived MLF-1 through MLF-9 evidence packages except link-only
  maintenance.
- Keep `MLF10-P2`, `MLF10-P5`, and `MLF10-P6` serial.
- If a packet needs new source ingestion, stop and re-scope before fetching or
  admitting it.

## Worker Packet Requirements

Each worker packet must state:

- exact cluster id;
- allowed write set;
- source artifacts to read;
- forbidden claims;
- validation command or inspection checklist;
- residuals to return if evidence stays fail-closed.

## Validation Plan

- Markdown link check over MLF-10 docs and parent A2 README files.
- `git diff --check` over MLF-10 docs and any touched tooling/tests.
- If tooling is added: `py_compile` plus focused pytest fixtures covering
  admitted, retained-non-authoritative, rejected, blocked, and fail-closed
  evidence.

## Acceptance Criteria

- MLF-10 can classify existing calibration-like evidence without changing
  runtime behavior.
- Every admitted or candidate calibration statement carries source, provenance,
  denominator, uncertainty, and authority metadata.
- Real-world Pk, deterministic fuze, weapon-specific lethality, target-specific
  lethality, reward authority, and entity deletion remain refused unless an
  explicit gate admits them.

## Residual Map

| Residual | Handling |
| --- | --- |
| `RES-013` Pk boundary | Remains blocked until independent Pk evidence chain exists |
| `RES-014` deterministic fuze boundary | Remains blocked until live fuze/target-signature/reliability evidence chain exists |
| Fail-closed TP-21/BEC-O selected outputs | Remain fail-closed unless replacement signoff packet passes |
| Current runtime proxy parameters | Treat as engineering proxies until contract admits a narrower claim |
| MLF-9 trend outputs | Treat as synthetic trend input; not real-world calibration by default |
