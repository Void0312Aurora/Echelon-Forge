# Realism Program And Taskboard Subproject

Language:
- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Status: `2026-05-17` actively maintained.

This subproject collects cross-slice status summaries, staged taskboards, and
current scheduling entrypoints for the `flight_dynamics` mainline, without
repeating deep technical detail from each direction.

## Document Entry Points

- [realism mainline convergence plan](realism_program_convergence_plan_20260517.md)
  - Unifies the current overall phase, main blockers, maintained scope, and
    convergence order. This is the recommended top-level entrypoint.
- [current status of the realism mainline and linked subprojects](realism_program_current_status_20260517.md)
  - Quick check for current green/red surfaces, active directions, and linked
    subproject entrypoints.
- [realism master taskboard (P0)](realism_program_taskboard_20260516.zh.md)
  - Preserves the original unified `P0` taskboard for the three main lines; do
    not use it as the real-time progress source now.
- [realism P1 master taskboard](realism_program_p1_taskboard_20260517.md)
  - Records post-`P0` closeout items and the deeper realism schedule for `P1`.
- [realism delegated execution plan](realism_program_delegated_execution_plan_20260517.zh.md)
  - Retains lane/sidecar/delegation framing; read it alongside the convergence
    plan rather than as the latest overall-phase source by itself.

## Scope

1. Cross-subproject priorities, dependencies, and stage acceptance.
2. Which lines are actively advancing and which remain frozen analysis only.
3. Taskboard entrypoints that need to be dispatched from the main thread into
   each subproject.

## Not Maintained Here

1. Detailed technical analysis for a single direction.
2. File-by-file implementation packages for one subsystem.
3. Progress checkpoints that already moved into a dedicated subproject folder.
