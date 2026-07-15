#pragma once

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
};

struct MissileGuidanceDefaults {
    static constexpr int kDefaultPnLosRateSource =
        static_cast<int>(MissilePnLosRateSource::LegacyBodyRates);
    static constexpr int kDefaultTargetKinematicsEstimator =
        static_cast<int>(MissileTargetKinematicsEstimator::LegacyPolarDifference);
    static constexpr double kWorldCvTrackerAlpha = 0.20;
    static constexpr double kWorldCvTrackerBeta = 0.02;
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
    static constexpr double kDefaultApnTargetAccelGain = 0.50;
    static constexpr double kApnAccelFilterTauS = 0.45;
    static constexpr double kTargetKinematicsVelocityFilterTauS = 0.20;
    static constexpr double kTargetKinematicsAccelFilterTauS = 0.45;
    static constexpr double kLeadPredictionMaxTimeS = 2.5;
    static constexpr double kLeadPredictionMinClosingMps = 150.0;
    static constexpr double kLeadBlendMax = 0.55;
    static constexpr double kLeadBlendTerminalRangeM = 8000.0;
    static constexpr double kApnAccelLimitFraction = 0.35;
    static constexpr double kActuatorTauS = 0.03;
    static constexpr double kMachTransonicStart = 0.80;
    static constexpr double kMachTransonicEnd = 1.40;
    static constexpr double kCd0PowerOnRatio = 0.90;
};
