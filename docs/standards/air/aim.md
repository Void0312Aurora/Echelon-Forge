<!-- Machine-translated draft generated on 2026-05-18 from docs/standards/air/aim.zh.md. Review before treating this file as authoritative. -->

<!-- Machine-translated draft generated on 2026-05-18 from docs/standards/air/aim.md. Review before treating this file as authoritative. -->

# Lead Aircraft / Mission Command Standard

> Scope note (2026-03-23): This document is the `air specialization`, describing the dedicated semantics of `Tactical Intent / Execution Command` under the air profile. It is no longer a project-wide common core standard.
> For the current standardized main baseline, please first see [docs/standards/README.md](../README.md),
> [docs/standards/joint/command_and_modeling_baseline.md](../joint/command_and_modeling_baseline.md),
> [docs/standards/services/air_force.md](../services/air_force.md).

This document defines the command specification issued by the "Lead Aircraft" or "command layer" to the "wingman/digital pilot". These commands are highly abstract tactical objectives. The task of the digital pilot (RL Agent) is to translate these abstract objectives into physical aircraft motion through the operations in [act.md](act.md).

Under the new standard system:

- The joint/common core only defines the common skeleton of `intent / order / report`
- This document only defines how these objects are concretized under the air profile
- `CAP`, `runway approach`, `wingman formation` are all air-specific semantics

## 1. Core Vectoring

The most direct parameterized commands, used to define the desired flight state.

| Variable | Description | Physical Unit | Notes |
| :--- | :--- | :--- | :--- |
| `cmd_heading` | Target heading | Degrees (deg) | 0-360, magnetic or true heading |
| `cmd_alt` | Target altitude | Meters (m) | Typically MSL (Mean Sea Level) |
| `cmd_speed` | Target speed | Currently implemented as meters per second (m/s) | In real-world abstraction could correspond to IAS / TAS / Mach, but current in-repo flight-task training uniformly uses m/s |
| `cmd_vvi` | Target vertical speed | m/s | Optional, for precise control of climb/descent profile |

## 2. Procedural / Macro Commands

Defines the current mission phase, implying a comprehensive behavior pattern.

| Command Code | Semantic Description | Typical Parameter Configuration |
| :--- | :--- | :--- |
| `CODE_IDLE` | Ground static / awaiting instructions | Speed=0, Alt=Ground |
| `CODE_TAKEOFF` | Takeoff command | Heading=Rwy, Speed=V2, Alt=Initial |
| `CODE_CRUISE` | Heading-altitude-speed vector guidance | Heading/Alt/Speed |
| `CODE_ROUTE_NAV` | Route / waypoint navigation | Steerpoint Sequence, LNAV |
| `CODE_LAND` | Landing command | Heading=Rwy, Alt=GlideSlope, Speed=Vref |
| `CODE_ORBIT` | Holding orbit | ReferenceCoord, Radius |
| `CODE_RTB` | Return to base | HomeBaseID |

> Current in-repo implementation note: The numeric convention actually used in current single-aircraft flight training is
> `0=Idle`, `1=Takeoff`, `2=Vector/Cruise`, `3=Waypoint/LNAV Route Navigation`, `4=Landing/Final`.
> Among these, `command_code=3` means "execute route navigation according to steerpoint sequence",
> `command_code=4` means "runway-aligned approach/landing task".
> The longitudinal path for the landing task is not directly issued via privileged runway geometry, but is provided through
> `ILS`-style products (`loc_dev / gs_dev / dme`) in the observations.

## 3. Formation Controls

In multi-aircraft coordination, defines the relative spatial relationship with the lead aircraft.

| Variable | Description | Physical Unit | Notes |
| :--- | :--- | :--- | :--- |
| `form_pos_id` | Formation position ID | Integer | Line abreast, echelon, wedge, etc. |
| `form_offset_x` | Forward/backward offset relative to lead | Meters (m) | |
| `form_offset_y` | Left/right offset relative to lead | Meters (m) | |
| `form_offset_z` | Vertical offset relative to lead | Meters (m) | |

## 4. Tactical Intent

Defines the priorities for air combat behavior.

| Variable | Description | Value Range | Notes |
| :--- | :--- | :--- | :--- |
| `tac_target_id` | Specified assigned target ID | Entity ID | Tells the AI "that is your target" |
| `tac_engagement` | Engagement authorization | {HOLD, COVER, ENGAGE} | Whether weapon release is allowed |
| `tac_jettison` | Forced jettison command | Triggered | For high-G or fuel emergency situations |

## 5. Case Studies

### Scenario A: Takeoff

When the command layer issues `CODE_TAKEOFF`, the command stream will consist of the following data:
*   `cmd_heading`: Current runway heading (e.g., 090).
*   `cmd_alt`: Initial liftoff altitude (e.g., 1000m).
*   `cmd_speed`: Scheduled climb speed (e.g., 250kts).
*   **AI Task**: After observing these commands, maintain 090 heading during ground roll via stick and throttle, rotate at rotation speed, retract landing gear, and reach the target state.

### Scenario B: Cruise

When the command layer issues `CODE_CRUISE`:
*   `cmd_heading`: Cruise route bearing.
*   `cmd_alt`: Cruise level altitude (e.g., 8000m).
*   `cmd_speed`: Cruise economical Mach number (e.g., 0.7M).
*   **AI Task**: Smoothly climb to the specified altitude, adjust throttle to maintain Mach number.

### Scenario C: Route Navigation

When the command layer issues `CODE_ROUTE_NAV`:
*   `cmd_heading`: The desired ground track bug for the current active leg, not the "instantaneous bearing to fly directly to a point".
*   `cmd_alt`: Target altitude for the current active waypoint or leg.
*   `cmd_speed`: Target speed for the current active waypoint or leg.
*   `Additional navigation products`: Steerpoint number, distance to active waypoint, relative bearing, CDI/XTK, next turn angle / turn distance.
*   **AI Task**: Complete route tracking, turn anticipation, and segment altitude/speed constraints using LNAV/EGI-style navigation products.

### Scenario D: Landing / Final

When the command layer issues `CODE_LAND`:
*   `cmd_heading`: Runway final approach heading.
*   `cmd_alt`: Runway reference altitude / landing reference altitude.
*   `cmd_speed`: Approach reference speed.
*   `Additional instrument products`: `ILS` localizer deviation, glideslope deviation, DME.
*   **AI Task**: Capture localizer and glideslope, stabilize speed and attitude, touch down and decelerate within the runway.

## 6. Standardization Significance

1.  **Decouple decision-making from execution**: The lead layer only cares about "where to go / what to do", the pilot layer (RL) only cares about "how to fly".
2.  **Transformer training advantage**: The AI performs Cross-Attention between the `cmd_*` sequence and its own `alt/speed` sequence, enabling it to learn the implicit physical logic of "tracking" and "achieving" command objectives more quickly.
