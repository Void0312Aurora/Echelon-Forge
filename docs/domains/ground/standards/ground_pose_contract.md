# Ground movement pose contract

Language:
- English canonical contract.
- Chinese companion: `ground_pose_contract.zh.md`.
Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/domains/ground/standards/ground_pose_contract.md`
Owner: `systems/domains/ground/movement_system.h`
Last verified: `2026-10-10`

## Scope

`GroundInfantryMovement` owns the pose projection for the admitted native
individual-infantry `MoveStatic`, `OccupyStatic`, and `SupportStatic` slices. It
remains a horizontal kinematic primitive; this contract does not introduce a
6-DoF ground integrator, route planning, cover, sensing, or fire authority.

## Pose ownership

- `Transform.x/y` are the horizontal world position advanced by the movement
  primitive.
- `Transform.z` is the absolute terrain elevation at the ground entity anchor.
  The anchor is on the surface, so this field is not AGL height and does not
  encode eye height, weapon height, or a human body offset.
- `Velocity.vz` remains zero for this primitive. Ground contact and other
  consumers may use the absolute anchor elevation independently.
- `Transform.heading` uses the shared NAV convention (0 degrees north,
  clockwise positive).

## Heading policy

- Active `MoveStatic` projects the normalized `MissionCommandCore::cmd_heading_deg`
  into `Transform.heading`, including a zero-speed or blocked transition. The
  horizontal velocity uses the same heading when movement is admitted.
- Active `OccupyStatic` and `SupportStatic` stop the primitive and preserve the
  existing heading. Their ground task slice has no facing field, so the command
  cannot silently replace a hold orientation.
- Inactive or unsupported ground commands stop velocity and preserve the pose.

## Elevation policy

On each active movement or hold step, the system samples
`IEnvironmentModel::get_terrain_elevation(x, y)` and writes a finite result to
`Transform.z`. A non-finite environment result leaves the previous Z value in
place. A blocked transition grounds the current anchor but does not advance
`x/y`.

## Downstream boundary

The maintained native visual path and environment queries consume absolute
world coordinates, while the generic instrument system requires aircraft
flight components and therefore does not admit this ground slice. No
maintained ground LOS, direct-fire, or sensor consumer currently turns this
pose into an authority-bearing outcome. The native tests therefore verify the
pose contract itself and record downstream reachability separately instead of
claiming an end-to-end engagement result.
