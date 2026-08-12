#pragma once

#include "core/interfaces/effects_model.h"
#include "runtime/contracts/engagement_contracts.h"

namespace engagement_events {

inline void apply_effects_result_fields(EffectsEvent &effects, const EffectsResult &result) {
    // The overlap set (same member name on both sides) is owned by the
    // EF_EFFECTS_EVENT_RESULT_FIELD entries of the X-macro list; fields that
    // EffectsResult does not have expand to nothing here.
#define EF_EFFECTS_EVENT_FIELD(type, name, default_value)
#define EF_EFFECTS_EVENT_RESULT_FIELD(type, name, default_value) effects.name = result.name;
#include "runtime/contracts/detail/damage/effects_event_fields.inc"
#undef EF_EFFECTS_EVENT_RESULT_FIELD
#undef EF_EFFECTS_EVENT_FIELD
}

} // namespace engagement_events
