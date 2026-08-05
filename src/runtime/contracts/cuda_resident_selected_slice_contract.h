#pragma once

#include <cstdint>
#include <string>
#include <vector>

namespace runtime::cuda_resident {

// Typed future surfaces frozen by RB2. RB3-RB4 must implement these semantics
// rather than inventing anonymous device-only clock, version, event-order, or
// export-envelope fields after parity work has started.
struct DeviceClockContract {
    std::uint64_t tick = 0;
    double simulation_time_s = 0.0;
};

struct ShardVersionContract {
    std::string shard_id;
    std::uint64_t version = 0;
};

struct SnapshotLineageContract {
    std::uint64_t source_snapshot_version = 0;
    std::string source_backend_id;
    std::string source_request_id;
};

struct SnapshotIdentityContract {
    std::uint64_t world_id = 0;
    std::uint64_t global_version = 0;
    std::string barrier_id;
    std::uint64_t barrier_sequence = 0;
    std::vector<ShardVersionContract> shard_versions;
    SnapshotLineageContract lineage;
};

struct EventOrderKeyContract {
    double timestamp = 0.0;
    int priority = 0;
    std::uint64_t event_id = 0;
    std::string event_family_membership;
};

struct ExportEnvelopeContract {
    std::string schema_version;
    std::vector<std::string> field_set;
    std::string visibility_label;
    std::string provenance;
    std::uint64_t source_snapshot_version = 0;
};

} // namespace runtime::cuda_resident
