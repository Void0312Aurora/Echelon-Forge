# G4 Selected Runtime Slice Cluster

Status: `2026-05-21` held / waits for G3.

Inputs:

- [G4 README](README.md)
- [G3 execution surface preflight cluster](../g3_execution_surface_design/g3_execution_surface_preflight_cluster_20260521.md)
- [Subagent Usage Policy](../../../standards/governance/subagent_usage_policy.md)

## Purpose

Implement exactly one G3-selected ground runtime slice. This cluster is held
until G3 names the safe candidate, write scope, and test plan.

## Candidate Shapes

Possible candidates, pending G3:

- tasking-only lifecycle proof through setup/profile/defaults/report status
- minimal ground command-delivery packet without movement dynamics
- selected observation/report export over tasking state only

## Task Items

| ID | Item | Acceptance |
|----|------|------------|
| `G4-A1` | Implement selected slice | Code changes match the G3-approved write scope only. |
| `G4-A2` | Focused tests | Tests exercise the selected ground path through maintained shared entry points. |
| `G4-A3` | Compatibility guards | Air/naval profile and mission tests remain compatible. |
| `G4-A4` | No-private-path proof | Architecture or runtime tests prove no ground-only lifecycle was introduced. |
| `G4-A5` | Residual handoff | Movement, sensing, fires, terrain, observation, and effects residuals are recorded. |

## Write Scope

Held until G3. The eventual worker must receive a disjoint file list before
implementation starts.

Do not edit until released:

- movement/physics systems
- sensor/track systems
- fire-control, weapon, or damage runtime
- broad facade API surfaces

## Suggested Validation

To be filled by G3. Baseline expectation:

```bash
git diff --check
python -m pytest -q <focused ground tests>
python -m pytest -q <focused air/naval compatibility tests>
```

## Handoff

Return:

- touched files
- commands run
- evidence for maintained entry points
- compatibility results
- residual map
