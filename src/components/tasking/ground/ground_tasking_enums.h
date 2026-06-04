#pragma once

enum class GroundTaskGrade : int {
    Unspecified = 0,
    TaskingStatus = 1,
    StaticOccupySupport = 2,
};

enum class GroundTaskKind : int {
    Unspecified = 0,
    Move = 1,
    Occupy = 2,
    Support = 3,
};

enum class GroundSchemaBoundary : int {
    Unspecified = 0,
    CompatibilityShell = 1,
    NativeStaticSchema = 2,
};
