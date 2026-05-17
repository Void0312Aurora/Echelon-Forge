#pragma once

#include <algorithm>
#include <vector>
#include <cstdint>
#include "components/basic/common.h"

enum class TrackSource {
    None = 0,
    Radar,
    RWR,
    DataLink,
    Fused, // Merged from multiple sources
    Sonar
};

enum class TrackClass {
    Unknown = 0,
    Friendly,
    Hostile,
    Neutral
};

enum class TrackStatus {
    Tentative = 0,
    Confirmed,
    Coasted
};

enum class TrackUsability {
    None = 0,      // Not suitable for tactical use yet
    Advisory,      // Situationally useful, but stale / not for weapons-quality actions
    Tactical       // Fresh enough for tactical cueing / action gating
};

struct SystemTrack {
    uint64_t track_id;
    uint64_t entity_id; // True ID (cheating/lookup) or purely internal logic?
                        // Ideally we correlate by ID if DL, but by position if Radar.
                        // For simplicity in MVP: Store entity_id if known (DL), else 0? 
                        // Actually, sensors often provide a handle. Let's store entity_id for ground truth correlation/debugging, 
                        // but logic should rely on position.
                        
    double x, y, z; // Estimated Position
    double vx, vy, vz; // Estimated Velocity
    
    double range;
    double azimuth;
    double elevation;
    
    TrackSource main_source;
    TrackSource local_source = TrackSource::None;
    TrackClass classification;
    TrackStatus status = TrackStatus::Tentative;
    
    double confidence; // 0.0 - 1.0
    double time_since_update;
    double quality = 0.0;
    int confirm_hit_count = 0;
    int confirm_miss_count = 0;
    int confirm_window_progress = 0;
    double last_local_update_time = -1.0;
    double last_datalink_update_time = -1.0;
    double alpha_beta_alpha = 0.65;
    double alpha_beta_beta = 0.12;
    bool iff_known = false;
    double classification_confidence = 0.0;
};

// Component attached to the Agent/Aircraft
struct TrackDatabase {
    std::vector<SystemTrack> tracks;
    std::vector<SystemTrack> tentative_tracks;
    // Configuration
    double fusion_radius_m = 1000.0; // Correlate within 1km
    int max_tracks = 32;
};

constexpr double kTrackAdvisoryQualityThreshold = 0.35;
constexpr double kTrackAdvisoryConfidenceThreshold = 0.35;
constexpr double kTrackTacticalQualityThreshold = 0.60;
constexpr double kTrackTacticalConfidenceThreshold = 0.60;
constexpr double kTrackRecentDataLinkSupportWindowS = 5.0;
constexpr double kTrackDropGraceMinS = 10.0;

inline bool track_source_is_local(TrackSource source) {
    return source == TrackSource::Radar
        || source == TrackSource::RWR
        || source == TrackSource::Sonar;
}

inline double track_recent_local_support_window_s(double scan_period_s) {
    return std::max(1.0, scan_period_s * 1.5);
}

inline bool track_has_recent_local_support(
    const SystemTrack& track,
    double current_time,
    double local_support_window_s
) {
    return track_source_is_local(track.local_source)
        && track.last_local_update_time >= 0.0
        && (current_time - track.last_local_update_time) <= local_support_window_s;
}

inline bool track_has_recent_datalink_support(
    const SystemTrack& track,
    double current_time,
    double datalink_support_window_s = kTrackRecentDataLinkSupportWindowS
) {
    return track.last_datalink_update_time >= 0.0
        && (current_time - track.last_datalink_update_time) <= datalink_support_window_s;
}

inline bool track_has_local_geometry_this_update(
    const SystemTrack& track,
    double current_time
) {
    return track.last_local_update_time >= 0.0
        && std::abs(track.last_local_update_time - current_time) <= 1.0e-6;
}

