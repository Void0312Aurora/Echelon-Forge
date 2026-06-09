# Naval

Status: active naval-realism workline; N4 pre-fire bridge closed on
`2026-05-25`, and the N4 RL action/observation surface repair landed on
`2026-05-27`.

## Current Status

- The current naval line has already moved beyond a bare minimum contact demo
  into a tactical prototype with maritime motion, situational awareness,
  localized weapon-chain skeleton, and support-chain rudiments.
- The latest state summary is
  [naval_current_progress_20260524.md](./naval_current_progress_20260524.md).
- The N4 threat/ROE bridge is closed as a pre-fire scenario and active
  training-entry gate. Its original task path is now a lightweight pointer, and
  the full closure/evidence package lives under
  [archive/archive/n4_threat_roe_bridge/](./archive/archive/n4_threat_roe_bridge/README.md):
  [naval_n4_closure_20260525.md](./archive/archive/n4_threat_roe_bridge/naval_n4_closure_20260525.md).
- The RL action/observation-surface split is implemented and retained as an
  accepted N4 training-entry repair record. Its original task path is now a
  lightweight pointer, and the full packet lives under
  [archive/archive/n5_rl_action_surface_split/](./archive/archive/n5_rl_action_surface_split/README.md):
  [naval_n5_rl_action_surface_split_cluster_20260526.md](./archive/archive/n5_rl_action_surface_split/naval_n5_rl_action_surface_split_cluster_20260526.md).
  Despite the folder name, this is an N4 pre-fire training-entry repair, not a
  release of N5 weapon engagement. New naval surface-split work should continue
  in the domain-surface split package below.
- The current domain-surface split is tracked in
  [naval_domain_surface_split/README.md](./naval_domain_surface_split/README.md).
  It continues separating maintained naval action, command, observation, and
  configuration surfaces from air-first compatibility carriers before any N5/N6
  claim is opened.
- The older `2026-05-17` progress checkpoint remains archived for historical
  traceability.
- The line remains active, but the main focus is closure and stabilization of
  the existing naval command, sensor, runtime, and RL/tasking chain rather than
  broad new feature expansion.

## Current Entry Points

- Current progress tracking:
  [naval_current_progress_20260524.md](./naval_current_progress_20260524.md)
- Current domain-surface split continuation:
  [naval_domain_surface_split/README.md](./naval_domain_surface_split/README.md)
- Archive index:
  [archive/README.md](./archive/README.md)
- Historical planning/checkpoint material has been moved into the archive.

## Closed / Retained Records

These records are closed or accepted. Keep them visible through this section
for provenance, tests, and gate checks, but do not use them as new active
subproject entrypoints.

- Closed N4 scenario-expansion subproject:
  [archive/n4_threat_roe_bridge/README.md](./archive/n4_threat_roe_bridge/README.md)
- N4 closure record:
  [archive/archive/n4_threat_roe_bridge/naval_n4_closure_20260525.md](./archive/archive/n4_threat_roe_bridge/naval_n4_closure_20260525.md)
- Implemented N4 RL action/observation repair, despite the `N5` directory name:
  [archive/n5_rl_action_surface_split/README.md](./archive/n5_rl_action_surface_split/README.md)
  and
  [archive/archive/n5_rl_action_surface_split/README.md](./archive/archive/n5_rl_action_surface_split/README.md)

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
- continue splitting the remaining air-first compatibility carriers:
  neutral `PilotAction` transport, flat `MissionCommand` aggregation,
  Python-owned naval mission observation fallback, and air-labeled backend
  config names
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
