#include <echelon_forge/runtime_contracts/runtime_identity.h>

#include <array>

namespace rtc = echelon_forge::runtime_contracts::v1;

namespace {

rtc::RuntimeHostIdentity make_host() {
    return {
        .host_id = {.high = 1, .low = 2},
        .boot_id = {.high = 3, .low = 4},
    };
}

rtc::RuntimeIncarnationRef make_incarnation() {
    return {
        .host = make_host(),
        .incarnation_epoch = 1,
    };
}

rtc::RuntimeWorldRef make_world() {
    return {
        .incarnation = make_incarnation(),
        .world_slot = 0,
        .world_generation = 1,
    };
}

rtc::RuntimeEpisodeRef make_episode() {
    return {
        .world = make_world(),
        .episode_id = {.high = 5, .low = 6},
        .episode_generation = 1,
    };
}

rtc::RuntimeRequestRef make_request() {
    return {
        .episode = make_episode(),
        .request_sequence = 1,
    };
}

} // namespace

int main() {
    const rtc::RuntimeHostIdentity host = make_host();
    const rtc::RuntimeIncarnationRef incarnation = make_incarnation();
    const rtc::RuntimeWorldRef world = make_world();
    const rtc::RuntimeEntityRef entity{
        .world = world,
        .entity_id = 7,
        .entity_generation = 1,
    };
    const rtc::RuntimeEpisodeRef episode = make_episode();
    const rtc::RuntimeRequestRef request = make_request();
    const rtc::RuntimeResultRef result{.request = request};

    const std::array well_formed_values{
        host.well_formed(),   incarnation.well_formed(), world.well_formed(),
        entity.well_formed(), episode.well_formed(),     request.well_formed(),
        result.well_formed(),
    };
    for (const bool value : well_formed_values) {
        if (!value) {
            return 1;
        }
    }

    rtc::RuntimeIncarnationRef next_incarnation = incarnation;
    ++next_incarnation.incarnation_epoch;
    if (!rtc::same_runtime_host(incarnation.host, next_incarnation.host) ||
        rtc::same_runtime_incarnation(incarnation, next_incarnation)) {
        return 2;
    }

    rtc::RuntimeWorldRef next_world = world;
    ++next_world.world_generation;
    rtc::RuntimeEntityRef entity_in_next_world = entity;
    entity_in_next_world.world = next_world;
    if (world == next_world || entity == entity_in_next_world) {
        return 3;
    }

    rtc::RuntimeEpisodeRef next_episode = episode;
    ++next_episode.episode_generation;
    rtc::RuntimeRequestRef request_in_next_episode = request;
    request_in_next_episode.episode = next_episode;
    rtc::RuntimeResultRef result_in_next_episode{.request = request_in_next_episode};
    if (episode == next_episode || request == request_in_next_episode ||
        result == result_in_next_episode) {
        return 4;
    }

    rtc::RuntimeHostIdentity missing_host_id = host;
    missing_host_id.host_id = {};
    rtc::RuntimeHostIdentity missing_boot_id = host;
    missing_boot_id.boot_id = {};
    rtc::RuntimeIncarnationRef missing_epoch = incarnation;
    missing_epoch.incarnation_epoch = rtc::kInvalidRuntimeGeneration;
    rtc::RuntimeWorldRef missing_world_generation = world;
    missing_world_generation.world_generation = rtc::kInvalidRuntimeGeneration;
    rtc::RuntimeEntityRef missing_entity_id = entity;
    missing_entity_id.entity_id = 0;
    rtc::RuntimeEntityRef missing_entity_generation = entity;
    missing_entity_generation.entity_generation = rtc::kInvalidRuntimeGeneration;
    rtc::RuntimeEpisodeRef missing_episode_id = episode;
    missing_episode_id.episode_id = {};
    rtc::RuntimeEpisodeRef missing_episode_generation = episode;
    missing_episode_generation.episode_generation = rtc::kInvalidRuntimeGeneration;
    rtc::RuntimeRequestRef missing_request_sequence = request;
    missing_request_sequence.request_sequence = 0;
    rtc::RuntimeResultRef result_with_bad_request{.request = missing_request_sequence};

    const std::array malformed_values{
        missing_host_id.well_formed(),
        missing_boot_id.well_formed(),
        missing_epoch.well_formed(),
        missing_world_generation.well_formed(),
        missing_entity_id.well_formed(),
        missing_entity_generation.well_formed(),
        missing_episode_id.well_formed(),
        missing_episode_generation.well_formed(),
        missing_request_sequence.well_formed(),
        result_with_bad_request.well_formed(),
    };
    for (const bool value : malformed_values) {
        if (value) {
            return 5;
        }
    }

    if (rtc::runtime_identity_contract_generation() != rtc::kRuntimeIdentityContractGeneration) {
        return 6;
    }
    return 0;
}
