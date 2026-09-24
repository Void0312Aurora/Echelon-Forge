#pragma once

enum class GroundTaskMode : int {
    Unspecified = 0,
    MoveStatic = 1,
    OccupyStatic = 2,
    SupportStatic = 3,
};

// Native tactical posture admitted by the bounded infantry movement slice.
// These values affect movement cost only; cover, concealment, exposure, and
// weapon employment remain separate owners.
enum class GroundStance : int {
    Stand = 0,
    Crouch = 1,
    Prone = 2,
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
