#include <echelon_forge/runtime_contracts/runtime_identity.h>

namespace echelon_forge::runtime_contracts::v1 {

std::uint32_t runtime_identity_contract_generation() noexcept {
    return kRuntimeIdentityContractGeneration;
}

} // namespace echelon_forge::runtime_contracts::v1
