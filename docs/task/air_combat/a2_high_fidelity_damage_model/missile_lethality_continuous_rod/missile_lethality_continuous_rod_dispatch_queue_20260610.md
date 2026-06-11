# A2 MLF-4 Dispatch Queue

Status: `2026-06-11` dispatch queue. `MLF-4A-X1`, `MLF-4B-W1-R2`, `MLF-4C-W1`, `MLF-4D-W1`, and `MLF-4E-W1` are accepted; `MLF-4F-C1` is ready for closeout/archive preparation.

Chinese main text: [missile_lethality_continuous_rod_dispatch_queue_20260610.zh.md](missile_lethality_continuous_rod_dispatch_queue_20260610.zh.md)

Parent task clusters: [missile_lethality_continuous_rod_task_clusters_20260610.md](missile_lethality_continuous_rod_task_clusters_20260610.md)

## Queue

| Packet | Cluster | Suggested owner | Write set | Goal | Status |
| --- | --- | --- | --- | --- | --- |
| `MLF-4A-X1` | `MLF-4A Boundary And Inventory` | read-only worker | docs inventory packet only | Inventory rod fields, continuous_rod branches, historical tests, and gaps. | accepted |
| `MLF-4B-W1` | `MLF-4B Standard Rod Event Surface` | current-session worker | event contracts/export/store/tests | Stabilize standard rod/cut facts. | accepted via R2 |
| `MLF-4C-W1` | `MLF-4C Generic Rod Geometry` | current-session worker | default effects rod geometry/tests | Validate generic cut corridor/orientation behavior. | accepted |
| `MLF-4D-W1` | `MLF-4D Component Cut Projection` | current-session worker `019eb268-2e2d-7bf2-bb1b-3fb048a192ee` / Carver | spatial/component projection/tests | Project rod cut exposure to components. | accepted |
| `MLF-4E-W1` | `MLF-4E Diagnostics And Gates` | main thread | diagnostics + guard tests | Explain rod/cut facts and guard false rod rows. | accepted |
| `MLF-4F-C1` | `MLF-4F Acceptance And Archive Prep` | main thread | docs/index/archive | Summarize accepted/held state and residuals. | ready |

## Recent Dispatch

| Packet | Worker | Model / reasoning | Started | Expected packet |
| --- | --- | --- | --- | --- |
| `MLF-4A-X1` | current-session controlled explorer `019eb210-9e5e-7b80-bc77-335b98d5796c`, recovered by main-thread review | `gpt-5.4-mini` / `xhigh` | `2026-06-10` | [accepted inventory packet](missile_lethality_continuous_rod_inventory_20260610.md). |
| `MLF-4B-W1` | current-session controlled worker `019eb24d-db2b-7161-be3f-b02566339d3d` / Goodall | inherited model / `high` | `2026-06-11` | Failed / closed before packet: attempted broad out-of-scope `src/` formatting changes; main thread discarded those changes. |
| `MLF-4B-W1-R2` | current-session controlled worker `019eb255-383b-7851-a721-e33bdfbda459` / Kepler | inherited model / `high` | `2026-06-11` | Returned pass; accepted after local verification. Added [test_continuous_rod_event_surface.py](../../../../../tests/runtime/air_combat/test_continuous_rod_event_surface.py). |
| `MLF-4C-W1` | current-session controlled worker `019eb268-2e2d-7bf2-bb1b-3fb048a192ee` / Carver | inherited model / `high` | `2026-06-11` | Returned pass; accepted after local verification. Added [test_continuous_rod_geometry_response.py](../../../../../tests/runtime/air_combat/test_continuous_rod_geometry_response.py). |
| `MLF-4D-W1` | current-session controlled worker `019eb268-2e2d-7bf2-bb1b-3fb048a192ee` / Carver | inherited model / `high` | `2026-06-11` | Returned pass; accepted after local verification. Added [test_continuous_rod_component_cut_projection.py](../../../../../tests/runtime/air_combat/test_continuous_rod_component_cut_projection.py). |
| `MLF-4E-W1` | main-thread local implementation and verification | n/a | `2026-06-11` | Accepted. Added [test_continuous_rod_diagnostic_projection.py](../../../../../tests/runtime/air_combat/test_continuous_rod_diagnostic_projection.py) and updated the diagnostic probe rod/cut snapshots plus no-detonation fallback gate. |

## Dispatch Notes

- `MLF-4E-W1` is accepted; start next with `MLF-4F-C1` acceptance/archive prep.
- Do not dispatch 4C/4D concurrently until the event-surface decision is accepted.
- Do not enter MLF-5 component failure or MLF-6 structural breakup while MLF-4 is still only planning.
- Returned packets must preserve the generic research-data rule and name any default constants they touch.

## Worker Packet Checklist

- status
- touched files
- commands/outcomes
- remaining paths
- behavior risks
- integration notes
- no-detonation/non-rod gate status
- forbidden claims avoided
