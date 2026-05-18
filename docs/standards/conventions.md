# Simulation Conventions

This document is `Authoritative` for engine-level neutral conventions.

It belongs to the `joint/common core` side of the standards tree:

- [Standards Overview](README.md)
- [Joint Baseline](joint/command_and_modeling_baseline.md)

It does **not** define service-specific organization or platform-specific task semantics.

This document defines the shared conventions used across core systems, bindings,
and visualization. Keep these consistent when adding new features.

## Coordinate System
- World frame: ENU (East-North-Up).
- Position: meters.
- Velocity: meters per second.

## Angles
- Heading is NAV degrees: 0 = North, positive clockwise, range [0, 360).
- Relative azimuth is NAV degrees: -180..180, positive clockwise.
- Transform stores heading/pitch/roll in degrees.

Conversions:
- Math angle (atan2 dy, dx) is 0 = East, CCW positive.
- NAV deg = 90 - math deg, wrapped to [0, 360).

## Commands

Current code still exposes legacy command structs such as `MovementCommand`.

Standards alignment note:

- engine/core conventions stay here
- service profile and platform/task command semantics belong elsewhere
- air-specific mission semantics belong under [air/README.md](air/README.md)

## Sensors
- `Sensor.fov_deg` is total FOV angle. A contact is visible if
  `abs(relative_azimuth) <= fov_deg / 2`.
- `Detection.bearing` stores relative azimuth in NAV degrees (-180..180).
- `TrackData.azimuth` uses the same convention as `Detection.bearing`.

## Observations
- `AgentObservation.heading/pitch/roll` are degrees in NAV convention.
- `get_all_units().heading` is derived from velocity and returned as NAV degrees.

## Time
- Simulation time is in seconds.
