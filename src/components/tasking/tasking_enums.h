#pragma once

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

enum class TakeoffProcedureType : int {
    Unspecified = 0,
    SingleShip = 1,
    Interval = 2,
    Wing = 3,
};

enum class TakeoffClearanceState : int {
    Unspecified = 0,
    HoldShort = 1,
    LineUpAndWait = 2,
    ClearedForTakeoff = 3,
    Rolling = 4,
    Airborne = 5,
    Abort = 6,
};

enum class RunwaySlotPosition : int {
    Unspecified = 0,
    Center = 1,
    Left = 2,
    Right = 3,
};