inline TrackSource resolved_track_source(
    const SystemTrack& track,
    double current_time,
    double local_support_window_s,
    double datalink_support_window_s = kTrackRecentDataLinkSupportWindowS
) {
    const bool has_local = track_has_recent_local_support(track, current_time, local_support_window_s);
    const bool has_datalink = track_has_recent_datalink_support(track, current_time, datalink_support_window_s);
    if (has_local && has_datalink) {
        return TrackSource::Fused;
    }
    if (has_local) {
        return track.local_source;
    }
    if (has_datalink) {
        return TrackSource::DataLink;
    }
    if (track_source_is_local(track.local_source)) {
        return track.local_source;
    }
    if (track.last_datalink_update_time >= 0.0) {
        return TrackSource::DataLink;
    }
    if (track.main_source != TrackSource::Fused) {
        return track.main_source;
    }
    return TrackSource::None;
}

inline void refresh_track_source(
    SystemTrack& track,
    double current_time,
    double local_support_window_s,
    double datalink_support_window_s = kTrackRecentDataLinkSupportWindowS
) {
    track.main_source = resolved_track_source(
        track,
        current_time,
        local_support_window_s,
        datalink_support_window_s
    );
}

inline bool track_source_supports_positive_iff(TrackSource source) {
    return source == TrackSource::DataLink || source == TrackSource::Fused;
}

inline bool track_has_any_recent_support(
    const SystemTrack& track,
    double current_time,
    double local_support_window_s,
    double datalink_support_window_s = kTrackRecentDataLinkSupportWindowS
) {
    return track_has_recent_local_support(track, current_time, local_support_window_s)
        || track_has_recent_datalink_support(track, current_time, datalink_support_window_s);
}

inline double default_classification_confidence(
    TrackSource source,
    TrackClass classification,
    bool iff_known
) {
    if (classification == TrackClass::Unknown) {
        return 0.0;
    }
    if (iff_known) {
        return 0.90;
    }
    switch (source) {
        case TrackSource::RWR:
            return 0.25;
        case TrackSource::Sonar:
            return 0.30;
        case TrackSource::Radar:
            return 0.35;
        case TrackSource::DataLink:
        case TrackSource::Fused:
            return 0.90;
        case TrackSource::None:
        default:
            return 0.20;
    }
}

inline void refresh_track_identification(
    SystemTrack& track,
    double current_time,
    double datalink_support_window_s = kTrackRecentDataLinkSupportWindowS
) {
    const bool inferred_iff =
        track.classification != TrackClass::Unknown
        && track_has_recent_datalink_support(track, current_time, datalink_support_window_s)
        && track_source_supports_positive_iff(track.main_source);
    track.iff_known = inferred_iff;

    if (track.classification == TrackClass::Unknown && !track.iff_known) {
        track.classification_confidence = 0.0;
        return;
    }

    track.classification_confidence =
        default_classification_confidence(track.main_source, track.classification, track.iff_known);
}

inline double track_drop_timeout_s(double track_memory_s, double scan_period_s) {
    return std::max(
        kTrackDropGraceMinS,
        std::max(track_memory_s * 2.0, scan_period_s * 3.0)
    );
}

inline TrackUsability track_usability_from_semantics(
    TrackStatus status,
    double quality,
    double confidence
) {
    if (status == TrackStatus::Tentative) {
        return TrackUsability::None;
    }
    if (quality < kTrackAdvisoryQualityThreshold || confidence < kTrackAdvisoryConfidenceThreshold) {
        return TrackUsability::None;
    }
    if (status == TrackStatus::Coasted) {
        return TrackUsability::Advisory;
    }
    if (quality >= kTrackTacticalQualityThreshold && confidence >= kTrackTacticalConfidenceThreshold) {
        return TrackUsability::Tactical;
    }
    return TrackUsability::Advisory;
}

inline TrackUsability track_usability_for(const SystemTrack& track) {
    return track_usability_from_semantics(track.status, track.quality, track.confidence);
}

inline bool track_is_tactically_usable(const SystemTrack& track) {
    return track_usability_for(track) == TrackUsability::Tactical;
}
