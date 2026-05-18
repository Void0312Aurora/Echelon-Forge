<!-- Machine-translated draft generated on 2026-05-18 from docs/task/flight_dynamics/naval/naval_realism_analysis_20260516.zh.md. Review before treating this file as authoritative. -->

# Naval Warfare Simulation Realism Analysis

Status: `2026-05-16` Frozen analysis version.

Associated files:

- [ShipMotion System (Ship Kinematics)](../../../../src/systems/naval/ship_motion_system.h)
- [ShipPlatform Component Definition](../../../../src/components/naval/ship_platform.h)
- [NavalTaskingEnums](../../../../src/components/tasking/naval/naval_tasking_enums.h)
- [TaskOrderNaval](../../../../src/components/tasking/naval/task_order_naval.h)
- [LeaderIntentNaval](../../../../src/components/tasking/naval/leader_intent_naval.h)
- [PilotReportNaval](../../../../src/components/tasking/naval/pilot_report_naval.h)
- [DDG-51 Unit Definition](../../../../examples/config/database/ships/units/ddg51_flight_i_uss_arleigh_burke.json)
- [T-AKE-1 Unit Definition](../../../../examples/config/database/ships/units/take1_usns_lewis_and_clark.json)
- [AN/SPS-67(V) Sensor Definition](../../../../examples/config/database/ships/modules/sensors/an_sps_67_v_surface_search.json)
- [Auxiliary Ship Navigation Radar Definition](../../../../examples/config/database/ships/modules/sensors/civil_navigation_surface_radar.json)
- [DDG-51 Screen Minimum Scenario](../../../../scenarios/naval/ddg51_take1_screen_contact_report_v1.json)
- [Screen Approach Variant Scenario](../../../../scenarios/naval/ddg51_take1_screen_closing_contact_v1.json)
- [Naval Unit Parameters Reference](../../../standards/naval/ship_unit_references.md)
- [Naval Mission Minimum Structure](../../../standards/naval/minimal_task_structure.md)
- [Naval Tests](../../../../tests/runtime/test_naval_ship_database.py)
- [Screen Scenario Tests](../../../../tests/runtime/test_naval_screen_scenario.py)
- [Sensor and Situational Awareness Analysis (Related)](../sensor_situation/sensor_situation_realism_analysis_20260516.zh.md)
- [Weapon System Analysis (Related)](../weapon_guidance/weapon_guidance_realism_analysis_20260516.zh.md)

Document positioning:

- This document only records the known deficiencies of the current naval warfare pipeline and their corresponding real physical/engineering conditions.
- It does not cover acceptable simplifications, does not provide priority ordering, and does not give a work plan.

Current status guidance:

- This document is a frozen analysis input, not a current execution status board.
- For the actual progress and regression of the current naval warfare, please refer primarily to:
  - [Naval Warfare Progress Checkpoint](../../naval/naval_progress_checkpoint_20260517.zh.md)
  - [Naval Warfare Subsequent Delegation Execution Sheet](../../naval/naval_delegated_execution_backlog_20260517.zh.md)
  - [Realism Mainline and Related Subprojects Current Status](../program/realism_program_current_status_20260517.zh.md)

## Postscript: `2026-05-17` Conclusion Mark

Marking criteria:

- `Unresolved`: The original argument is largely still valid.
- `Partially resolved`: There is already a partial implementation or minimal skeleton, but the main distortion remains.
- `Minimum conclusion exists`: It is no longer appropriate to describe it as "completely missing"; a minimal closed loop already exists.
- `Resolved`: The old discussion is no longer suitable as a description of the current state.

This postscript only answers "whether these naval warfare points are still valid today", and does not rewrite this document into a progress board.

