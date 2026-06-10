#pragma once

enum class NavalWarfareRole : int {
    Unspecified = 0,
    ScreenCommander = 1,
    SurfaceActionCommander = 2,
    AirDefenseCommander = 3,
    SeaControlCommander = 4,
    LogisticsCoordinator = 5,
};

enum class NavalStationType : int {
    Unspecified = 0,
    Screen = 1,
    Support = 2,
    PatrolStation = 3,
    ReplenishmentTrack = 4,
};
