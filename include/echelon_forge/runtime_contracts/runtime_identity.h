#pragma once

#include <cstddef>
#include <cstdint>
#include <type_traits>

namespace echelon_forge::runtime_contracts::v1 {

// This generation identifies the source-level value-contract family. It is
// not a cross-release binary ABI or platform-support claim.
inline constexpr std::uint32_t kRuntimeIdentityContractGeneration = 1;
inline constexpr std::uint64_t kInvalidRuntimeGeneration = 0;

// These engine-independent DTOs are safe to copy as values within one
// process/build. Their object representation is never a wire/storage format:
// raw-memory persistence, hashing, signing, or IPC encoding is forbidden. P3-B
// must provide the only canonical JSON projection and detached digest for artifacts.
struct RuntimeIdentity128 {
#define EF_RUNTIME_IDENTITY_128_FIELD(type, name, default_value) type name = default_value;
#include <echelon_forge/runtime_contracts/detail/runtime_identity_128_fields.inc>

    [[nodiscard]] constexpr bool well_formed() const noexcept { return high != 0 || low != 0; }
    bool operator==(const RuntimeIdentity128 &) const = default;
};

// Stable for the lifetime of one native host process. This does not identify a
// published runtime incarnation.
struct RuntimeHostIdentity {
#define EF_RUNTIME_HOST_IDENTITY_FIELD(type, name, default_value) type name = default_value;
#include <echelon_forge/runtime_contracts/detail/runtime_host_identity_fields.inc>

    [[nodiscard]] constexpr bool well_formed() const noexcept {
        return host_id.well_formed() && boot_id.well_formed();
    }
    bool operator==(const RuntimeHostIdentity &) const = default;
};

// Identifies one published slot under a stable host identity.
struct RuntimeIncarnationRef {
#define EF_RUNTIME_INCARNATION_REF_FIELD(type, name, default_value) type name = default_value;
#include <echelon_forge/runtime_contracts/detail/runtime_incarnation_ref_fields.inc>

    [[nodiscard]] constexpr bool well_formed() const noexcept {
        return host.well_formed() && incarnation_epoch != kInvalidRuntimeGeneration;
    }
    bool operator==(const RuntimeIncarnationRef &) const = default;
};

struct RuntimeWorldRef {
#define EF_RUNTIME_WORLD_REF_FIELD(type, name, default_value) type name = default_value;
#include <echelon_forge/runtime_contracts/detail/runtime_world_ref_fields.inc>

    [[nodiscard]] constexpr bool well_formed() const noexcept {
        return incarnation.well_formed() && world_generation != kInvalidRuntimeGeneration;
    }
    bool operator==(const RuntimeWorldRef &) const = default;
};

struct RuntimeEntityRef {
#define EF_RUNTIME_ENTITY_REF_FIELD(type, name, default_value) type name = default_value;
#include <echelon_forge/runtime_contracts/detail/runtime_entity_ref_fields.inc>

    [[nodiscard]] constexpr bool well_formed() const noexcept {
        return world.well_formed() && entity_id != 0 &&
               entity_generation != kInvalidRuntimeGeneration;
    }
    bool operator==(const RuntimeEntityRef &) const = default;
};

struct RuntimeEpisodeRef {
#define EF_RUNTIME_EPISODE_REF_FIELD(type, name, default_value) type name = default_value;
#include <echelon_forge/runtime_contracts/detail/runtime_episode_ref_fields.inc>

    [[nodiscard]] constexpr bool well_formed() const noexcept {
        return world.well_formed() && episode_id.well_formed() &&
               episode_generation != kInvalidRuntimeGeneration;
    }
    bool operator==(const RuntimeEpisodeRef &) const = default;
};

// Execution requests are episode-scoped. Host lifecycle commands use private
// host-control types and cannot masquerade as simulation requests.
struct RuntimeRequestRef {
#define EF_RUNTIME_REQUEST_REF_FIELD(type, name, default_value) type name = default_value;
#include <echelon_forge/runtime_contracts/detail/runtime_request_ref_fields.inc>

    [[nodiscard]] constexpr bool well_formed() const noexcept {
        return episode.well_formed() && request_sequence != 0;
    }
    bool operator==(const RuntimeRequestRef &) const = default;
};

// There is exactly one authoritative terminal-result identity per admitted
// request. Streaming fragments, if introduced later, require a separately
// reviewed protocol and cannot create another result identity namespace here.
struct RuntimeResultRef {
#define EF_RUNTIME_RESULT_REF_FIELD(type, name, default_value) type name = default_value;
#include <echelon_forge/runtime_contracts/detail/runtime_result_ref_fields.inc>

