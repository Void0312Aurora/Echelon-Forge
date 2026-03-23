#pragma once

#include <flecs.h>
#include <cstdint>

// --- New Standards Implementation ---

enum class TaskType : int {
    Idle = 0,
    Scramble = 1,
    CAP = 2,
    RTB = 3,
    RecoverLand = 4,
    CAPMission = 5,
};

enum class StationType : int {
    Orbit = 0,
    Racetrack = 1,
    RouteCAP = 2,
};

enum class LeaderPhase : int {
    Idle = 0,
    Scramble = 1,
    Takeoff = 2,
    Departure = 3,
    TransitToStation = 4,
    EstablishCAP = 5,
    OnStation = 6,
    Reposition = 7,
    RTB = 8,
    ApproachArmed = 9,
    LandingFinal = 10,
    Rollout = 11,
    Abort = 12,
};

enum class RecoveryApproachType : int {
    None = 0,
    StraightIn = 1,
    ILS = 2,
    Visual = 3,
    Overhead = 4,
    TACAN = 5,
};

enum class ServiceProfile : int {
    Unspecified = 0,
    AirForce = 1,
    Army = 2,
    Navy = 3,
    MarineCorps = 4,
};

enum class TaskFamily : int {
    Unspecified = 0,
    Transit = 1,
    Patrol = 2,
    Escort = 3,
    Intercept = 4,
    Attack = 5,
    Defend = 6,
    Recover = 7,
    Withdraw = 8,
};

enum class TacticalUnitType : int {
    Unspecified = 0,
    Platform = 1,
    TacticalUnit = 2,
    MissionPackage = 3,
    CommandNode = 4,
};

enum class CommandRelationship : int {
    None = 0,
    COCOM = 1,
    OPCON = 2,
    TACON = 3,
    Support = 4,
    ADCON = 5,
    CoordinatingAuthority = 6,
    DIRLAUTH = 7,
};

enum class AuthorityScope : int {
    Unspecified = 0,
    Strategic = 1,
    Operational = 2,
    Tactical = 3,
    Execution = 4,
};

enum class AssigneeKind : int {
    Aircraft = 0,
    Element = 1,
    Package = 2,
};

enum class FormationRole : int {
    Unspecified = 0,
    ElementLead = 1,
    Wingman = 2,
};

enum class WingmanSlot : int {
    Unspecified = 0,
    Left = 1,
    Right = 2,
    Trail = 3,
};

enum class FormationMode : int {
    Unspecified = 0,
    Prejoin = 1,
    Joining = 2,
    Cruise = 3,
    CAP = 4,
    Rejoin = 5,
    Recover = 6,
    SplitAbort = 7,
};

enum class WingmanCommandMode : int {
    None = 0,
    HoldSlot = 1,
    Rejoin = 2,
    OffsetLeft = 3,
    OffsetRight = 4,
    Trail = 5,
    Support = 6,
    AbortForm = 7,
};

enum class CoordinationMode : int {
    Unspecified = 0,
    Independent = 1,
    Attached = 2,
    Follow = 3,
    Support = 4,
    Screen = 5,
    Rejoin = 6,
    Recover = 7,
    Detached = 8,
};

/**
 * PilotAction
 * Implements [act.md]: The physical interface for the Digital Pilot.
 */
struct PilotAction {
    // 1. Primary Flight Controls (Continuous [-1, 1] or [0, 1])
    double stick_pitch;      // [-1, 1] (Pull back = negative pitch up? wait. Standard: Pull back = +q. Let's use standard: -1=Pitch Down, 1=Pitch Up? No, Stick Aft is usually positive pitch rate command in FBW? 
                             // Let's follow convention: Stick Pull (+q) is usually Positive Pitch Rate. Stick Push (-q).
                             // Let's stick to standard internal defs: positive = nose up.
    double stick_roll;       // [-1, 1] Positive = Right Roll
    double rudder;           // [-1, 1] Positive = Nose Right (Yaw)
    double throttle;         // [0, 1] 0=Idle, 1=Max AB
    
    // 2. Secondary Controls
    float gear_handle;       // 0.0 (Up) to 1.0 (Down)
    float flaps;             // 0.0 (Up) to 1.0 (Full)
    float speedbrake;        // 0.0 (Retracted) to 1.0 (Extended)
    double brake;            // 0.0 (Off) to 1.0 (Full)
    bool brake_left;         // Wheel brake
    bool brake_right;        // Wheel brake
    
