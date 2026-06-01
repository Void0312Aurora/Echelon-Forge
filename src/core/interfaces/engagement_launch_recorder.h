#pragma once

#include <cstdint>
#include <string>

class IEngagementLaunchRecorder {
public:
    virtual ~IEngagementLaunchRecorder() = default;

    virtual std::uint64_t record_legacy_launch_event(
        std::uint64_t shooter_id,
        std::uint64_t target_id,
        std::uint64_t spawned_munition_id,
        const std::string& selected_launcher,
        const std::string& selected_munition,
        int ammo_delta,
        double cooldown_delta_s,
        double event_time_s
    ) = 0;

    virtual void set_pending_effects_launch_event_id(std::uint64_t launch_event_id) = 0;
};