    [[nodiscard]] constexpr bool well_formed() const noexcept { return request.well_formed(); }
    bool operator==(const RuntimeResultRef &) const = default;
};

[[nodiscard]] constexpr bool same_runtime_host(const RuntimeHostIdentity &lhs,
                                               const RuntimeHostIdentity &rhs) noexcept {
    return lhs.well_formed() && rhs.well_formed() && lhs == rhs;
}

[[nodiscard]] constexpr bool same_runtime_incarnation(const RuntimeIncarnationRef &lhs,
                                                      const RuntimeIncarnationRef &rhs) noexcept {
    return lhs.well_formed() && rhs.well_formed() && lhs == rhs;
}

// well_formed() proves only local non-zero structural shape. P4 must validate
// freshness, tombstones, enclosing generations and the active lease through
// the singular host authority before any reference can access runtime truth.
[[nodiscard]] std::uint32_t runtime_identity_contract_generation() noexcept;

#define EF_ASSERT_PUBLIC_VALUE_CONTRACT(type_name)                                                 \
    static_assert(std::is_standard_layout_v<type_name>);                                           \
    static_assert(std::is_trivially_copyable_v<type_name>);                                        \
    static_assert(alignof(type_name) == alignof(std::uint64_t))

EF_ASSERT_PUBLIC_VALUE_CONTRACT(RuntimeIdentity128);
EF_ASSERT_PUBLIC_VALUE_CONTRACT(RuntimeHostIdentity);
EF_ASSERT_PUBLIC_VALUE_CONTRACT(RuntimeIncarnationRef);
EF_ASSERT_PUBLIC_VALUE_CONTRACT(RuntimeWorldRef);
EF_ASSERT_PUBLIC_VALUE_CONTRACT(RuntimeEntityRef);
EF_ASSERT_PUBLIC_VALUE_CONTRACT(RuntimeEpisodeRef);
EF_ASSERT_PUBLIC_VALUE_CONTRACT(RuntimeRequestRef);
EF_ASSERT_PUBLIC_VALUE_CONTRACT(RuntimeResultRef);

#undef EF_ASSERT_PUBLIC_VALUE_CONTRACT

// These same-build layout sentinels detect accidental drift in the generated
// v1 field lists. They do not make the native object representation portable
// or canonical and do not qualify any Windows/Linux release row.
static_assert(sizeof(RuntimeIdentity128) == 16);
static_assert(sizeof(RuntimeHostIdentity) == 32);
static_assert(sizeof(RuntimeIncarnationRef) == 40);
static_assert(sizeof(RuntimeWorldRef) == 56);
static_assert(sizeof(RuntimeEntityRef) == 72);
static_assert(sizeof(RuntimeEpisodeRef) == 80);
static_assert(sizeof(RuntimeRequestRef) == 88);
static_assert(sizeof(RuntimeResultRef) == 88);

static_assert(offsetof(RuntimeIdentity128, high) == 0);
static_assert(offsetof(RuntimeIdentity128, low) == 8);
static_assert(offsetof(RuntimeHostIdentity, host_id) == 0);
static_assert(offsetof(RuntimeHostIdentity, boot_id) == 16);
static_assert(offsetof(RuntimeIncarnationRef, host) == 0);
static_assert(offsetof(RuntimeIncarnationRef, incarnation_epoch) == 32);
static_assert(offsetof(RuntimeWorldRef, incarnation) == 0);
static_assert(offsetof(RuntimeWorldRef, world_slot) == 40);
static_assert(offsetof(RuntimeWorldRef, world_generation) == 48);
static_assert(offsetof(RuntimeEntityRef, world) == 0);
static_assert(offsetof(RuntimeEntityRef, entity_id) == 56);
static_assert(offsetof(RuntimeEntityRef, entity_generation) == 64);
static_assert(offsetof(RuntimeEpisodeRef, world) == 0);
static_assert(offsetof(RuntimeEpisodeRef, episode_id) == 56);
static_assert(offsetof(RuntimeEpisodeRef, episode_generation) == 72);
static_assert(offsetof(RuntimeRequestRef, episode) == 0);
static_assert(offsetof(RuntimeRequestRef, request_sequence) == 80);
static_assert(offsetof(RuntimeResultRef, request) == 0);

} // namespace echelon_forge::runtime_contracts::v1
