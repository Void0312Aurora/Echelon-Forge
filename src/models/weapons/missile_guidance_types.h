#pragma once

enum class MissileSeekerMode {
    Track = 0,
    Memory = 1,
    Ballistic = 2,
};

struct MissileGuidanceDefaults {
    static constexpr double kTrackFilterTauS = 0.12;
    static constexpr double kTrackMemoryTimeoutS = 0.75;
    static constexpr double kBoostTimeS = 3.0;
    static constexpr double kSustainTimeS = 0.0;
    static constexpr double kReferenceAreaM2 = 0.02;
    static constexpr double kCd0Subsonic = 0.28;
    static constexpr double kCd0Supersonic = 0.60;
    static constexpr double kInducedDragScale = 9.0;
    static constexpr double kPropellantMassFraction = 0.35;
    static constexpr double kMinPropellantMassKg = 8.0;
    static constexpr double kAutopilotTauS = 0.12;
    static constexpr double kAccelResponseGps = 120.0;
    static constexpr double kCaptureGain = 8.0;
    static constexpr double kTerminalCaptureRangeM = 6000.0;
    static constexpr double kPnGainScale = 1.2;
    static constexpr double kDefaultApnTargetAccelGain = 0.0;
    static constexpr double kApnAccelFilterTauS = 0.30;
    static constexpr double kActuatorTauS = 0.03;
    static constexpr double kMachTransonicStart = 0.80;
    static constexpr double kMachTransonicEnd = 1.40;
    static constexpr double kCd0PowerOnRatio = 0.90;
};
