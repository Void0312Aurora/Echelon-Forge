#pragma once

enum class GroundTaskMode : int {
    Unspecified = 0,
    MoveStatic = 1,
    OccupyStatic = 2,
    SupportStatic = 3,
};

enum class GroundStatusPhase : int {
    Unspecified = 0,
    Assigned = 1,
    Preparing = 2,
    HoldingStatic = 3,
    OccupyingStatic = 4,
    SupportingStatic = 5,
    Complete = 6,
};
