#include <cstdlib>
#include <iostream>

#include "runtime/contracts/cuda_resident_resource_evidence_contract.h"

namespace {

namespace evidence = runtime::cuda_resident::resource_evidence;

static_assert(evidence::kCaptureProbeV1Retired);

} // namespace

int main() {
    std::cerr << "CUDA resident resource probe retired: "
              << evidence::kCaptureProbeV1RetirementReason << '\n';
    return EXIT_FAILURE;
}
