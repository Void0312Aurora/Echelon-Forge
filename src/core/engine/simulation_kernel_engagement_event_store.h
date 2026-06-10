#pragma once

#include <cstddef>
#include <cstdint>
#include <string>

#include <flecs.h>

#include "core/engine/engagement_event_types.h"
#include "core/interfaces/engagement_event_recorder.h"
#include "core/interfaces/engagement_launch_recorder.h"

class SimulationKernelEngagementEventStore final : public IEngagementEventRecorder,
                                                   public IEngagementLaunchRecorder {
  public:
    explicit SimulationKernelEngagementEventStore(flecs::world &ecs);

    EngagementDamageStateSnapshot
    capture_engagement_damage_state(std::uint64_t target_id) const override;

    std::uint64_t record_effects_damage_event(EngagementEffectsDamageEventRecord record) override;

    std::uint64_t
    record_nearest_approach_event(EngagementNearestApproachEventRecord record) override;

    std::uint64_t record_fuze_evaluation_event(EngagementFuzeEvaluationEventRecord record) override;

    std::uint64_t
    record_warhead_mechanism_event(EngagementWarheadMechanismEventRecord record) override;

    std::uint64_t
    record_spatial_coverage_event(EngagementSpatialCoverageEventRecord record) override;

    std::uint64_t record_component_load_event(EngagementComponentLoadEventRecord record) override;

    std::uint64_t record_legacy_launch_event(std::uint64_t shooter_id, std::uint64_t target_id,
                                             std::uint64_t spawned_munition_id,
                                             const std::string &selected_launcher,
                                             const std::string &selected_munition, int ammo_delta,
                                             double cooldown_delta_s, double event_time_s) override;

    void set_pending_effects_launch_event_id(std::uint64_t launch_event_id) override;
    RecentEngagementEvents export_recent_events_sorted() const;
    void clear();

  private:
    void reset_if_event_clock_rewound(double event_time_s);

    flecs::world &ecs_;
    RecentEngagementEvents recent_engagement_events_;
    std::uint64_t next_engagement_event_id_ = 1;
    std::uint64_t pending_effects_launch_event_id_ = 0;
    double recent_engagement_event_epoch_time_s_ = 0.0;
    std::int64_t recent_engagement_event_epoch_frame_ = 0;
    static constexpr std::size_t kMaxRecentEngagementEvents = 64;
};
