#pragma once

#include "core/interfaces/engagement_event_recorder.h"
#include "core/interfaces/engagement_launch_recorder.h"

class IEngagementEventStore : public IEngagementEventRecorder, public IEngagementLaunchRecorder {
  public:
    ~IEngagementEventStore() override = default;

    [[nodiscard]] virtual RecentEngagementEvents export_recent_events_sorted() const = 0;
    virtual void clear() = 0;
};
