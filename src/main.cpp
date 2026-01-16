#include <flecs.h>
#include <spdlog/spdlog.h>
#include <iostream>

// Component
struct Position {
    double x, y;
};

struct Velocity {
    double x, y;
};

void run_simulation() {
    flecs::world ecs;

    ecs.system<Position, const Velocity>("Move")
        .each([](Position& p, const Velocity& v) {
            p.x += v.x;
            p.y += v.y;
            spdlog::info("Moved to ({}, {})", p.x, p.y);
        });

    auto e = ecs.entity("MyEntity")
        .set<Position>({0, 0})
        .set<Velocity>({1, 1});

    spdlog::info("Simulation started. Entity created: {}", e.name().c_str());

    // Run for a few ticks
    for (int i = 0; i < 5; ++i) {
        ecs.progress();
    }
}

int main(int argc, char* argv[]) {
    // Basic check to run only if it's the standalone app
    // In a real app we might handle args differently
    run_simulation();
    return 0;
}
