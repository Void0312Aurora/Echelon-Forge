#pragma once

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
