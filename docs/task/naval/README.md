# Naval

Status: active naval-realism workline; N4 pre-fire bridge closed on
`2026-05-25`.

## Current Status

- The current naval line has already moved beyond a bare minimum contact demo
  into a tactical prototype with maritime motion, situational awareness,
  localized weapon-chain skeleton, and support-chain rudiments.
- The latest state summary is
  [naval_current_progress_20260524.md](./naval_current_progress_20260524.md).
- The current N4 threat/ROE bridge is closed as a pre-fire scenario and active
  training-entry gate:
  [naval_n4_closure_20260525.md](./n4_threat_roe_bridge/naval_n4_closure_20260525.md).
- The current RL action-surface split is tracked in
  [n5_rl_action_surface_split/README.md](./n5_rl_action_surface_split/README.md).
- The older `2026-05-17` progress checkpoint remains archived for historical
  traceability.
- The line remains active, but the main focus is closure and stabilization of
  the existing naval command, sensor, runtime, and RL/tasking chain rather than
  broad new feature expansion.

## Recommended Reading Order

- Current progress tracking:
  [naval_current_progress_20260524.md](./naval_current_progress_20260524.md)
- Next scenario-expansion subproject:
  [n4_threat_roe_bridge/README.md](./n4_threat_roe_bridge/README.md)
- N4 closure:
  [n4_threat_roe_bridge/naval_n4_closure_20260525.md](./n4_threat_roe_bridge/naval_n4_closure_20260525.md)
- Current RL action-surface split:
  [n5_rl_action_surface_split/README.md](./n5_rl_action_surface_split/README.md)
- Archive index:
  [archive/README.md](./archive/README.md)
- Historical planning/checkpoint material has been moved into the archive.

## Current Follow-On Focus

- treat `N4` as closed and avoid reopening it for engagement work
- continue from the active N4 smoke/probe entries:
  `naval_contact_report_threat_roe_v1`,
  `naval_screen_station_hold_threat_aware_v1`, and
  `naval_screen_station_recovery_threat_aware_v1`
- keep those entries on the dedicated `naval_station3` station-order action
  surface rather than the air `takeoff4` training surface
- keep their policy mission input on `naval_screen_station_v1` rather than the
  air formation-role observation surface
- keep limited weapon engagement behind a separate N5 package and opening gate
- continue moving business-bearing loader-owned raw simulation compatibility
  seams to facade-owned maintained surfaces
- add facade/world-batch gates for `MissionCommand -> naval weapon`,
  `screen-hold`, and `tasking_profile: naval`
- stabilize maritime state, sensor/LOS coupling, naval weapon command chains,
  and training entrypoints before expanding into larger high-fidelity fleet
  combat

The earlier scenario-bound freeze snapshot now lives under
[archive/README.md](./archive/README.md).
