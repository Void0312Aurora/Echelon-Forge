# Physics input boundary audit (#121)

| Path | Maintained query/reachability | Resolution |
| --- | --- | --- |
| ComputeForces | `ForceAccumulator, Transform, Velocity, Mass, Propulsion, FlightModel`; normal aircraft; no separate static-only gate | Reject non-finite or non-positive total mass by skipping that entity. Preserve every finite positive mass, including below 1 kg. |
| LeapfrogIntegrate | `Transform, Velocity, ForceAccumulator, Mass`; rigid bodies and some missile/platform paths | Same mass rule; small positive values are integrated as authored. |
| ComputeAerodynamics | `ForceAccumulator, AeroState, MassProperties, Velocity, Transform`; airframe aero bodies | Reject non-finite/non-positive reference area; preserve valid sub-1 m2 values. |
| GroundContact | `ForceAccumulator, Transform, Velocity, Mass, GroundState`; requires a live environment provider, usually gear/contact bodies | Share the same positive-mass rule and timestep resolver as rotational/translation integration. Invalid mass skips contact and does not invent aircraft mass. |
| RotationalIntegrate | `Transform, AngularVelocity, Inertia, ForceAccumulator` | Shares the existing pause/initialization fallback timestep. Inertia validation is outside this ticket. |

SimulationKernel's full setup and world progress normally use the validated
positive kernel timestep from #132. The native Flecs callback also has a `0.05 s`
compatibility fallback for direct `ecs.progress(0)` use, pause and initialization
paths. It is retained in one shared policy function. NaN, infinity, zero and
negative callback deltas resolve to this compatibility step; changing pause
semantics belongs to a separately measured runtime decision.

Mass/reference-area substitution at one kilogram or one square metre was not a
physical default: it silently converted valid small entities. The former 15000
kg fallback constants are retained as named compatibility constants for source
compatibility, but are no longer used in dynamics. Invalid mass or area skips
only its owning ECS entity; no exception crosses a Flecs callback. In the ground
contact chain, contact and both downstream integrators use the exact same shared
mass and timestep policy.

This is an input validity and reachability inventory, not evidence that the
maintained missile path previously received 15000 kg or the airframe path 30 m2.
No mass, area or timestep fitting or aircraft baseline tuning is included.
EOF
