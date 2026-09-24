#include "runtime/facade/runtime_facade.h"
#include <spdlog/spdlog.h>
#include <string>

int main() {
    RuntimeFacade facade(1);
    if (!facade.load_database("examples/config/database")) {
        spdlog::error("C++ App: failed to load runtime database");
        return 1;
    }

    BatchWorldSetupRequest setup{};
    setup.seeds = {42};
    setup.time_steps = {0.05};
    WorldTerrainAssignment terrain{};
    terrain.world_index = 0;
    terrain.terrain_type = "flat";
    setup.terrain_assignments = {terrain};
    WorldSpawnRequest spawn{};
    spawn.world_index = 0;
    spawn.side = Side::Blue;
    spawn.type_name = "Aircraft";
    spawn.entity_name = "StandaloneAircraft";
    spawn.x = 0.0;
    spawn.y = 0.0;
    spawn.z = 0.0;
    spawn.vx = 10.0;
    spawn.vy = 5.0;
    setup.spawn_requests = {spawn};

    spdlog::info("C++ App: Spawning Unit");
    const auto setup_result = facade.apply_world_setup(setup);
    if (setup_result.entity_ids.empty()) {
        spdlog::error("C++ App: facade setup did not materialize an entity");
        return 1;
    }
    const WorldEntityRef entity_ref{0, setup_result.entity_ids.front()};

    spdlog::info("C++ App: Running Simulation");
    for (int i = 0; i < 60; ++i) {
        facade.step_batch();
        if (i % 10 == 0) {
            const auto observations = facade.get_agent_observations_batch({entity_ref});
            if (observations.empty()) {
                spdlog::error("C++ App: facade returned no observation");
                return 1;
            }
            const auto &observation = observations.front();
            spdlog::info("Tick {}: Unit at ({:.2f}, {:.2f}, {:.2f})", i, observation.x,
                         observation.y, observation.z);
        }
    }
    
    return 0;
}
