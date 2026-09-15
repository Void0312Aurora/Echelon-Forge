#pragma once

// Lightweight guidance mode identifiers shared by content parsing, ECS
// components, and replaceable guidance implementations. Behavior and
// numerical defaults remain owned by models/weapons.
enum class MissileSeekerMode {
    Track = 0,
    Memory = 1,
    Ballistic = 2,
};

enum class MissilePnLosRateSource {
    LegacyBodyRates = 0,
    WorldLosHistory = 1,
};

enum class MissileTargetKinematicsEstimator {
    LegacyPolarDifference = 0,
    WorldCv = 1,
    WorldCva = 2,
};

enum class MissileCaptureGuidanceMode {
    Disabled = 0,
    LegacyPursuit = 1,
};
