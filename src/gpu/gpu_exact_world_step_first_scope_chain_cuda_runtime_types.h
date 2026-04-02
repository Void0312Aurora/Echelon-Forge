#pragma once

#include <cstdint>

#include "gpu/gpu_exact_world_step_aircraft_chain_cuda_runtime_types.h"
#include "gpu/gpu_exact_world_step_missile_guidance_cuda_runtime_types.h"

namespace gpu::first_scope_chain_cuda {

using AircraftState = aircraft_chain_cuda::ExactWorldStepAircraftChainCudaState;
using Missile = missile_guidance_cuda::Missile;
using ContactListSummary = missile_guidance_cuda::ContactListSummary;

struct ExactWorldStepFirstScopeChainCudaState {
    AircraftState aircraft{};

    std::uint64_t entity_id = 0;
    double world_time_s = 0.0;
    Missile missile{};
    ContactListSummary contact_list_summary{};

    bool has_missile = false;
    bool has_contact_list_summary = false;
};

}  // namespace gpu::first_scope_chain_cuda