    // 3. Sensors / Avionics
    bool radar_active;       // Main Radar Switch
    double radar_scan_az;    // Scan Center Azimuth
    double radar_scan_el;    // Scan Center Elevation
    bool tms_up;             // Target Management Switch Up (Lock)
    
    // 4. Weapons
    bool master_arm;
    bool fire_weapon;        // Pickle/Trigger
    bool fire_gun;           // Gun Trigger
    int weapon_select_id;    // Selected Weapon Station/Type
    bool jettison_emergency; 
    
    // 5. Countermeasures
    bool program_chaff;
    bool program_flare;
    
    bool active;             // Validity flag
};

/**
 * MissionCommand
 * Implements [aim.md]: The high-level intent from Commander.
 */
struct MissionCommand {
    // 1. Command-bound parameters
    // These fields are not globally free parameters. They must be interpreted
    // according to command_code:
    //   - command_code == 3: route/LNAV target track-altitude-speed reference
    //   - command_code == 4: terminal recovery metadata selects the procedure;
    //                        terminal heading/alt/speed should come from the
    //                        chosen recovery program rather than free leader bias
    double cmd_heading_deg;  // Route/LNAV track bug when command_code == 3
    double cmd_altitude_m;   // Route/stage reference altitude
    double cmd_speed_mps;    // Route/stage reference speed

    // 2. Macro Codes
    // Project-local convention used by the current RL/scenario stack:
    //   0 = Idle / no mission
    //   1 = Takeoff / runway departure
    //   2 = Heading-altitude-speed vectoring / stable flight
    //   3 = Waypoint / LNAV route navigation
    // Tactical task codes (attack/RTB/etc.) are reserved for future mission layers.
    int command_code;

    // 2.1 Route / recovery references
    uint64_t route_ref_id;
    uint64_t recovery_base_id;
    uint64_t recovery_runway_id;
    RecoveryApproachType recovery_approach_type;
    
    // 3. Formation
    int formation_id;
    double form_offset_x;
    double form_offset_y;
    double form_offset_z;
    
    // 4. Tactical
    uint64_t assigned_target_id;
    bool authorization_to_fire;

    bool active;
};

/**
 * TaskOrder
 * Implements task_order_leader_standard.md: the C2 -> Leader task object.
 */
struct TaskOrder {
    uint64_t task_id = 0;
    TaskType task_type = TaskType::Idle;
    ServiceProfile service_profile = ServiceProfile::Unspecified;
    TaskFamily task_family = TaskFamily::Unspecified;
    TacticalUnitType tactical_unit_type = TacticalUnitType::Unspecified;
    int priority = 0;
    uint64_t issuer_id = 0;
    uint64_t assignee_id = 0;
    CommandRelationship command_relationship = CommandRelationship::None;
    AuthorityScope authority_scope = AuthorityScope::Unspecified;
    uint64_t parent_node_id = 0;
    uint64_t task_group_id = 0;
    uint64_t supported_node_id = 0;
    uint64_t supporting_node_id = 0;
    int role_code = 0;
    CoordinationMode coordination_mode = CoordinationMode::Unspecified;
    int relative_slot_code = 0;
    AssigneeKind assignee_kind = AssigneeKind::Aircraft;
    uint64_t recovery_site_id = 0;
    uint64_t element_id = 0;
    uint64_t package_id = 0;
    uint64_t lead_aircraft_id = 0;
    bool active = false;
    double issue_time_s = 0.0;

    double anchor_x_m = 0.0;
    double anchor_y_m = 0.0;
    double anchor_z_m = 0.0;
    StationType station_type = StationType::Orbit;
    double station_radius_m = 0.0;
    double station_leg_length_m = 0.0;
    double station_heading_deg = 0.0;

    double altitude_block_min_m = 0.0;
    double altitude_block_max_m = 0.0;
    double target_altitude_m = 0.0;
    double speed_min_mps = 0.0;
    double speed_max_mps = 0.0;
    double target_speed_mps = 0.0;

