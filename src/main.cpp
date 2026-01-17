#include "core/engine/simulation_kernel.h"
#include <spdlog/spdlog.h>
#include "components/basic/common.h"

int main() {
    SimulationKernel kernel;
    kernel.reset(42);

    spdlog::info("C++ App: Spawning Unit");
    spdlog::info("C++ App: Spawning Unit");
    auto e = kernel.spawn_unit(Side::Blue, "Aircraft", 0, 0, 0, 10, 5, 0);

    spdlog::info("C++ App: Running Simulation");
    for (int i = 0; i < 60; ++i) {
        kernel.step();
        const auto* t = e.get<Transform>();
        if (i % 10 == 0) {
            spdlog::info("Tick {}: Unit at ({:.2f}, {:.2f}, {:.2f})", i, t->x, t->y, t->z);
        }
    }
    
    return 0;
}
