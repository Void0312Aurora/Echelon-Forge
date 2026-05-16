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