| Item | Current Mark | Description |
|------|----------|------|
| Section 1 Current Naval Warfare Pipeline | `Partially resolved` | Should now be reread as "naval warfare MVP expanded to include Sonar / embarked helo / naval weapons / UNREP / intermediate damage states" |
| `2.1` Ship Kinematics – No Fluid Dynamics | `Partially resolved` | Has progressed from pure geometric placeholder to minimal ship kinematics with low-speed rudder effectiveness and sea state coupling, but still not real fluid dynamics |
| `2.2` Sea State and Wave Response Completely Missing | `Minimum conclusion exists` | `sea_state / roll / pitch / added resistance` now have minimal proxies |
| `2.3` Surface Sensors Share Air Radar Framework | `Partially resolved` | Still reuses shared framework, but has added specialized fields for naval radar, ESM MVP, and surface LOS patching |
| `2.4` No Shipboard Sonar / Anti-Submarine Warfare | `Minimum conclusion exists` | Minimal ASW closed loop with Submarine + Sonar + helo relay now exists |
| `2.5` Shipboard Weapon Systems – Metadata Placeholder, No Runtime Implementation | `Partially resolved` | VLS / gun / CIWS have entered structured runtime, but main gun direct fire and MissionCommand -> CIWS are still not green |
| `2.6` Ship Damage Model – HP Placeholder, No Sinking/Disablement Physics | `Partially resolved` | Has mission/mobility/sensor kill and continuous damage propagation, but still lacks high-fidelity models for buoyancy/compartmentation/stability |
| `2.7` Red Force Uses T-AKE-1 Placeholder | `Resolved` | The red force placeholder ship issue has been replaced and is no longer a valid description of the current state |
| `2.8` Maritime Formation and Screen Control | `Partially resolved` | Minimal screen-hold and station recovery closed loop exists, but still not complete formation maneuver/multi-ship coordination |
| `2.9` Data Link – Faction-Level Approximation, No Fleet C2 Semantics | `Partially resolved` | Task-group-level convergence and shared track/report approximation exist, but still not full fleet C2 |
| `2.10` Underway Replenishment and Logistics | `Partially resolved` | Abstract inventory and minimal UNREP are connected, but still not a complete replenishment doctrine |
| `2.11` No Naval Aviation Interaction | `Partially resolved` | Embarked helo token-level coordination exists, but no complete deck operations/aviation sortie system |

---

## 1. Current Naval Warfare Pipeline Processing Chain

```
ShipMotionSystem        → Constrained 2D ship kinematics (high-level course/speed commands, first-order acceleration/deceleration and turn rate constraints, z=0)
  └ Ships bypass all flight physics pipelines (forces, aerodynamics, ground contact, rotational integration)

SensorSystem            → Shared air sensor framework (geometric gating + probability detection + Gaussian noise)
  └ Surface radar adds radar horizon constraint (DDG-51: 46.3km, T-AKE-1: 36.3km)

DataLinkSystem          → Shared P2P data link (network number assigned by faction, adds ship antenna height LOS calculation)
  └ Shared track/report messages are still engineering approximations, far weaker than real fleet tactical data links

TrackManagerSystem      → Shared track database (entity_id association, no filter, no velocity estimation)

DamageSystem            → Shared proximity fuse (no ship-specific damage logic)
  └ Hit boxes are structural placeholders (armor=0, system_health has no dynamic degradation)

EWSystem                → Shared chaff/flare (no shipboard passive/active countermeasures)
```

Naval mission layer (Python side):

```
naval_profile.py        → TASK_SCREEN/TASK_SUPPORT semantic mapping
  └ NavalWarfareRole / NavalStationType enumeration parsing
  └ Builds MissionCommand (no dynamic screen-keeping control logic)
```

## 2. Known Distortions

### 2.1 Ship Kinematics – No Fluid Dynamics

The current `ShipMotion` is no longer the original "instantaneous speed limit + zero turn radius" version, but:

- Reads target course and target speed from `MissionCommand/MovementCommand`
- Approaches speed using first-order approximation via `max_accel_mps2 / max_decel_mps2`
- Approaches course using first-order approximation via `max_turn_rate_deg_s` and low-speed turn reduction
- Still forces `z=0, pitch=0, roll=0`

This means the current implementation has progressed from "pure geometric drift" to "minimal constrained 2D ship kinematics", but it still has not entered the realm of real ship fluid dynamics.

Real ship motion involves:

