<!-- Machine-translated draft generated on 2026-05-18 from docs/standards/air/obs.zh.md. Review before treating this file as authoritative. -->

<!-- Machine-translated draft generated on 2026-05-18 from docs/standards/air/obs.md. Review before treating this file as authoritative. -->

# Pilot Observation Space Standard

> Scope note (2026-03-23): This document is the `air specialization` and applies only to platform observation semantics under the air profile. For the current main standardization baseline, please first refer to [docs/standards/README.md](../README.md), [docs/standards/services/air_force.md](../services/air_force.md), [docs/standards/air/README.md](README.md).

This document defines the observation data that a "digital pilot" (RL Agent) can obtain in a simulation environment. This data strictly simulates the raw information that a real fighter pilot obtains through instruments, head-up display (HUD), and senses.

It does not define:

- command relationships of the joint/common core
- platform observations of Army/Navy/Marine Corps
- a unified data model skeleton for the entire project

## 1. Flight Dynamics
The pilot's direct perception of the aircraft's motion state.

| Variable name | Description | Physical unit | Real-world counterpart |
| :--- | :--- | :--- | :--- |
| `alt_baro` | Barometric altitude (mean sea level) | meter (m) | Barometric altimeter |
| `alt_radar` | Radar altitude (actual height above ground) | meter (m) | Radar altimeter |
| `ias` | Indicated airspeed | knots (kts) / meters per second (m/s) | Airspeed indicator |
| `mach` | Mach number | Mach | Mach meter |
| `vvi` | Vertical velocity indicator | meters per second (m/s) | Variometer / VSI |
| `pitch` | Pitch angle | degrees (deg) | Attitude Director Indicator (ADI) |
| `roll` | Roll angle | degrees (deg) | Attitude Director Indicator (ADI) |
| `heading` | Magnetic heading / True heading | degrees (deg) | Horizontal Situation Indicator (HSI) |
| `aoa` | Angle of Attack | degrees (deg) | AoA indicator |
| `beta` | Sideslip angle | degrees (deg) | Slip ball / sideslip indicator |
| `g_load` | Normal load factor | g | Accelerometer |
| `p, q, r` | Angular rates (roll, pitch, yaw rates) | degrees per second (deg/s) | Rate gyros |

## 2. Propulsion & Systems
Monitor engine operating status and its impact on the airframe.

| Variable name | Description | Physical unit | Notes |
| :--- | :--- | :--- | :--- |
| `engine_rpm_pct` | Core speed percentage | % | N1 / N2 |
| `engine_temp` | Exhaust gas temperature / Turbine inlet temperature | degrees Celsius (℃) | EGT / FTIT |
| `fuel_internal` | Internal fuel weight | kilogram (kg) | Fuel gauge |
| `fuel_external` | External fuel weight | kilogram (kg) | Fuel gauge |
| `fuel_flow` | Instantaneous fuel flow | kilograms per hour (kg/h) | Flow meter |
| `throttle_pos` | Current throttle lever actual position | 0.0 - 1.0 | Feedback feel |

## 3. Configuration
Current state of the airframe's mechanical structure.

| Variable name | Description | State values | Notes |
| :--- | :--- | :--- | :--- |
| `gear_pos` | Landing gear status | 0.0 (retracted) - 1.0 (extended) | Includes transition state |
| `flaps_pos` | Flaps angle | degrees (deg) / position | |
| `speedbrake_pos` | Speedbrake deployment | 0.0 - 1.0 | |
| `master_arm` | Master arm switch | ON / OFF | |

## 4. Environment & Navigation
Mission objectives issued by the lead aircraft/command layer and external dynamics.

| Variable name | Description | Physical unit | Notes |
| :--- | :--- | :--- | :--- |
| `target_heading` | Commanded target heading | degrees (deg) | Lead aircraft command content |
| `target_alt` | Commanded target altitude | meters (m) | Lead aircraft command content |
| `target_speed` | Commanded target speed | m/s | Lead aircraft command content |
| `oat` | Outside air temperature | degrees Celsius (℃) | Static temperature and pressure |
| `wind_vec` | Estimated wind vector | m/s | Pilot perception compensation |

## 5. Tactical & Sensors
Battlefield situation acquired through electronic devices.

| Variable name | Description | Physical unit | Notes |
| :--- | :--- | :--- | :--- |
| `rwr_state` | Radar warning receiver status | Quadrant, type, intensity | Warning tone and display |
| `radar_contacts` | List of friendly and hostile targets detected by radar | Bearing, range, Doppler velocity | Raw observations |
| `missile_count` | Number of remaining available missiles | Integer | Count by type |
