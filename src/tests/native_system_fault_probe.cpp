#include "core/engine/world_batch_runtime.h"

#include <atomic>
#include <chrono>
#include <cstdlib>
#include <iostream>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

#ifdef _WIN32
#include <windows.h>
#endif

namespace {
struct FaultProbeState {
    unsigned visits = 0;
};
void require(bool condition, const char *message) {
    if (!condition) {
        throw std::runtime_error(message);
    }
}

template <typename Fn> void require_fenced(Fn &&operation) {
    try {
        operation();
    } catch (const std::exception &error) {
        require(std::string(error.what()).find("failed-closed") != std::string::npos,
                "unexpected fence diagnostic");
        return;
    }
    throw std::runtime_error("failed generation escaped its fence");
}
} // namespace

int main(int argc, char **argv) {
#ifdef _WIN32
    SetErrorMode(SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX);
    _set_abort_behavior(0, _WRITE_ABORT_MSG | _CALL_REPORTFAULT);
#endif
    if (argc != 4) {
        return 2;
    }
    const std::string mode = argv[1];
    const auto world_count = std::stoul(argv[2]);
    const auto threads = std::stoul(argv[3]);
    if ((mode != "throw" && mode != "fatal" && mode != "hang" && mode != "healthy") || world_count < 2 ||
        world_count > 4 || threads < 1 || threads > 4) {
        return 2;
    }
    try {
        std::vector<std::atomic<unsigned>> visits(world_count);
        std::atomic<bool> inject{true};
        {
            WorldBatchRuntime batch(world_count);
            batch.set_worker_threads(threads);
            if (mode == "healthy") {
                batch.reset_batch();
                batch.step_batch();
                require(batch.batch_healthy(), "replacement process batch is unhealthy");
                std::cout << "REPLACEMENT_PROCESS_HEALTHY" << std::endl;
                return 0;
            }
            const auto generation = batch.batch_generation();
            for (std::size_t index = 0; index < world_count; ++index) {
                auto lease = batch.world_raw_quarantine(index).acquire_world_lease();
                lease.world().entity("QualificationFaultState").set<FaultProbeState>({});
                lease.world().system<FaultProbeState>("QualificationNativeFault")
                    .kind(flecs::OnUpdate)
                    .each([&, index](FaultProbeState &state) {
                        ++state.visits; // Native ECS mutation before the injected fault.
                        ++visits[index];
                        if (index != 1 || !inject.load()) {
                            return;
                        }
                        std::cout << "FAULT_CALLBACK_ENTERED" << std::endl;
                        if (mode == "fatal") {
                            std::abort();
                        }
                        if (mode == "hang") {
                            for (;;) {
                                std::this_thread::sleep_for(std::chrono::milliseconds(100));
                            }
                        }
                        throw std::runtime_error("injected running native system failure");
                    });
            }
            try {
                batch.step_batch();
                throw std::runtime_error("native fault was not propagated");
            } catch (const std::runtime_error &error) {
                require(std::string(error.what()) == "injected running native system failure",
                        "unexpected step failure");
            }
            require(visits[1] == 1, "faulting callback did not mutate its state");
            for (std::size_t index = 0; index < world_count; ++index) {
                const unsigned expected_visits = threads == 1 && index > 1 ? 0 : 1;
                require(visits[index] == expected_visits, "unexpected worker completion pattern");
                auto lease = batch.world_raw_quarantine(index).acquire_world_lease();
                const double clock = ecs_get_world_info(lease.world().c_ptr())->world_time_total;
                require((clock > 0) == (expected_visits == 1), "unexpected diagnostic clock");
                std::cout << "FAULT_WORLD " << index << " " << clock << " " << visits[index]
                          << std::endl;
            }
            require(!batch.batch_healthy(), "native callback failure was not fenced");
            require(batch.batch_requires_host_recreate(), "native owner allowed unsafe reset recovery");
            require(batch.batch_generation() == generation, "failed generation changed");
            require_fenced([&] { batch.step_batch(); });
            require_fenced([&] { batch.get_agent_observations_batch({}); });
            require_fenced([&] { (void)batch.composition_diagnostics(); });
            std::cout << "FAULT_FENCED" << std::endl;
            inject = false;
            {
                auto lease = batch.world_raw_quarantine(1).acquire_world_lease();
                require(lease.world().is_readonly(), "fixture did not interrupt readonly pipeline");
                require(lease.world().lookup("QualificationFaultState").get<FaultProbeState>()->visits == 1,
                        "native mutation before failure was not retained");
            }
            for (unsigned attempt = 0; attempt < 2; ++attempt) {
                try {
                    batch.reset_batch();
                    throw std::runtime_error("reset certified an unfinished pipeline");
                } catch (const std::logic_error &error) {
                    require(std::string(error.what()).find("recreate the host process") != std::string::npos,
                            "unexpected reset rejection");
                }
                require(!batch.batch_healthy(), "failed reset reopened the batch");
                require(batch.batch_requires_host_recreate(), "failed reset cleared terminal recovery");
                require(batch.batch_generation() == generation, "failed reset changed generation");
                require_fenced([&] { batch.step_batch(); });
                require_fenced([&] { batch.get_agent_observations_batch({}); });
            }
            try {
                batch.world_raw_quarantine(1).step();
                throw std::runtime_error("raw quarantine step resumed an unfinished pipeline");
            } catch (const std::logic_error &error) {
                require(std::string(error.what()).find("recreate the host process") != std::string::npos,
                        "unexpected raw step rejection");
            }
            std::cout << "PROCESS_RECREATE_REQUIRED" << std::endl;
            // Flecs iterator/defer scopes are not exception safe. Retire this
            // disposable host without claiming in-process teardown is safe.
            std::_Exit(0);
        }
        return 0;
    } catch (const std::exception &error) {
        std::cerr << error.what() << std::endl;
        return 1;
    }
}