    int entry_condition_code = 0;
    int exit_condition_code = 0;
    double on_station_time_s = 0.0;
    double fuel_bingo_override_kg = 0.0;
    uint64_t recovery_base_id = 0;
    uint64_t recovery_runway_id = 0;
    RecoveryApproachType recovery_approach_type = RecoveryApproachType::None;
    uint64_t formation_template_id = 0;
    uint64_t formation_contract_id = 0;
    FormationRole formation_role_id = FormationRole::Unspecified;
    WingmanSlot wingman_slot_id = WingmanSlot::Unspecified;
    int join_policy_id = 0;
    int rejoin_policy_id = 0;
    int mutual_support_mode = 0;
    uint64_t support_sector_id = 0;
};

/**
 * LeaderIntent
 * Internal Leader-layer output before mapping into MissionCommand.
 */
struct LeaderIntent {
    LeaderPhase phase_id = LeaderPhase::Idle;
    int element_phase_id = 0;
    ServiceProfile service_profile = ServiceProfile::Unspecified;
    TaskFamily task_family = TaskFamily::Unspecified;
    TacticalUnitType tactical_unit_type = TacticalUnitType::Unspecified;
    uint64_t tactical_unit_id = 0;
    uint64_t task_group_id = 0;
    int role_code = 0;
    CoordinationMode coordination_mode = CoordinationMode::Unspecified;
    int relative_slot_code = 0;
    uint64_t recovery_site_id = 0;
    int command_code = 0;
    uint64_t route_ref_id = 0;
    uint64_t recovery_base_id = 0;
    uint64_t recovery_runway_id = 0;
    RecoveryApproachType recovery_approach_type = RecoveryApproachType::None;
    double cmd_heading_deg = 0.0;
    double cmd_altitude_m = 0.0;
    double cmd_speed_mps = 0.0;
    int formation_id = 0;
    double form_offset_x = 0.0;
    double form_offset_y = 0.0;
    double form_offset_z = 0.0;
    uint64_t assigned_target_id = 0;
    bool authorization_to_fire = false;
    FormationMode formation_mode_id = FormationMode::Unspecified;
    bool join_required_flag = false;
    bool rejoin_required_flag = false;
    bool split_flag = false;
    double support_anchor_x_m = 0.0;
    double support_anchor_y_m = 0.0;
    double support_slot_offset_x_m = 0.0;
    double support_slot_offset_y_m = 0.0;
    WingmanCommandMode wingman_command_mode = WingmanCommandMode::None;
    bool approach_armed = false;
    bool commit_to_land = false;
    bool abort_flag = false;
    bool active = false;
};


// --- Legacy Components (To be Deprecated) ---

struct MovementCommand {
    double target_heading; // Degrees, 0 = North, Clockwise
    double target_speed;   // m/s
    double target_altitude;// m (New)
    
    // Direct Stick Inputs (Overlay) - MOVED TO PILOT ACTION
    bool use_stick_control; 
    double stick_roll;      
    double stick_pitch;     
    double throttle_cmd;    
    bool gear_handle;       
    
    bool active;           
};

struct ActionCommand {
    double turn_rate_cmd;  // Normalized [-1, 1]
    double accel_cmd;      // Normalized [-1, 1]
    double climb_rate_cmd; // Normalized [-1, 1]
    
    double fire_cmd;       // [0, 1], optional
    bool release_chaff;    // Instantaneous trigger
    bool release_flare;    // Instantaneous trigger
    bool jettison_tanks;   // Instantaneous trigger
    bool send_msg;         // C2: Send a message
    int msg_type;          // C2: CommMsgType cast to int
    uint64_t msg_recipient;// C2: Target ID (0=Broadcast)
    uint64_t msg_arg;      // C2: Reference ID (e.g. Target)
    bool active;
};

struct ActionSpaceConfig {
    double max_turn_rate_deg_s;
    double max_accel_mps2;
    double max_climb_rate_mps;
    double min_speed_mps;
    double max_speed_mps;
    double min_alt_m;
    double max_alt_m;
};

struct CommandLag {
    double heading_tau_s;
    double speed_tau_s;
    double altitude_tau_s;
};

struct LaggedCommand {
    double target_heading;
    double target_speed;
    double target_altitude;
    bool active;
};

struct CommandLink {
    double latency_s;   // One-way command latency
    double drop_prob;   // [0,1] command drop probability
};

struct PendingMovementCommand {
    MovementCommand command;
    double deliver_time;
    bool active;
};

struct PendingActionCommand {
    ActionCommand command;
    double deliver_time;
    bool active;
};

struct PendingMissionCommand {
    MissionCommand command;
    double deliver_time;
    bool active;
};
