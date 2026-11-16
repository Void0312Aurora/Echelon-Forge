#include "core/engine/world_batch_runtime.h"
#include "core/engine/testing/simulation_kernel_composition_test_access.h"
#include "components/basic/common.h"
#include "components/basic/stable_identity.h"
#include "runtime/facade/internal/testing/runtime_facade_test_access.h"

#include <atomic>
#include <chrono>
#include <cstdlib>
#include <iostream>
#include <stdexcept>
#include <string>
#include <thread>
#include <tuple>
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
    if ((mode != "throw" && mode != "fatal" && mode != "hang" && mode != "healthy") ||
        world_count < 2 || world_count > 4 || threads < 1 || threads > 4) {
        return 2;
    }
    try {
        std::vector<std::atomic<unsigned>> visits(world_count);
        std::atomic<bool> inject{true};
        {
            RuntimeFacade facade(world_count);
            WorldBatchRuntime &batch =
                runtime::facade::testing::RuntimeFacadeTestAccess::world_batch_runtime(facade);
            batch.set_worker_threads(threads);
            if (mode == "healthy") {
                facade.reset_batch();
                facade.step_batch();
                require(facade.batch_failure_status().healthy,
                        "replacement process facade batch is unhealthy");
                std::cout << "REPLACEMENT_PROCESS_HEALTHY" << std::endl;
                return 0;
            }
            facade.reset_batch(BatchResetRequest{.seeds = {41}});
            const auto generation = batch.batch_generation();
            for (std::size_t index = 0; index < world_count; ++index) {
                auto lease = batch.world_raw_quarantine(index).acquire_world_lease();
                lease.world().entity("QualificationResetMarker").add<SimObject>();
                lease.world().entity("QualificationFaultState").set<FaultProbeState>({});
                lease.world()
                    .system<FaultProbeState>("QualificationNativeFault")
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
                facade.step_batch();
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
            const auto failure_status = facade.batch_failure_status();
            require(!failure_status.healthy, "native callback failure was not fenced");
            require(failure_status.requires_host_recreate,
                    "native owner allowed unsafe reset recovery");
            require(failure_status.generation == generation, "failed generation changed");
            require_fenced([&] { facade.step_batch(); });
            require_fenced([&] { (void)facade.export_composition_evidence(); });
            require_fenced([&] { (void)facade.get_agent_observations_batch({}); });
            std::cout << "FAULT_FENCED" << std::endl;
            inject = false;
            {
                auto lease = batch.world_raw_quarantine(1).acquire_world_lease();
                require(lease.world().is_readonly(), "fixture did not interrupt readonly pipeline");
                require(lease.world()
                                .lookup("QualificationFaultState")
                                .get<FaultProbeState>()
                                ->visits == 1,
                        "native mutation before failure was not retained");
            }
            using RetainedFacts = std::tuple<std::uint64_t, std::uint64_t, double, double,
                                             std::int64_t, bool, std::string>;
            auto retained_facts = [&] {
                std::vector<RetainedFacts> result;
                for (std::size_t index = 0; index < world_count; ++index) {
                    auto &kernel = batch.world_raw_quarantine(index);
                    const auto rng =
                        SimulationKernelCompositionTestAccess::rng_state_for_testing(kernel);
                    auto lease = kernel.acquire_world_lease();
                    const auto *identity = lease.world().get<StableIdentityState>();
                    const auto *clock = ecs_get_world_info(lease.world().c_ptr());
                    result.emplace_back(
                        identity->episode_seed, identity->next_serial, clock->world_time_total,
                        clock->world_time_total_raw, clock->frame_count_total,
                        lease.world().lookup("QualificationResetMarker").is_alive(), rng);
                }
                return result;
            };
            const auto before_reset = retained_facts();
            auto require_retained = [](bool condition, const char *message) {
                if (!condition) {
                    std::cerr << message << std::endl;
                    // Failed assertions also retire the interrupted pipeline;
                    // normal stack unwinding is not a teardown guarantee.
                    std::_Exit(1);
                }
            };
            for (unsigned attempt = 0; attempt < 2; ++attempt) {
                try {
                    facade.reset_batch(BatchResetRequest{.seeds = {101}});
                    throw std::runtime_error("reset certified an unfinished pipeline");
                } catch (const std::logic_error &error) {
                    require(std::string(error.what()).find("recreate the host process") !=
                                std::string::npos,
                            "unexpected reset rejection");
                }
                const auto failed_reset_status = facade.batch_failure_status();
                require_retained(retained_facts() == before_reset,
                                 "fatal reset changed native seed/entity/clock/RNG facts");
                require_retained(failed_reset_status.failure_reason == failure_status.failure_reason,
                                 "fatal reset replaced the original failure reason");
                require(!failed_reset_status.healthy, "failed reset reopened the batch");
                require(failed_reset_status.requires_host_recreate,
                        "failed reset cleared terminal recovery");
                require(failed_reset_status.generation == generation,
                        "failed reset changed generation");
                require_fenced([&] { facade.step_batch(); });
                require_fenced([&] { (void)facade.export_composition_evidence(); });
            }
            try {
                batch.world_raw_quarantine(1).step();
                throw std::runtime_error("raw quarantine step resumed an unfinished pipeline");
            } catch (const std::logic_error &error) {
                require(std::string(error.what()).find("recreate the host process") !=
                            std::string::npos,
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