- **Hydrodynamic resistance**: Ship resistance = frictional resistance (∝ V² × wetted surface area) + wave-making resistance (strongly correlated with Froude number Fr = V/√(gL)) + viscous pressure resistance. The resistance curve has a "hump" (wave-making resistance peaks at Fr ≈ 0.35-0.5), where acceleration is severely limited. The current model can instantaneously change direction at any speed – this is equivalent to infinite side thrust and zero hydrodynamic damping.
- **Turning performance**: Real surface ships have a minimum turning radius (tactical diameter); they cannot turn instantly with zero turning radius like the current implementation. Publicly available information supports "ships have limited turning, with steady turning and heel response", but the specific tactical diameter values for DDG-51 are not suitable for hard-coding from open sources.
- **Acceleration/deceleration inertia**: A ship does not accelerate from stop to high speed, or decelerate from high speed, instantaneously. Public professional sources support that Arleigh Burke-class ships have significant propulsion and maneuvering response delays, but certain "minute-level" numbers in the current document should not be treated as verified hard facts. The current model's speed scaling takes effect per frame without mass inertia.
- **Propulsion system response**: Gas turbines take tens of seconds from idle to full power (LM2500 from idle to full power about 30-60 seconds), and usually deliver thrust through controllable-pitch propellers (CPP) or reduction gears, introducing mechanical response delays.
- **Rudder effectiveness**: Rudder force is related to speed, rudder angle, and flow field; rudder effectiveness decreases significantly at low speeds. Currently, there is no rudder model.
- **Wind/current effects on motion**: Real ships experience yaw moments and leeway due to crosswinds, and overall drift due to ocean currents. At low speeds, wind pressure area (lateral area of superstructure) can dominate bow orientation.

### 2.2 Sea State and Wave Response Completely Missing

Currently, `z=0, pitch=0, roll=0` means the sea surface is a geometric plane.

Real sea conditions:

- **Wave-induced six-degree-of-freedom motion**: Heave, pitch, and roll are functions of the wave spectrum (e.g., Pierson-Moskowitz or JONSWAP spectrum). SS5 (significant wave height 2.5-4.0m) is sufficient to cause noticeable changes in ship attitude and sensor operating conditions, but specific pitch/roll amplitudes depend strongly on ship type, wave direction, speed, and loading, so they should not be written as hard facts here.
- **Wave-added resistance**: Ships navigating in waves experience additional resistance and speed loss. Public course materials support "significant added resistance in high sea states", but specific speed loss percentages and knots should be treated as engineering orders of magnitude, not fixed facts.
- **Deck availability limitations**: Beyond a certain sea state, the flight deck (DDG-51 has a helicopter deck) becomes unusable, limiting shipboard helicopter operating windows.
- **Wave effects on draft**: A ship's actual draft in waves varies between still-water draft ± (wave amplitude × hull response function), directly affecting shallow water operations (e.g., littoral combat).

### 2.3 Surface Sensors Share Air Radar Framework

Ship surface search radars and airborne radars share the same `Sensor` component and `DefaultSensorModel`, but the physical environments they face are fundamentally different:

