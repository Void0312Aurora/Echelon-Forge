# Released decoy kinematics (#129)

EW chaff and flare entities intentionally do not carry `Mass` or
`ForceAccumulator`, so they cannot enter the rigid-body `LeapfrogIntegrate`
query. Their release velocity was therefore only stored, not applied to
`Transform`; the lifetime system aged and removed them while they stayed at
their spawn coordinates.

The EW factory now owns `EW_Decoy_Kinematics`, a narrow `Decoy, Transform,
const Velocity` OnUpdate system. It advances each released decoy by
`Transform += Velocity * delta_time` once per frame. It is registered in the
same factory after release and before lifetime aging. Deferred entities begin
moving on the next frame, so release timing remains deterministic. No gravity,
drag or mass model is introduced.

The broad legacy `UpdatePosition` path remains unregistered. Aircraft, missiles,
ships and ground units retain their existing integrators and cannot be moved by
this node. Stable serials and velocity are preserved; lifetime expiry still
removes decoys at the configured age.

Native tests release both chaff and flare with positive and negative velocity,
assert one-step-per-frame displacement, lifetime ageing, serial stability and
expiry. Existing seeker tests continue to cover target ownership, FOV,
resolution-cell boundaries, local sensor provenance and stable draw ordering;
the movement test supplies the missing actual-release kinematic proof.
