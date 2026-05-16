#pragma once

#include "components/tasking/air/leader_intent_air.h"
#include "components/tasking/common/leader_intent_core.h"
#include "components/tasking/naval/leader_intent_naval.h"

/**
 * LeaderIntent
 * Internal Leader-layer output before mapping into MissionCommand.
 */
struct LeaderIntent : LeaderIntentCore, LeaderIntentAir, LeaderIntentNaval {};
