#include "runtime/facade/internal/cuda_resident/cuda_resident_backend.h"

#include <stdexcept>
#include <string>

namespace runtime::cuda_resident {

runtime::backend::Configuration CudaResidentBackend::configuration() const noexcept {
    return {
        .world_count = store_.world_capacity(),
        .worker_threads = worker_threads_,
        .effective_worker_threads = 1,
    };
}

void CudaResidentBackend::configure(const runtime::backend::ConfigureRequest &request) {
    if (request.worker_threads.has_value()) {
        worker_threads_ = *request.worker_threads;
    }
    if (request.world_count.has_value() && !store_.configure(*request.world_count)) {
        throw std::runtime_error("CUDA resident backend configure failed: " +
                                 store_.diagnostics().last_error);
    }
}

runtime::backend::ContentResult
CudaResidentBackend::load_content(const runtime::backend::ContentRequest &) {
    reject_unimplemented_operation("load_content");
}

void CudaResidentBackend::reset(const runtime::backend::ResetRequest &request) {
    if (!store_.reset(request.seeds.get())) {
        throw std::runtime_error("CUDA resident backend reset failed: " +
                                 store_.diagnostics().last_error);
    }
}

runtime::backend::SetupResult CudaResidentBackend::setup(const runtime::backend::SetupRequest &) {
    reject_unimplemented_operation("setup");
}

runtime::backend::InputResult CudaResidentBackend::inject(const runtime::backend::InputBatch &) {
    reject_unimplemented_operation("inject");
}

runtime::backend::EvaluationResult
CudaResidentBackend::evaluate(const runtime::backend::EvaluationRequest &) const {
    reject_unimplemented_operation("evaluate");
}

runtime::backend::AdvanceResult
CudaResidentBackend::advance(const runtime::backend::AdvanceRequest &) {
    reject_unimplemented_operation("advance");
}

runtime::backend::ExportResult
CudaResidentBackend::export_state(const runtime::backend::ExportRequest &) const {
    reject_unimplemented_operation("export_state");
}

runtime::backend::Diagnostics CudaResidentBackend::diagnostics() const {
    return {
        .backend_id = "cuda_resident.lifecycle_shell",
        .world_count = store_.diagnostics().world_capacity,
    };
}

CudaWorldStoreDiagnostics CudaResidentBackend::store_diagnostics() const {
    return store_.diagnostics();
}

void CudaResidentBackend::reject_unimplemented_operation(const char *operation) {
    throw std::logic_error(std::string("CUDA resident backend ") + operation +
                           " is not implemented by the RB3 lifecycle shell");
}

} // namespace runtime::cuda_resident