- **Sea clutter**: The primary limitation for surface search radars is not receiver thermal noise, but backscattered clutter from the sea surface. Sea clutter RCS varies with sea state, grazing angle, polarization, and wavelength. At low grazing angles (<5°), the amplitude distribution of sea clutter is long-tailed non-Gaussian (K-distribution), resulting in significantly higher false alarm rates than thermal noise baselines. The current model has no sea clutter.
- **Atmospheric ducts**: Maritime environments frequently experience evaporation ducts (height typically a few meters to tens of meters above the sea surface) and surface ducts, leading to over-the-horizon detection and duct blind zones. The range extension depends heavily on weather and frequency band and should not be written as fixed capability values here.
- **Multipath effects**: Surface reflection creates interference between direct and reflected paths, causing periodic signal attenuation at specific ranges for low-altitude/surface targets (Lloyd's mirror effect). This has a decisive impact on detection of sea-skimming anti-ship missiles.
- **No shipboard ESM**: Real warships are equipped with broadband Electronic Support Measures (ESM) systems for passive detection, identification, and localization of enemy radar emitters. This is the most important source of situational awareness in surface warfare other than radar. Currently, RWR is only used for airborne platforms.
- **Radar limited to surface search**: DDG-51 is equipped with the SPY-1D phased array radar (air search/track) and SPS-67 (surface search), with complementary functions. Currently, only SPS-67 surface search is implemented – SPY-1D volume search, multi-target tracking, and fire control support are completely unmodeled.

### 2.4 No Shipboard Sonar / Anti-Submarine Warfare

There are no sonar components, underwater acoustic models, or submarine entities anywhere in the project:

- **No hull-mounted sonar** (e.g., AN/SQS-53): Active/passive sonar is a publicly confirmable ASW capability of DDG-51, but specific detection ranges depend heavily on hydrology, target noise, and tactical situation, and should not be written as fixed performance metrics here.
- **No towed array sonar** (e.g., AN/SQR-19 TACTAS): Towed arrays are also a publicly confirmable capability, but specific "long range" magnitudes are more suitable as engineering approximations rather than fixed hard metrics.
- **No variable depth sonar (VDS)**: Sonar that can be lowered below the thermocline to overcome sound speed profile curvature.
- **No sound velocity profile/hydrological conditions**: The propagation path of sound in seawater depends strongly on temperature/salinity/depth gradients (sound velocity profile). The thermocline creates shadow zones, and convergence zones (CZ) produce annular high-probability detection bands at approximately 30-35 nmi intervals. Not modeling this means it's impossible to distinguish "good hydrology" from "bad hydrology".
- **No submarine entities**: The `UnitType` enumeration has no submarine type, no concepts of dive depth/anechoic coating/quiet speed.
- **No torpedoes/depth charges/ASW rockets**: Anti-submarine weapons are completely absent.

### 2.5 Shipboard Weapon Systems – Metadata Placeholder, No Runtime Implementation

The weapon systems listed in the DDG-51 JSON definition are explicitly marked as metadata only in `_provenance.modeling_notes`:

> "Weapon inventory is recorded in metadata but not loaded into runtime ammo because current Ammo only represents generic missiles_remaining."

Specifically:

- **Mk 41 VLS**: DDG-51 Flight I has 90 cells (29 forward + 61 aft), capable of loading Standard Missile (SM-2/SM-6 air defense), Tomahawk (land attack), VL-ASROC (ASW), and other missiles. Currently, there is no VLS launch logic – no missile type distinction, no launch rate limit, no difference between hot launch/cold launch, no unavailable state after VLS cell depletion. The `fire_missile()` API from air combat is designed for air-launched munitions and does not accept VLS as a launch platform.
- **5-inch/54 gun**: DDG-51 is equipped with a Mk 45 Mod 1/2 5-inch/54 caliber naval gun. Real rate of fire is 16-20 rounds/min, maximum range about 24 km (conventional ammunition) / 36 km (extended range guided munition). Capable of surface, land, and limited anti-air warfare. Currently completely unimplemented – no projectile ballistics, no turret traverse/elevation rate limits, no ammunition type distinction.
- **Phalanx CIWS**: Mk 15 close-in weapon system, 20mm six-barreled Gatling gun, rate of fire 3000-4500 rounds/min, effective intercept range about 1.5 km, with its own Ku-band search/track radar. Currently completely unimplemented – no ballistic model for the CIWS, no intercept decision logic, no radar/electro-optical fire control loop for the CIWS itself.
- **Harpoon anti-ship missile**: Active radar terminal homing anti-ship missiles like RGM-84 Harpoon are currently not implemented. Publicly available information supports "Harpoon equipment family exists in early DDG-51 configurations", but specific range values for different batches/variants should not be fixed here.
- **No anti-air missile fire control chain**: The search, fire control, and terminal support chain for the Standard Missile family is currently unimplemented. More accurately: the current project does not distinguish between Aegis search/midcourse control and terminal illumination/autonomous terminal homing differences, so it cannot express different modes like SM-2 / SM-6.
- **No shipboard electronic warfare system**: The SLQ-32(V) electronic warfare suite can perform threat warning, jamming, and chaff/infrared decoy launching (Mk 36 SRBOC). Currently, there are no shipboard ECM/ESM systems.

### 2.6 Ship Damage Model – HP Placeholder, No Sinking/Disablement Physics

```cpp
// Default 1 HP / metric ton full load displacement
// DDG-51: 8,362,000 HP → equivalent to 8362 ton reference value
// T-AKE-1: 41,000,000 HP → equivalent to 41000 ton reference value
```

Real ship survivability cannot be modeled with a scalar HP. Key characteristics of ship damage include:

- **Watertight integrity**: A ship does not sink because "HP reaches zero", but because watertight compartments fail to prevent flooding spread. Publicly available information supports "watertight integrity, damage control, and flooding propagation are core to ship survivability", but specific numbers of compartments or how many compartments a single hit can penetrate should not be written as verified facts here.
- **Flooding propagation and stability**: Flooding volume → increased draft → reduced freeboard → more compartments flood (free surface effect → reduced stability → capsizing). This is the typical chain reaction leading to real warship sinking. The HP zero → destruct logic cannot express this gradual process, nor can it distinguish between "slow sinking (can be abandoned)" and "capsizing (uncontrollable)".
- **Mission kill ≠ sinking**: Mission kill can occur without the ship sinking – radar/combat system destroyed prevents air defense missions, but the ship can still move and communicate. Mobility kill – propulsion system or rudder destroyed, ship loses steering but remains afloat and can fight. The current model uses destruct as the only failure mode, with no intermediate disablement states.
- **Armor value is zero**: The hit boxes for DDG-51 and T-AKE-1 both have `armor_mm = 0.0`, indicating that the runtime has not yet established dedicated judgment for armor penetration, fragmentation, flooding, or damage resistance for ships. Public sources support that DDG-51 and commercial-grade replenishment ships have significant differences in damage resistance design, but specific numbers like Kevlar tonnage are more suitable as supplemental engineering or community information, not hard facts here.
- **No fire propagation**: Missile hit → fuel/ammunition fire → fire spread → temperature/smoke → casualties/system failures. This is the most common damage mode in ship combat. The current model only has an immediate `system_health -= 1.0`.
- **No redundant system effects**: DDG-51 has 4 LM2500 gas turbines (in two groups, two engine rooms). If one engine room is destroyed, the other can still provide about 50% propulsion power. Currently, propulsion only has a single `mil_thrust_n/ab_thrust_n`, unable to express this redundancy.

### 2.7 Red Force Uses T-AKE-1 Placeholder

Currently, red contacts use the T-AKE-1 hull configuration (`take1_usns_lewis_and_clark.json`) as a placeholder at runtime:

- T-AKE-1 is an **unarmed commercial-grade replenishment ship** (Lewis and Clark class), with a maximum speed of only 20 kt, no weapons, no armor, no combat system.
- Using this hull for the red force implies: red force approaches the blue formation at 20 kt slow speed, with no threat capability (itself not a warship); its "merchant-grade RCS/sensor characteristics" are more suitable as engineering inferences, not verified first-hand facts here.
- There is no modeling of any real potential adversary (e.g., destroyer, frigate, or submarine).
- This means the current "red contact" physically lacks the behavioral characteristics of an enemy ship – it's just a geometric entity moving at a fixed speed with an incorrect ship type label.

### 2.8 Maritime Formation and Screen Control

The core semantics of the current scenario are DDG-51 screening T-AKE-1, but:

- **Currently only a minimal station-keeping closed loop**: The project now has added a minimal closed loop based on `reference_entity_id + station_radius_m + station_heading_deg` at the loader behavior layer, elevating screening from "pure initial geometry" to an engineering approximation with "recoverable stations". However, it is still not a threat-response-driven real formation control, and lacks sector rotation, coordinated turns, or multi-ship formation resolution.
- **No formation maneuver coordination**: During a real formation turn, ships need to coordinate turn rate and radius to avoid collisions and maintain station. Currently, there is no formation-level control.
- **No multi-ship formation logic**: Only two ships (DDG-51 + T-AKE-1), no sector stations for multiple screen ships, no multi-layer defense in depth (outer air defense / mid-layer anti-ship / inner CIWS), no complex formation geometry for a carrier battle group.

### 2.9 Data Link – Faction-Level Approximation, No Fleet C2 Semantics

- **Network number = faction number**: `network_id = 1` means blue force, `network_id = 2` means red force. Real fleet data links (Link 16 / Link 11 / Link 22) have more complex organization – a carrier battle group may have multiple independent networks (different NPGs) and require cross-network gateway forwarding. Within the same faction, there are also distinctions between different task groups.
- **Only minimal shared track/report approximation**: The current implementation is no longer just "each local sensor sees its own", but can share tracks between platforms on the same network and generate report messages; however, it still does not have task assignment/receipt, engagement authorization transfer, weapon coordination (e.g., CEC), or real Link 16/NPG semantics. More accurately, the current implementation is still far weaker than real tactical data links and fleet C2 organization.
- **No message priority or time slot allocation**: Link 16 TDMA slots are divided into multiple NPGs, with different message types (surveillance tracks, EW data, voice, mission management) occupying different slot resources. In dense electromagnetic environments, there is slot contention and priority queuing.

### 2.10 Underway Replenishment and Logistics

The core mission of T-AKE-1 is underway replenishment (UNREP), but:

- **No underway replenishment (UNREP) mechanism**: Real UNREP requires alongside navigation, strict relative position control, and a replenishment state machine. Public and experiential sources support this as a highly constrained operation requiring dedicated geometry and procedural guarantees, but specific distances, speeds, and durations are more suitable as engineering approximations than hard facts here. Currently, T-AKE-1 is just "a cargo hold moving on the surface" with no cargo transfer capability.
- **No ammunition/fuel/consumables inventory model**: T-AKE-1's replenishment stocks are not modeled – no ammunition counts, fuel volumes, dry cargo tonnage, refrigerated cargo, etc. VLS ammunition consumed by DDG-51 cannot be replenished from T-AKE-1 (even without considering the physical feasibility of UNREP).
- **No replenishment vulnerability constraints**: During underway replenishment, both ships are in an unusually vulnerable state – cannot maneuver significantly, narrow inter-ship distance, predictable replenishment time windows. This is tactically a golden attack opportunity for enemy submarines.

### 2.11 No Naval Aviation Interaction

The DDG-51 class has shipboard aviation coordination capabilities, but the currently selected `DDG-51 Flight I` configuration should not be described as a "ship with double hangars typically carrying 2 MH-60R". More accurately: the current project has no shipboard helicopter operations or aviation coordination runtime, but:

- **No shipboard helicopter modeling**: MH-60R provides long-range ASW search (dipping sonar/sonobuoys), anti-ship missile midcourse guidance, over-the-horizon targeting, search and rescue, vertical replenishment (VERTREP), and other critical capabilities. Currently, there are no helicopter entities, no launch/recovery logic, no deck state (deck unavailable conditions).
- **No VERTREP logic**: Vertical replenishment is another replenishment method besides UNREP – helicopters transport cargo between T-AKE-1 and DDG-51 without requiring the ships to be alongside. This is faster than UNREP and does not constrain formation maneuver.

## 3. Statements That Should Not Be Used Currently

To avoid future semantic drift, the following expressions should be explicitly avoided:

1. The current naval warfare scenario should not be called "naval warfare engagement simulation" – it is
   a **"minimal realistic surface screen contact scenario"**, with no weapon engagement, no damage, no maneuver combat.
2. The current DDG-51 should not be called a "realized Aegis warship" – it is
   a **"surface geometric entity with realistic public dimensions/displacement parameters + placeholder HP"**,
   without SPY-1D, without VLS launch chain, without fire control, without CEC.
3. The current ship damage model should not be called "ship survivability simulation" – it is
   a **"1 HP/metric ton + armor=0 hit box placeholder"**,
   without compartment flooding, without fire propagation, without stability loss, without mission disablement grading.
4. The current screen geometry should not be called "complete formation escort control" – it is
   a **"screen approximation with minimal station-keeping closed loop"**, still without formation maneuver coordination, threat-driven reconfiguration, or multi-ship formation control.
5. The current red contact should not be called "enemy ship" – it is
   a **"placeholder entity reusing T-AKE-1 merchant hull parameters"**, not a real enemy ship model.
6. The current data link sharing should not be called "fleet tactical data link" – it is
   a **"same-faction track/report sharing engineering approximation"**,
   without Link 16 NPGs, without time slots, without command relationships, without CEC weapon coordination.

More accurate descriptions are:

- **Minimal realistic surface screen contact baseline**
- **Escort / detection / shared situational awareness validation scenario**
- **Naval warfare startup example before entering weapon, damage, and formation control modeling**

This conclusion is frozen until the next explicit reopening of naval warfare progress.

---

## 4. Source Notes and Evidence Levels

- `Official/semi-official public facts`: DDG-51 equipment family, SQQ-89/SLQ-32/MH-60R capability chain, Flight I aviation facility boundaries – primarily reference US Navy public fact files, ship characteristics pages, and NAVAIR/NAVSEA public materials.
- `Professional public materials`: Sea clutter, evaporation ducts, multipath, sound velocity profiles, convergence zones, etc. – primarily reference published papers, course materials, and technical surveys.
- `Community/instructional materials`: Sonar first convergence zone magnitude order, some sea state and maneuvering empirical values – can be used as engineering approximation supplements, but not treated as hard metrics.
- `Engineering approximations, not public fixed values`: DDG-51 specific tactical diameter, SS5 pitch/roll amplitudes, fixed speed loss percentages, Harpoon specific batch range, specific compartment numbers and penetration compartment count.
- `Current repository modeling notes`: Ship `max_accel_mps2 / max_decel_mps2 / max_turn_rate_deg_s / low_speed_turn_factor` are runtime calibration quantities, not claimed as authoritative ship class maneuvering data.
