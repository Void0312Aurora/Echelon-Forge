<!-- Machine-translated draft generated on 2026-05-18 from docs/standards/air/rep.zh.md. Review before treating this file as authoritative. -->

<!-- Machine-translated draft generated on 2026-05-18 from docs/standards/air/rep.md. Review before treating this file as authoritative. -->

# Pilot Reporting Standard

> Scope note (2026-03-23): This document is the `Air Specialization`, describing platform and tactical reporting semantics in an air configuration.
> For the current standardized master baseline, first see [docs/standards/README.md](../README.md),
> [docs/standards/joint/command_and_modeling_baseline.md](../joint/command_and_modeling_baseline.md),
> [docs/standards/services/air_force.md](../services/air_force.md).

This document defines the specification for "wingman/digital pilot" reporting information to the "lead/command layer". This is a key component of the bidirectional tactical link, enabling the command layer to adjust tactics based on each aircraft's real-time status, observations, and mission progress.

In the new standard system:

- joint/common core handles the common reporting skeleton
- This document only addresses the specific reporting semantics for air configuration
- The brevity/wingman/return-to-base expressions here should not be directly generalized to maritime/land domains

## 1. Command Acknowledgment
Basic feedback to commands from the lead.

| Report Code | Semantic Description | Remarks |
| :--- | :--- | :--- |
| `REP_WILCO` | Will comply with the instruction | Command acceptance confirmation |
| `REP_ROGER` | Received (Received) | Only acknowledges receipt, does not imply execution |
| `REP_UNABLE` | Cannot execute the instruction | Usually accompanied by a reason (e.g., low fuel, excessive load factor) |
| `REP_CANT_DO` | Received but cannot achieve due to airframe limitations | E.g., requested speed of 2.0M but aircraft cannot reach it |

## 2. Status Report
Periodic or responsive summary of own aircraft status.

| Variable | Description | Data Type | Remarks |
| :--- | :--- | :--- | :--- |
| `status_fuel` | Fuel status code | {Joker, Bingo, State} | Joker: Needs withdrawal; Bingo: Must return to base; State: Specific reading |
| `status_ammo` | Ammunition remaining status | {Winchester, Remington, State} | Winchester: Ammo expended; Remington: Only limited self-defense remaining |
| `status_damage` | Airframe damage level | 0.0 (undamaged) - 1.0 (destroyed/uncontrollable) | Based on health/system damage |
| `status_pos` | Current position report | {x, y, z} | Auto-sync or response sync |

## 3. Tactical/Brevity Reports
Data-driven representation of air combat brevity codes.

| Report Code | Description | Corresponding Parameters | Remarks |
| :--- | :--- | :--- | :--- |
| `REP_TALLY` | Visual contact with enemy target | `target_id`, `pos` | Target confirmed as hostile |
| `REP_VISUAL` | Visual contact with friendly target | `target_id`, `pos` | Confirms position of lead or other wingman |
| `REP_BLIND` | Lost visual/radar contact with target | `target_id` | Alerts the formation |
| `REP_SPIKE` | Continuous radar lock by enemy | `threat_type`, `azimuth` | Alert from Radar Warning Receiver |
| `REP_ENGAGED` | Currently engaged in combat | `target_id` | Informs lead that own aircraft has entered dogfight/attack state |
| `REP_SPLASH` | Successfully shot down target | `target_id` | Air-to-air kill confirmation |
| `REP_DEFENDING` | Evading a threat | `threat_type` | Informs own side that defensive maneuvers are underway |

## 4. Mission Progress
Completion status of macro instructions from [aim.md](aim.md).

| Report Code | Description | Remarks |
| :--- | :--- | :--- |
| `REP_ON_STATION` | Arrived at designated area/station | Formation assembly complete or patrol arrival |
| `REP_FENCE_IN` | Preparing to enter combat zone | All weapons/sensors status ready check complete |
| `REP_FENCE_OUT` | Leaving combat zone | Phased feedback for mission completion, returning to base |
| `REP_RTB` | Returning to base | Final confirmation |

## 5. Emergency/Warning
Unplanned contingencies.

| Variable | Description | Remarks |
| :--- | :--- | :--- |
| `warn_flameout` | Engine flameout warning | Fuel exhausted or damage |
| `warn_bingo` | Reached bingo fuel level | Mandatory reminder to lead |
| `warn_missile_launch` | Enemy missile launch detected | Highest priority alert |

## 6. Standardization Significance
1.  **Closed-loop Command**: Lead issues instructions ([aim.md](aim.md)), wingman provides feedback ([rep.md](rep.md)), forming a closed loop.
2.  **Multi-Agent Collaboration (MARL)**: In multi-aircraft training, these reports serve as key inputs for Transformers to learn "coordination". The lead Agent adjusts subsequent tactical task allocation based on wingman feedback.
3.  **Logging & Analysis**: All report content is recorded as timestamped logs, greatly facilitating post-training debriefing and visualization.
