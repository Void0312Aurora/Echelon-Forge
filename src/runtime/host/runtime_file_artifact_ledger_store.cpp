#include "runtime_file_artifact_ledger_store.h"

#include "runtime/contracts/authority/runtime_authority_contract.h"

#include <algorithm>
#include <cerrno>
#include <fstream>
#include <limits>
#include <set>
#include <system_error>
#include <vector>

#include <nlohmann/json.hpp>

#ifdef _WIN32
#include <fcntl.h>
#include <io.h>
#include <share.h>
#include <windows.h>
#include <Aclapi.h>
#include <sddl.h>
#ifdef max
#undef max
#endif
#else
#include <fcntl.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <unistd.h>
#endif

namespace runtime::host {
namespace {

using Json = nlohmann::json;

std::string token_name(std::string_view value) {
    return runtime::authority_contracts::sha256_hex(value);
}

bool is_audit_event_filename(std::string_view name) {
    constexpr std::size_t prefix_size = 6U;  // event-
    constexpr std::size_t sequence_size = 20U;
    constexpr std::size_t suffix_size = 5U;  // .json
    if (name.size() != prefix_size + sequence_size + suffix_size ||
        !name.starts_with("event-") || !name.ends_with(".json"))
        return false;
    for (std::size_t index = prefix_size; index < prefix_size + sequence_size; ++index) {
        if (name[index] < '0' || name[index] > '9') return false;
    }
    return true;
}

bool is_audit_event_temporary_filename(std::string_view name) {
    constexpr std::size_t marker_size = 5U;  // .tmp-
    const auto marker = name.find(".json.tmp-");
    if (marker == std::string_view::npos || marker + 10U != name.size() - 16U)
        return false;
    if (!is_audit_event_filename(name.substr(0, marker + 5U))) return false;
    for (std::size_t index = marker + marker_size + 5U; index < name.size(); ++index) {
        const char value = name[index];
        if (!((value >= '0' && value <= '9') || (value >= 'a' && value <= 'f'))) return false;
    }
    return true;
}

std::string_view role_name(RuntimeArtifactLedgerRole role) {
    switch (role) {
    case RuntimeArtifactLedgerRole::RuntimeHost: return "runtime_host";
    case RuntimeArtifactLedgerRole::CrashReconciler: return "crash_reconciler";
    case RuntimeArtifactLedgerRole::PlanCompiler: return "plan_compiler";
    case RuntimeArtifactLedgerRole::ReleaseArtifactPipeline: return "release_artifact_pipeline";
    case RuntimeArtifactLedgerRole::BackupOperator: return "backup_operator";
    case RuntimeArtifactLedgerRole::ReadOnlyAuditor: return "read_only_auditor";
    }
    return "unknown";
}

bool role_can_write_artifact_media(RuntimeArtifactLedgerRole role,
                                   std::string_view media_type) {
    switch (role) {
    case RuntimeArtifactLedgerRole::RuntimeHost:
        return media_type == "application/octet-stream" ||
               media_type == "application/vnd.echelon-forge.runtime-state.v1+octets";
    case RuntimeArtifactLedgerRole::PlanCompiler:
        return media_type == "application/vnd.echelon-forge.resolved-execution-plan.v1+json" ||
               media_type == "application/vnd.echelon-forge.runtime-composition-request.v1+json";
    case RuntimeArtifactLedgerRole::ReleaseArtifactPipeline:
        return media_type == "application/vnd.echelon-forge.release-manifest.v1+json" ||
               media_type == "application/vnd.echelon-forge.release-package.v1+octets" ||
               media_type ==
                   "application/vnd.echelon-forge.stored-artifact-inventory.v1+json";
    case RuntimeArtifactLedgerRole::CrashReconciler:
    case RuntimeArtifactLedgerRole::BackupOperator:
    case RuntimeArtifactLedgerRole::ReadOnlyAuditor:
        return false;
    }
    return false;
}

bool read_text(const std::filesystem::path &path, std::string &output) {
    std::ifstream input(path, std::ios::binary);
    if (!input) return false;
    output.assign(std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>());
    return input.good() || input.eof();
}

#ifndef _WIN32
bool sync_directory(const std::filesystem::path &directory);
#endif

bool copy_tree_without_lock(const std::filesystem::path &source,
                            const std::filesystem::path &target,
                            std::string &detail) {
    std::error_code error;
    std::filesystem::create_directories(target, error);
    if (error) {
        detail = "native ArtifactLedger backup target creation failed";
        return false;
    }
    for (const auto &entry : std::filesystem::recursive_directory_iterator(source, error)) {
        if (error) {
            detail = "native ArtifactLedger backup source enumeration failed";
            return false;
        }
        const auto name = entry.path().filename().string();
        if (name == ".artifact-ledger.lock" || name.find(".tmp-") != std::string::npos)
            continue;
        const auto relative = std::filesystem::relative(entry.path(), source, error);
        if (error) {
            detail = "native ArtifactLedger backup relative path failed";
            return false;
        }
        const auto destination = target / relative;
        if (entry.is_directory(error)) {
            std::filesystem::create_directories(destination, error);
        } else if (entry.is_regular_file(error)) {
            std::filesystem::create_directories(destination.parent_path(), error);
            std::filesystem::copy_file(entry.path(), destination,
                                       std::filesystem::copy_options::overwrite_existing, error);
        }
        if (error) {
            detail = "native ArtifactLedger backup copy failed";
            return false;
        }
    }
#ifndef _WIN32
    if (!sync_directory(target)) {
        detail = "native ArtifactLedger backup directory sync failed";
        return false;
    }
#endif
    return true;
}

std::string hex_encode(std::string_view value) {
    static constexpr char digits[] = "0123456789abcdef";
    std::string output;
    output.reserve(value.size() * 2U);
    for (const unsigned char byte : value) {
        output.push_back(digits[byte >> 4U]);
        output.push_back(digits[byte & 0x0fU]);
    }
    return output;
}

bool hex_decode(std::string_view value, std::string &output) {
    if (value.size() % 2U != 0U) return false;
    output.clear();
    output.reserve(value.size() / 2U);
    const auto digit = [](char c) -> int {
        if (c >= '0' && c <= '9') return c - '0';
        if (c >= 'a' && c <= 'f') return c - 'a' + 10;
        return -1;
    };
    for (std::size_t i = 0; i < value.size(); i += 2U) {
        const int high = digit(value[i]);
        const int low = digit(value[i + 1U]);
        if (high < 0 || low < 0) return false;
        output.push_back(static_cast<char>((high << 4) | low));
    }
    return true;
}

bool write_all(int fd, const char *data, std::size_t size) {
    while (size != 0U) {
#ifdef _WIN32
        const unsigned chunk = static_cast<unsigned>(std::min<std::size_t>(size, 1U << 20U));
        const int written = _write(fd, data, chunk);
#else
        const auto written = ::write(fd, data, size);
#endif
        if (written <= 0) return false;
        data += written;
        size -= static_cast<std::size_t>(written);
    }
    return true;
}

#ifndef _WIN32
bool sync_directory(const std::filesystem::path &directory) {
    const int fd = ::open(directory.c_str(), O_RDONLY | O_DIRECTORY);
    if (fd < 0) return false;
    const bool synced = ::fsync(fd) == 0;
    ::close(fd);
    return synced;
}
#endif

bool parse_sequence(std::string_view name, std::uint64_t &sequence) {
    constexpr std::string_view prefix = "frame-";
    constexpr std::string_view suffix = ".json";
    if (!name.starts_with(prefix) || !name.ends_with(suffix)) return false;
    const auto digits = name.substr(prefix.size(), name.size() - prefix.size() - suffix.size());
    if (digits.empty() ||
        !std::all_of(digits.begin(), digits.end(), [](char c) { return c >= '0' && c <= '9'; }))
        return false;
    try {
        sequence = std::stoull(std::string(digits));
    } catch (...) {
        return false;
    }
    return true;
}

bool receipt_matches_header(const Json &payload, const Json &header, std::string &detail) {
    if (!header.contains("receipt_bindings") ||
        !header.contains("admission_binding_sha256")) {
        detail = "native ArtifactLedger header lacks admission bindings";
        return false;
    }
    const auto &bindings = header.at("receipt_bindings");
    if (payload.at("admission_binding_sha256") != header.at("admission_binding_sha256") ||
        payload.at("receipt_id") != bindings.at("receipt_id") ||
        payload.at("attempt_id") != bindings.at("attempt_id") ||
        payload.at("plan_binding") != bindings.at("plan_binding") ||
        payload.at("release_binding") != bindings.at("release_binding") ||
        payload.at("executable") != bindings.at("executable") ||
        payload.at("package") != bindings.at("package") ||
        payload.at("build") != bindings.at("build") ||
        payload.at("platform") != bindings.at("platform") ||
        payload.at("inputs") != bindings.at("inputs") ||
        payload.at("backend") != bindings.at("backend") ||
        payload.at("reader_generation_min") != bindings.at("reader_generation_min") ||
        payload.at("reader_generation_max") != bindings.at("reader_generation_max")) {
        detail = "native ArtifactLedger receipt differs from durable admission bindings";
        return false;
    }
    return true;
}

Json frame_identity(const Json &frame) {
    return Json{{"fence_generation", frame.at("fence_generation")},
                {"journal_id", frame.at("journal_id")},
                {"payload_sha256", frame.at("payload_sha256")},
                {"payload_size", frame.at("payload_size")},
                {"prior_record_sha256", frame.at("prior_record_sha256")},
                {"sequence", frame.at("sequence")},
                {"stream_id", frame.at("stream_id")},
                {"writer_id", frame.at("writer_id")}};
}

std::uint32_t crc32(std::string_view bytes) {
    std::uint32_t checksum = 0xffffffffU;
    for (const unsigned char byte : bytes) {
        checksum ^= byte;
        for (unsigned bit = 0; bit < 8U; ++bit) {
            const auto mask = static_cast<std::uint32_t>(
                -static_cast<std::int32_t>(checksum & 1U));
            checksum = (checksum >> 1U) ^ (0xedb88320U & mask);
        }
    }
    return checksum ^ 0xffffffffU;
}

std::string crash_marker_observation_digest(std::string_view stream_id,
                                            std::uint64_t prior_generation,
                                            std::string_view prior_writer_id,
                                            std::uint64_t recovery_generation,
                                            std::string_view recovery_writer_id) {
    return runtime::authority_contracts::sha256_hex(
        "native-root-lock-released:" + std::string(stream_id) + ":" +
        std::to_string(prior_generation) + ":" + std::string(prior_writer_id) + ":" +
        std::to_string(recovery_generation) + ":" + std::string(recovery_writer_id));
}

bool validate_crash_marker(const Json &marker, std::string_view stream_id,
                           std::uint64_t recovery_generation,
                           std::string_view recovery_writer_id, std::uint64_t prior_generation,
                           std::string_view prior_writer_id, std::string &detail) {
    if (!marker.is_object()) {
        detail = "native crash reconciliation marker is not an object";
        return false;
    }
    static const std::set<std::string> fields = {
        "event", "observed_exit_sha256", "prior_writer_generation", "prior_writer_id",
        "recovery_writer_generation", "recovery_writer_id"};
    std::set<std::string> actual;
    for (auto it = marker.begin(); it != marker.end(); ++it) actual.insert(it.key());
    const auto expected_observation = crash_marker_observation_digest(
        stream_id, prior_generation, prior_writer_id, recovery_generation, recovery_writer_id);
    if (actual != fields || marker.at("event").get<std::string>() != "crash_reconciled" ||
        marker.at("prior_writer_generation").get<std::uint64_t>() != prior_generation ||
        marker.at("prior_writer_id").get<std::string>() != prior_writer_id ||
        marker.at("recovery_writer_generation").get<std::uint64_t>() != recovery_generation ||
        marker.at("recovery_writer_id").get<std::string>() != recovery_writer_id ||
        marker.at("observed_exit_sha256").get<std::string>() != expected_observation) {
        detail = "native crash reconciliation marker does not bind the released root lock and fence";
        if (actual != fields) {
            detail += ": fields actual=";
            for (const auto &field : actual) detail += field + ",";
        }
        else if (marker.at("event").get<std::string>() != "crash_reconciled") detail += ": event";
        else if (marker.at("prior_writer_generation").get<std::uint64_t>() != prior_generation) detail += ": prior generation";
        else if (marker.at("prior_writer_id").get<std::string>() != prior_writer_id) detail += ": prior writer";
        else if (marker.at("recovery_writer_generation").get<std::uint64_t>() != recovery_generation) detail += ": recovery generation";
        else if (marker.at("recovery_writer_id").get<std::string>() != recovery_writer_id) detail += ": recovery writer";
        else detail += ": observation";
        return false;
    }
    return true;
}

} // namespace

RuntimeFileArtifactLedgerStore::RuntimeFileArtifactLedgerStore(
    std::filesystem::path root, RuntimeArtifactLedgerAccessContext access)
    : root_(std::move(root)), access_(std::move(access)) {
    if (access_.audit_identity.empty() || access_.audit_identity.find_first_of("/\\") !=
                                               std::string::npos) {
        throw std::invalid_argument("ArtifactLedger audit identity is invalid");
    }
    std::error_code error;
    std::filesystem::create_directories(root_, error);
    if (error) throw std::system_error(error, "create ArtifactLedger root");
    std::filesystem::create_directories(root_ / "fences", error);
    std::filesystem::create_directories(root_ / "fences" / "history", error);
    std::filesystem::create_directories(root_ / "journals", error);
    std::filesystem::create_directories(root_ / "checkpoints", error);
    std::filesystem::create_directories(root_ / "blobs", error);
    std::filesystem::create_directories(root_ / "audit", error);
    if (error) throw std::system_error(error, "create ArtifactLedger directories");
    std::string security_detail;
    if (!secure_root_permissions(security_detail))
        throw std::runtime_error(security_detail);

    const auto lock_path = root_ / ".artifact-ledger.lock";
    int root_lock_error = 0;
#ifdef _WIN32
    const auto open_error =
        _wsopen_s(&root_lock_fd_, lock_path.wstring().c_str(), _O_CREAT | _O_RDWR | _O_BINARY,
                  _SH_DENYRW, _S_IREAD | _S_IWRITE);
    if (open_error != 0) {
        root_lock_error = static_cast<int>(open_error);
        root_lock_fd_ = -1;
    }
#else
    root_lock_fd_ = ::open(lock_path.c_str(), O_CREAT | O_RDWR, 0600);
    if (root_lock_fd_ < 0) root_lock_error = errno;
    if (root_lock_fd_ >= 0 && ::flock(root_lock_fd_, LOCK_EX | LOCK_NB) != 0) {
        root_lock_error = errno;
        ::close(root_lock_fd_);
        root_lock_fd_ = -1;
    }
#endif
    if (root_lock_fd_ < 0) {
        throw std::system_error(root_lock_error, std::generic_category(),
                                "acquire ArtifactLedger root lock");
    }
    // A crash can leave an uncommitted audit temp file behind. The root lock
    // makes cleanup exclusive; only the exact durable-write temp shape is
    // removed, while malformed or committed events remain visible to audit.
    for (const auto &entry : std::filesystem::directory_iterator(root_ / "audit", error)) {
        if (error) break;
        const auto name = entry.path().filename().string();
        if (!is_audit_event_temporary_filename(name)) continue;
        std::filesystem::remove(entry.path(), error);
        if (error) {
            throw std::system_error(error, "remove stale ArtifactLedger audit temp");
        }
    }
}

RuntimeFileArtifactLedgerStore::~RuntimeFileArtifactLedgerStore() {
    release_root_lock();
}

void RuntimeFileArtifactLedgerStore::release_root_lock() noexcept {
    if (root_lock_fd_ < 0) return;
#ifdef _WIN32
    _close(root_lock_fd_);
#else
    ::flock(root_lock_fd_, LOCK_UN);
    ::close(root_lock_fd_);
#endif
    root_lock_fd_ = -1;
}

std::filesystem::path
RuntimeFileArtifactLedgerStore::stream_path(std::string_view stream_id) const {
    return root_ / "journals" / token_name(stream_id);
}

std::filesystem::path RuntimeFileArtifactLedgerStore::fence_path(std::string_view stream_id) const {
    return root_ / "fences" / (token_name(stream_id) + ".json");
}

std::filesystem::path RuntimeFileArtifactLedgerStore::fence_history_path(
    std::string_view stream_id, std::uint64_t generation) const {
    return root_ / "fences" / "history" /
           (token_name(stream_id) + "-" + std::to_string(generation) + ".json");
}

bool RuntimeFileArtifactLedgerStore::active_fence(std::string_view stream_id,
                                                  std::uint64_t generation,
                                                  std::string_view writer_id,
                                                  std::string &detail) const {
    std::string bytes;
    if (!read_text(fence_path(stream_id), bytes)) {
        detail = "native ArtifactLedger fence is absent";
        return false;
    }
    try {
        const auto state = Json::parse(bytes.begin(), bytes.end());
        if (!state.is_object() || state.dump() != bytes || state.size() != 3U ||
            !state.contains("generation") || !state.contains("stream_id") ||
            !state.contains("writer_id") ||
            state.at("generation").get<std::uint64_t>() != generation ||
            state.at("stream_id").get<std::string>() != stream_id ||
            state.at("writer_id").get<std::string>() != writer_id) {
            detail = "stale or absent native ArtifactLedger fence";
            return false;
        }
    } catch (const Json::exception &) {
        detail = "native ArtifactLedger fence is corrupt";
        return false;
    }
    return true;
}

bool RuntimeFileArtifactLedgerStore::durable_write(const std::filesystem::path &path,
                                                   std::string_view bytes,
                                                   std::string &detail) const {
    const auto temporary = path.string() + ".tmp-" + token_name(bytes).substr(0, 16);
#ifdef _WIN32
    int fd = -1;
    if (_wsopen_s(&fd, std::filesystem::path(temporary).wstring().c_str(),
                  _O_WRONLY | _O_CREAT | _O_TRUNC | _O_BINARY, _SH_DENYRW,
                  _S_IREAD | _S_IWRITE) != 0) {
        fd = -1;
    }
#else
    const int fd = ::open(temporary.c_str(), O_WRONLY | O_CREAT | O_TRUNC, 0600);
#endif
    if (fd < 0 || !write_all(fd, bytes.data(), bytes.size())) {
        if (fd >= 0) {
#ifdef _WIN32
            _close(fd);
#else
            ::close(fd);
#endif
        }
        detail = "native ArtifactLedger durable write failed";
        return false;
    }
#ifdef _WIN32
    const auto handle = reinterpret_cast<HANDLE>(_get_osfhandle(fd));
    const bool synced = handle != INVALID_HANDLE_VALUE && FlushFileBuffers(handle) != FALSE;
    _close(fd);
    const bool moved =
        synced &&
        MoveFileExW(std::filesystem::path(temporary).wstring().c_str(), path.wstring().c_str(),
                    MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH) != 0;
#else
    const bool synced = ::fsync(fd) == 0;
    ::close(fd);
    const bool moved = synced && ::rename(temporary.c_str(), path.c_str()) == 0;
    if (moved) {
        if (!sync_directory(path.parent_path()) ||
            !sync_directory(path.parent_path().parent_path())) {
            detail = "native ArtifactLedger parent directory sync failed";
            return false;
        }
    }
#endif
    if (!moved) {
        std::error_code ignored;
        std::filesystem::remove(temporary, ignored);
        detail = "native ArtifactLedger atomic replacement failed";
        return false;
    }
#ifndef _WIN32
    (void)::chmod(path.c_str(), 0600);
#endif
    return true;
}

bool RuntimeFileArtifactLedgerStore::authorize(std::string_view operation,
                                               std::string &detail) const {
    const auto role = access_.role;
    const bool read_operation = operation == "read" || operation == "availability";
    if (read_operation) return true;
    if (operation == "receipt_read" || operation == "checkpoint_read") {
        if (role == RuntimeArtifactLedgerRole::RuntimeHost ||
            role == RuntimeArtifactLedgerRole::CrashReconciler ||
            role == RuntimeArtifactLedgerRole::BackupOperator ||
            role == RuntimeArtifactLedgerRole::ReadOnlyAuditor)
            return true;
        detail = "ArtifactLedger role is not authorized for " + std::string(operation);
        return false;
    }
    if (operation == "acquire_fence" || operation == "append") {
        if (role == RuntimeArtifactLedgerRole::RuntimeHost ||
            role == RuntimeArtifactLedgerRole::CrashReconciler)
            return true;
    } else if (operation == "commit_header" || operation == "checkpoint") {
        if (role == RuntimeArtifactLedgerRole::RuntimeHost) return true;
    } else if (operation == "artifact") {
        if (role == RuntimeArtifactLedgerRole::RuntimeHost ||
            role == RuntimeArtifactLedgerRole::PlanCompiler ||
            role == RuntimeArtifactLedgerRole::ReleaseArtifactPipeline)
            return true;
    } else if (operation == "finalize") {
        if (role == RuntimeArtifactLedgerRole::RuntimeHost ||
            role == RuntimeArtifactLedgerRole::CrashReconciler)
            return true;
    } else if (operation == "backup") {
        if (role == RuntimeArtifactLedgerRole::RuntimeHost ||
            role == RuntimeArtifactLedgerRole::BackupOperator)
            return true;
    } else if (operation == "restore") {
        if (role == RuntimeArtifactLedgerRole::BackupOperator) return true;
    }
    detail = "ArtifactLedger role is not authorized for " + std::string(operation);
    return false;
}

bool RuntimeFileArtifactLedgerStore::record_audit(std::string_view operation,
                                                  std::string_view resource,
                                                  std::string_view outcome_sha256,
                                                  std::string &detail) const {
    std::size_t next = 0;
    std::string previous;
    std::size_t ignored = 0;
    if (!verify_audit_chain(ignored, previous, detail)) return false;
    std::error_code error;
    for (const auto &entry : std::filesystem::directory_iterator(root_ / "audit", error)) {
        if (error) break;
        const auto name = entry.path().filename().string();
        if (!is_audit_event_filename(name)) continue;
        try {
            const auto value = std::stoull(name.substr(6, name.size() - 11));
            next = std::max(next, static_cast<std::size_t>(value + 1U));
        } catch (...) {
            detail = "ArtifactLedger audit filename is invalid";
            return false;
        }
    }
    const Json event = {{"audit_identity", access_.audit_identity},
                        {"operation", operation},
                        {"outcome_sha256", outcome_sha256},
                        {"previous_event_sha256", previous},
                        {"resource", resource},
                        {"role", role_name(access_.role)},
                        {"sequence", next}};
    const auto canonical = runtime::authority_contracts::canonical_authority_json(event.dump());
    if (!canonical.has_value()) {
        detail = "ArtifactLedger audit event is not canonical";
        return false;
    }
    const auto digest = runtime::authority_contracts::sha256_hex(*canonical);
    auto persisted = event;
    persisted["event_sha256"] = digest;
    const auto canonical_persisted =
        runtime::authority_contracts::canonical_authority_json(persisted.dump());
    const auto sequence_text = std::to_string(next);
    const auto event_name = "event-" + std::string(20U - sequence_text.size(), '0') +
                            sequence_text + ".json";
    return canonical_persisted.has_value() &&
           durable_write(root_ / "audit" / event_name,
                         *canonical_persisted, detail);
}

bool RuntimeFileArtifactLedgerStore::verify_audit_chain(
    std::size_t &event_count, std::string &last_event_sha256, std::string &detail) const {
    event_count = 0;
    last_event_sha256.clear();
    std::vector<std::filesystem::path> paths;
    std::error_code error;
    for (const auto &entry : std::filesystem::directory_iterator(root_ / "audit", error)) {
        if (error) break;
        if (is_audit_event_filename(entry.path().filename().string())) paths.push_back(entry.path());
    }
    if (error) {
        detail = "ArtifactLedger audit directory cannot be read";
        return false;
    }
    std::sort(paths.begin(), paths.end());
    std::string previous;
    for (const auto &path : paths) {
        std::string bytes;
        if (!read_text(path, bytes)) {
            detail = "ArtifactLedger audit event is unreadable";
            return false;
        }
        try {
            const auto event = Json::parse(bytes.begin(), bytes.end());
            if (event.dump() != bytes || event.value("sequence", event_count) != event_count ||
                event.value("previous_event_sha256", "") != previous ||
                !event.contains("event_sha256")) {
                detail = "ArtifactLedger audit chain is invalid";
                return false;
            }
            auto material = event;
            const auto actual = material.at("event_sha256").get<std::string>();
            material.erase("event_sha256");
            const auto canonical =
                runtime::authority_contracts::canonical_authority_json(material.dump());
            if (!canonical.has_value() || runtime::authority_contracts::sha256_hex(*canonical) != actual) {
                detail = "ArtifactLedger audit event digest is invalid";
                return false;
            }
            previous = actual;
            ++event_count;
        } catch (const Json::exception &) {
            detail = "ArtifactLedger audit event is not JSON";
            return false;
        }
    }
    last_event_sha256 = previous;
    return true;
}

bool RuntimeFileArtifactLedgerStore::secure_root_permissions(std::string &detail) const {
#ifdef _WIN32
    HANDLE token = nullptr;
    if (!OpenProcessToken(GetCurrentProcess(), TOKEN_QUERY, &token)) {
        detail = "ArtifactLedger cannot inspect current Windows identity";
        return false;
    }
    DWORD size = 0;
    GetTokenInformation(token, TokenUser, nullptr, 0, &size);
    std::vector<std::byte> buffer(size);
    if (!GetTokenInformation(token, TokenUser, buffer.data(), size, &size)) {
        CloseHandle(token);
        detail = "ArtifactLedger cannot read current Windows identity";
        return false;
    }
    const auto user = reinterpret_cast<TOKEN_USER *>(buffer.data())->User.Sid;
    PSID system = nullptr;
    if (!ConvertStringSidToSidW(L"S-1-5-18", &system)) {
        CloseHandle(token);
        detail = "ArtifactLedger cannot resolve SYSTEM identity";
        return false;
    }
    EXPLICIT_ACCESSW entries[2]{};
    for (auto &entry : entries) {
        entry.grfAccessPermissions = GENERIC_ALL;
        entry.grfAccessMode = SET_ACCESS;
        entry.grfInheritance = SUB_CONTAINERS_AND_OBJECTS_INHERIT;
        entry.Trustee.TrusteeForm = TRUSTEE_IS_SID;
        entry.Trustee.TrusteeType = TRUSTEE_IS_USER;
    }
    entries[0].Trustee.ptstrName = reinterpret_cast<LPWSTR>(user);
    entries[1].Trustee.ptstrName = reinterpret_cast<LPWSTR>(system);
    PACL acl = nullptr;
    const auto acl_error = SetEntriesInAclW(2, entries, nullptr, &acl);
    const auto set_error = acl_error == ERROR_SUCCESS
                               ? SetNamedSecurityInfoW(
                                     const_cast<LPWSTR>(root_.wstring().c_str()), SE_FILE_OBJECT,
                                     DACL_SECURITY_INFORMATION | PROTECTED_DACL_SECURITY_INFORMATION,
                                     nullptr, nullptr, acl, nullptr)
                               : acl_error;
    if (acl != nullptr) LocalFree(acl);
    LocalFree(system);
    CloseHandle(token);
    if (set_error != ERROR_SUCCESS) {
        detail = "ArtifactLedger cannot set private Windows root ACL";
        return false;
    }
    return true;
#else
    std::error_code error;
    std::filesystem::permissions(root_, std::filesystem::perms::owner_all,
                                 std::filesystem::perm_options::replace, error);
    if (error) {
        detail = "ArtifactLedger cannot set private root permissions";
        return false;
    }
    for (const auto name : {"fences", "fences/history", "journals", "checkpoints", "blobs",
                            "audit"}) {
        std::filesystem::permissions(root_ / name, std::filesystem::perms::owner_all,
                                     std::filesystem::perm_options::replace, error);
        if (error) return false;
    }
    return true;
#endif
}

bool RuntimeFileArtifactLedgerStore::acquire_fence(std::string_view stream_id,
                                                   std::string_view writer_id,
                                                   std::uint64_t &generation, std::string &detail) {
    if (!authorize("acquire_fence", detail)) return false;
    if (stream_id.empty() || writer_id.empty()) {
        detail = "native ArtifactLedger fence identities are required";
        return false;
    }
    std::lock_guard lock(mutex_);
    std::uint64_t previous = 0;
    std::string bytes;
    if (read_text(fence_path(stream_id), bytes)) {
        try {
            previous =
                Json::parse(bytes.begin(), bytes.end()).at("generation").get<std::uint64_t>();
        } catch (const Json::exception &) {
            detail = "native ArtifactLedger fence is corrupt";
            return false;
        }
    }
    if (previous == std::numeric_limits<std::uint64_t>::max()) {
        detail = "native ArtifactLedger fence generation overflow";
        return false;
    }
    if (access_.role == RuntimeArtifactLedgerRole::CrashReconciler && previous == 0U) {
        detail = "crash reconciler cannot create a new journal fence";
        return false;
    }
    generation = previous + 1U;
    const auto current =
        Json{{"generation", generation}, {"stream_id", stream_id}, {"writer_id", writer_id}};
    std::filesystem::create_directories(root_ / "fences" / "history");
    const auto fence_digest = runtime::authority_contracts::sha256_hex(current.dump());
    if (!record_audit("intent.acquire_fence", stream_id, fence_digest, detail) ||
        !durable_write(fence_history_path(stream_id, generation), current.dump(), detail))
        return false;
    if (!durable_write(fence_path(stream_id), current.dump(), detail)) return false;
    return record_audit("outcome.acquire_fence", stream_id, fence_digest, detail);
}

bool RuntimeFileArtifactLedgerStore::commit_header(std::string_view journal_id,
                                                   std::uint64_t generation,
                                                   std::string_view writer_id,
                                                   std::string_view header_json,
                                                   std::string &detail) {
    (void)journal_id;
    (void)generation;
    (void)writer_id;
    (void)header_json;
    detail = "native ArtifactLedger header commit requires a recorder admission capability";
    return false;
}

bool RuntimeFileArtifactLedgerStore::commit_header_impl(std::string_view journal_id,
                                                        std::uint64_t generation,
                                                        std::string_view writer_id,
                                                        std::string_view header_json,
                                                        std::string &detail) {
    if (!authorize("commit_header", detail)) return false;
    std::lock_guard lock(mutex_);
    if (!active_fence("journal:" + std::string(journal_id), generation, writer_id, detail))
        return false;
    const auto directory = stream_path("journal:" + std::string(journal_id));
    std::error_code error;
    std::filesystem::create_directories(directory, error);
    if (error) {
        detail = "native ArtifactLedger journal directory creation failed";
        return false;
    }
    if (std::filesystem::exists(directory / "header.json")) {
        detail = "native ArtifactLedger journal header already exists";
        return false;
    }
    try {
        const auto header = Json::parse(header_json.begin(), header_json.end());
        if (!header.is_object() || header.dump() != header_json ||
            header.value("run_id", "") != journal_id) {
            detail = "native ArtifactLedger journal header is not canonical or run-bound";
            return false;
        }
        if (!validate_runtime_run_header_json(journal_id, header_json, detail)) {
            return false;
        }
        if (header.contains("receipt_bindings") &&
            !verify_admission_artifacts_unlocked(header.at("receipt_bindings").dump(), detail))
            return false;
    } catch (const Json::exception &) {
        detail = "native ArtifactLedger journal header is not JSON";
        return false;
    }
    const auto header_digest = runtime::authority_contracts::sha256_hex(header_json);
    if (!record_audit("intent.commit_header", journal_id, header_digest, detail) ||
        !durable_write(directory / "header.json", header_json, detail))
        return false;
    return record_audit("outcome.commit_header", journal_id, header_digest, detail);
}

bool RuntimeFileArtifactLedgerStore::commit_header_authorized(
    std::string_view journal_id, std::uint64_t generation, std::string_view writer_id,
    std::string_view header_json, const RuntimeRunAdmissionCapability &capability,
    std::string &detail) {
    if (!capability.valid()) {
        detail = "native ArtifactLedger admission capability is invalid";
        return false;
    }
    if (!commit_header_impl(journal_id, generation, writer_id, header_json, detail)) return false;
    std::lock_guard lock(mutex_);
    admission_capabilities_[std::string(journal_id)] = std::string(capability.token());
    return true;
}

bool RuntimeFileArtifactLedgerStore::resume_journal(
    std::string_view journal_id, std::uint64_t generation, std::string_view writer_id,
    std::string_view header_json,
    std::uint64_t &next_sequence, std::string &last_record_sha256, std::string &detail) {
    (void)journal_id;
    (void)generation;
    (void)writer_id;
    (void)header_json;
    (void)next_sequence;
    (void)last_record_sha256;
    detail = "native ArtifactLedger journal resume requires a recorder admission capability";
    return false;
}

bool RuntimeFileArtifactLedgerStore::resume_journal_impl(
    std::string_view journal_id, std::uint64_t generation, std::string_view writer_id,
    std::string_view header_json,
    std::uint64_t &next_sequence, std::string &last_record_sha256, std::string &detail) {
    if (!authorize("append", detail)) return false;
    std::lock_guard lock(mutex_);
    if (!active_fence("journal:" + std::string(journal_id), generation, writer_id, detail))
        return false;
    const auto directory = stream_path("journal:" + std::string(journal_id));
    std::string existing_header;
    if (!read_text(directory / "header.json", existing_header)) {
        detail = "native ArtifactLedger journal header is absent for resume";
        return false;
    }
    if (!validate_runtime_run_header_json(journal_id, existing_header, detail)) return false;
    const auto parsed_header = Json::parse(existing_header);
    if (parsed_header.contains("receipt_bindings") &&
        !verify_admission_artifacts_unlocked(parsed_header.at("receipt_bindings").dump(), detail))
        return false;
    if (!header_json.empty() && existing_header != header_json) {
        detail = "native ArtifactLedger journal header differs during resume";
        return false;
    }
    // A completed receipt may be reopened for an idempotent recorder retry when
    // the receipt write succeeded but its outcome audit acknowledgement did not.
    // append_record and finalize_receipt still enforce their own finalized/capability
    // gates, so this does not reopen the journal for mutation.
    if (!scan_journal(directory, journal_id, generation, next_sequence, last_record_sha256,
                      detail))
        return false;
    return record_audit("resume_journal", journal_id,
                        runtime::authority_contracts::sha256_hex(existing_header), detail);
}

bool RuntimeFileArtifactLedgerStore::resume_journal_authorized(
    std::string_view journal_id, std::uint64_t generation, std::string_view writer_id,
    std::string_view header_json, const RuntimeRunAdmissionCapability &capability,
    std::uint64_t &next_sequence, std::string &last_record_sha256, std::string &detail) {
    if (!capability.valid()) {
        detail = "native ArtifactLedger admission capability is invalid";
        return false;
    }
    if (!resume_journal_impl(journal_id, generation, writer_id, header_json, next_sequence,
                             last_record_sha256, detail))
        return false;
    std::lock_guard lock(mutex_);
    admission_capabilities_[std::string(journal_id)] = std::string(capability.token());
    return true;
}

bool RuntimeFileArtifactLedgerStore::scan_journal(const std::filesystem::path &directory,
                                                  std::string_view journal_id,
                                                  std::uint64_t expected_generation,
                                                  std::uint64_t &next_sequence,
                                                  std::string &last_record_sha256,
                                                  std::string &detail) const {
    if (!std::filesystem::exists(directory / "header.json")) {
        detail = "native ArtifactLedger journal header is absent";
        return false;
    }
    next_sequence = 0;
    last_record_sha256.assign(64U, '0');
    std::uint64_t previous_generation = 0U;
    for (;;) {
        const auto frame_path = directory / ("frame-" + std::to_string(next_sequence) + ".json");
        if (!std::filesystem::exists(frame_path)) break;
        std::string frame_bytes;
        if (!read_text(frame_path, frame_bytes)) {
            detail = "native ArtifactLedger journal frame is unreadable";
            return false;
        }
        try {
            const auto frame = Json::parse(frame_bytes.begin(), frame_bytes.end());
            std::string payload;
            const auto identity_bytes = frame_identity(frame).dump();
            if (frame.dump() != frame_bytes ||
                frame.value("frame_size", std::numeric_limits<std::size_t>::max()) !=
                    frame_bytes.size() ||
                frame.value("journal_id", "") != journal_id ||
                frame.value("stream_id", "") != "journal:" + std::string(journal_id) ||
                frame.value("writer_id", "").empty() ||
                frame.value("fence_generation", 0ULL) == 0U ||
                frame.value("fence_generation", 0ULL) < previous_generation ||
                frame.value("fence_generation", std::numeric_limits<std::uint64_t>::max()) >
                    expected_generation ||
                ![&] {
                    std::string history;
                    if (!read_text(fence_history_path(frame.value("stream_id", ""),
                                                      frame.value("fence_generation", 0ULL)),
                                   history))
                        return false;
                    try {
                        const auto state = Json::parse(history.begin(), history.end());
                        return state.dump() == history &&
                               state.value("stream_id", "") == frame.value("stream_id", "") &&
                               state.value("generation", 0ULL) ==
                                   frame.value("fence_generation", 0ULL) &&
                               state.value("writer_id", "") == frame.value("writer_id", "");
                    } catch (const Json::exception &) {
                        return false;
                    }
                }() ||
                frame.value("sequence", std::numeric_limits<std::uint64_t>::max()) !=
                    next_sequence ||
                !hex_decode(frame.value("payload_hex", ""), payload) ||
                frame.value("payload_size", std::numeric_limits<std::size_t>::max()) !=
                    payload.size() ||
                frame.value("payload_sha256", "") !=
                    runtime::authority_contracts::sha256_hex(payload) ||
                frame.value("frame_length", std::numeric_limits<std::size_t>::max()) !=
                    identity_bytes.size() + sizeof(std::uint32_t) ||
                frame.value("frame_checksum", std::numeric_limits<std::uint32_t>::max()) !=
                    crc32(identity_bytes) ||
                frame.value("frame_sha256", "") !=
                    runtime::authority_contracts::sha256_hex(identity_bytes) ||
                frame.value("prior_record_sha256", "") != last_record_sha256) {
                detail = "native ArtifactLedger journal frame integrity failure";
                return false;
            }
            last_record_sha256 = frame.value("frame_sha256", "");
            previous_generation = frame.value("fence_generation", 0ULL);
        } catch (const Json::exception &) {
            detail = "native ArtifactLedger journal frame is not canonical JSON";
            return false;
        }
        ++next_sequence;
    }
    for (const auto &entry : std::filesystem::directory_iterator(directory)) {
        std::uint64_t sequence = 0;
        if (parse_sequence(entry.path().filename().string(), sequence) &&
            sequence >= next_sequence) {
            detail = "native ArtifactLedger journal has a non-contiguous frame";
            return false;
        }
    }
    return true;
}

bool RuntimeFileArtifactLedgerStore::append_record(std::string_view journal_id,
                                                   std::uint64_t generation,
                                                   std::string_view writer_id,
                                                   std::uint64_t sequence,
                                                   std::string_view payload,
                                                   RuntimeRunRecorderAppendAck &ack,
                                                   std::string &detail) {
    (void)journal_id;
    (void)generation;
    (void)writer_id;
    (void)sequence;
    (void)payload;
    (void)ack;
    detail = "native ArtifactLedger append requires a recorder admission capability";
    return false;
}

bool RuntimeFileArtifactLedgerStore::append_record_authorized(
    std::string_view journal_id, std::uint64_t generation, std::string_view writer_id,
    std::uint64_t sequence, std::string_view payload,
    const RuntimeRunAdmissionCapability &capability, RuntimeRunRecorderAppendAck &ack,
    std::string &detail) {
    return append_record_impl(journal_id, generation, writer_id, sequence, payload, &capability,
                              ack, detail);
}

bool RuntimeFileArtifactLedgerStore::append_record_impl(
    std::string_view journal_id, std::uint64_t generation, std::string_view writer_id,
    std::uint64_t sequence, std::string_view payload,
    const RuntimeRunAdmissionCapability *capability, RuntimeRunRecorderAppendAck &ack,
    std::string &detail) {
    if (capability == nullptr || !capability->valid()) {
        detail = "native ArtifactLedger append requires a recorder admission capability";
        return false;
    }
    if (!authorize("append", detail)) return false;
    std::lock_guard lock(mutex_);
    const auto admitted = admission_capabilities_.find(std::string(journal_id));
    if (admitted == admission_capabilities_.end() || admitted->second != capability->token()) {
        detail = "native ArtifactLedger admission capability does not own this journal";
        return false;
    }
    if (!active_fence("journal:" + std::string(journal_id), generation, writer_id, detail))
        return false;
    const auto directory = stream_path("journal:" + std::string(journal_id));
    std::uint64_t next = 0;
    std::string prior;
    if (!scan_journal(directory, journal_id, generation, next, prior, detail) ||
        sequence != next) {
        if (detail.empty()) detail = "native ArtifactLedger journal sequence is not monotonic";
        return false;
    }
    if (std::filesystem::exists(directory / "receipt.json")) {
        detail = "native ArtifactLedger journal is already finalized";
        return false;
    }
    if (access_.role == RuntimeArtifactLedgerRole::CrashReconciler) {
        try {
            const auto recovery = Json::parse(payload.begin(), payload.end());
            if (generation <= 1U) {
                detail = "crash reconciler requires a prior writer generation";
                return false;
            }
            std::string prior_fence_bytes;
            if (!read_text(fence_history_path("journal:" + std::string(journal_id), generation - 1U),
                           prior_fence_bytes)) {
                detail = "crash reconciler lacks the prior durable fence";
                return false;
            }
            const auto prior_fence = Json::parse(prior_fence_bytes.begin(), prior_fence_bytes.end());
            const auto prior_writer_id = prior_fence.at("writer_id").get<std::string>();
            if (recovery.value("event", "") == "crash_reconciled") {
                if (!validate_crash_marker(recovery, "journal:" + std::string(journal_id), generation,
                                           writer_id, generation - 1U, prior_writer_id, detail))
                    return false;
            } else if (recovery.value("event", "") == "runtime_lifecycle" &&
                       recovery.value("lifecycle_event", "") == "terminal") {
                bool found_marker = false;
                for (std::uint64_t index = sequence; index-- > 0U;) {
                    std::string frame_bytes;
                    if (!read_text(stream_path("journal:" + std::string(journal_id)) /
                                       ("frame-" + std::to_string(index) + ".json"),
                                   frame_bytes))
                        continue;
                    const auto frame = Json::parse(frame_bytes.begin(), frame_bytes.end());
                    std::string marker_bytes;
                    if (!hex_decode(frame.value("payload_hex", ""), marker_bytes)) continue;
                    const auto marker = Json::parse(marker_bytes.begin(), marker_bytes.end());
                    if (marker.is_object() && marker.value("event", "") == "crash_reconciled" &&
                        validate_crash_marker(marker, "journal:" + std::string(journal_id), generation,
                                              writer_id, generation - 1U, prior_writer_id, detail)) {
                        found_marker = true;
                        break;
                    }
                }
                if (!found_marker) {
                    detail = "crash reconciler terminal record lacks a validated marker";
                    return false;
                }
            } else {
                detail = "crash reconciler may append only a strict marker or terminal record";
                return false;
            }
        } catch (const Json::exception &) {
            detail = "crash reconciler payload is not canonical recovery JSON";
            return false;
        }
    }
    const auto record_sha256 = runtime::authority_contracts::sha256_hex(payload);
    const auto identity = Json{{"fence_generation", generation},
                               {"journal_id", journal_id},
                               {"payload_sha256", record_sha256},
                               {"payload_size", payload.size()},
                               {"prior_record_sha256", prior},
                               {"sequence", sequence},
                               {"stream_id", "journal:" + std::string(journal_id)},
                               {"writer_id", writer_id}};
    const auto identity_bytes = identity.dump();
    const auto frame_sha256 = runtime::authority_contracts::sha256_hex(identity_bytes);
    auto frame = Json{{"fence_generation", identity.at("fence_generation")},
                            {"frame_checksum", crc32(identity_bytes)},
                            {"frame_length", identity_bytes.size() + sizeof(std::uint32_t)},
                            {"frame_sha256", frame_sha256},
                            {"journal_id", identity.at("journal_id")},
                            {"payload_hex", hex_encode(payload)},
                            {"payload_sha256", identity.at("payload_sha256")},
                            {"payload_size", identity.at("payload_size")},
                            {"prior_record_sha256", identity.at("prior_record_sha256")},
                            {"sequence", identity.at("sequence")},
                            {"stream_id", identity.at("stream_id")},
                            {"writer_id", identity.at("writer_id")}};
    std::size_t frame_size = 0;
    for (;;) {
        frame["frame_size"] = frame_size;
        const auto measured = frame.dump().size();
        if (measured == frame_size) break;
        frame_size = measured;
    }
    if (!record_audit("intent.append_record", journal_id, frame_sha256, detail) ||
        !durable_write(directory / ("frame-" + std::to_string(sequence) + ".json"), frame.dump(),
                       detail))
        return false;
    if (!record_audit("outcome.append_record", journal_id, frame_sha256, detail)) return false;
    ack = {.durable = true,
           .sequence = sequence,
           .payload_sha256 = record_sha256,
           .record_sha256 = frame_sha256};
    return true;
}

bool RuntimeFileArtifactLedgerStore::finalize_receipt(std::string_view,
                                                      std::uint64_t,
                                                      std::string_view,
                                                      std::string_view,
                                                      RuntimeRunRecorderFinalizeAck &,
                                                      std::string &detail) {
    detail = "native ArtifactLedger receipt finalization requires a recorder admission capability";
    return false;
}

bool RuntimeFileArtifactLedgerStore::finalize_receipt_authorized(
    std::string_view journal_id, std::uint64_t generation, std::string_view writer_id,
    std::string_view receipt_json, const RuntimeRunAdmissionCapability &capability,
    RuntimeRunRecorderFinalizeAck &ack, std::string &detail) {
    return finalize_receipt_impl(journal_id, generation, writer_id, receipt_json, &capability,
                                 ack, detail);
}

bool RuntimeFileArtifactLedgerStore::finalize_receipt_impl(
    std::string_view journal_id, std::uint64_t generation, std::string_view writer_id,
    std::string_view receipt_json, const RuntimeRunAdmissionCapability *capability,
    RuntimeRunRecorderFinalizeAck &ack, std::string &detail) {
    if (capability == nullptr || !capability->valid()) {
        detail = "native ArtifactLedger receipt finalization requires a recorder admission capability";
        return false;
    }
    {
        std::lock_guard lock(mutex_);
        const auto admitted = admission_capabilities_.find(std::string(journal_id));
        if (admitted == admission_capabilities_.end() ||
            admitted->second != capability->token()) {
            detail = "native ArtifactLedger admission capability does not own this journal";
            return false;
        }
    }
    if (!authorize("finalize", detail)) return false;
    std::lock_guard lock(mutex_);
    if (!active_fence("journal:" + std::string(journal_id), generation, writer_id, detail))
        return false;
    const auto directory = stream_path("journal:" + std::string(journal_id));
    std::uint64_t next = 0;
    std::string last_record_sha256;
    if (!scan_journal(directory, journal_id, generation, next, last_record_sha256, detail) ||
        next == 0U)
        return false;
    if (!validate_runtime_run_receipt_json(receipt_json, detail)) return false;
    try {
        const auto receipt = Json::parse(receipt_json.begin(), receipt_json.end());
        const auto &payload = receipt.at("payload");
        const auto path = directory / "receipt.json";
        bool existing_exact = false;
        if (std::filesystem::exists(path)) {
            std::string existing;
            if (!read_text(path, existing) || existing != receipt_json) {
                detail = "native ArtifactLedger receipt is immutable and already differs";
                return false;
            }
            existing_exact = true;
        }
        const auto receipt_generation_text =
            payload.at("writer_generation").get<std::string>();
        std::size_t parsed_characters = 0U;
        const auto receipt_generation = std::stoull(receipt_generation_text, &parsed_characters);
        if (parsed_characters != receipt_generation_text.size() || receipt_generation == 0U ||
            receipt_generation > generation) {
            detail = "native ArtifactLedger receipt writer generation is outside the active fence";
            return false;
        }
        if (existing_exact) {
            std::string tail_frame_bytes;
            if (!read_text(directory / ("frame-" + std::to_string(next - 1U) + ".json"),
                           tail_frame_bytes) ||
                Json::parse(tail_frame_bytes).at("fence_generation").get<std::uint64_t>() !=
                    receipt_generation) {
                detail = "existing receipt does not belong to the durable writer tail";
                return false;
            }
        } else if (receipt_generation != generation) {
            detail = "new receipt does not belong to the active writer fence";
            return false;
        }
        if (access_.role == RuntimeArtifactLedgerRole::CrashReconciler && !existing_exact) {
            const auto terminal_state = payload.at("terminal_state").get<std::string>();
            if (terminal_state != "crashed" && terminal_state != "incomplete") {
                detail = "crash reconciler may finalize only crashed or incomplete receipts";
                return false;
            }
            if (generation <= 1U || next == 0U) {
                detail = "crash reconciler receipt lacks a recovery generation";
                return false;
            }
            std::string last_frame_bytes;
            if (!read_text(directory / ("frame-" + std::to_string(next - 1U) + ".json"),
                           last_frame_bytes)) {
                detail = "crash reconciler receipt lacks a terminal marker frame";
                return false;
            }
            Json marker;
            bool found_marker = false;
            for (std::uint64_t index = next; index-- > 0U;) {
                std::string frame_bytes;
                if (!read_text(directory / ("frame-" + std::to_string(index) + ".json"),
                               frame_bytes)) {
                    detail = "crash reconciler terminal marker frame is unreadable";
                    return false;
                }
                const auto frame = Json::parse(frame_bytes.begin(), frame_bytes.end());
                std::string marker_bytes;
                if (!hex_decode(frame.at("payload_hex").get<std::string>(), marker_bytes)) {
                    detail = "crash reconciler marker payload is invalid";
                    return false;
                }
                const auto candidate = Json::parse(marker_bytes.begin(), marker_bytes.end());
                if (candidate.is_object() && candidate.value("event", "") == "crash_reconciled") {
                    marker = candidate;
                    found_marker = true;
                    break;
                }
            }
            if (!found_marker) {
                detail = "crash reconciler receipt lacks a crash reconciliation marker";
                return false;
            }
            std::string prior_fence_bytes;
            if (!read_text(fence_history_path("journal:" + std::string(journal_id), generation - 1U),
                           prior_fence_bytes)) {
                detail = "crash reconciler receipt lacks the prior durable fence";
                return false;
            }
            const auto prior_fence = Json::parse(prior_fence_bytes.begin(), prior_fence_bytes.end());
            if (!validate_crash_marker(marker, "journal:" + std::string(journal_id), generation,
                                       writer_id, generation - 1U,
                                       prior_fence.at("writer_id").get<std::string>(), detail))
                return false;
        }
        std::string header_bytes;
        if (!read_text(directory / "header.json", header_bytes)) {
            detail = "native ArtifactLedger journal header is absent at finalization";
            return false;
        }
        const auto header = Json::parse(header_bytes.begin(), header_bytes.end());
        if (!validate_runtime_run_header_json(journal_id, header_bytes, detail)) return false;
        if (!receipt_matches_header(payload, header, detail)) return false;
        if (!verify_admission_artifacts_unlocked(payload.dump(), detail)) return false;
        if (payload.at("journal_last_sequence") != next - 1U ||
            payload.at("journal_last_record_sha256") != last_record_sha256) {
            detail = "native ArtifactLedger receipt does not bind the durable journal tail";
            return false;
        }
        if (!validate_receipt_checkpoints_unlocked(payload.dump(), receipt_generation, detail))
            return false;
        if (payload.at("terminal_state") == "completed") {
            for (const auto &artifact : payload.at("results").at("output_artifacts")) {
                const auto digest = artifact.at("digest").get<std::string>();
                const auto location = artifact.at("retrieval_location").get<std::string>();
                if (location != "ledger://blob-" + digest ||
                    !verify_artifact(digest, artifact.at("size").get<std::size_t>(),
                                     artifact.at("media_type").get<std::string>(),
                                     artifact.at("retention_class").get<std::string>(), detail)) {
                    if (detail.empty()) detail = "native ArtifactLedger receipt output is not durable";
                    return false;
                }
            }
        }
        const auto receipt_digest = receipt.at("payload_sha256").get<std::string>();
        if (!record_audit("intent.finalize_receipt", journal_id, receipt_digest, detail))
            return false;
        if (!existing_exact && !durable_write(path, receipt_json, detail)) {
            return false;
        }
        if (!record_audit("outcome.finalize_receipt", journal_id, receipt_digest, detail))
            return false;
        ack = {.durable = true, .receipt_sha256 = receipt.at("payload_sha256").get<std::string>()};
    } catch (const std::exception &) {
        detail = "native ArtifactLedger receipt is not canonical JSON or has an invalid generation";
        return false;
    }
    return true;
}

bool RuntimeFileArtifactLedgerStore::commit_checkpoint(
    std::string_view journal_id, std::uint64_t generation, std::string_view writer_id,
    std::string_view checkpoint_json,
    std::string_view validation_json, RuntimeRunRecorderCheckpointAck &ack, std::string &detail) {
    (void)journal_id;
    (void)generation;
    (void)writer_id;
    (void)checkpoint_json;
    (void)validation_json;
    (void)ack;
    detail = "native ArtifactLedger checkpoint commit requires a recorder admission capability";
    return false;
}

bool RuntimeFileArtifactLedgerStore::commit_checkpoint_authorized(
    std::string_view journal_id, std::uint64_t generation, std::string_view writer_id,
    std::string_view checkpoint_json, std::string_view validation_json,
    const RuntimeRunAdmissionCapability &capability, RuntimeRunRecorderCheckpointAck &ack,
    std::string &detail) {
    return commit_checkpoint_impl(journal_id, generation, writer_id, checkpoint_json,
                                  validation_json, &capability, ack, detail);
}

bool RuntimeFileArtifactLedgerStore::commit_checkpoint_impl(
    std::string_view journal_id, std::uint64_t generation, std::string_view writer_id,
    std::string_view checkpoint_json, std::string_view validation_json,
    const RuntimeRunAdmissionCapability *capability, RuntimeRunRecorderCheckpointAck &ack,
    std::string &detail) {
    if (capability == nullptr || !capability->valid()) {
        detail = "native ArtifactLedger checkpoint commit requires a recorder admission capability";
        return false;
    }
    if (!authorize("checkpoint", detail)) return false;
    std::lock_guard lock(mutex_);
    const auto admitted = admission_capabilities_.find(std::string(journal_id));
    if (admitted == admission_capabilities_.end() || admitted->second != capability->token()) {
        detail = "native ArtifactLedger admission capability does not own this journal";
        return false;
    }
    if (!active_fence("journal:" + std::string(journal_id), generation, writer_id, detail))
        return false;
    try {
        const auto checkpoint = Json::parse(checkpoint_json.begin(), checkpoint_json.end());
        const auto &payload = checkpoint.at("payload");
        const auto checkpoint_id = payload.at("checkpoint_id").get<std::string>();
        if (payload.value("run_id", "") != journal_id) {
            detail = "native ArtifactLedger checkpoint run identity differs from journal";
            return false;
        }
        const auto canonical_payload =
            runtime::authority_contracts::canonical_authority_json(payload.dump());
        if (!canonical_payload.has_value() ||
            !runtime::authority_contracts::validate_authority_envelope_json(
                 checkpoint_json, *canonical_payload)
                 .valid) {
            detail = "native ArtifactLedger checkpoint authority is invalid";
            return false;
        }
        if (payload.at("writer_generation") != std::to_string(generation)) {
            detail = "native ArtifactLedger checkpoint writer generation differs from fence";
            return false;
        }
        std::string header_bytes;
        if (!read_text(stream_path("journal:" + std::string(journal_id)) / "header.json",
                       header_bytes)) {
            detail = "native ArtifactLedger checkpoint journal header is absent";
            return false;
        }
        const auto header = Json::parse(header_bytes.begin(), header_bytes.end());
        if (!validate_runtime_run_header_json(journal_id, header_bytes, detail)) return false;
        const auto &bindings = header.at("receipt_bindings");
        const auto release = Json::parse(
            bindings.at("release_manifest_envelope_json").get<std::string>());
        if (payload.at("state_schema_generation") !=
            release.at("payload").at("state_schema_generation")) {
            detail = "native ArtifactLedger checkpoint state schema differs from release";
            return false;
        }
        if (payload.at("plan_sha256") != bindings.at("plan_binding").at("plan_sha256") ||
            payload.at("release_id") != bindings.at("release_binding").at("release_id") ||
            payload.at("decision_id") !=
                bindings.at("release_binding").at("rollout_decision_id") ||
            payload.at("target_reader_generation_min") !=
                bindings.at("reader_generation_min") ||
            payload.at("target_reader_generation_max") !=
                bindings.at("reader_generation_max")) {
            detail = "native ArtifactLedger checkpoint differs from durable admission bindings";
            return false;
        }
        const auto validation = Json::parse(validation_json.begin(), validation_json.end());
        if (!validation.is_object() || validation.value("accepted", false) != true ||
            validation.value("checkpoint_id", "") != checkpoint_id ||
            !validation.contains("state_payload_hex") || !validation.contains("state_sha256") ||
            !validation.contains("aggregate_replay_sha256") || !validation.contains("validator_id") ||
            runtime::authority_contracts::canonical_authority_json(validation_json).value_or("") !=
                validation_json) {
            detail = "native ArtifactLedger checkpoint validation evidence is not accepted";
            return false;
        }
        std::uint64_t transfer_fence = 0;
        try {
            transfer_fence = std::stoull(payload.at("transfer_fence_sequence").get<std::string>());
        } catch (...) {
            detail = "native ArtifactLedger checkpoint transfer fence is invalid";
            return false;
        }
        std::uint64_t journal_next = 0;
        std::string journal_tail;
        if (!scan_journal(stream_path("journal:" + std::string(journal_id)), journal_id,
                          generation, journal_next, journal_tail, detail) ||
            transfer_fence == 0U || transfer_fence >= journal_next) {
            detail = "native ArtifactLedger checkpoint transfer fence is not a durable journal sequence";
            return false;
        }
        std::string intent_frame_bytes;
        if (!read_text(stream_path("journal:" + std::string(journal_id)) /
                           ("frame-" + std::to_string(transfer_fence) + ".json"),
                       intent_frame_bytes)) {
            detail = "native ArtifactLedger checkpoint commit intent is absent";
            return false;
        }
        const auto intent_frame = Json::parse(intent_frame_bytes.begin(), intent_frame_bytes.end());
        std::string intent_payload;
        if (!hex_decode(intent_frame.at("payload_hex").get<std::string>(), intent_payload)) {
            detail = "native ArtifactLedger checkpoint commit intent is not decodable";
            return false;
        }
        const auto intent = Json::parse(intent_payload.begin(), intent_payload.end());
        if (!intent.is_object() || intent.value("event", "") != "checkpoint_commit" ||
            intent.value("checkpoint_id", "") != checkpoint_id ||
            intent.value("checkpoint_sha256", "") != runtime::authority_contracts::sha256_hex(checkpoint_json) ||
            intent.value("validation_sha256", "") != runtime::authority_contracts::sha256_hex(validation_json) ||
            intent.value("transfer_fence_sequence", "") !=
                payload.at("transfer_fence_sequence").get<std::string>()) {
            detail = "native ArtifactLedger checkpoint commit intent does not bind the checkpoint";
            return false;
        }
        std::string state_payload;
        if (!hex_decode(validation.at("state_payload_hex").get<std::string>(), state_payload) ||
            validation.value("state_sha256", "") !=
                runtime::authority_contracts::sha256_hex(state_payload) ||
            validation.value("state_sha256", "") != payload.value("aggregate_state_sha256", "") ||
            validation.value("aggregate_replay_sha256", "") !=
                runtime::authority_contracts::checkpoint_replay_aggregate_sha256(payload.dump()).value_or("")) {
            detail = "native ArtifactLedger checkpoint validation evidence is not state/replay bound";
            return false;
        }
        const auto directory = root_ / "checkpoints" / token_name(checkpoint_id);
        std::error_code error;
        std::filesystem::create_directories(directory, error);
        if (error) {
            detail = "native ArtifactLedger checkpoint directory creation failed";
            return false;
        }
        const auto bundle = Json{{"checkpoint", checkpoint}, {"validation", validation}}.dump();
        const auto checkpoint_digest =
            runtime::authority_contracts::sha256_hex(checkpoint_json);
        if (!record_audit("intent.commit_checkpoint", checkpoint_id, checkpoint_digest, detail))
            return false;
        const auto bundle_path = directory / "bundle.json";
        if (std::filesystem::exists(bundle_path)) {
            std::string existing;
            if (!read_text(bundle_path, existing) || existing != bundle) {
                detail = "native ArtifactLedger checkpoint slot is immutable and differs";
                return false;
            }
        } else if (!durable_write(bundle_path, bundle, detail)) {
            return false;
        }
        if (!record_audit("outcome.commit_checkpoint", checkpoint_id, checkpoint_digest, detail))
            return false;
        ack = {.durable = true,
               .checkpoint_sha256 = checkpoint_digest,
               .validation_sha256 = runtime::authority_contracts::sha256_hex(validation_json),
               .state_schema_generation = payload.at("state_schema_generation")};
    } catch (const Json::exception &) {
        detail = "native ArtifactLedger checkpoint is not canonical JSON";
        return false;
    }
    return true;
}

bool RuntimeFileArtifactLedgerStore::rehydrate_state_authorized(
    std::string_view journal_id, const RuntimeRunAdmissionCapability &capability,
    RuntimeRunRecorderRecoveryState &state, std::string &detail) {
    if (!capability.valid()) {
        detail = "native ArtifactLedger checkpoint rehydration requires a recorder admission capability";
        return false;
    }
    std::lock_guard lock(mutex_);
    const auto admitted = admission_capabilities_.find(std::string(journal_id));
    if (admitted == admission_capabilities_.end() || admitted->second != capability.token()) {
        detail = "native ArtifactLedger admission capability does not own this journal";
        return false;
    }
    state = {};
    try {
        const auto journal_directory = stream_path("journal:" + std::string(journal_id));
        if (std::filesystem::exists(journal_directory / "receipt.json")) {
            if (!read_text(journal_directory / "receipt.json", state.existing_receipt_json) ||
                !validate_runtime_run_receipt_json(state.existing_receipt_json, detail) ||
                Json::parse(state.existing_receipt_json).at("payload").value("run_id", "") !=
                    journal_id) {
                if (detail.empty())
                    detail = "native ArtifactLedger existing receipt cannot be rehydrated";
                return false;
            }
        }
        for (std::uint64_t sequence = 0U;; ++sequence) {
            std::string frame_json;
            if (!read_text(journal_directory / ("frame-" + std::to_string(sequence) + ".json"),
                           frame_json))
                break;
            const auto frame = Json::parse(frame_json.begin(), frame_json.end());
            std::string payload_json;
            if (!hex_decode(frame.at("payload_hex").get<std::string>(), payload_json)) {
                detail = "native ArtifactLedger recovery frame payload is invalid";
                return false;
            }
            Json payload;
            try {
                payload = Json::parse(payload_json.begin(), payload_json.end());
            } catch (const Json::exception &) {
                continue;
            }
            if (!payload.is_object()) continue;
            if (payload.value("event", "") == "runtime_identity_bound") {
                state.host_boot_id = payload.at("host_boot_id").get<std::string>();
                state.incarnation_epoch = payload.at("incarnation_epoch").get<std::string>();
                state.execution_scope_json = payload.at("execution_scope").dump();
            } else if (payload.value("event", "") == "runtime_entity_observed" &&
                       !state.execution_scope_json.empty()) {
                auto scope = Json::parse(state.execution_scope_json);
                auto &entities = scope.at("entity_ids");
                const auto entity_id = payload.at("entity_id").get<std::string>();
                if (std::find(entities.begin(), entities.end(), Json(entity_id)) == entities.end())
                    entities.push_back(entity_id);
                std::sort(entities.begin(), entities.end());
                scope.at("epochs")["entity"] = payload.at("entity_epoch");
                state.execution_scope_json = scope.dump();
            } else if (payload.value("event", "") == "runtime_lifecycle") {
                const auto event = payload.at("lifecycle_event").get<std::string>();
                const auto timestamp = payload.at("timestamp").get<std::string>();
                const auto epoch = state.incarnation_epoch.empty() ? "0" : state.incarnation_epoch;
                state.lifecycle_events.push_back(
                    Json{{"sequence", state.lifecycle_events.size()},
                         {"event", event},
                         {"timestamp", timestamp},
                         {"epoch", epoch},
                         {"durable_sequence", sequence}}
                        .dump());
                if (event == "journal_admitted") state.admitted_at = timestamp;
            }
        }
        std::error_code error;
        for (const auto &entry : std::filesystem::directory_iterator(root_ / "checkpoints", error)) {
            if (error) {
                detail = "native ArtifactLedger checkpoint inventory cannot be enumerated";
                return false;
            }
            if (!entry.is_directory()) continue;
            std::string bundle_json;
            if (!read_text(entry.path() / "bundle.json", bundle_json)) {
                detail = "native ArtifactLedger checkpoint inventory contains an unreadable bundle";
                return false;
            }
            const auto bundle = Json::parse(bundle_json.begin(), bundle_json.end());
            const auto &checkpoint = bundle.at("checkpoint");
            const auto &payload = checkpoint.at("payload");
            if (payload.value("run_id", "") != journal_id) continue;
            const auto checkpoint_id = payload.at("checkpoint_id").get<std::string>();
            std::string verified;
            if (!read_checkpoint_unlocked(checkpoint_id, verified, detail)) return false;
            const auto &validation = bundle.at("validation");
            state.committed_checkpoints.push_back(
                {checkpoint_id, runtime::authority_contracts::sha256_hex(checkpoint.dump()),
                 runtime::authority_contracts::sha256_hex(validation.dump()),
                 payload.at("state_schema_generation").get<std::string>()});
        }
        if (error) {
            detail = "native ArtifactLedger checkpoint inventory cannot be enumerated";
            return false;
        }
        auto &checkpoints = state.committed_checkpoints;
        std::sort(checkpoints.begin(), checkpoints.end(),
                  [](const auto &left, const auto &right) {
                      return left.checkpoint_id < right.checkpoint_id;
                  });
        if (std::adjacent_find(checkpoints.begin(), checkpoints.end(),
                               [](const auto &left, const auto &right) {
                                   return left.checkpoint_id == right.checkpoint_id;
                               }) != checkpoints.end()) {
            detail = "native ArtifactLedger checkpoint inventory has duplicate identities";
            return false;
        }
    } catch (const Json::exception &) {
        detail = "native ArtifactLedger checkpoint inventory is not canonical JSON";
        return false;
    }
    return true;
}

bool RuntimeFileArtifactLedgerStore::put_artifact(std::string_view bytes,
                                                  std::string_view media_type,
                                                  std::string_view retention_class,
                                                  std::string &digest,
                                                  std::string &retrieval_location,
                                                  std::string &detail) {
    if (!authorize("artifact", detail)) return false;
    if (bytes.empty() || media_type.empty() || retention_class.empty()) {
        detail = "native ArtifactLedger artifact content metadata is required";
        return false;
    }
    if (!role_can_write_artifact_media(access_.role, media_type)) {
        detail = "ArtifactLedger role is not authorized for artifact media type " +
                 std::string(media_type);
        return false;
    }
    digest = runtime::authority_contracts::sha256_hex(bytes);
    if (digest.size() != 64U) {
        detail = "native ArtifactLedger artifact digest is invalid";
        return false;
    }
    std::lock_guard lock(mutex_);
    std::error_code error;
    std::filesystem::create_directories(root_ / "blobs", error);
    if (error) {
        detail = "native ArtifactLedger blob directory creation failed";
        return false;
    }
    const auto data_path = root_ / "blobs" / (digest + ".data");
    const auto meta_path = root_ / "blobs" / (digest + ".json");
    const auto metadata = Json{{"digest", digest},
                               {"media_type", media_type},
                               {"retention_class", retention_class},
                               {"size", bytes.size()}};
    if (!record_audit("intent.put_artifact", digest, digest, detail)) return false;
    if (std::filesystem::exists(data_path) || std::filesystem::exists(meta_path)) {
        if (!verify_artifact(digest, bytes.size(), media_type, retention_class, detail))
            return false;
    } else {
        if (!durable_write(data_path, bytes, detail))
            return false;
        if (!durable_write(meta_path, metadata.dump(), detail)) {
            std::error_code ignored;
            std::filesystem::remove(data_path, ignored);
            return false;
        }
    }
    retrieval_location = "ledger://blob-" + digest;
    return record_audit("outcome.put_artifact", digest, digest, detail);
}

bool RuntimeFileArtifactLedgerStore::verify_artifact(std::string_view digest, std::size_t size,
                                                     std::string_view media_type,
                                                     std::string_view retention_class,
                                                     std::string &detail) const {
    std::string bytes;
    std::string metadata_bytes;
    if (!read_text(root_ / "blobs" / (std::string(digest) + ".data"), bytes) ||
        !read_text(root_ / "blobs" / (std::string(digest) + ".json"), metadata_bytes)) {
        detail = "native ArtifactLedger referenced blob is absent";
        return false;
    }
    try {
        const auto metadata = Json::parse(metadata_bytes.begin(), metadata_bytes.end());
        if (metadata.dump() != metadata_bytes || metadata.value("digest", "") != digest ||
            metadata.value("media_type", "") != media_type ||
            metadata.value("retention_class", "") != retention_class ||
            metadata.value("size", std::numeric_limits<std::size_t>::max()) != size ||
            runtime::authority_contracts::sha256_hex(bytes) != digest) {
            detail = "native ArtifactLedger referenced blob integrity failure";
            return false;
        }
    } catch (const Json::exception &) {
        detail = "native ArtifactLedger blob metadata is not canonical JSON";
        return false;
    }
    return true;
}

bool RuntimeFileArtifactLedgerStore::verify_admission_artifacts_unlocked(
    std::string_view receipt_payload_json, std::string &detail) const {
    try {
        const auto receipt_payload = Json::parse(receipt_payload_json.begin(), receipt_payload_json.end());
        const auto &artifacts = receipt_payload.at("inputs").at("artifacts");
        const auto verify_authority_blob = [&](const std::string &digest,
                                               const std::string &media_type,
                                               const char *label) {
            std::string metadata_bytes;
            if (!read_text(root_ / "blobs" / (digest + ".json"), metadata_bytes)) {
                detail = std::string("native ArtifactLedger admitted ") + label +
                         " blob is absent";
                return false;
            }
            const auto metadata = Json::parse(metadata_bytes);
            if (metadata.value("media_type", "") != media_type ||
                metadata.value("retention_class", "") != "active-release" ||
                !verify_artifact(digest, metadata.at("size").get<std::size_t>(), media_type,
                                 "active-release", detail)) {
                detail = std::string("native ArtifactLedger admitted ") + label +
                         " blob is not durable";
                return false;
            }
            return true;
        };
        if (!verify_authority_blob(
                artifacts.at("resolved_execution_plan").get<std::string>(),
                "application/vnd.echelon-forge.resolved-execution-plan.v1+json", "execution plan") ||
            !verify_authority_blob(
                artifacts.at("request").get<std::string>(),
                "application/vnd.echelon-forge.runtime-composition-request.v1+json", "request"))
            return false;
    } catch (const std::exception &) {
        detail = "native ArtifactLedger admission artifact references are invalid";
        return false;
    }
    return true;
}

bool RuntimeFileArtifactLedgerStore::verify_checkpoint_commit_intent_unlocked(
    const std::string &checkpoint_json, const std::string &validation_json,
    std::string &detail) const {
    try {
        const auto checkpoint = Json::parse(checkpoint_json);
        const auto validation = Json::parse(validation_json);
        const auto &payload = checkpoint.at("payload");
        const auto run_id = payload.at("run_id").get<std::string>();
        const auto checkpoint_id = payload.at("checkpoint_id").get<std::string>();
        const auto transfer_text = payload.at("transfer_fence_sequence").get<std::string>();
        const auto writer_text = payload.at("writer_generation").get<std::string>();
        std::size_t transfer_chars = 0U;
        std::size_t writer_chars = 0U;
        const auto transfer_fence = std::stoull(transfer_text, &transfer_chars);
        const auto writer_generation = std::stoull(writer_text, &writer_chars);
        if (transfer_chars != transfer_text.size() || writer_chars != writer_text.size() ||
            transfer_fence == 0U || writer_generation == 0U) {
            detail = "native ArtifactLedger checkpoint commit intent sequence is invalid";
            return false;
        }
        const auto journal_directory = stream_path("journal:" + run_id);
        std::string fence_bytes;
        if (!read_text(fence_path("journal:" + run_id), fence_bytes)) {
            detail = "native ArtifactLedger checkpoint owning fence is absent";
            return false;
        }
        const auto current_fence = Json::parse(fence_bytes);
        const auto current_generation = current_fence.at("generation").get<std::uint64_t>();
        std::uint64_t next_sequence = 0U;
        std::string tail_digest;
        if (!scan_journal(journal_directory, run_id, current_generation, next_sequence, tail_digest,
                          detail) ||
            transfer_fence >= next_sequence) {
            if (detail.empty()) detail = "native ArtifactLedger checkpoint intent is outside the journal";
            return false;
        }
        std::string frame_bytes;
        if (!read_text(journal_directory / ("frame-" + std::to_string(transfer_fence) + ".json"),
                       frame_bytes)) {
            detail = "native ArtifactLedger checkpoint commit intent is absent";
            return false;
        }
        const auto frame = Json::parse(frame_bytes);
        if (frame.at("fence_generation").get<std::uint64_t>() != writer_generation) {
            detail = "native ArtifactLedger checkpoint intent writer generation differs";
            return false;
        }
        std::string intent_bytes;
        if (!hex_decode(frame.at("payload_hex").get<std::string>(), intent_bytes)) {
            detail = "native ArtifactLedger checkpoint commit intent is not decodable";
            return false;
        }
        const auto intent = Json::parse(intent_bytes);
        const auto canonical_checkpoint =
            runtime::authority_contracts::canonical_authority_json(checkpoint.dump());
        const auto canonical_validation =
            runtime::authority_contracts::canonical_authority_json(validation.dump());
        if (!canonical_checkpoint.has_value() || !canonical_validation.has_value() ||
            !intent.is_object() || intent.value("event", "") != "checkpoint_commit" ||
            intent.value("checkpoint_id", "") != checkpoint_id ||
            intent.value("checkpoint_sha256", "") !=
                runtime::authority_contracts::sha256_hex(*canonical_checkpoint) ||
            intent.value("validation_sha256", "") !=
                runtime::authority_contracts::sha256_hex(*canonical_validation) ||
            intent.value("transfer_fence_sequence", "") != transfer_text) {
            detail = "native ArtifactLedger checkpoint commit intent does not bind the bundle";
            return false;
        }
    } catch (const std::exception &) {
        detail = "native ArtifactLedger checkpoint commit intent is invalid";
        return false;
    }
    return true;
}

bool RuntimeFileArtifactLedgerStore::read_checkpoint_unlocked(std::string_view checkpoint_id,
                                                              std::string &bundle_json,
                                                              std::string &detail) const {
    if (!read_text(root_ / "checkpoints" / token_name(checkpoint_id) / "bundle.json",
                   bundle_json)) {
        detail = "native ArtifactLedger checkpoint is absent";
        return false;
    }
    try {
        const auto bundle = Json::parse(bundle_json.begin(), bundle_json.end());
        if (!bundle.is_object() || bundle.size() != 2U || bundle.dump() != bundle_json ||
            !bundle.contains("checkpoint") || !bundle.contains("validation")) {
            detail = "native ArtifactLedger checkpoint bundle is not canonical";
            return false;
        }
        const auto &checkpoint = bundle.at("checkpoint");
        const auto &payload = checkpoint.at("payload");
        if (payload.at("checkpoint_id").get<std::string>() != checkpoint_id) {
            detail = "native ArtifactLedger checkpoint identity differs";
            return false;
        }
        const auto canonical_payload =
            runtime::authority_contracts::canonical_authority_json(payload.dump());
        if (!canonical_payload.has_value() ||
            !runtime::authority_contracts::validate_authority_envelope_json(
                 checkpoint.dump(), *canonical_payload)
                 .valid) {
            detail = "native ArtifactLedger checkpoint authority is invalid";
            return false;
        }
        const auto &validation = bundle.at("validation");
        std::string state_payload;
        if (!validation.value("accepted", false) ||
            validation.value("checkpoint_id", "") != checkpoint_id ||
            !validation.contains("aggregate_replay_sha256") ||
            !validation.contains("validator_id") ||
            runtime::authority_contracts::canonical_authority_json(validation.dump()).value_or("") !=
                validation.dump() ||
            !hex_decode(validation.value("state_payload_hex", ""), state_payload) ||
            validation.value("state_sha256", "") !=
                runtime::authority_contracts::sha256_hex(state_payload) ||
            validation.value("state_sha256", "") != payload.value("aggregate_state_sha256", "") ||
            validation.value("aggregate_replay_sha256", "") !=
                runtime::authority_contracts::checkpoint_replay_aggregate_sha256(payload.dump())
                    .value_or("")) {
            detail = "native ArtifactLedger checkpoint validation is invalid";
            return false;
        }
        const auto run_id = payload.at("run_id").get<std::string>();
        std::string header_bytes;
        if (!read_text(stream_path("journal:" + run_id) / "header.json", header_bytes)) {
            detail = "native ArtifactLedger checkpoint owning journal header is absent";
            return false;
        }
        const auto header = Json::parse(header_bytes.begin(), header_bytes.end());
        std::string header_detail;
        if (!validate_runtime_run_header_json(run_id, header_bytes, header_detail)) {
            detail = "native ArtifactLedger checkpoint owning header is invalid: " + header_detail;
            return false;
        }
        const auto &bindings = header.at("receipt_bindings");
        const auto release = Json::parse(
            bindings.at("release_manifest_envelope_json").get<std::string>());
        if (payload.at("state_schema_generation") !=
            release.at("payload").at("state_schema_generation")) {
            detail = "native ArtifactLedger checkpoint state schema differs from owning release";
            return false;
        }
        if (payload.at("plan_sha256") != bindings.at("plan_binding").at("plan_sha256") ||
            payload.at("release_id") != bindings.at("release_binding").at("release_id") ||
            payload.at("decision_id") !=
                bindings.at("release_binding").at("rollout_decision_id") ||
            payload.at("target_reader_generation_min") !=
                bindings.at("reader_generation_min") ||
            payload.at("target_reader_generation_max") !=
                bindings.at("reader_generation_max")) {
            detail = "native ArtifactLedger checkpoint differs from owning admission bindings";
            return false;
        }
        if (!verify_checkpoint_commit_intent_unlocked(checkpoint.dump(), validation.dump(), detail))
            return false;
    } catch (const Json::exception &) {
        detail = "native ArtifactLedger checkpoint bundle is not JSON";
        return false;
    }
    return true;
}

bool RuntimeFileArtifactLedgerStore::validate_checkpoint_reference_unlocked(
    const std::string &reference_json, const std::string &receipt_payload_json, bool created,
    std::string &detail) const {
    try {
        const auto reference = Json::parse(reference_json);
        const auto receipt = Json::parse(receipt_payload_json);
        const auto checkpoint_id = reference.at("checkpoint_id").get<std::string>();
        std::string bundle_json;
        if (!read_checkpoint_unlocked(checkpoint_id, bundle_json, detail)) return false;
        const auto bundle = Json::parse(bundle_json);
        const auto &checkpoint = bundle.at("checkpoint");
        const auto &payload = checkpoint.at("payload");
        const auto &validation = bundle.at("validation");
        if (reference.at("checkpoint_sha256") !=
                runtime::authority_contracts::sha256_hex(checkpoint.dump()) ||
            reference.at("validation_sha256") !=
                runtime::authority_contracts::sha256_hex(validation.dump()) ||
            reference.at("state_schema_generation") !=
                payload.at("state_schema_generation") ||
            reference.at("retrieval_location") != "ledger://checkpoint-" + checkpoint_id ||
            payload.at("plan_sha256") != receipt.at("plan_binding").at("plan_sha256") ||
            payload.at("release_id") != receipt.at("release_binding").at("release_id") ||
            payload.at("decision_id") !=
                receipt.at("release_binding").at("rollout_decision_id") ||
            payload.at("target_reader_generation_min") !=
                receipt.at("reader_generation_min") ||
            payload.at("target_reader_generation_max") !=
                receipt.at("reader_generation_max")) {
            detail = "native ArtifactLedger checkpoint reference differs from durable bundle";
            return false;
        }
        if (created &&
            (payload.at("run_id") != receipt.at("run_id") ||
             payload.at("host_boot_id") != receipt.at("host_boot_id") ||
             payload.at("incarnation_epoch") != receipt.at("incarnation_epoch"))) {
            detail = "created checkpoint differs from receipt run/boot/incarnation";
            return false;
        }
        const auto &scope = receipt.at("execution_scope");
        for (const auto &fragment : payload.at("world_fragments")) {
            if (std::find(scope.at("world_ids").begin(), scope.at("world_ids").end(),
                          fragment.at("world_id")) == scope.at("world_ids").end()) {
                detail = "checkpoint world is outside receipt execution scope";
                return false;
            }
            for (const auto &episode_id : fragment.at("episode_ids")) {
                if (std::find(scope.at("episode_ids").begin(), scope.at("episode_ids").end(),
                              episode_id) == scope.at("episode_ids").end()) {
                    detail = "checkpoint episode is outside receipt execution scope";
                    return false;
                }
            }
        }
        const auto fence = std::stoull(payload.at("transfer_fence_sequence").get<std::string>());
        if (fence == 0U || fence > receipt.at("journal_last_sequence").get<std::uint64_t>()) {
            detail = "checkpoint transfer fence is outside the durable journal tail";
            return false;
        }
    } catch (const std::exception &) {
        detail = "native ArtifactLedger checkpoint reference is invalid";
        return false;
    }
    return true;
}

bool RuntimeFileArtifactLedgerStore::validate_receipt_checkpoints_unlocked(
    const std::string &receipt_payload_json, std::uint64_t writer_generation,
    std::string &detail) const {
    (void)writer_generation;
    try {
        const auto receipt = Json::parse(receipt_payload_json);
        std::set<std::string> referenced_created;
        for (const auto collection_name : {"source_refs", "created_refs"}) {
            const bool created = std::string_view(collection_name) == "created_refs";
            for (const auto &reference : receipt.at("checkpoints").at(collection_name)) {
                if (!validate_checkpoint_reference_unlocked(reference.dump(), receipt_payload_json,
                                                            created, detail))
                    return false;
                if (created)
                    referenced_created.insert(
                        reference.at("checkpoint_id").get<std::string>());
            }
        }
        std::set<std::string> committed_created;
        std::error_code error;
        for (const auto &entry : std::filesystem::directory_iterator(root_ / "checkpoints", error)) {
            if (error) break;
            if (!entry.is_directory(error) || error) continue;
            std::string bundle_json;
            if (!read_text(entry.path() / "bundle.json", bundle_json)) continue;
            const auto bundle = Json::parse(bundle_json);
            const auto &payload = bundle.at("checkpoint").at("payload");
            if (payload.at("run_id") == receipt.at("run_id"))
                committed_created.insert(payload.at("checkpoint_id").get<std::string>());
        }
        if (error || committed_created != referenced_created) {
            detail = "receipt created checkpoint refs do not equal durable run checkpoints";
            return false;
        }
    } catch (const Json::exception &) {
        detail = "native ArtifactLedger receipt checkpoint collection is invalid";
        return false;
    }
    return true;
}

bool RuntimeFileArtifactLedgerStore::backup_to(const std::filesystem::path &target,
                                               std::string &detail) const {
    if (!authorize("backup", detail)) return false;
    std::lock_guard lock(mutex_);
    const auto root_absolute = std::filesystem::absolute(root_).lexically_normal();
    const auto target_absolute = std::filesystem::absolute(target).lexically_normal();
    const auto relative = target_absolute.lexically_relative(root_absolute);
    const bool target_inside_root = relative.empty() ||
                                    (!relative.has_root_name() && relative.begin() != relative.end() &&
                                     *relative.begin() != "..");
    if (target.empty() || target_inside_root) {
        detail = "native ArtifactLedger backup target must differ from the live root";
        return false;
    }
    if (std::filesystem::exists(target)) {
        detail = "native ArtifactLedger backup target already exists";
        return false;
    }
    const auto backup_digest = runtime::authority_contracts::sha256_hex(target.generic_string());
    if (!record_audit("intent.backup", target.generic_string(), backup_digest, detail) ||
        !copy_tree_without_lock(root_, target, detail))
        return false;
    return record_audit("outcome.backup", target.generic_string(), backup_digest, detail);
}

bool RuntimeFileArtifactLedgerStore::availability_report(std::string &report_json,
                                                         std::string &detail) const {
    if (!authorize("availability", detail)) return false;
    std::lock_guard lock(mutex_);
    try {
        std::size_t audit_events = 0;
        std::string audit_tail;
        if (!verify_audit_chain(audit_events, audit_tail, detail)) return false;
        std::size_t journal_count = 0;
        std::size_t receipt_count = 0;
        std::size_t checkpoint_count = 0;
        std::size_t blob_count = 0;
        std::error_code error;
        for (const auto &entry : std::filesystem::directory_iterator(root_ / "journals", error)) {
            if (error) break;
            if (!entry.is_directory(error) || error) continue;
            std::string header_bytes;
            if (!read_text(entry.path() / "header.json", header_bytes)) {
                detail = "ArtifactLedger availability audit found a missing journal header";
                return false;
            }
            const auto header = Json::parse(header_bytes);
            const auto run_id = header.at("run_id").get<std::string>();
            if (!validate_runtime_run_header_json(run_id, header_bytes, detail)) return false;
            std::string fence_bytes;
            if (!read_text(fence_path("journal:" + run_id), fence_bytes)) return false;
            const auto generation =
                Json::parse(fence_bytes).at("generation").get<std::uint64_t>();
            std::uint64_t next = 0;
            std::string tail;
            if (!scan_journal(entry.path(), run_id, generation, next, tail, detail)) return false;
            ++journal_count;
            std::string receipt_bytes;
            if (!read_text(entry.path() / "receipt.json", receipt_bytes)) continue;
            if (!validate_runtime_run_receipt_json(receipt_bytes, detail)) return false;
            const auto receipt = Json::parse(receipt_bytes);
            const auto &payload = receipt.at("payload");
            if (!receipt_matches_header(payload, header, detail) || next == 0U ||
                !verify_admission_artifacts_unlocked(payload.dump(), detail) ||
                payload.at("journal_last_sequence") != next - 1U ||
                payload.at("journal_last_record_sha256") != tail ||
                !validate_receipt_checkpoints_unlocked(payload.dump(), generation, detail))
                return false;
            for (const auto &artifact : payload.at("results").at("output_artifacts")) {
                if (!verify_artifact(artifact.at("digest").get<std::string>(),
                                     artifact.at("size").get<std::size_t>(),
                                     artifact.at("media_type").get<std::string>(),
                                     artifact.at("retention_class").get<std::string>(), detail))
                    return false;
            }
            ++receipt_count;
        }
        if (error) return false;
        for (const auto &entry :
             std::filesystem::directory_iterator(root_ / "checkpoints", error)) {
            if (error) break;
            if (!entry.is_directory(error) || error) continue;
            std::string bundle_bytes;
            if (!read_text(entry.path() / "bundle.json", bundle_bytes)) return false;
            const auto checkpoint_id = Json::parse(bundle_bytes)
                                           .at("checkpoint")
                                           .at("payload")
                                           .at("checkpoint_id")
                                           .get<std::string>();
            if (!read_checkpoint_unlocked(checkpoint_id, bundle_bytes, detail)) return false;
            ++checkpoint_count;
        }
        if (error) return false;
        for (const auto &entry : std::filesystem::directory_iterator(root_ / "blobs", error)) {
            if (error) break;
            if (entry.path().extension() != ".json") continue;
            std::string metadata_bytes;
            if (!read_text(entry.path(), metadata_bytes)) return false;
            const auto metadata = Json::parse(metadata_bytes);
            if (!verify_artifact(metadata.at("digest").get<std::string>(),
                                 metadata.at("size").get<std::size_t>(),
                                 metadata.at("media_type").get<std::string>(),
                                 metadata.at("retention_class").get<std::string>(), detail))
                return false;
            ++blob_count;
        }
        if (error) return false;
        bool private_root = false;
#ifdef _WIN32
        PSECURITY_DESCRIPTOR descriptor = nullptr;
        PACL dacl = nullptr;
        const auto root_path = root_.wstring();
        const auto security_error = GetNamedSecurityInfoW(
            const_cast<LPWSTR>(root_path.c_str()), SE_FILE_OBJECT, DACL_SECURITY_INFORMATION,
            nullptr, nullptr, &dacl, nullptr, &descriptor);
        SECURITY_DESCRIPTOR_CONTROL control = 0;
        DWORD revision = 0;
        private_root = security_error == ERROR_SUCCESS && descriptor != nullptr && dacl != nullptr &&
                       GetSecurityDescriptorControl(descriptor, &control, &revision) != FALSE &&
                       (control & SE_DACL_PROTECTED) != 0;
        if (descriptor != nullptr) LocalFree(descriptor);
#else
        struct stat root_stat {};
        private_root = ::stat(root_.c_str(), &root_stat) == 0 &&
                       (root_stat.st_mode & (S_IRWXG | S_IRWXO)) == 0;
#endif
        if (!private_root) {
            detail = "ArtifactLedger root permissions are not private";
            return false;
        }
        const Json report = {{"audit_event_count", audit_events},
                             {"audit_tail_sha256", audit_tail},
                             {"available", true},
                             {"blob_count", blob_count},
                             {"checkpoint_count", checkpoint_count},
                             {"hash_correct", true},
                             {"journal_count", journal_count},
                             {"private_root", true},
                             {"receipt_count", receipt_count}};
        report_json =
            runtime::authority_contracts::canonical_authority_json(report.dump()).value();
        return true;
    } catch (const std::exception &error) {
        detail = std::string("ArtifactLedger availability audit failed: ") + error.what();
        return false;
    }
}

bool RuntimeFileArtifactLedgerStore::restore_from(const std::filesystem::path &source,
                                                  const std::filesystem::path &target,
                                                  const RuntimeArtifactLedgerAccessContext &access,
                                                  std::string &detail) {
    if (access.role != RuntimeArtifactLedgerRole::BackupOperator ||
        access.audit_identity.empty()) {
        detail = "ArtifactLedger restore requires a backup-operator audit identity";
        return false;
    }
    if (source.empty() || target.empty() ||
        std::filesystem::absolute(source) == std::filesystem::absolute(target) ||
        !std::filesystem::is_directory(source) || std::filesystem::exists(target)) {
        detail = "native ArtifactLedger restore source/target is invalid";
        return false;
    }
    if (!copy_tree_without_lock(source, target, detail)) {
        std::error_code ignored;
        std::filesystem::remove_all(target, ignored);
        return false;
    }
    try {
        RuntimeFileArtifactLedgerStore restored(target, access);
        const auto fail_restore = [&]() -> bool {
            throw std::runtime_error(detail.empty()
                                         ? "native ArtifactLedger restore verification failed"
                                         : detail);
        };
        for (const auto &entry : std::filesystem::directory_iterator(target / "journals")) {
            if (!entry.is_directory()) continue;
            std::string header_bytes;
            if (!read_text(entry.path() / "header.json", header_bytes)) {
                detail = "native ArtifactLedger restore journal header is absent";
                return fail_restore();
            }
            const auto header = Json::parse(header_bytes.begin(), header_bytes.end());
            const auto journal_id = header.at("run_id").get<std::string>();
            std::string fence_bytes;
            if (!read_text(restored.fence_path("journal:" + journal_id), fence_bytes))
                return fail_restore();
            const auto fence = Json::parse(fence_bytes.begin(), fence_bytes.end());
            const auto expected_generation = fence.at("generation").get<std::uint64_t>();
            std::uint64_t next = 0;
            std::string tail;
            if (!restored.scan_journal(entry.path(), journal_id, expected_generation, next, tail,
                                       detail))
                return fail_restore();
            if (std::filesystem::exists(entry.path() / "receipt.json")) {
                std::string receipt;
                if (!restored.read_receipt(journal_id, receipt, detail)) return fail_restore();
            }
        }
        for (const auto &entry : std::filesystem::directory_iterator(target / "checkpoints")) {
            if (!entry.is_directory()) continue;
            std::string bundle;
            if (!read_text(entry.path() / "bundle.json", bundle)) return fail_restore();
            const auto parsed = Json::parse(bundle.begin(), bundle.end());
            if (!parsed.is_object() || parsed.dump() != bundle || !parsed.contains("checkpoint") ||
                !parsed.contains("validation"))
                return fail_restore();
            const auto &checkpoint = parsed.at("checkpoint");
            const auto checkpoint_id = checkpoint.at("payload").at("checkpoint_id").get<std::string>();
            std::string verified;
            if (!restored.read_checkpoint(checkpoint_id, verified, detail)) return fail_restore();
        }
        for (const auto &entry : std::filesystem::directory_iterator(target / "blobs")) {
            if (entry.path().extension() != ".json") continue;
            const auto digest = entry.path().stem().string();
            std::string metadata_bytes;
            if (!read_text(entry.path(), metadata_bytes)) return fail_restore();
            const auto metadata = Json::parse(metadata_bytes.begin(), metadata_bytes.end());
            if (metadata.value("digest", "") != digest) return fail_restore();
            std::string blob_detail;
            if (!restored.verify_artifact(digest, metadata.at("size").get<std::size_t>(),
                                          metadata.at("media_type").get<std::string>(),
                                          metadata.at("retention_class").get<std::string>(),
                                          blob_detail)) {
                detail = blob_detail;
                return fail_restore();
            }
        }
        if (!restored.record_audit("restore", source.generic_string(),
                                   runtime::authority_contracts::sha256_hex(
                                       source.generic_string()),
                                   detail))
            return fail_restore();
        return true;
    } catch (const std::exception &error) {
        detail = std::string("native ArtifactLedger restore verification failed: ") + error.what();
    }
    std::error_code ignored;
    std::filesystem::remove_all(target, ignored);
    return false;
}

bool RuntimeFileArtifactLedgerStore::read_receipt(std::string_view journal_id,
                                                  std::string &receipt_json,
                                                  std::string &detail) const {
    if (!authorize("receipt_read", detail)) return false;
    std::lock_guard lock(mutex_);
    if (!read_text(stream_path("journal:" + std::string(journal_id)) / "receipt.json",
                   receipt_json)) {
        detail = "native ArtifactLedger receipt is absent";
        return false;
    }
    if (!validate_runtime_run_receipt_json(receipt_json, detail)) return false;
    try {
        const auto receipt = Json::parse(receipt_json.begin(), receipt_json.end());
        const auto canonical = runtime::authority_contracts::canonical_authority_json(receipt_json);
        if (!canonical.has_value() || *canonical != receipt_json ||
            !receipt.is_object() || receipt.size() != 7U ||
            receipt.value("domain", "") != "runtime.run-receipt" ||
            receipt.value("media_type", "") !=
                "application/vnd.echelon-forge.run-receipt.v1+json" ||
            receipt.at("payload_sha256") != runtime::authority_contracts::authority_digest_sha256_hex(
                "runtime.run-receipt", "application/vnd.echelon-forge.run-receipt.v1+json",
                runtime::authority_contracts::canonical_authority_json(
                    receipt.at("payload").dump())
                    .value())) {
            detail = "native ArtifactLedger stored receipt envelope is invalid";
            return false;
        }
        const auto &payload = receipt.at("payload");
        if (payload.at("run_id").get<std::string>() != journal_id ||
            payload.at("journal_id").get<std::string>() != journal_id) {
            detail = "native ArtifactLedger stored receipt identity differs";
            return false;
        }
        std::string header_bytes;
        if (!read_text(stream_path("journal:" + std::string(journal_id)) / "header.json",
                       header_bytes) ||
            !validate_runtime_run_header_json(journal_id, header_bytes, detail) ||
            !receipt_matches_header(payload, Json::parse(header_bytes), detail))
            return false;
        if (!verify_admission_artifacts_unlocked(payload.dump(), detail)) return false;
        const auto fence = Json::parse(
            [&] { std::string value; read_text(fence_path("journal:" + std::string(journal_id)), value); return value; }());
        std::uint64_t next = 0;
        std::string tail;
        if (!scan_journal(stream_path("journal:" + std::string(journal_id)), journal_id,
                          fence.at("generation").get<std::uint64_t>(), next, tail, detail) ||
            payload.at("journal_last_sequence") != next - 1U ||
            payload.at("journal_last_record_sha256") != tail) {
            detail = "native ArtifactLedger stored receipt does not bind journal tail";
            return false;
        }
        if (!validate_receipt_checkpoints_unlocked(
                payload.dump(), fence.at("generation").get<std::uint64_t>(), detail))
            return false;
        if (payload.at("terminal_state") == "completed") {
            for (const auto &artifact : payload.at("results").at("output_artifacts")) {
                if (artifact.at("retrieval_location").get<std::string>() !=
                        "ledger://blob-" + artifact.at("digest").get<std::string>() ||
                    !verify_artifact(artifact.at("digest").get<std::string>(),
                                     artifact.at("size").get<std::size_t>(),
                                     artifact.at("media_type").get<std::string>(),
                                     artifact.at("retention_class").get<std::string>(), detail))
                    return false;
            }
        }
    } catch (const Json::exception &) {
        detail = "native ArtifactLedger stored receipt is not canonical JSON";
        return false;
    }
    return true;
}

bool RuntimeFileArtifactLedgerStore::read_checkpoint(std::string_view checkpoint_id,
                                                     std::string &bundle_json,
                                                     std::string &detail) const {
    if (!authorize("checkpoint_read", detail)) return false;
    std::lock_guard lock(mutex_);
    return read_checkpoint_unlocked(checkpoint_id, bundle_json, detail);
}

} // namespace runtime::host
