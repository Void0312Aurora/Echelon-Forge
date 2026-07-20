#pragma once

#include <vector>

#include "runtime/contracts/engagement_contracts.h"

struct RecentEngagementEvents {
#define EF_RECENT_ENGAGEMENT_EVENTS_FIELD(type, name, default_value) type name = default_value;
#include "core/engine/detail/recent_engagement_events.inc"
};
