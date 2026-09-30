#include "runtime_state_transfer_candidate.h"

#include <algorithm>
#include <array>
#include <atomic>
#include <bit>
#include <chrono>
#include <cstdio>
#include <fcntl.h>
#include <fstream>
#include <iomanip>
#include <limits>
#include <mutex>
#include <random>
#include <sstream>
#include <thread>
#include <utility>

#ifdef _WIN32
#include <io.h>
#include <share.h>
#include <sys/stat.h>
#else
#include <unistd.h>
#include <sys/file.h>
#endif

namespace runtime::host {

namespace {

constexpr std::size_t kMaxTransitionReceipts = 4096;

RuntimeStateTransferStatus success() {
    return {};
}

RuntimeStateTransferStatus failure(RuntimeStateTransferError error, std::string detail) {
    return {.error = error, .detail = std::move(detail)};
}

bool is_lower_hex_sha256(std::string_view value) {
    return value.size() == 64 &&
           std::all_of(value.begin(), value.end(), [](unsigned char character) {
               return (character >= '0' && character <= '9') ||
                      (character >= 'a' && character <= 'f');
           });
}

std::string sha256_hex(std::string_view input);

std::string hex_encode(const std::vector<std::uint8_t> &bytes) {
    static constexpr char digits[] = "0123456789abcdef";
    std::string encoded;
    encoded.reserve(bytes.size() * 2);
    for (const std::uint8_t byte : bytes) {
        encoded.push_back(digits[byte >> 4]);
        encoded.push_back(digits[byte & 0x0fU]);
    }
    return encoded;
}

bool hex_decode(std::string_view encoded, std::vector<std::uint8_t> *bytes) {
    if (bytes == nullptr || encoded.size() % 2 != 0) {
        return false;
    }
    const auto nibble = [](char value) -> int {
        if (value >= '0' && value <= '9') {
            return value - '0';
        }
        if (value >= 'a' && value <= 'f') {
            return value - 'a' + 10;
        }
        return -1;
    };
    std::vector<std::uint8_t> decoded;
    decoded.reserve(encoded.size() / 2);
    for (std::size_t index = 0; index < encoded.size(); index += 2) {
        const int high = nibble(encoded[index]);
        const int low = nibble(encoded[index + 1]);
        if (high < 0 || low < 0) {
            return false;
        }
        decoded.push_back(static_cast<std::uint8_t>((high << 4) | low));
    }
    *bytes = std::move(decoded);
    return true;
}

std::string_view journal_phase_name(RuntimeStateOwnerImportTransactionPhase phase) noexcept {
    switch (phase) {
    case RuntimeStateOwnerImportTransactionPhase::Prepared:
        return "prepared";
    case RuntimeStateOwnerImportTransactionPhase::Committing:
        return "committing";
    case RuntimeStateOwnerImportTransactionPhase::Committed:
        return "committed";
    case RuntimeStateOwnerImportTransactionPhase::Aborting:
        return "aborting";
    case RuntimeStateOwnerImportTransactionPhase::Aborted:
        return "aborted";
    case RuntimeStateOwnerImportTransactionPhase::Ambiguous:
        return "ambiguous";
    }
    return "unsupported";
}

std::optional<RuntimeStateOwnerImportTransactionPhase>
parse_journal_phase(std::string_view value) noexcept {
    constexpr std::array<std::pair<std::string_view, RuntimeStateOwnerImportTransactionPhase>, 6>
        phases = {{{"prepared", RuntimeStateOwnerImportTransactionPhase::Prepared},
                   {"committing", RuntimeStateOwnerImportTransactionPhase::Committing},
                   {"committed", RuntimeStateOwnerImportTransactionPhase::Committed},
                   {"aborting", RuntimeStateOwnerImportTransactionPhase::Aborting},
                   {"aborted", RuntimeStateOwnerImportTransactionPhase::Aborted},
                   {"ambiguous", RuntimeStateOwnerImportTransactionPhase::Ambiguous}}};
    const auto position = std::find_if(phases.begin(), phases.end(),
                                       [value](const auto &entry) { return entry.first == value; });
    return position == phases.end()
               ? std::nullopt
               : std::optional<RuntimeStateOwnerImportTransactionPhase>(position->second);
}

std::string journal_record_body(std::uint64_t sequence, std::string_view transaction_id,
                                RuntimeStateOwnerImportTransactionPhase phase,
                                std::string_view payload_sha256,
                                std::string_view pre_mutation_sha256 = {},
                                const std::vector<std::uint8_t> &pre_mutation_payload = {}) {
    std::string body;
    body.reserve(64 + transaction_id.size() + payload_sha256.size());
    body.append(std::to_string(sequence));
    body.push_back('\t');
    body.append(transaction_id);
    body.push_back('\t');
    body.append(journal_phase_name(phase));
    body.push_back('\t');
    body.append(payload_sha256);
    body.push_back('\t');
    body.append(pre_mutation_sha256);
    body.push_back('\t');
    body.append(hex_encode(pre_mutation_payload));
    return body;
}

bool valid_journal_component(std::string_view value) noexcept {
    return !value.empty() && value.find_first_of("\t\r\n") == std::string_view::npos;
}

bool parse_journal_record_line(std::string_view line, RuntimeStateTransferJournalRecord &record) {
    std::array<std::string_view, 7> fields{};
    std::size_t field_count = 0;
    std::size_t start = 0;
    while (start <= line.size() && field_count < fields.size()) {
        const std::size_t delimiter = line.find('\t', start);
        const std::size_t end = delimiter == std::string_view::npos ? line.size() : delimiter;
        fields[field_count++] = line.substr(start, end - start);
        if (delimiter == std::string_view::npos) {
            break;
        }
        if (field_count == fields.size()) {
            return false;
        }
        start = delimiter + 1;
    }
    if ((field_count != 5 && field_count != 7) || fields[0].empty() || fields[1].empty() ||
        fields[2].empty() || !is_lower_hex_sha256(fields[3]) ||
        (field_count == 7 && !fields[4].empty() && !is_lower_hex_sha256(fields[4])) ||
        !is_lower_hex_sha256(fields[field_count == 7 ? 6 : 4])) {
        return false;
    }
    std::uint64_t sequence = 0;
    try {
        const std::string sequence_text(fields[0]);
        std::size_t consumed = 0;
        sequence = std::stoull(sequence_text, &consumed, 10);
        if (consumed != sequence_text.size() || sequence == 0) {
            return false;
        }
    } catch (...) {
        return false;
    }
    const auto phase = parse_journal_phase(fields[2]);
    if (!phase || !valid_journal_component(fields[1])) {
        return false;
    }
    std::vector<std::uint8_t> pre_mutation_payload;
    if (field_count == 7 && !hex_decode(fields[5], &pre_mutation_payload)) {
        return false;
    }
    if (field_count == 7 &&
        ((fields[4].empty() && !pre_mutation_payload.empty()) ||
         (!fields[4].empty() &&
          sha256_hex(std::string_view(reinterpret_cast<const char *>(pre_mutation_payload.data()),
                                      pre_mutation_payload.size())) != fields[4]))) {
        return false;
    }
    const std::string body = field_count == 7
                                 ? journal_record_body(sequence, fields[1], *phase, fields[3],
                                                       fields[4], pre_mutation_payload)
                                 : [&] {
                                       std::string legacy;
                                       legacy.reserve(64 + fields[1].size() + fields[3].size());
                                       legacy.append(fields[0]);
                                       legacy.push_back('\t');
                                       legacy.append(fields[1]);
                                       legacy.push_back('\t');
                                       legacy.append(fields[2]);
                                       legacy.push_back('\t');
                                       legacy.append(fields[3]);
                                       return legacy;
                                   }();
    if (sha256_hex(body) != fields[field_count == 7 ? 6 : 4]) {
        return false;
    }
    record = {.sequence = sequence,
              .transaction_id = std::string(fields[1]),
              .phase = *phase,
              .payload_sha256 = std::string(fields[3]),
              .pre_mutation_sha256 = field_count == 7 ? std::string(fields[4]) : std::string{},
              .pre_mutation_payload = std::move(pre_mutation_payload)};
    return true;
}

bool valid_journal_transition(const std::optional<RuntimeStateTransferJournalRecord> &previous,
                              RuntimeStateOwnerImportTransactionPhase next,
                              std::string_view payload_sha256,
                              std::string_view pre_mutation_sha256 = {},
                              const std::vector<std::uint8_t> &pre_mutation_payload = {}) noexcept {
    if (!previous) {
        return next == RuntimeStateOwnerImportTransactionPhase::Prepared;
    }
    if (previous->payload_sha256 != payload_sha256 ||
        previous->pre_mutation_sha256 != pre_mutation_sha256 ||
        previous->pre_mutation_payload != pre_mutation_payload) {
        return false;
    }
    switch (previous->phase) {
    case RuntimeStateOwnerImportTransactionPhase::Prepared:
        return next == RuntimeStateOwnerImportTransactionPhase::Committing ||
               next == RuntimeStateOwnerImportTransactionPhase::Aborting ||
               next == RuntimeStateOwnerImportTransactionPhase::Aborted ||
               next == RuntimeStateOwnerImportTransactionPhase::Ambiguous;
    case RuntimeStateOwnerImportTransactionPhase::Committing:
    case RuntimeStateOwnerImportTransactionPhase::Aborting:
    case RuntimeStateOwnerImportTransactionPhase::Ambiguous:
        return next == RuntimeStateOwnerImportTransactionPhase::Committed ||
               next == RuntimeStateOwnerImportTransactionPhase::Aborted ||
               next == RuntimeStateOwnerImportTransactionPhase::Ambiguous;
    case RuntimeStateOwnerImportTransactionPhase::Committed:
        // A composite transaction may compensate a previously committed
        // child.  The owner verification path is the only caller allowed to
        // append this terminal correction after proving the target matches
        // its pre-image.
        return next == RuntimeStateOwnerImportTransactionPhase::Committed ||
               next == RuntimeStateOwnerImportTransactionPhase::Aborted;
    case RuntimeStateOwnerImportTransactionPhase::Aborted:
        // Re-affirming an already-aborted record is needed when recovery had
        // to re-run after a failed verification; it does not permit an
        // aborted transaction to become committed.
        return next == RuntimeStateOwnerImportTransactionPhase::Aborted;
    }
    return false;
}

struct JournalScanResult {
    RuntimeStateTransferStatus status;
    std::vector<RuntimeStateTransferJournalRecord> records;
    std::uint64_t next_sequence = 1;
    std::uint64_t valid_size = 0;
    std::uint64_t file_size = 0;
};

JournalScanResult scan_journal_file(const std::string &path) {
    JournalScanResult result;
    std::ifstream input(path, std::ios::binary);
    if (!input) {
        result.status = failure(RuntimeStateTransferError::ImportJournalUnavailable,
                                "state-transfer journal cannot be opened");
        return result;
    }
    const std::string bytes((std::istreambuf_iterator<char>(input)),
                            std::istreambuf_iterator<char>());
    result.file_size = static_cast<std::uint64_t>(bytes.size());
    if (!input.eof() && input.fail()) {
        result.status = failure(RuntimeStateTransferError::ImportJournalUnavailable,
                                "state-transfer journal cannot be read");
        return result;
    }
    const std::size_t complete_end = bytes.rfind('\n');
    if (complete_end == std::string::npos) {
        // No newline means no frame ever reached the durable framing
        // boundary. Treat the entire file as a torn first append and let the
        // caller truncate it to zero; a newline-terminated malformed frame is
        // still rejected below as corruption.
        return result;
    }
    result.valid_size = static_cast<std::uint64_t>(complete_end + 1);
    std::size_t start = 0;
    std::uint64_t previous_sequence = 0;
    while (start <= complete_end) {
        const std::size_t end = bytes.find('\n', start);
        if (end == std::string::npos || end > complete_end) {
            break;
        }
        if (end == start) {
            result.status = failure(RuntimeStateTransferError::ImportJournalCorrupt,
                                    "state-transfer journal contains an empty frame");
            return result;
        }
        RuntimeStateTransferJournalRecord record;
        if (!parse_journal_record_line(std::string_view(bytes).substr(start, end - start),
                                       record) ||
            record.sequence != previous_sequence + 1) {
            result.status = failure(RuntimeStateTransferError::ImportJournalCorrupt,
                                    "state-transfer journal frame integrity failed");
            return result;
        }
        const auto previous =
            std::find_if(result.records.rbegin(), result.records.rend(),
                         [&](const RuntimeStateTransferJournalRecord &candidate) {
                             return candidate.transaction_id == record.transaction_id;
                         });
        const std::optional<RuntimeStateTransferJournalRecord> previous_record =
            previous == result.records.rend()
                ? std::nullopt
                : std::optional<RuntimeStateTransferJournalRecord>(*previous);
        if (!valid_journal_transition(previous_record, record.phase, record.payload_sha256,
                                      record.pre_mutation_sha256, record.pre_mutation_payload)) {
            result.status = failure(RuntimeStateTransferError::ImportJournalCorrupt,
                                    "state-transfer journal phase transition is invalid");
            return result;
        }
        previous_sequence = record.sequence;
        result.records.push_back(std::move(record));
        start = end + 1;
    }
    if (previous_sequence == std::numeric_limits<std::uint64_t>::max()) {
        result.status = failure(RuntimeStateTransferError::SequenceExhausted,
                                "state-transfer journal sequence is exhausted");
        return result;
    }
    result.next_sequence = previous_sequence + 1;
    return result;
}

bool append_journal_record_with_lock(const std::string &path, std::string_view transaction_id,
                                     RuntimeStateOwnerImportTransactionPhase phase,
                                     std::string_view payload_sha256,
                                     std::string_view pre_mutation_sha256,
                                     const std::vector<std::uint8_t> &pre_mutation_payload,
                                     std::uint64_t *sequence_out) noexcept {
    std::FILE *file = nullptr;
    int descriptor = -1;
#ifdef _WIN32
    for (int attempt = 0; attempt < 1000 && descriptor < 0; ++attempt) {
        if (_sopen_s(&descriptor, path.c_str(), _O_WRONLY | _O_APPEND | _O_CREAT | _O_BINARY,
                     _SH_DENYWR, _S_IREAD | _S_IWRITE) == 0 &&
            descriptor >= 0) {
            break;
        }
        descriptor = -1;
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
    if (descriptor >= 0) {
        file = _fdopen(descriptor, "ab");
        if (file == nullptr) {
            _close(descriptor);
            descriptor = -1;
        }
    }
#else
    descriptor = ::open(path.c_str(), O_WRONLY | O_APPEND | O_CREAT, 0666);
    if (descriptor >= 0 && ::flock(descriptor, LOCK_EX) == 0) {
        file = ::fdopen(descriptor, "ab");
    } else if (descriptor >= 0) {
        ::close(descriptor);
        descriptor = -1;
    }
#endif
    if (file == nullptr) {
        return false;
    }
    // The advisory lock is acquired before rescanning and assigning the
    // sequence.  This closes the cross-process duplicate-sequence race: a
    // second writer must observe the first writer's durable tail before it can
    // construct its own frame (Windows' share-deny open provides the same
    // exclusion).
    const JournalScanResult scan = scan_journal_file(path);
    if (!scan.status || scan.valid_size != scan.file_size) {
        std::fclose(file);
        return false;
    }
    const auto previous = std::find_if(scan.records.rbegin(), scan.records.rend(),
                                       [&](const RuntimeStateTransferJournalRecord &candidate) {
                                           return candidate.transaction_id == transaction_id;
                                       });
    const std::optional<RuntimeStateTransferJournalRecord> previous_record =
        previous == scan.records.rend()
            ? std::nullopt
            : std::optional<RuntimeStateTransferJournalRecord>(*previous);
    if (!valid_journal_transition(previous_record, phase, payload_sha256, pre_mutation_sha256,
                                  pre_mutation_payload) ||
        scan.next_sequence == 0) {
        std::fclose(file);
        return false;
    }
    const std::uint64_t sequence = scan.next_sequence;
    const std::string body = journal_record_body(sequence, transaction_id, phase, payload_sha256,
                                                 pre_mutation_sha256, pre_mutation_payload);
    std::string line = body;
    line.push_back('\t');
    line.append(sha256_hex(body));
    line.push_back('\n');
    const bool wrote = std::fwrite(line.data(), 1, line.size(), file) == line.size();
    const bool flushed = wrote && std::fflush(file) == 0;
#ifdef _WIN32
    const bool synced = flushed && _commit(_fileno(file)) == 0;
#else
    const bool synced = flushed && ::fsync(fileno(file)) == 0;
#endif
    const bool closed = std::fclose(file) == 0;
    if (wrote && flushed && synced && closed && sequence_out != nullptr) {
        *sequence_out = sequence;
    }
    return wrote && flushed && synced && closed;
}

bool truncate_journal_file(const std::string &path, std::uint64_t size) noexcept {
#ifdef _WIN32
    int descriptor = -1;
    if (_sopen_s(&descriptor, path.c_str(), _O_RDWR | _O_BINARY, _SH_DENYNO,
                 _S_IREAD | _S_IWRITE) != 0) {
        descriptor = -1;
    }
    if (descriptor < 0) {
        return false;
    }
    const bool truncated = _chsize_s(descriptor, size) == 0;
    const bool synced = truncated && _commit(descriptor) == 0;
    const bool closed = _close(descriptor) == 0;
#else
    const int descriptor = ::open(path.c_str(), O_RDWR);
    if (descriptor < 0) {
        return false;
    }
    const bool truncated = ::ftruncate(descriptor, static_cast<off_t>(size)) == 0;
    const bool synced = truncated && ::fsync(descriptor) == 0;
    const bool closed = ::close(descriptor) == 0;
#endif
    return truncated && synced && closed;
}

bool same_episode(const RuntimeEpisodeRef &lhs, const RuntimeEpisodeRef &rhs) {
    return lhs.well_formed() && rhs.well_formed() && lhs == rhs;
}

RuntimeIdentity128 mint_nonce() {
    static std::atomic<std::uint64_t> fallback_sequence{1};
    RuntimeIdentity128 output;
    try {
        std::random_device random;
        auto next64 = [&random]() {
            std::uint64_t value = 0;
            for (int index = 0; index < 4; ++index) {
                value = (value << 16U) ^ static_cast<std::uint64_t>(random());
            }
            return value;
        };
        output = {.high = next64(), .low = next64()};
    } catch (...) {
        output = {};
    }
    const std::uint64_t fallback = fallback_sequence.fetch_add(1, std::memory_order_relaxed);
    output.low ^= fallback == 0 ? 1 : fallback;
    if (!output.well_formed()) {
        output.low = fallback == 0 ? 1 : fallback;
    }
    return output;
}

constexpr std::array<std::uint32_t, 64> kSha256RoundConstants = {
    0x428a2f98U, 0x71374491U, 0xb5c0fbcfU, 0xe9b5dba5U, 0x3956c25bU, 0x59f111f1U, 0x923f82a4U,
    0xab1c5ed5U, 0xd807aa98U, 0x12835b01U, 0x243185beU, 0x550c7dc3U, 0x72be5d74U, 0x80deb1feU,
    0x9bdc06a7U, 0xc19bf174U, 0xe49b69c1U, 0xefbe4786U, 0x0fc19dc6U, 0x240ca1ccU, 0x2de92c6fU,
    0x4a7484aaU, 0x5cb0a9dcU, 0x76f988daU, 0x983e5152U, 0xa831c66dU, 0xb00327c8U, 0xbf597fc7U,
    0xc6e00bf3U, 0xd5a79147U, 0x06ca6351U, 0x14292967U, 0x27b70a85U, 0x2e1b2138U, 0x4d2c6dfcU,
    0x53380d13U, 0x650a7354U, 0x766a0abbU, 0x81c2c92eU, 0x92722c85U, 0xa2bfe8a1U, 0xa81a664bU,
    0xc24b8b70U, 0xc76c51a3U, 0xd192e819U, 0xd6990624U, 0xf40e3585U, 0x106aa070U, 0x19a4c116U,
    0x1e376c08U, 0x2748774cU, 0x34b0bcb5U, 0x391c0cb3U, 0x4ed8aa4aU, 0x5b9cca4fU, 0x682e6ff3U,
    0x748f82eeU, 0x78a5636fU, 0x84c87814U, 0x8cc70208U, 0x90befffaU, 0xa4506cebU, 0xbef9a3f7U,
    0xc67178f2U,
};

std::string sha256_hex(std::string_view input) {
    std::vector<std::uint8_t> bytes(input.begin(), input.end());
    const std::uint64_t bit_length = static_cast<std::uint64_t>(bytes.size()) * 8U;
    bytes.push_back(0x80U);
    while ((bytes.size() % 64U) != 56U) {
        bytes.push_back(0U);
    }
    for (int shift = 56; shift >= 0; shift -= 8) {
        bytes.push_back(static_cast<std::uint8_t>((bit_length >> shift) & 0xffU));
    }

    std::array<std::uint32_t, 8> hash = {
        0x6a09e667U, 0xbb67ae85U, 0x3c6ef372U, 0xa54ff53aU,
        0x510e527fU, 0x9b05688cU, 0x1f83d9abU, 0x5be0cd19U,
    };
    for (std::size_t offset = 0; offset < bytes.size(); offset += 64U) {
        std::array<std::uint32_t, 64> words{};
        for (std::size_t index = 0; index < 16; ++index) {
            const std::size_t cursor = offset + index * 4U;
            words[index] = (static_cast<std::uint32_t>(bytes[cursor]) << 24U) |
                           (static_cast<std::uint32_t>(bytes[cursor + 1]) << 16U) |
                           (static_cast<std::uint32_t>(bytes[cursor + 2]) << 8U) |
                           static_cast<std::uint32_t>(bytes[cursor + 3]);
        }
        for (std::size_t index = 16; index < words.size(); ++index) {
            const std::uint32_t s0 = std::rotr(words[index - 15], 7) ^
                                     std::rotr(words[index - 15], 18) ^ (words[index - 15] >> 3U);
            const std::uint32_t s1 = std::rotr(words[index - 2], 17) ^
                                     std::rotr(words[index - 2], 19) ^ (words[index - 2] >> 10U);
            words[index] = words[index - 16] + s0 + words[index - 7] + s1;
        }

        std::uint32_t a = hash[0];
        std::uint32_t b = hash[1];
        std::uint32_t c = hash[2];
        std::uint32_t d = hash[3];
        std::uint32_t e = hash[4];
        std::uint32_t f = hash[5];
        std::uint32_t g = hash[6];
        std::uint32_t h = hash[7];
        for (std::size_t index = 0; index < words.size(); ++index) {
            const std::uint32_t sum1 = std::rotr(e, 6) ^ std::rotr(e, 11) ^ std::rotr(e, 25);
            const std::uint32_t choose = (e & f) ^ ((~e) & g);
            const std::uint32_t temporary1 =
                h + sum1 + choose + kSha256RoundConstants[index] + words[index];
            const std::uint32_t sum0 = std::rotr(a, 2) ^ std::rotr(a, 13) ^ std::rotr(a, 22);
            const std::uint32_t majority = (a & b) ^ (a & c) ^ (b & c);
            const std::uint32_t temporary2 = sum0 + majority;
            h = g;
            g = f;
            f = e;
            e = d + temporary1;
            d = c;
            c = b;
            b = a;
            a = temporary1 + temporary2;
        }
        hash[0] += a;
        hash[1] += b;
        hash[2] += c;
        hash[3] += d;
        hash[4] += e;
        hash[5] += f;
        hash[6] += g;
        hash[7] += h;
    }

    std::ostringstream output;
    output << std::hex << std::setfill('0');
    for (const std::uint32_t value : hash) {
        output << std::setw(8) << value;
    }
    return output.str();
}

void append_number(std::string &output, std::string_view name, std::uint64_t value) {
    output.append(name);
    output.push_back('=');
    output.append(std::to_string(value));
    output.push_back('\n');
}

void append_text(std::string &output, std::string_view name, std::string_view value) {
    output.append(name);
    output.push_back('=');
    output.append(std::to_string(value.size()));
    output.push_back(':');
    output.append(value);
    output.push_back('\n');
}

void append_identity(std::string &output, std::string_view prefix,
                     const RuntimeIdentity128 &identity) {
    append_number(output, std::string(prefix) + "_high", identity.high);
    append_number(output, std::string(prefix) + "_low", identity.low);
}

void append_episode(std::string &output, std::string_view prefix,
                    const RuntimeEpisodeRef &episode) {
    append_identity(output, std::string(prefix) + "_host_id",
                    episode.world.incarnation.host.host_id);
    append_identity(output, std::string(prefix) + "_boot_id",
                    episode.world.incarnation.host.boot_id);
    append_number(output, std::string(prefix) + "_incarnation_epoch",
                  episode.world.incarnation.incarnation_epoch);
    append_number(output, std::string(prefix) + "_world_slot", episode.world.world_slot);
    append_number(output, std::string(prefix) + "_world_generation",
                  episode.world.world_generation);
    append_identity(output, std::string(prefix) + "_episode_id", episode.episode_id);
    append_number(output, std::string(prefix) + "_episode_generation", episode.episode_generation);
}

std::string intent_fingerprint(const RuntimeEpisodeTransitionIntent &intent) {
    return sha256_hex(canonical_episode_transition_intent_bytes(intent));
}

struct CoordinatorRegistry {
    std::mutex mutex;
    std::vector<RuntimeWorldRef> worlds;
};

CoordinatorRegistry &coordinator_registry() {
    static auto *registry = new CoordinatorRegistry();
    return *registry;
}

bool reserve_world(const RuntimeWorldRef &world) {
    CoordinatorRegistry &registry = coordinator_registry();
    std::lock_guard<std::mutex> lock(registry.mutex);
    if (std::find(registry.worlds.begin(), registry.worlds.end(), world) != registry.worlds.end()) {
        return false;
    }
    registry.worlds.push_back(world);
    return true;
}

void release_world(const RuntimeWorldRef &world) noexcept {
    try {
        CoordinatorRegistry &registry = coordinator_registry();
        std::lock_guard<std::mutex> lock(registry.mutex);
        const auto position = std::find(registry.worlds.begin(), registry.worlds.end(), world);
        if (position != registry.worlds.end()) {
            registry.worlds.erase(position);
        }
    } catch (...) {
        std::terminate();
    }
}

bool supported_intent(RuntimeEpisodeIntentKind kind) {
    switch (kind) {
    case RuntimeEpisodeIntentKind::Action:
    case RuntimeEpisodeIntentKind::Reset:
        return true;
    }
    return false;
}

bool supported_category(RuntimeStateCategory category) {
    return static_cast<std::size_t>(category) < kRuntimeStateCategoryCount;
}

bool supported_disposition(RuntimeStateDisposition disposition) {
    switch (disposition) {
    case RuntimeStateDisposition::Transfer:
    case RuntimeStateDisposition::Rederive:
    case RuntimeStateDisposition::Cancel:
    case RuntimeStateDisposition::Drain:
    case RuntimeStateDisposition::Reject:
    case RuntimeStateDisposition::NotApplicable:
        return true;
    }
    return false;
}

bool category_requires_truth_schema(RuntimeStateCategory category) {
    switch (category) {
    case RuntimeStateCategory::EcsComponentTruth:
    case RuntimeStateCategory::RngState:
    case RuntimeStateCategory::ClockCadence:
    case RuntimeStateCategory::DelayedEventsQueues:
    case RuntimeStateCategory::CommandsLinksPendingIntent:
    case RuntimeStateCategory::EpisodeRewardTermination:
        return true;
    default:
        return false;
    }
}

} // namespace

struct RuntimeEpisodeCoordinatorState {
    struct ReceiptRecord {
        RuntimeIdentity128 idempotency_key;
        std::string intent_fingerprint;
        RuntimeEpisodeTransitionReceipt receipt;
    };

    explicit RuntimeEpisodeCoordinatorState(const RuntimeEpisodeCoordinatorConfig &config)
        : episode(config.initial_episode), phase(config.initial_phase),
          step_sequence(config.initial_step_sequence),
          barrier_sequence(config.initial_barrier_sequence),
          snapshot_id(config.initial_snapshot_id), snapshot_sha256(config.initial_snapshot_sha256),
          coordinator_nonce(mint_nonce()) {}

    ~RuntimeEpisodeCoordinatorState() { release_world(episode.world); }

    mutable std::mutex mutex;
    RuntimeEpisodeRef episode;
    RuntimeEpisodePhase phase = RuntimeEpisodePhase::Running;
    std::uint64_t step_sequence = 0;
    std::uint64_t barrier_sequence = 0;
    RuntimeIdentity128 snapshot_id;
    std::string snapshot_sha256;
    RuntimeIdentity128 coordinator_nonce;
    RuntimeIdentity128 open_barrier_nonce;
    bool mutation_in_progress = false;
    std::uint64_t compacted_step_sequence = 0;
    std::uint64_t compacted_barrier_sequence = 0;
    std::string compacted_receipt_sha256;
    std::vector<ReceiptRecord> receipts;
};

struct RuntimeEpisodeBarrierToken {
    std::weak_ptr<RuntimeEpisodeCoordinatorState> coordinator;
    RuntimeIdentity128 coordinator_nonce;
    RuntimeIdentity128 barrier_nonce;
    RuntimeEpisodeCoordinatorSnapshot snapshot;
    RuntimeIdentity128 host_instance_nonce;
    std::uint64_t world_slot = 0;
    bool host_bound = false;
    mutable std::mutex mutex;
    bool claimed = false;
    bool released = false;
};

struct RuntimeNativeEpisodeToken {
    std::weak_ptr<RuntimeEpisodeCoordinatorState> coordinator;
    std::shared_ptr<RuntimeEpisodeCoordinatorState> coordinator_owner;
    RuntimeIdentity128 coordinator_nonce;
    RuntimeEpisodeRef episode;
    std::uint64_t step_sequence = 0;
    mutable std::mutex mutex;
    bool host_claimed = false;
};

struct RuntimeHostQuiescenceToken {
    mutable std::mutex mutex;
    RuntimeIncarnationRef source_slot;
    std::string source_plan_sha256;
    std::string target_plan_sha256;
    RuntimeIdentity128 source_resource_identity;
    RuntimeIdentity128 candidate_resource_identity;
    std::shared_ptr<RuntimeStateTransferOwnerRegistry> source_owner_registry;
    std::shared_ptr<RuntimeStateTransferOwnerRegistry> target_owner_registry;
    RuntimeIdentity128 host_instance_nonce;
    std::function<bool()> host_revalidate;
    std::function<void()> host_rollback;
    std::function<bool()> host_begin_transfer;
    std::function<bool()> host_claim_transfer;
    std::function<void()> host_end_transfer;
    std::uint64_t lifecycle_ticket = 0;
    std::uint64_t candidate_sequence = 0;
    std::uint64_t mutation_fence_sequence = 0;
    std::size_t source_read_only_result_leases = 0;
    bool cooperative_cancellation_acknowledged = false;
    bool claimed = false;
    bool released = false;
};

enum class RuntimeValidatedTransferLifecycle : std::uint8_t {
    Ready,
    Prepared,
    Committing,
    Aborting,
    Committed,
    Aborted,
    Ambiguous,
};

struct RuntimeValidatedStateTransferState {
    mutable std::mutex mutex;
    RuntimeIncarnationRef source_slot;
    std::string source_plan_sha256;
    std::string target_plan_sha256;
    std::string state_bundle_sha256;
    std::uint64_t transfer_fence_sequence = 0;
    std::uint64_t episode_barrier_sequence = 0;
    RuntimeEpisodeCoordinatorSnapshot source_barrier_snapshot;
    std::uint64_t lifecycle_ticket = 0;
    std::uint64_t candidate_sequence = 0;
    RuntimeIdentity128 candidate_resource_identity;
    std::shared_ptr<RuntimeHostQuiescenceToken> quiescence_token;
    std::shared_ptr<RuntimeEpisodeBarrierToken> barrier_token;
    std::shared_ptr<RuntimeEpisodeCoordinatorState> coordinator_owner;
    std::shared_ptr<RuntimeStateOwnerImportTransaction> import_transaction;
    std::function<void()> host_end_transfer;
    RuntimeValidatedTransferLifecycle lifecycle = RuntimeValidatedTransferLifecycle::Ready;
};

namespace {

void release_unclaimed_barrier(const std::shared_ptr<RuntimeEpisodeBarrierToken> &token) noexcept {
    if (token == nullptr) {
        return;
    }
    try {
        std::lock_guard<std::mutex> token_lock(token->mutex);
        if (token->claimed || token->released) {
            return;
        }
        const auto coordinator = token->coordinator.lock();
        if (coordinator != nullptr) {
            std::lock_guard<std::mutex> coordinator_lock(coordinator->mutex);
            if (coordinator->phase == RuntimeEpisodePhase::ReplacementBarrier &&
                coordinator->coordinator_nonce == token->coordinator_nonce &&
                coordinator->open_barrier_nonce == token->barrier_nonce &&
                coordinator->barrier_sequence == token->snapshot.barrier_sequence) {
                coordinator->phase = RuntimeEpisodePhase::Terminal;
                coordinator->open_barrier_nonce = {};
            }
        }
        token->released = true;
    } catch (...) {
        std::terminate();
    }
}

void release_unclaimed_quiescence(
    const std::shared_ptr<RuntimeHostQuiescenceToken> &token) noexcept {
    if (token == nullptr) {
        return;
    }
    try {
        std::function<void()> rollback;
        {
            std::lock_guard<std::mutex> lock(token->mutex);
            if (!token->claimed) {
                token->released = true;
                rollback = std::move(token->host_rollback);
            }
        }
        if (rollback) {
            rollback();
        }
    } catch (...) {
        std::terminate();
    }
}

struct HostTransferReservationGuard {
    std::function<void()> release;
    bool active = false;

    ~HostTransferReservationGuard() noexcept {
        if (!active || !release) {
            return;
        }
        try {
            release();
        } catch (...) {
            // A failed validation must not throw from capability cleanup.  The
            // host remains conservatively pinned and can be retried by poll.
        }
    }

    [[nodiscard]] std::function<void()> disarm() noexcept {
        active = false;
        return std::move(release);
    }
};

struct ImportTransactionAbortGuard {
    std::shared_ptr<RuntimeStateOwnerImportTransaction> transaction;
    bool active = false;

    ~ImportTransactionAbortGuard() noexcept {
        if (active && transaction != nullptr) {
            const auto aborted = transaction->abort_with_deadline(0, 0);
            if (aborted.phase != RuntimeStateOwnerImportTransactionPhase::Aborted) {
                // The guard is used on every validation-failure edge.  A
                // failed best-effort abort must not silently discard a
                // transaction whose owner may still be Committing; give the
                // durable transaction one bounded recovery attempt before the
                // shared pointer is released.
                (void)transaction->recover_with_deadline(0, 0);
            }
        }
    }

    void disarm() noexcept {
        active = false;
        transaction.reset();
    }
};

struct OwnerImportPreparationGuard {
    std::vector<std::shared_ptr<RuntimeStateOwnerImportTransaction>> *transactions = nullptr;
    bool active = true;

    ~OwnerImportPreparationGuard() noexcept {
        if (!active || transactions == nullptr) {
            return;
        }
        for (auto position = transactions->rbegin(); position != transactions->rend(); ++position) {
            if (*position != nullptr) {
                (void)(*position)->abort_with_deadline(0, 0);
            }
        }
    }

    void disarm() noexcept { active = false; }
};

struct OwnerImportReceiptGuard {
    RuntimeStateOwnerImportReceipt *receipt = nullptr;
    bool active = true;

    ~OwnerImportReceiptGuard() noexcept {
        if (active && receipt != nullptr) {
            receipt->observations.clear();
            receipt->transaction.reset();
        }
    }

    void disarm() noexcept { active = false; }
};

RuntimeStateTransferStatus validate_profile(const RuntimeStateTransferProfile &profile) {
    if (profile.profile_id.empty() || profile.profile_generation == 0 ||
        !is_lower_hex_sha256(profile.source_plan_sha256) ||
        !is_lower_hex_sha256(profile.target_plan_sha256) ||
        profile.rows.size() != kRuntimeStateCategoryCount) {
        return failure(RuntimeStateTransferError::InvalidCensusProfile,
                       "state-transfer profile is incomplete or malformed");
    }
    std::array<bool, kRuntimeStateCategoryCount> seen{};
    for (const RuntimeStateCensusRowPolicy &row : profile.rows) {
        if (!supported_category(row.category)) {
            return failure(RuntimeStateTransferError::InvalidCensusProfile,
                           "profile contains an unsupported state category");
        }
        const std::size_t index = static_cast<std::size_t>(row.category);
        if (seen[index]) {
            return failure(RuntimeStateTransferError::DuplicateCategory,
                           "profile contains a duplicate state category");
        }
        seen[index] = true;
        const RuntimeStateDecoderReplayRule *decoder_rule =
            runtime_state_decoder_replay_rule(row.category);
        if (!supported_disposition(row.disposition) || row.owner_id.empty() ||
            row.schema_id.empty() || row.minimum_schema_generation == 0 ||
            row.maximum_schema_generation < row.minimum_schema_generation ||
            (category_requires_truth_schema(row.category) && !row.truth_affecting) ||
            decoder_rule == nullptr || row.owner_id != decoder_rule->owner_id ||
            row.schema_id != decoder_rule->schema_id ||
            row.owner_id != runtime_state_owner_id(row.category) ||
            row.schema_id != runtime_state_schema_id(row.category) ||
            row.minimum_schema_generation < decoder_rule->previous_schema_generation ||
            row.maximum_schema_generation > decoder_rule->current_schema_generation ||
            row.maximum_schema_generation > kRuntimeStateTransferContractGeneration) {
            return failure(RuntimeStateTransferError::InvalidCensusProfile,
                           "profile row ownership, disposition, or schema range is invalid");
        }
        if (row.disposition != decoder_rule->disposition) {
            if (row.category == RuntimeStateCategory::BackendDeviceAllocationsLeases &&
                row.disposition == RuntimeStateDisposition::Transfer) {
                return failure(RuntimeStateTransferError::RawHandleTransferForbidden,
                               "backend/device raw handles and leases cannot transfer");
            }
            if (row.category == RuntimeStateCategory::ExternalSideEffects &&
                row.disposition == RuntimeStateDisposition::Reject) {
                return failure(
                    RuntimeStateTransferError::ReplacementRejected,
                    "profile rejects replacement while external side effects are unresolved");
            }
            return failure(RuntimeStateTransferError::DispositionMismatch,
                           "profile disposition does not match the decoder/replay matrix");
        }
    }
    return success();
}

RuntimeStateTransferStatus
validate_category_semantics(const RuntimeStateCensusEntry &entry,
                            const RuntimeEpisodeCoordinatorSnapshot &barrier_snapshot) {
    switch (entry.category) {
    case RuntimeStateCategory::CompositionProviderSystemGraph:
        if (entry.disposition != RuntimeStateDisposition::Rederive) {
            return failure(
                RuntimeStateTransferError::DispositionMismatch,
                "composition/provider/system graph must be rebuilt from the closed plan");
        }
        break;
    case RuntimeStateCategory::EcsComponentTruth:
    case RuntimeStateCategory::RngState:
    case RuntimeStateCategory::ClockCadence:
    case RuntimeStateCategory::DelayedEventsQueues:
    case RuntimeStateCategory::EpisodeRewardTermination:
        if (entry.disposition != RuntimeStateDisposition::Transfer) {
            return failure(RuntimeStateTransferError::DispositionMismatch,
                           "truth state category requires canonical transfer");
        }
        break;
    case RuntimeStateCategory::PythonLoaderControllerCaches:
        if (entry.disposition != RuntimeStateDisposition::Rederive) {
            return failure(RuntimeStateTransferError::DispositionMismatch,
                           "Python mirrors and caches must rederive from native state");
        }
        break;
    case RuntimeStateCategory::BackendDeviceAllocationsLeases:
        if (entry.disposition == RuntimeStateDisposition::Transfer) {
            return failure(RuntimeStateTransferError::RawHandleTransferForbidden,
                           "backend/device raw handles and leases cannot transfer");
        }
        if (entry.disposition != RuntimeStateDisposition::Rederive &&
            entry.disposition != RuntimeStateDisposition::NotApplicable) {
            return failure(RuntimeStateTransferError::DispositionMismatch,
                           "backend/device resources must rehydrate or be not applicable");
        }
        break;
    case RuntimeStateCategory::InFlightRequestsResults:
        if (entry.disposition == RuntimeStateDisposition::Transfer && !entry.replay_idempotent) {
            return failure(RuntimeStateTransferError::UnsettledWork,
                           "in-flight replay requires an explicit idempotency proof");
        }
        if (entry.disposition != RuntimeStateDisposition::Transfer &&
            entry.disposition != RuntimeStateDisposition::Cancel &&
            entry.disposition != RuntimeStateDisposition::Drain &&
            entry.disposition != RuntimeStateDisposition::NotApplicable) {
            return failure(RuntimeStateTransferError::DispositionMismatch,
                           "in-flight work must drain, cancel, idempotently replay, or be absent");
        }
        break;
    case RuntimeStateCategory::ExternalSideEffects:
        if (entry.disposition == RuntimeStateDisposition::Reject) {
            return failure(
                RuntimeStateTransferError::ReplacementRejected,
                "profile rejects replacement while external side effects are unresolved");
        }
        if (entry.disposition != RuntimeStateDisposition::Drain &&
            entry.disposition != RuntimeStateDisposition::NotApplicable) {
            return failure(RuntimeStateTransferError::DispositionMismatch,
                           "external side effects require a settled outbox or explicit absence");
        }
        break;
    case RuntimeStateCategory::DiagnosticsTelemetry:
        if (entry.disposition != RuntimeStateDisposition::Rederive &&
            entry.disposition != RuntimeStateDisposition::NotApplicable) {
            return failure(RuntimeStateTransferError::DispositionMismatch,
                           "diagnostics may only rederive or be not applicable");
        }
        break;
    case RuntimeStateCategory::CommandsLinksPendingIntent:
        if (entry.disposition != RuntimeStateDisposition::Transfer &&
            entry.disposition != RuntimeStateDisposition::Cancel &&
            entry.disposition != RuntimeStateDisposition::Drain &&
            entry.disposition != RuntimeStateDisposition::NotApplicable) {
            return failure(RuntimeStateTransferError::DispositionMismatch,
                           "commands and links require transfer or explicit settlement");
        }
        break;
    }

    if ((entry.category == RuntimeStateCategory::ClockCadence ||
         entry.category == RuntimeStateCategory::EpisodeRewardTermination) &&
        (entry.step_sequence != barrier_snapshot.step_sequence ||
         entry.barrier_sequence != barrier_snapshot.barrier_sequence)) {
        return failure(RuntimeStateTransferError::StaleIntent,
                       "clock/episode census does not bind the active native barrier");
    }
    return success();
}

RuntimeStateTransferStatus
validate_entry(const RuntimeStateCensusRowPolicy &policy, const RuntimeStateCensusEntry &entry,
               const RuntimeEpisodeCoordinatorSnapshot &barrier_snapshot) {
    if (entry.owner_id != policy.owner_id) {
        return failure(RuntimeStateTransferError::OwnerMismatch,
                       "state category owner does not match the admitted profile");
    }
    if (entry.disposition != policy.disposition) {
        return failure(RuntimeStateTransferError::DispositionMismatch,
                       "state category disposition does not match the admitted profile");
    }
    if (entry.schema_id != policy.schema_id ||
        entry.schema_generation < policy.minimum_schema_generation ||
        entry.schema_generation > policy.maximum_schema_generation) {
        return failure(RuntimeStateTransferError::SchemaMismatch,
                       "state category schema is outside the admitted generation window");
    }
    if (policy.truth_affecting && entry.contains_unknown_truth_fields) {
        return failure(RuntimeStateTransferError::UnknownTruthField,
                       "unknown truth-affecting fields reject transfer");
    }

    switch (entry.disposition) {
    case RuntimeStateDisposition::Transfer:
        if (!is_lower_hex_sha256(entry.state_content_sha256) ||
            entry.canonical_payload != runtime_state_canonical_payload(entry) ||
            entry.canonical_payload.empty() ||
            runtime_state_payload_sha256(entry.canonical_payload) !=
                entry.canonical_payload_sha256) {
            return failure(RuntimeStateTransferError::PayloadDigestMismatch,
                           "canonical transfer payload is absent or has the wrong digest");
        }
        if (!is_lower_hex_sha256(entry.semantic_evidence_sha256)) {
            return failure(RuntimeStateTransferError::SemanticEvidenceMissing,
                           "transfer row lacks semantic replay evidence");
        }
        break;
    case RuntimeStateDisposition::Rederive:
        if (!entry.canonical_payload.empty() || !entry.canonical_payload_sha256.empty() ||
            !is_lower_hex_sha256(entry.semantic_evidence_sha256)) {
            return failure(RuntimeStateTransferError::SemanticEvidenceMissing,
                           "rederive row must bind derivation evidence without payload bytes");
        }
        break;
    case RuntimeStateDisposition::Cancel:
    case RuntimeStateDisposition::Drain:
        if (!entry.canonical_payload.empty() || !entry.canonical_payload_sha256.empty() ||
            entry.item_count != entry.settled_item_count ||
            !is_lower_hex_sha256(entry.semantic_evidence_sha256)) {
            return failure(RuntimeStateTransferError::UnsettledWork,
                           "cancel/drain row must prove every item settled");
        }
        break;
    case RuntimeStateDisposition::Reject:
        return failure(RuntimeStateTransferError::ReplacementRejected,
                       "profile explicitly rejects replacement for this category");
    case RuntimeStateDisposition::NotApplicable:
        if (!entry.canonical_payload.empty() || !entry.canonical_payload_sha256.empty() ||
            !entry.semantic_evidence_sha256.empty() || entry.item_count != 0 ||
            entry.settled_item_count != 0) {
            return failure(RuntimeStateTransferError::InvalidArgument,
                           "not-applicable row must carry no state or settlement evidence");
        }
        break;
    }
    return validate_category_semantics(entry, barrier_snapshot);
}

std::string
canonical_state_bundle_bytes(const RuntimeStateTransferProfile &profile,
                             const RuntimeStateCensus &census,
                             const std::vector<RuntimeStateOwnerArtifact> &artifacts,
                             const RuntimeStateTransferEvidence &evidence,
                             const RuntimeEpisodeCoordinatorSnapshot &barrier_snapshot) {
    std::string output("echelon_forge.runtime_state_transfer_bundle.v1\n");
    append_text(output, "profile_id", profile.profile_id);
    append_number(output, "profile_generation", profile.profile_generation);
    append_text(output, "source_plan_sha256", profile.source_plan_sha256);
    append_text(output, "target_plan_sha256", profile.target_plan_sha256);
    append_episode(output, "barrier_episode", barrier_snapshot.episode);
    append_number(output, "barrier_step_sequence", barrier_snapshot.step_sequence);
    append_number(output, "barrier_sequence", barrier_snapshot.barrier_sequence);
    append_identity(output, "barrier_snapshot_id", barrier_snapshot.snapshot_id);
    append_text(output, "barrier_snapshot_sha256", barrier_snapshot.snapshot_sha256);
    append_number(output, "source_final_mutation_fence_sequence",
                  evidence.source_final_mutation_fence_sequence);

    std::vector<RuntimeStateCensusEntry> sorted = census.entries;
    std::sort(sorted.begin(), sorted.end(), [](const auto &lhs, const auto &rhs) {
        return static_cast<std::uint8_t>(lhs.category) < static_cast<std::uint8_t>(rhs.category);
    });
    for (const RuntimeStateCensusEntry &entry : sorted) {
        append_text(output, "category", runtime_state_category_name(entry.category));
        append_text(output, "disposition", runtime_state_disposition_name(entry.disposition));
        append_text(output, "owner_id", entry.owner_id);
        append_text(output, "schema_id", entry.schema_id);
        append_number(output, "schema_generation", entry.schema_generation);
        append_number(output, "payload_size", entry.canonical_payload.size());
        output.append(reinterpret_cast<const char *>(entry.canonical_payload.data()),
                      entry.canonical_payload.size());
        output.push_back('\n');
        append_text(output, "payload_sha256", entry.canonical_payload_sha256);
        append_text(output, "semantic_evidence_sha256", entry.semantic_evidence_sha256);
        append_number(output, "unknown_truth_fields", entry.contains_unknown_truth_fields ? 1 : 0);
        append_number(output, "replay_idempotent", entry.replay_idempotent ? 1 : 0);
        append_number(output, "item_count", entry.item_count);
        append_number(output, "settled_item_count", entry.settled_item_count);
        append_number(output, "sequence_high_watermark", entry.sequence_high_watermark);
        append_number(output, "rng_draw_position", entry.rng_draw_position);
        append_number(output, "simulation_tick", entry.simulation_tick);
        append_number(output, "step_sequence", entry.step_sequence);
        append_number(output, "barrier_sequence", entry.barrier_sequence);
    }
    std::vector<RuntimeStateOwnerArtifact> sorted_artifacts = artifacts;
    std::sort(sorted_artifacts.begin(), sorted_artifacts.end(),
              [](const auto &lhs, const auto &rhs) {
                  return static_cast<std::uint8_t>(lhs.category) <
                         static_cast<std::uint8_t>(rhs.category);
              });
    for (const RuntimeStateOwnerArtifact &artifact : sorted_artifacts) {
        append_text(output, "artifact_category", runtime_state_category_name(artifact.category));
        append_text(output, "artifact_schema_id", artifact.schema_id);
        append_number(output, "artifact_schema_generation", artifact.schema_generation);
        append_number(output, "artifact_payload_size", artifact.payload.size());
        output.append(reinterpret_cast<const char *>(artifact.payload.data()),
                      artifact.payload.size());
        output.push_back('\n');
        append_text(output, "artifact_payload_sha256", artifact.payload_sha256);
    }
    return output;
}

std::string canonical_state_entry_bytes(const RuntimeStateCensusEntry &entry) {
    std::string output("echelon_forge.runtime_state_census_entry.v1\n");
    append_text(output, "category", runtime_state_category_name(entry.category));
    append_text(output, "disposition", runtime_state_disposition_name(entry.disposition));
    append_text(output, "owner_id", entry.owner_id);
    append_text(output, "schema_id", entry.schema_id);
    append_number(output, "schema_generation", entry.schema_generation);
    append_text(output, "state_content_sha256", entry.state_content_sha256);
    append_text(output, "canonical_payload_sha256", entry.canonical_payload_sha256);
    append_text(output, "semantic_evidence_sha256", entry.semantic_evidence_sha256);
    append_number(output, "unknown_truth_fields", entry.contains_unknown_truth_fields ? 1 : 0);
    append_number(output, "replay_idempotent", entry.replay_idempotent ? 1 : 0);
    append_number(output, "item_count", entry.item_count);
    append_number(output, "settled_item_count", entry.settled_item_count);
    append_number(output, "sequence_high_watermark", entry.sequence_high_watermark);
    append_number(output, "rng_draw_position", entry.rng_draw_position);
    append_number(output, "simulation_tick", entry.simulation_tick);
    append_number(output, "step_sequence", entry.step_sequence);
    append_number(output, "barrier_sequence", entry.barrier_sequence);
    append_number(output, "payload_size", entry.canonical_payload.size());
    output.append(reinterpret_cast<const char *>(entry.canonical_payload.data()),
                  entry.canonical_payload.size());
    output.push_back('\n');
    return output;
}

bool same_source_census(const RuntimeStateCensus &expected, const RuntimeStateCensus &observed) {
    if (expected.contract_generation != observed.contract_generation ||
        expected.profile_id != observed.profile_id ||
        expected.profile_generation != observed.profile_generation ||
        expected.source_slot != observed.source_slot ||
        expected.source_plan_sha256 != observed.source_plan_sha256 ||
        expected.target_plan_sha256 != observed.target_plan_sha256 ||
        expected.entries.size() != observed.entries.size()) {
        return false;
    }
    for (const RuntimeStateCensusEntry &expected_entry : expected.entries) {
        const auto observed_entry =
            std::find_if(observed.entries.begin(), observed.entries.end(),
                         [&](const RuntimeStateCensusEntry &entry) {
                             return entry.category == expected_entry.category;
                         });
        if (observed_entry == observed.entries.end() ||
            canonical_state_entry_bytes(expected_entry) !=
                canonical_state_entry_bytes(*observed_entry)) {
            return false;
        }
    }
    return true;
}

RuntimeStateTransferStatus validate_source_artifacts(const RuntimeStateTransferProfile &profile,
                                                     const RuntimeStateCensus &census,
                                                     const RuntimeStateOwnerExport &source_export) {
    if (source_export.artifacts.size() != kRuntimeStateCategoryCount) {
        return failure(RuntimeStateTransferError::MissingCategory,
                       "owner source export does not contain one artifact per category");
    }
    std::array<const RuntimeStateOwnerArtifact *, kRuntimeStateCategoryCount> artifacts{};
    for (const RuntimeStateOwnerArtifact &artifact : source_export.artifacts) {
        if (!supported_category(artifact.category)) {
            return failure(RuntimeStateTransferError::SchemaMismatch,
                           "owner source export contains an unsupported artifact category");
        }
        const std::size_t index = static_cast<std::size_t>(artifact.category);
        if (artifacts[index] != nullptr) {
            return failure(RuntimeStateTransferError::DuplicateCategory,
                           "owner source export contains duplicate artifacts");
        }
        artifacts[index] = &artifact;
        if (!is_lower_hex_sha256(artifact.payload_sha256) ||
            runtime_state_payload_sha256(artifact.payload) != artifact.payload_sha256) {
            return failure(RuntimeStateTransferError::PayloadDigestMismatch,
                           "owner source artifact payload digest is invalid");
        }
    }
    for (const RuntimeStateCensusRowPolicy &policy : profile.rows) {
        const auto entry = std::find_if(census.entries.begin(), census.entries.end(),
                                        [&](const RuntimeStateCensusEntry &candidate) {
                                            return candidate.category == policy.category;
                                        });
        const auto *artifact = artifacts[static_cast<std::size_t>(policy.category)];
        if (entry == census.entries.end() || artifact == nullptr ||
            artifact->schema_id != policy.schema_id ||
            artifact->schema_generation != entry->schema_generation ||
            (policy.disposition == RuntimeStateDisposition::Transfer &&
             (artifact->payload.empty() ||
              artifact->payload_sha256 != entry->state_content_sha256))) {
            return failure(RuntimeStateTransferError::PayloadDigestMismatch,
                           "owner source artifact is not bound to its census schema");
        }
    }
    return success();
}

class CompositeOwnerImportTransaction final : public RuntimeStateOwnerImportTransaction {
  public:
    explicit CompositeOwnerImportTransaction(
        std::vector<std::shared_ptr<RuntimeStateOwnerImportTransaction>> transactions)
        : transactions_(std::move(transactions)) {}

    [[nodiscard]] RuntimeStateOwnerImportTransactionStatus
    commit_with_deadline(std::uint64_t now_tick, std::uint64_t deadline_tick) noexcept override {
        std::lock_guard<std::mutex> lock(mutex_);
        if (terminal()) {
            return status_;
        }
        status_.phase = RuntimeStateOwnerImportTransactionPhase::Committing;
        bool committed_any = false;
        std::vector<std::shared_ptr<RuntimeStateOwnerImportTransaction>> committed_children;
        std::uint64_t last_journal_sequence = 0;
        for (const auto &transaction : transactions_) {
            if (transaction == nullptr) {
                status_ = {.phase = RuntimeStateOwnerImportTransactionPhase::Ambiguous,
                           .error = RuntimeStateTransferError::ImportTransactionStateInvalid};
                return status_;
            }
            auto child = transaction->commit_with_deadline(now_tick, deadline_tick);
            if (child.phase == RuntimeStateOwnerImportTransactionPhase::Committed &&
                child.error == RuntimeStateTransferError::None && child.durable &&
                child.journal_sequence != 0) {
                committed_any = true;
                committed_children.push_back(transaction);
                last_journal_sequence = std::max(last_journal_sequence, child.journal_sequence);
                continue;
            }
            // The failing child may have crossed its deadline after applying
            // owner state, so its returned Ambiguous/Committing status is not
            // evidence that it remained untouched. Reconcile that child first
            // and compensate it if recovery proves it committed.
            bool current_child_compensated =
                child.phase == RuntimeStateOwnerImportTransactionPhase::Aborted &&
                child.error == RuntimeStateTransferError::None && child.durable &&
                child.journal_sequence != 0;
            if (child.phase == RuntimeStateOwnerImportTransactionPhase::Ambiguous ||
                child.phase == RuntimeStateOwnerImportTransactionPhase::Committing) {
                child = transaction->recover_with_deadline(now_tick, deadline_tick);
                last_journal_sequence = std::max(last_journal_sequence, child.journal_sequence);
                if (child.phase == RuntimeStateOwnerImportTransactionPhase::Committed &&
                    child.error == RuntimeStateTransferError::None && child.durable &&
                    child.journal_sequence != 0) {
                    current_child_compensated = transaction->rollback_committed();
                    if (current_child_compensated) {
                        child = transaction->status();
                        last_journal_sequence =
                            std::max(last_journal_sequence, child.journal_sequence);
                    }
                } else if (child.phase == RuntimeStateOwnerImportTransactionPhase::Aborted &&
                           child.error == RuntimeStateTransferError::None && child.durable &&
                           child.journal_sequence != 0) {
                    current_child_compensated = true;
                }
            } else if (child.phase == RuntimeStateOwnerImportTransactionPhase::Committed &&
                       child.durable && child.journal_sequence != 0) {
                current_child_compensated = transaction->rollback_committed();
                if (current_child_compensated) {
                    child = transaction->status();
                    last_journal_sequence = std::max(last_journal_sequence, child.journal_sequence);
                }
            }
            // A later child can fail after earlier children have committed.
            // Compensate in reverse order before exposing a terminal result;
            // otherwise the target is left with a mixed owner state that no
            // host-level rollback can prove safe.
            bool compensated = true;
            for (auto position = committed_children.rbegin(); position != committed_children.rend();
                 ++position) {
                if (!(*position)->rollback_committed()) {
                    compensated = false;
                }
            }
            status_ = {
                .phase = committed_any ? (compensated && current_child_compensated
                                              ? RuntimeStateOwnerImportTransactionPhase::Aborted
                                              : RuntimeStateOwnerImportTransactionPhase::Ambiguous)
                                       : (current_child_compensated
                                              ? RuntimeStateOwnerImportTransactionPhase::Aborted
                                              : RuntimeStateOwnerImportTransactionPhase::Ambiguous),
                .error = (((!committed_any || compensated) && current_child_compensated))
                             ? RuntimeStateTransferError::None
                             : (child.error == RuntimeStateTransferError::None
                                    ? RuntimeStateTransferError::ImportTransactionAmbiguous
                                    : child.error),
                .journal_sequence = last_journal_sequence,
                .durable = ((!committed_any || compensated) && current_child_compensated &&
                            last_journal_sequence != 0),
            };
            return status_;
        }
        status_ = {.phase = RuntimeStateOwnerImportTransactionPhase::Committed,
                   .error = RuntimeStateTransferError::None,
                   .journal_sequence = last_journal_sequence,
                   .durable = !transactions_.empty() && last_journal_sequence != 0};
        return status_;
    }

    [[nodiscard]] RuntimeStateOwnerImportTransactionStatus
    abort_with_deadline(std::uint64_t now_tick, std::uint64_t deadline_tick) noexcept override {
        std::lock_guard<std::mutex> lock(mutex_);
        if (status_.phase == RuntimeStateOwnerImportTransactionPhase::Aborted) {
            return status_;
        }
        if (status_.phase == RuntimeStateOwnerImportTransactionPhase::Committed) {
            return {.phase = RuntimeStateOwnerImportTransactionPhase::Committed,
                    .error = RuntimeStateTransferError::ImportTransactionStateInvalid,
                    .journal_sequence = status_.journal_sequence,
                    .durable = status_.durable};
        }
        status_.phase = RuntimeStateOwnerImportTransactionPhase::Aborting;
        std::uint64_t last_journal_sequence = status_.journal_sequence;
        for (auto position = transactions_.rbegin(); position != transactions_.rend(); ++position) {
            if (*position == nullptr) {
                status_ = {.phase = RuntimeStateOwnerImportTransactionPhase::Ambiguous,
                           .error = RuntimeStateTransferError::ImportTransactionStateInvalid,
                           .journal_sequence = last_journal_sequence};
                return status_;
            }
            auto child = (*position)->abort_with_deadline(now_tick, deadline_tick);
            last_journal_sequence = std::max(last_journal_sequence, child.journal_sequence);
            // A prefix child may already have committed before the parent was
            // asked to abort.  Its normal abort path is intentionally
            // state-invalid; compensate the durable commit instead of
            // converting a safely reversible prefix into a false ambiguity.
            if (child.phase == RuntimeStateOwnerImportTransactionPhase::Committed &&
                child.durable && child.journal_sequence != 0) {
                const bool compensated = (*position)->rollback_committed();
                child = (*position)->status();
                last_journal_sequence = std::max(last_journal_sequence, child.journal_sequence);
                if (compensated &&
                    child.phase == RuntimeStateOwnerImportTransactionPhase::Aborted &&
                    child.error == RuntimeStateTransferError::None && child.durable &&
                    child.journal_sequence != 0) {
                    continue;
                }
            }
            if (child.phase == RuntimeStateOwnerImportTransactionPhase::Ambiguous ||
                child.phase == RuntimeStateOwnerImportTransactionPhase::Committing ||
                child.phase == RuntimeStateOwnerImportTransactionPhase::Aborting) {
                child = (*position)->recover_with_deadline(now_tick, deadline_tick);
                last_journal_sequence = std::max(last_journal_sequence, child.journal_sequence);
                if (child.phase == RuntimeStateOwnerImportTransactionPhase::Committed &&
                    child.durable && child.journal_sequence != 0) {
                    const bool compensated = (*position)->rollback_committed();
                    child = (*position)->status();
                    last_journal_sequence = std::max(last_journal_sequence, child.journal_sequence);
                    if (compensated &&
                        child.phase == RuntimeStateOwnerImportTransactionPhase::Aborted &&
                        child.error == RuntimeStateTransferError::None && child.durable &&
                        child.journal_sequence != 0) {
                        continue;
                    }
                }
            }
            if (child.phase != RuntimeStateOwnerImportTransactionPhase::Aborted ||
                child.error != RuntimeStateTransferError::None || !child.durable ||
                child.journal_sequence == 0) {
                status_ = {
                    .phase = RuntimeStateOwnerImportTransactionPhase::Ambiguous,
                    .error = child.error == RuntimeStateTransferError::None
                                 ? RuntimeStateTransferError::ImportTransactionAmbiguous
                                 : child.error,
                    .journal_sequence = last_journal_sequence,
                    .durable = false,
                };
                return status_;
            }
        }
        status_ = {.phase = RuntimeStateOwnerImportTransactionPhase::Aborted,
                   .error = RuntimeStateTransferError::None,
                   .journal_sequence = last_journal_sequence,
                   .durable = !transactions_.empty() && last_journal_sequence != 0};
        return status_;
    }

    [[nodiscard]] RuntimeStateOwnerImportTransactionStatus
    recover_with_deadline(std::uint64_t now_tick, std::uint64_t deadline_tick) noexcept override {
        std::lock_guard<std::mutex> lock(mutex_);
        // A composite outcome is itself the durable result of the ordered
        // child protocol.  Once compensation has produced Aborted (or all
        // children have committed), do not re-derive a different outcome by
        // inspecting child markers on a later recovery call.
        if (terminal()) {
            return status_;
        }
        bool saw_committed = false;
        bool saw_aborted = false;
        std::vector<std::shared_ptr<RuntimeStateOwnerImportTransaction>> committed_children;
        bool unresolved = false;
        bool committed_needs_compensation = false;
        RuntimeStateTransferError unresolved_error =
            RuntimeStateTransferError::ImportTransactionAmbiguous;
        std::uint64_t last_journal_sequence = status_.journal_sequence;
        for (const auto &transaction : transactions_) {
            if (transaction == nullptr) {
                status_ = {.phase = RuntimeStateOwnerImportTransactionPhase::Ambiguous,
                           .error = RuntimeStateTransferError::ImportTransactionStateInvalid,
                           .journal_sequence = last_journal_sequence};
                return status_;
            }
            auto child = transaction->status();
            if (child.phase != RuntimeStateOwnerImportTransactionPhase::Committed &&
                child.phase != RuntimeStateOwnerImportTransactionPhase::Aborted) {
                child = transaction->recover_with_deadline(now_tick, deadline_tick);
            }
            last_journal_sequence = std::max(last_journal_sequence, child.journal_sequence);
            if (child.phase == RuntimeStateOwnerImportTransactionPhase::Committed &&
                child.durable && child.journal_sequence != 0) {
                saw_committed = true;
                committed_children.push_back(transaction);
                // A durable Committed marker with a non-zero error is still
                // applied owner truth; force the safe abort direction instead
                // of losing it before compensation.
                committed_needs_compensation =
                    committed_needs_compensation || child.error != RuntimeStateTransferError::None;
                continue;
            }
            if (child.phase == RuntimeStateOwnerImportTransactionPhase::Aborted &&
                child.error == RuntimeStateTransferError::None && child.durable &&
                child.journal_sequence != 0) {
                saw_aborted = true;
                continue;
            }
            {
                unresolved = true;
                if (child.error != RuntimeStateTransferError::None) {
                    unresolved_error = child.error;
                }
                continue;
            }
        }
        // Recovery after a process restart has no in-memory parent marker.  A
        // mixed child outcome therefore follows the same deterministic
        // fail-safe policy as an interrupted commit: preserve an all-committed
        // result, otherwise compensate every committed child in reverse order
        // and converge to a durable all-aborted outcome.  This prevents a
        // committed prefix from becoming an unrecoverable mixed world.
        if (unresolved || (saw_committed && saw_aborted) || committed_needs_compensation) {
            bool compensated = true;
            for (auto position = committed_children.rbegin(); position != committed_children.rend();
                 ++position) {
                if (!(*position)->rollback_committed()) {
                    compensated = false;
                }
            }
            if (compensated && !unresolved) {
                status_ = {.phase = RuntimeStateOwnerImportTransactionPhase::Aborted,
                           .error = RuntimeStateTransferError::None,
                           .journal_sequence = last_journal_sequence,
                           .durable = last_journal_sequence != 0};
                return status_;
            }
            status_ = {.phase = RuntimeStateOwnerImportTransactionPhase::Ambiguous,
                       .error = unresolved ? unresolved_error
                                           : RuntimeStateTransferError::ImportTransactionAmbiguous,
                       .journal_sequence = last_journal_sequence};
            return status_;
        }
        if (!saw_committed && !saw_aborted) {
            status_ = {.phase = RuntimeStateOwnerImportTransactionPhase::Ambiguous,
                       .error = RuntimeStateTransferError::ImportTransactionAmbiguous,
                       .journal_sequence = last_journal_sequence};
            return status_;
        }
        status_ = {.phase = saw_committed ? RuntimeStateOwnerImportTransactionPhase::Committed
                                          : RuntimeStateOwnerImportTransactionPhase::Aborted,
                   .error = RuntimeStateTransferError::None,
                   .journal_sequence = last_journal_sequence,
                   .durable = true};
        return status_;
    }

    [[nodiscard]] RuntimeStateOwnerImportTransactionStatus status() const noexcept override {
        std::lock_guard<std::mutex> lock(mutex_);
        return status_;
    }

  private:
    [[nodiscard]] bool terminal() const noexcept {
        return status_.phase == RuntimeStateOwnerImportTransactionPhase::Committed ||
               status_.phase == RuntimeStateOwnerImportTransactionPhase::Aborted;
    }

    mutable std::mutex mutex_;
    std::vector<std::shared_ptr<RuntimeStateOwnerImportTransaction>> transactions_;
    RuntimeStateOwnerImportTransactionStatus status_{};
};

} // namespace

struct RuntimeStateTransferFileJournal::State {
    explicit State(std::string value) : path(std::move(value)) {}

    std::mutex mutex;
    std::string path;
    RuntimeStateTransferStatus initialization_status;
    std::uint64_t next_sequence = 1;
};

RuntimeStateTransferFileJournal::RuntimeStateTransferFileJournal(std::string path)
    : state_(std::make_unique<State>(std::move(path))) {
    if (state_->path.empty()) {
        state_->initialization_status = failure(RuntimeStateTransferError::ImportJournalUnavailable,
                                                "state-transfer journal path is empty");
        return;
    }
    std::FILE *file = nullptr;
#ifdef _WIN32
    if (fopen_s(&file, state_->path.c_str(), "ab") != 0) {
        file = nullptr;
    }
#else
    file = std::fopen(state_->path.c_str(), "ab");
#endif
    if (file == nullptr || std::fclose(file) != 0) {
        state_->initialization_status = failure(RuntimeStateTransferError::ImportJournalUnavailable,
                                                "state-transfer journal cannot be created");
        return;
    }
    JournalScanResult scan = scan_journal_file(state_->path);
    state_->initialization_status = scan.status;
    state_->next_sequence = scan.next_sequence;
    if (state_->initialization_status && scan.valid_size != scan.file_size &&
        !truncate_journal_file(state_->path, scan.valid_size)) {
        state_->initialization_status =
            failure(RuntimeStateTransferError::ImportJournalUnavailable,
                    "state-transfer journal torn tail cannot be truncated on reopen");
    }
}

RuntimeStateTransferFileJournal::~RuntimeStateTransferFileJournal() = default;

RuntimeStateTransferJournalAppendResult RuntimeStateTransferFileJournal::append_and_sync(
    std::string_view transaction_id, RuntimeStateOwnerImportTransactionPhase phase,
    std::string_view payload_sha256, std::string_view pre_mutation_sha256,
    const std::vector<std::uint8_t> &pre_mutation_payload) noexcept {
    RuntimeStateTransferJournalAppendResult result;
    if (state_ == nullptr) {
        result.status = failure(RuntimeStateTransferError::ImportJournalUnavailable,
                                "state-transfer journal is unavailable");
        return result;
    }
    try {
        std::lock_guard<std::mutex> lock(state_->mutex);
        if (!state_->initialization_status) {
            result.status = state_->initialization_status;
            return result;
        }
        if (!valid_journal_component(transaction_id) || !is_lower_hex_sha256(payload_sha256) ||
            (!pre_mutation_sha256.empty() && !is_lower_hex_sha256(pre_mutation_sha256)) ||
            (pre_mutation_sha256.empty() && !pre_mutation_payload.empty()) ||
            (!pre_mutation_sha256.empty() &&
             sha256_hex(
                 std::string_view(reinterpret_cast<const char *>(pre_mutation_payload.data()),
                                  pre_mutation_payload.size())) != pre_mutation_sha256) ||
            state_->next_sequence == 0) {
            result.status = failure(RuntimeStateTransferError::InvalidArgument,
                                    "state-transfer journal append is invalid");
            return result;
        }
        std::uint64_t sequence = 0;
        if (!append_journal_record_with_lock(state_->path, transaction_id, phase, payload_sha256,
                                             pre_mutation_sha256, pre_mutation_payload,
                                             &sequence)) {
            result.status = failure(RuntimeStateTransferError::ImportTransactionStateInvalid,
                                    "state-transfer journal append failed or transition changed");
            return result;
        }
        state_->next_sequence = sequence + 1;
        result.sequence = sequence;
    } catch (...) {
        result.status = failure(RuntimeStateTransferError::ImportJournalUnavailable,
                                "state-transfer journal append failed");
    }
    return result;
}

RuntimeStateTransferJournalReadResult
RuntimeStateTransferFileJournal::latest(std::string_view transaction_id) noexcept {
    RuntimeStateTransferJournalReadResult result;
    if (state_ == nullptr) {
        result.status = failure(RuntimeStateTransferError::ImportJournalUnavailable,
                                "state-transfer journal is unavailable");
        return result;
    }
    try {
        std::lock_guard<std::mutex> lock(state_->mutex);
        if (!state_->initialization_status) {
            result.status = state_->initialization_status;
            return result;
        }
        if (!valid_journal_component(transaction_id)) {
            result.status = failure(RuntimeStateTransferError::InvalidArgument,
                                    "state-transfer transaction id is invalid");
            return result;
        }
        JournalScanResult scan = scan_journal_file(state_->path);
        if (!scan.status) {
            state_->initialization_status = scan.status;
            result.status = scan.status;
            return result;
        }
        if (scan.valid_size != scan.file_size) {
            // A torn tail can be observed by an already-live journal object
            // after an interrupted append.  Truncate the incomplete frame
            // before recovery appends its terminal decision; otherwise the
            // append path would reject the same instance forever.
            if (!truncate_journal_file(state_->path, scan.valid_size)) {
                result.status = failure(RuntimeStateTransferError::ImportJournalUnavailable,
                                        "state-transfer journal torn tail cannot be truncated");
                return result;
            }
            scan.file_size = scan.valid_size;
        }
        state_->next_sequence = scan.next_sequence;
        const auto position = std::find_if(scan.records.rbegin(), scan.records.rend(),
                                           [&](const RuntimeStateTransferJournalRecord &candidate) {
                                               return candidate.transaction_id == transaction_id;
                                           });
        if (position != scan.records.rend()) {
            result.record = *position;
        }
    } catch (...) {
        result.status = failure(RuntimeStateTransferError::ImportJournalUnavailable,
                                "state-transfer journal read failed");
    }
    return result;
}

void RuntimeStateOwnerImportTransaction::commit() noexcept {}

void RuntimeStateOwnerImportTransaction::abort() noexcept {}

RuntimeStateOwnerImportTransactionStatus
RuntimeStateOwnerImportTransaction::commit_with_deadline(std::uint64_t now_tick,
                                                         std::uint64_t deadline_tick) noexcept {
    if (deadline_tick != 0 && now_tick >= deadline_tick) {
        return {.phase = RuntimeStateOwnerImportTransactionPhase::Prepared,
                .error = RuntimeStateTransferError::ImportTransactionDeadlineExceeded,
                .journal_sequence = 0,
                .durable = false};
    }
    commit();
    return {.phase = RuntimeStateOwnerImportTransactionPhase::Committed,
            .error = RuntimeStateTransferError::None,
            .journal_sequence = 0,
            .durable = false};
}

RuntimeStateOwnerImportTransactionStatus
RuntimeStateOwnerImportTransaction::abort_with_deadline(std::uint64_t now_tick,
                                                        std::uint64_t deadline_tick) noexcept {
    if (deadline_tick != 0 && now_tick >= deadline_tick) {
        return {.phase = RuntimeStateOwnerImportTransactionPhase::Ambiguous,
                .error = RuntimeStateTransferError::ImportTransactionDeadlineExceeded,
                .journal_sequence = 0,
                .durable = false};
    }
    abort();
    return {.phase = RuntimeStateOwnerImportTransactionPhase::Aborted,
            .error = RuntimeStateTransferError::None,
            .journal_sequence = 0,
            .durable = false};
}

RuntimeStateOwnerImportTransactionStatus
RuntimeStateOwnerImportTransaction::recover_with_deadline(std::uint64_t now_tick,
                                                          std::uint64_t deadline_tick) noexcept {
    (void)now_tick;
    (void)deadline_tick;
    return {.phase = RuntimeStateOwnerImportTransactionPhase::Ambiguous,
            .error = RuntimeStateTransferError::ImportTransactionAmbiguous,
            .journal_sequence = 0,
            .durable = false};
}

bool RuntimeStateOwnerImportTransaction::rollback_committed() noexcept {
    return false;
}

RuntimeStateOwnerImportTransactionStatus
RuntimeStateOwnerImportTransaction::status() const noexcept {
    return {.phase = RuntimeStateOwnerImportTransactionPhase::Prepared,
            .error = RuntimeStateTransferError::None,
            .journal_sequence = 0,
            .durable = false};
}

RuntimeDurableOwnerImportTransaction::RuntimeDurableOwnerImportTransaction(
    std::string transaction_id, std::string payload_sha256,
    std::shared_ptr<RuntimeStateTransferJournal> journal,
    RuntimeStateOwnerImportRecoveryCallbacks callbacks, std::string pre_mutation_sha256,
    std::vector<std::uint8_t> pre_mutation_payload) noexcept
    : transaction_id_(std::move(transaction_id)), payload_sha256_(std::move(payload_sha256)),
      pre_mutation_sha256_(std::move(pre_mutation_sha256)),
      pre_mutation_payload_(std::move(pre_mutation_payload)), journal_(std::move(journal)),
      callbacks_(std::move(callbacks)) {
    if (!valid_journal_component(transaction_id_) || !is_lower_hex_sha256(payload_sha256_) ||
        journal_ == nullptr || !callbacks_.commit || !callbacks_.abort || !callbacks_.recover) {
        status_ = {.phase = RuntimeStateOwnerImportTransactionPhase::Ambiguous,
                   .error = RuntimeStateTransferError::InvalidArgument};
        return;
    }
    const RuntimeStateTransferJournalReadResult existing = journal_->latest(transaction_id_);
    if (!existing.status) {
        status_ = {.phase = RuntimeStateOwnerImportTransactionPhase::Ambiguous,
                   .error = existing.status.error};
        return;
    }
    if (existing.record) {
        if (existing.record->payload_sha256 != payload_sha256_ ||
            existing.record->pre_mutation_sha256 != pre_mutation_sha256_ ||
            existing.record->pre_mutation_payload != pre_mutation_payload_) {
            status_ = {.phase = RuntimeStateOwnerImportTransactionPhase::Ambiguous,
                       .error = RuntimeStateTransferError::ImportJournalCorrupt,
                       .journal_sequence = existing.record->sequence};
            return;
        }
        status_ = {.phase = existing.record->phase,
                   .error =
                       existing.record->phase == RuntimeStateOwnerImportTransactionPhase::Ambiguous
                           ? RuntimeStateTransferError::ImportTransactionAmbiguous
                           : RuntimeStateTransferError::None,
                   .journal_sequence = existing.record->sequence,
                   .durable = true};
        // A terminal WAL record is only a claim until the owner verifies the
        // corresponding bytes.  If verification is unavailable or fails,
        // force the transaction through the normal recovery path instead of
        // trusting a stale terminal marker after a crash.
        if (status_.phase == RuntimeStateOwnerImportTransactionPhase::Committed ||
            status_.phase == RuntimeStateOwnerImportTransactionPhase::Aborted) {
            bool verified = false;
            try {
                verified = callbacks_.verify && callbacks_.verify(status_.phase);
            } catch (...) {
                verified = false;
            }
            if (!verified) {
                status_.phase = RuntimeStateOwnerImportTransactionPhase::Ambiguous;
                status_.error = RuntimeStateTransferError::ImportTransactionAmbiguous;
            }
        }
        return;
    }
    const RuntimeStateTransferJournalAppendResult prepared = journal_->append_and_sync(
        transaction_id_, RuntimeStateOwnerImportTransactionPhase::Prepared, payload_sha256_,
        pre_mutation_sha256_, pre_mutation_payload_);
    status_ = {.phase = prepared.status ? RuntimeStateOwnerImportTransactionPhase::Prepared
                                        : RuntimeStateOwnerImportTransactionPhase::Ambiguous,
               .error = prepared.status.error,
               .journal_sequence = prepared.sequence,
               .durable = static_cast<bool>(prepared.status) && prepared.sequence != 0};
}

RuntimeStateOwnerImportTransactionStatus RuntimeDurableOwnerImportTransaction::append_terminal(
    RuntimeStateOwnerImportTransactionPhase phase) noexcept {
    const RuntimeStateTransferJournalAppendResult appended = journal_->append_and_sync(
        transaction_id_, phase, payload_sha256_, pre_mutation_sha256_, pre_mutation_payload_);
    status_ = {.phase =
                   appended.status ? phase : RuntimeStateOwnerImportTransactionPhase::Ambiguous,
               .error = appended.status.error,
               .journal_sequence = appended.sequence,
               .durable = static_cast<bool>(appended.status) && appended.sequence != 0};
    if (phase == RuntimeStateOwnerImportTransactionPhase::Ambiguous && appended.status) {
        status_.error = RuntimeStateTransferError::ImportTransactionAmbiguous;
    }
    return status_;
}

RuntimeStateOwnerImportTransactionStatus
RuntimeDurableOwnerImportTransaction::commit_with_deadline(std::uint64_t now_tick,
                                                           std::uint64_t deadline_tick) noexcept {
    std::lock_guard<std::mutex> lock(mutex_);
    if (status_.phase == RuntimeStateOwnerImportTransactionPhase::Committed) {
        return status_;
    }
    if (status_.phase != RuntimeStateOwnerImportTransactionPhase::Prepared ||
        status_.error != RuntimeStateTransferError::None || !status_.durable) {
        status_.error = RuntimeStateTransferError::ImportTransactionStateInvalid;
        return status_;
    }
    bool clock_valid = true;
    if (callbacks_.sample_tick) {
        try {
            now_tick = std::max(now_tick, callbacks_.sample_tick());
        } catch (...) {
            clock_valid = false;
        }
    }
    if (!clock_valid) {
        auto ambiguous = append_terminal(RuntimeStateOwnerImportTransactionPhase::Ambiguous);
        ambiguous.error = RuntimeStateTransferError::ImportTransactionAmbiguous;
        status_.error = ambiguous.error;
        return ambiguous;
    }
    if (deadline_tick != 0 && now_tick >= deadline_tick) {
        status_.error = RuntimeStateTransferError::ImportTransactionDeadlineExceeded;
        return status_;
    }
    const RuntimeStateTransferJournalAppendResult committing = journal_->append_and_sync(
        transaction_id_, RuntimeStateOwnerImportTransactionPhase::Committing, payload_sha256_,
        pre_mutation_sha256_, pre_mutation_payload_);
    if (!committing.status) {
        status_ = {.phase = RuntimeStateOwnerImportTransactionPhase::Ambiguous,
                   .error = committing.status.error,
                   .journal_sequence = committing.sequence};
        return status_;
    }
    status_ = {.phase = RuntimeStateOwnerImportTransactionPhase::Committing,
               .error = RuntimeStateTransferError::None,
               .journal_sequence = committing.sequence,
               .durable = true};
    bool applied = false;
    try {
        applied = callbacks_.commit();
    } catch (...) {
        applied = false;
    }
    bool deadline_crossed = false;
    clock_valid = true;
    if (callbacks_.sample_tick) {
        try {
            now_tick = std::max(now_tick, callbacks_.sample_tick());
        } catch (...) {
            clock_valid = false;
        }
    }
    deadline_crossed = deadline_tick != 0 && now_tick >= deadline_tick;
    if (!clock_valid || deadline_crossed) {
        applied = false;
    }
    auto terminal = append_terminal(applied ? RuntimeStateOwnerImportTransactionPhase::Committed
                                            : RuntimeStateOwnerImportTransactionPhase::Ambiguous);
    if (!clock_valid || deadline_crossed) {
        terminal.error = deadline_crossed
                             ? RuntimeStateTransferError::ImportTransactionDeadlineExceeded
                             : RuntimeStateTransferError::ImportTransactionAmbiguous;
        status_.error = terminal.error;
    }
    return terminal;
}

RuntimeStateOwnerImportTransactionStatus
RuntimeDurableOwnerImportTransaction::abort_with_deadline(std::uint64_t now_tick,
                                                          std::uint64_t deadline_tick) noexcept {
    std::unique_lock<std::mutex> lock(mutex_);
    if (status_.phase == RuntimeStateOwnerImportTransactionPhase::Aborted) {
        return status_;
    }
    if (status_.phase == RuntimeStateOwnerImportTransactionPhase::Committed) {
        status_.error = RuntimeStateTransferError::ImportTransactionStateInvalid;
        return status_;
    }
    if (status_.phase != RuntimeStateOwnerImportTransactionPhase::Prepared) {
        lock.unlock();
        return recover_with_deadline(now_tick, deadline_tick);
    }
    const RuntimeStateTransferJournalAppendResult aborting = journal_->append_and_sync(
        transaction_id_, RuntimeStateOwnerImportTransactionPhase::Aborting, payload_sha256_,
        pre_mutation_sha256_, pre_mutation_payload_);
    if (!aborting.status) {
        status_ = {.phase = RuntimeStateOwnerImportTransactionPhase::Ambiguous,
                   .error = aborting.status.error,
                   .journal_sequence = aborting.sequence};
        return status_;
    }
    status_ = {.phase = RuntimeStateOwnerImportTransactionPhase::Aborting,
               .error = RuntimeStateTransferError::None,
               .journal_sequence = aborting.sequence,
               .durable = true};
    bool rolled_back = false;
    try {
        rolled_back = callbacks_.abort();
    } catch (...) {
        rolled_back = false;
    }
    bool clock_valid = true;
    if (callbacks_.sample_tick) {
        try {
            now_tick = std::max(now_tick, callbacks_.sample_tick());
        } catch (...) {
            clock_valid = false;
        }
    }
    const bool deadline_crossed = deadline_tick != 0 && now_tick >= deadline_tick;
    if (!clock_valid) {
        rolled_back = false;
    }
    auto terminal =
        append_terminal(rolled_back ? RuntimeStateOwnerImportTransactionPhase::Aborted
                                    : RuntimeStateOwnerImportTransactionPhase::Ambiguous);
    if (!clock_valid || (deadline_crossed && !rolled_back)) {
        terminal.error = deadline_crossed
                             ? RuntimeStateTransferError::ImportTransactionDeadlineExceeded
                             : RuntimeStateTransferError::ImportTransactionAmbiguous;
        status_.error = terminal.error;
    }
    return terminal;
}

RuntimeStateOwnerImportTransactionStatus
RuntimeDurableOwnerImportTransaction::recover_with_deadline(std::uint64_t now_tick,
                                                            std::uint64_t deadline_tick) noexcept {
    std::lock_guard<std::mutex> lock(mutex_);
    bool clock_valid = true;
    if (callbacks_.sample_tick) {
        try {
            now_tick = std::max(now_tick, callbacks_.sample_tick());
        } catch (...) {
            clock_valid = false;
        }
    }
    bool deadline_crossed = deadline_tick != 0 && now_tick >= deadline_tick;
    const RuntimeStateTransferJournalReadResult latest = journal_->latest(transaction_id_);
    if (!latest.status || !latest.record || latest.record->payload_sha256 != payload_sha256_ ||
        (!pre_mutation_sha256_.empty() &&
         latest.record->pre_mutation_sha256 != pre_mutation_sha256_) ||
        latest.record->pre_mutation_payload != pre_mutation_payload_) {
        status_ = {.phase = RuntimeStateOwnerImportTransactionPhase::Ambiguous,
                   .error = latest.status ? RuntimeStateTransferError::ImportJournalCorrupt
                                          : latest.status.error};
        return status_;
    }
    status_ = {.phase = latest.record->phase,
               .error = RuntimeStateTransferError::None,
               .journal_sequence = latest.record->sequence,
               .durable = true};
    const RuntimeStateOwnerImportTransactionPhase journal_phase = status_.phase;
    if (status_.phase == RuntimeStateOwnerImportTransactionPhase::Committed ||
        status_.phase == RuntimeStateOwnerImportTransactionPhase::Aborted) {
        bool verified = false;
        try {
            verified = callbacks_.verify && callbacks_.verify(status_.phase);
        } catch (...) {
            verified = false;
        }
        if (verified) {
            if (status_.phase == RuntimeStateOwnerImportTransactionPhase::Aborted) {
                return status_;
            }
            if (clock_valid && !deadline_crossed) {
                return status_;
            }
        }
        status_.phase = RuntimeStateOwnerImportTransactionPhase::Ambiguous;
        status_.error = RuntimeStateTransferError::ImportTransactionAmbiguous;
    }
    RuntimeStateOwnerImportTransactionPhase outcome =
        RuntimeStateOwnerImportTransactionPhase::Ambiguous;
    try {
        outcome = callbacks_.recover();
    } catch (...) {
        outcome = RuntimeStateOwnerImportTransactionPhase::Ambiguous;
    }
    if (outcome != RuntimeStateOwnerImportTransactionPhase::Committed &&
        outcome != RuntimeStateOwnerImportTransactionPhase::Aborted) {
        outcome = RuntimeStateOwnerImportTransactionPhase::Ambiguous;
    }
    if (callbacks_.sample_tick) {
        try {
            now_tick = std::max(now_tick, callbacks_.sample_tick());
        } catch (...) {
            clock_valid = false;
        }
    }
    deadline_crossed = deadline_tick != 0 && now_tick >= deadline_tick;
    if (outcome == RuntimeStateOwnerImportTransactionPhase::Committed &&
        (journal_phase == RuntimeStateOwnerImportTransactionPhase::Aborted || !clock_valid ||
         deadline_crossed)) {
        bool compensated = false;
        try {
            compensated = callbacks_.compensate && callbacks_.compensate();
        } catch (...) {
            compensated = false;
        }
        if (compensated) {
            return append_terminal(RuntimeStateOwnerImportTransactionPhase::Aborted);
        }
        auto ambiguous = append_terminal(RuntimeStateOwnerImportTransactionPhase::Ambiguous);
        ambiguous.error = deadline_crossed
                              ? RuntimeStateTransferError::ImportTransactionDeadlineExceeded
                              : RuntimeStateTransferError::ImportTransactionAmbiguous;
        status_.error = ambiguous.error;
        return ambiguous;
    }
    if (!clock_valid) {
        outcome = RuntimeStateOwnerImportTransactionPhase::Ambiguous;
    }
    return append_terminal(outcome);
}

RuntimeStateOwnerImportTransactionStatus
RuntimeDurableOwnerImportTransaction::status() const noexcept {
    std::lock_guard<std::mutex> lock(mutex_);
    return status_;
}

bool RuntimeDurableOwnerImportTransaction::rollback_committed() noexcept {
    std::lock_guard<std::mutex> lock(mutex_);
    if (status_.phase != RuntimeStateOwnerImportTransactionPhase::Committed ||
        !callbacks_.compensate) {
        return false;
    }
    bool compensated = false;
    try {
        compensated = callbacks_.compensate();
    } catch (...) {
        compensated = false;
    }
    if (!compensated) {
        return false;
    }
    // Compensation is a terminal correction, not an in-memory hint.  Persist
    // the corrected outcome so a process restart cannot rediscover the child
    // as Committed and reconstruct a mixed composite result.
    const auto terminal = append_terminal(RuntimeStateOwnerImportTransactionPhase::Aborted);
    return terminal.phase == RuntimeStateOwnerImportTransactionPhase::Aborted &&
           terminal.error == RuntimeStateTransferError::None && terminal.durable &&
           terminal.journal_sequence != 0;
}

RuntimeStateOwnerAdapterRegistry::RuntimeStateOwnerAdapterRegistry(
    std::array<RuntimeStateOwnerAdapterRegistration, kRuntimeStateCategoryCount> registrations,
    RuntimeIdentity128 bound_resource_identity, const void *owner_binding_token)
    : bound_resource_identity_(bound_resource_identity), owner_binding_token_(owner_binding_token) {
    std::array<bool, kRuntimeStateCategoryCount> seen{};
    for (auto &registration : registrations) {
        if (!supported_category(registration.category)) {
            registration_status_ =
                failure(RuntimeStateTransferError::InvalidCensusProfile,
                        "owner adapter registry contains an unsupported category");
            return;
        }
        const std::size_t index = static_cast<std::size_t>(registration.category);
        if (seen[index]) {
            registration_status_ = failure(RuntimeStateTransferError::DuplicateCategory,
                                           "owner adapter registry contains a duplicate category");
            return;
        }
        const RuntimeStateDecoderReplayRule *rule =
            runtime_state_decoder_replay_rule(registration.category);
        if (rule == nullptr || registration.owner_id != rule->owner_id ||
            registration.schema_id != rule->schema_id || !registration.export_state ||
            registration.migration_sha256 != rule->migration_sha256 ||
            !registration.migrate_previous || !registration.import_state) {
            registration_status_ =
                failure(RuntimeStateTransferError::InvalidCensusProfile,
                        "owner adapter registration does not match the decoder matrix");
            return;
        }
        seen[index] = true;
        registrations_[index] = std::move(registration);
    }
    if (!std::all_of(seen.begin(), seen.end(), [](bool value) { return value; })) {
        registration_status_ = failure(RuntimeStateTransferError::MissingCategory,
                                       "owner adapter registry is missing a state category");
    }
}

RuntimeStateTransferStatus RuntimeStateOwnerAdapterRegistry::registration_status() const noexcept {
    return registration_status_;
}

const RuntimeStateOwnerAdapterRegistration *
RuntimeStateOwnerAdapterRegistry::registration(RuntimeStateCategory category) const noexcept {
    if (!registration_status_ || !supported_category(category)) {
        return nullptr;
    }
    const auto index = static_cast<std::size_t>(category);
    return registrations_[index].category == category ? &registrations_[index] : nullptr;
}

RuntimeStateOwnerExport RuntimeStateOwnerAdapterRegistry::export_source(
    const RuntimeStateTransferProfile &profile, const RuntimeIncarnationRef &source_slot,
    const RuntimeStateOwnerExportContext &context) noexcept {
    RuntimeStateOwnerExport output;
    output.source_slot = source_slot;
    output.census = {.profile_id = profile.profile_id,
                     .profile_generation = profile.profile_generation,
                     .source_slot = source_slot,
                     .source_plan_sha256 = profile.source_plan_sha256,
                     .target_plan_sha256 = profile.target_plan_sha256};
    if (!registration_status_) {
        output.status = registration_status_;
        return output;
    }
    if (const RuntimeStateTransferStatus profile_status = validate_profile(profile);
        !profile_status) {
        output.status = profile_status;
        return output;
    }
    if (!source_slot.well_formed()) {
        output.status =
            failure(RuntimeStateTransferError::InvalidArgument, "owner source slot is invalid");
        return output;
    }
    try {
        output.census.entries.reserve(kRuntimeStateCategoryCount);
        output.artifacts.reserve(kRuntimeStateCategoryCount);
        for (const RuntimeStateCensusRowPolicy &policy : profile.rows) {
            const auto &registration = registrations_[static_cast<std::size_t>(policy.category)];
            RuntimeStateOwnerAdapterExport exported =
                registration.export_state(profile, source_slot, context);
            if (exported.census_entry.category != policy.category ||
                exported.census_entry.owner_id != policy.owner_id ||
                exported.census_entry.schema_id != policy.schema_id ||
                exported.census_entry.disposition != policy.disposition ||
                exported.artifact.category != policy.category ||
                exported.artifact.schema_id != policy.schema_id ||
                exported.artifact.schema_generation != exported.census_entry.schema_generation) {
                output.status =
                    failure(RuntimeStateTransferError::OwnerMismatch,
                            "owner adapter export does not match its admitted category");
                output.census.entries.clear();
                output.artifacts.clear();
                return output;
            }
            output.census.entries.push_back(std::move(exported.census_entry));
            output.artifacts.push_back(std::move(exported.artifact));
        }
        output.status = validate_source_artifacts(profile, output.census, output);
    } catch (...) {
        output.status = failure(RuntimeStateTransferError::SemanticEvidenceMissing,
                                "owner adapter export failed");
        output.census.entries.clear();
        output.artifacts.clear();
    }
    return output;
}

RuntimeStateOwnerImportReceipt RuntimeStateOwnerAdapterRegistry::import_and_observe(
    const RuntimeStateTransferProfile &profile, const RuntimeStateOwnerExport &source_export,
    const RuntimeIdentity128 &candidate_resource_identity) noexcept {
    RuntimeStateOwnerImportReceipt receipt;
    receipt.candidate_resource_identity = candidate_resource_identity;
    if (!registration_status_) {
        receipt.status = registration_status_;
        return receipt;
    }
    if (const RuntimeStateTransferStatus profile_status = validate_profile(profile);
        !profile_status) {
        receipt.status = profile_status;
        return receipt;
    }
    if (!source_export.status) {
        receipt.status = source_export.status;
        return receipt;
    }
    if (!candidate_resource_identity.well_formed()) {
        receipt.status = failure(RuntimeStateTransferError::InvalidArgument,
                                 "candidate resource identity is invalid");
        return receipt;
    }
    if (!source_export.source_slot.well_formed() ||
        source_export.source_slot != source_export.census.source_slot ||
        source_export.census.profile_id != profile.profile_id ||
        source_export.census.profile_generation != profile.profile_generation ||
        source_export.census.source_plan_sha256 != profile.source_plan_sha256 ||
        source_export.census.target_plan_sha256 != profile.target_plan_sha256 ||
        source_export.census.entries.size() != kRuntimeStateCategoryCount ||
        (source_export.census.contract_generation != kRuntimeStateTransferContractGeneration &&
         source_export.census.contract_generation != kRuntimeStateTransferPreviousGeneration)) {
        receipt.status =
            failure(RuntimeStateTransferError::InvalidArgument,
                    "owner source export does not bind the admitted profile and source slot");
        return receipt;
    }
    if (const RuntimeStateTransferStatus artifact_status =
            validate_source_artifacts(profile, source_export.census, source_export);
        !artifact_status) {
        receipt.status = artifact_status;
        return receipt;
    }
    OwnerImportReceiptGuard receipt_failure{.receipt = &receipt};
    try {
        receipt.observations.reserve(kRuntimeStateCategoryCount);
        std::vector<std::shared_ptr<RuntimeStateOwnerImportTransaction>> transactions;
        transactions.reserve(kRuntimeStateCategoryCount);
        OwnerImportPreparationGuard transactions_abort{.transactions = &transactions};
        for (const RuntimeStateCensusRowPolicy &policy : profile.rows) {
            const auto entry = std::find_if(source_export.census.entries.begin(),
                                            source_export.census.entries.end(),
                                            [&](const RuntimeStateCensusEntry &candidate) {
                                                return candidate.category == policy.category;
                                            });
            const auto artifact =
                std::find_if(source_export.artifacts.begin(), source_export.artifacts.end(),
                             [&](const RuntimeStateOwnerArtifact &candidate) {
                                 return candidate.category == policy.category;
                             });
            if (entry == source_export.census.entries.end() ||
                artifact == source_export.artifacts.end()) {
                receipt.status = failure(RuntimeStateTransferError::MissingCategory,
                                         "owner adapter import is missing source state");
                return receipt;
            }
            const auto &registration = registrations_[static_cast<std::size_t>(policy.category)];
            RuntimeStateOwnerArtifact admitted_artifact = *artifact;
            if (artifact->schema_generation == kRuntimeStateTransferPreviousGeneration) {
                admitted_artifact = registration.migrate_previous(*artifact);
                if (admitted_artifact.category != policy.category ||
                    admitted_artifact.schema_id != policy.schema_id ||
                    admitted_artifact.schema_generation !=
                        kRuntimeStateTransferContractGeneration ||
                    !is_lower_hex_sha256(admitted_artifact.payload_sha256) ||
                    runtime_state_payload_sha256(admitted_artifact.payload) !=
                        admitted_artifact.payload_sha256) {
                    receipt.status =
                        failure(RuntimeStateTransferError::SchemaMismatch,
                                "owner adapter N-1 migration did not produce admitted N bytes");
                    return receipt;
                }
            } else if (artifact->schema_generation != kRuntimeStateTransferContractGeneration) {
                receipt.status = failure(RuntimeStateTransferError::SchemaMismatch,
                                         "owner adapter source generation is outside exact N/N-1");
                return receipt;
            }
            RuntimeStateOwnerAdapterImport imported =
                registration.import_state(profile, source_export.source_slot, *entry, *artifact,
                                          admitted_artifact, candidate_resource_identity);
            ImportTransactionAbortGuard imported_abort{
                .transaction = imported.transaction,
                .active = imported.transaction != nullptr,
            };
            if (imported.transaction == nullptr ||
                imported.observation.category != policy.category ||
                imported.observation.owner_id != policy.owner_id ||
                imported.observation.schema_id != policy.schema_id ||
                imported.observation.candidate_resource_identity != candidate_resource_identity ||
                imported.observation.source_schema_generation != entry->schema_generation ||
                imported.observation.schema_generation != kRuntimeStateTransferContractGeneration ||
                imported.observation.source_artifact_payload_sha256 != artifact->payload_sha256 ||
                !is_lower_hex_sha256(imported.observation.candidate_artifact_payload_sha256) ||
                (policy.disposition == RuntimeStateDisposition::Transfer &&
                 imported.observation.candidate_artifact_payload_sha256 !=
                     admitted_artifact.payload_sha256) ||
                !imported.observation.exact_schema_decoded) {
                receipt.status =
                    failure(RuntimeStateTransferError::SemanticEvidenceMissing,
                            "owner adapter import did not produce bound decoded evidence");
                return receipt;
            }
            receipt.observations.push_back(std::move(imported.observation));
            transactions.push_back(std::move(imported.transaction));
            imported_abort.disarm();
        }
        receipt.transaction = std::make_shared<CompositeOwnerImportTransaction>(transactions);
        transactions_abort.disarm();
        receipt_failure.disarm();
    } catch (const std::exception &exception) {
        receipt.status = failure(RuntimeStateTransferError::SemanticEvidenceMissing,
                                 std::string("owner adapter import failed: ") + exception.what());
        receipt.observations.clear();
        receipt.transaction.reset();
    } catch (...) {
        receipt.status = failure(RuntimeStateTransferError::SemanticEvidenceMissing,
                                 "owner adapter import failed: unknown exception");
        receipt.observations.clear();
        receipt.transaction.reset();
    }
    return receipt;
}

std::string_view runtime_state_category_name(RuntimeStateCategory category) noexcept {
    switch (category) {
    case RuntimeStateCategory::CompositionProviderSystemGraph:
        return "composition-provider-system-graph";
    case RuntimeStateCategory::EcsComponentTruth:
        return "ecs-component-truth";
    case RuntimeStateCategory::RngState:
        return "rng-state";
    case RuntimeStateCategory::ClockCadence:
        return "clock-cadence";
    case RuntimeStateCategory::DelayedEventsQueues:
        return "delayed-events-queues";
    case RuntimeStateCategory::CommandsLinksPendingIntent:
        return "commands-links-pending-intent";
    case RuntimeStateCategory::EpisodeRewardTermination:
        return "episode-reward-termination";
    case RuntimeStateCategory::PythonLoaderControllerCaches:
        return "python-loader-controller-caches";
    case RuntimeStateCategory::BackendDeviceAllocationsLeases:
        return "backend-device-allocations-leases";
    case RuntimeStateCategory::InFlightRequestsResults:
        return "in-flight-requests-results";
    case RuntimeStateCategory::ExternalSideEffects:
        return "external-side-effects";
    case RuntimeStateCategory::DiagnosticsTelemetry:
        return "diagnostics-telemetry";
    }
    return "unsupported";
}

std::string_view runtime_state_disposition_name(RuntimeStateDisposition disposition) noexcept {
    switch (disposition) {
    case RuntimeStateDisposition::Transfer:
        return "transfer";
    case RuntimeStateDisposition::Rederive:
        return "rederive";
    case RuntimeStateDisposition::Cancel:
        return "cancel";
    case RuntimeStateDisposition::Drain:
        return "drain";
    case RuntimeStateDisposition::Reject:
        return "reject";
    case RuntimeStateDisposition::NotApplicable:
        return "not-applicable";
    }
    return "unsupported";
}

std::string_view runtime_state_owner_id(RuntimeStateCategory category) noexcept {
    switch (category) {
    case RuntimeStateCategory::CompositionProviderSystemGraph:
        return "native.plan-owner";
    case RuntimeStateCategory::EcsComponentTruth:
        return "native.ecs-owner";
    case RuntimeStateCategory::RngState:
        return "native.rng-owner";
    case RuntimeStateCategory::ClockCadence:
        return "native.clock-owner";
    case RuntimeStateCategory::DelayedEventsQueues:
        return "native.event-queue-owner";
    case RuntimeStateCategory::CommandsLinksPendingIntent:
        return "native.command-link-owner";
    case RuntimeStateCategory::EpisodeRewardTermination:
        return "native.episode-coordinator";
    case RuntimeStateCategory::PythonLoaderControllerCaches:
        return "python.mirror-owner";
    case RuntimeStateCategory::BackendDeviceAllocationsLeases:
        return "native.backend-resource-owner";
    case RuntimeStateCategory::InFlightRequestsResults:
        return "native.request-registry";
    case RuntimeStateCategory::ExternalSideEffects:
        return "native.side-effect-outbox";
    case RuntimeStateCategory::DiagnosticsTelemetry:
        return "native.telemetry-owner";
    }
    return "unsupported";
}

std::string_view runtime_state_schema_id(RuntimeStateCategory category) noexcept {
    switch (category) {
    case RuntimeStateCategory::CompositionProviderSystemGraph:
        return "echelon_forge.runtime_state.composition_graph.v1";
    case RuntimeStateCategory::EcsComponentTruth:
        return "echelon_forge.runtime_state.ecs.v1";
    case RuntimeStateCategory::RngState:
        return "echelon_forge.runtime_state.rng.v1";
    case RuntimeStateCategory::ClockCadence:
        return "echelon_forge.runtime_state.clock.v1";
    case RuntimeStateCategory::DelayedEventsQueues:
        return "echelon_forge.runtime_state.event_queue.v1";
    case RuntimeStateCategory::CommandsLinksPendingIntent:
        return "echelon_forge.runtime_state.command_link.v1";
    case RuntimeStateCategory::EpisodeRewardTermination:
        return "echelon_forge.runtime_state.episode.v1";
    case RuntimeStateCategory::PythonLoaderControllerCaches:
        return "echelon_forge.runtime_state.python_mirror.v1";
    case RuntimeStateCategory::BackendDeviceAllocationsLeases:
        return "echelon_forge.runtime_state.backend_resource.v1";
    case RuntimeStateCategory::InFlightRequestsResults:
        return "echelon_forge.runtime_state.in_flight.v1";
    case RuntimeStateCategory::ExternalSideEffects:
        return "echelon_forge.runtime_state.side_effect_outbox.v1";
    case RuntimeStateCategory::DiagnosticsTelemetry:
        return "echelon_forge.runtime_state.telemetry.v1";
    }
    return "unsupported";
}

const std::array<RuntimeStateDecoderReplayRule, kRuntimeStateCategoryCount> &
runtime_state_decoder_replay_matrix() noexcept {
    // These digests pin the candidate's schema/generation declaration. They
    // are not a substitute for a maintained owner migration implementation or
    // a durable replay log.
    static constexpr std::array<RuntimeStateDecoderReplayRule, kRuntimeStateCategoryCount> matrix =
        {{
            {.category = RuntimeStateCategory::CompositionProviderSystemGraph,
             .disposition = RuntimeStateDisposition::Rederive,
             .owner_id = "native.plan-owner",
             .schema_id = "echelon_forge.runtime_state.composition_graph.v1",
             .unknown_field_policy = RuntimeStateUnknownFieldPolicy::IgnoreDerived,
             .replay_policy = RuntimeStateReplayPolicy::Rederive,
             .migration_sha256 =
                 "9ef9e3832adec552a55887bffc9a4b60d893ebb0d4ae86bb2cb7914468c07ec7"},
            {.category = RuntimeStateCategory::EcsComponentTruth,
             .disposition = RuntimeStateDisposition::Transfer,
             .owner_id = "native.ecs-owner",
             .schema_id = "echelon_forge.runtime_state.ecs.v1",
             .unknown_field_policy = RuntimeStateUnknownFieldPolicy::Reject,
             .replay_policy = RuntimeStateReplayPolicy::Transfer,
             .migration_sha256 =
                 "5111035f03d8744cc88aa0e9716c86d1f14cace9a4c86bd1853570909bbcaf0f"},
            {.category = RuntimeStateCategory::RngState,
             .disposition = RuntimeStateDisposition::Transfer,
             .owner_id = "native.rng-owner",
             .schema_id = "echelon_forge.runtime_state.rng.v1",
             .unknown_field_policy = RuntimeStateUnknownFieldPolicy::Reject,
             .replay_policy = RuntimeStateReplayPolicy::Transfer,
             .migration_sha256 =
                 "cab140c97bf173773b815ccf9dda160229d17a9877d827f1bdb898f22e032f98"},
            {.category = RuntimeStateCategory::ClockCadence,
             .disposition = RuntimeStateDisposition::Transfer,
             .owner_id = "native.clock-owner",
             .schema_id = "echelon_forge.runtime_state.clock.v1",
             .unknown_field_policy = RuntimeStateUnknownFieldPolicy::Reject,
             .replay_policy = RuntimeStateReplayPolicy::Transfer,
             .migration_sha256 =
                 "77574d276c28d69262251a9f3235b172a4de0be65b3f95762a57c3887a366810"},
            {.category = RuntimeStateCategory::DelayedEventsQueues,
             .disposition = RuntimeStateDisposition::Transfer,
             .owner_id = "native.event-queue-owner",
             .schema_id = "echelon_forge.runtime_state.event_queue.v1",
             .unknown_field_policy = RuntimeStateUnknownFieldPolicy::Reject,
             .replay_policy = RuntimeStateReplayPolicy::Transfer,
             .migration_sha256 =
                 "22b62cc2ddda03a92fe5241d75d0b8eef1a9733177a7013629bb38e6254d454e"},
            {.category = RuntimeStateCategory::CommandsLinksPendingIntent,
             .disposition = RuntimeStateDisposition::Transfer,
             .owner_id = "native.command-link-owner",
             .schema_id = "echelon_forge.runtime_state.command_link.v1",
             .unknown_field_policy = RuntimeStateUnknownFieldPolicy::Reject,
             .replay_policy = RuntimeStateReplayPolicy::Transfer,
             .migration_sha256 =
                 "a06155fc719bd7c0310e3f126d639de62249521d3c693ab42a8ea744cd6dc422"},
            {.category = RuntimeStateCategory::EpisodeRewardTermination,
             .disposition = RuntimeStateDisposition::Transfer,
             .owner_id = "native.episode-coordinator",
             .schema_id = "echelon_forge.runtime_state.episode.v1",
             .unknown_field_policy = RuntimeStateUnknownFieldPolicy::Reject,
             .replay_policy = RuntimeStateReplayPolicy::Transfer,
             .migration_sha256 =
                 "f81ed76d9c3baeed2599dbabc2969e0713358871fbc73d1d6d0aa640a7b7dbba"},
            {.category = RuntimeStateCategory::PythonLoaderControllerCaches,
             .disposition = RuntimeStateDisposition::Rederive,
             .owner_id = "python.mirror-owner",
             .schema_id = "echelon_forge.runtime_state.python_mirror.v1",
             .unknown_field_policy = RuntimeStateUnknownFieldPolicy::IgnoreDerived,
             .replay_policy = RuntimeStateReplayPolicy::Rederive,
             .migration_sha256 =
                 "ff8ccbd6a22104c5519531c97a9b01024cec0dd7f5f8d57035a88d1560e911e7"},
            {.category = RuntimeStateCategory::BackendDeviceAllocationsLeases,
             .disposition = RuntimeStateDisposition::Rederive,
             .owner_id = "native.backend-resource-owner",
             .schema_id = "echelon_forge.runtime_state.backend_resource.v1",
             .unknown_field_policy = RuntimeStateUnknownFieldPolicy::IgnoreDerived,
             .replay_policy = RuntimeStateReplayPolicy::Rederive,
             .migration_sha256 =
                 "5ae26b98c49d2373b12b056dbed3ff2731ddf4282bd2677459b13bdf09af0a88"},
            {.category = RuntimeStateCategory::InFlightRequestsResults,
             .disposition = RuntimeStateDisposition::Drain,
             .owner_id = "native.request-registry",
             .schema_id = "echelon_forge.runtime_state.in_flight.v1",
             .unknown_field_policy = RuntimeStateUnknownFieldPolicy::Reject,
             .replay_policy = RuntimeStateReplayPolicy::Drain,
             .migration_sha256 =
                 "34c0e4d9b44f62737a8eea38951319a20177a040457a77aabbc183574010b383"},
            {.category = RuntimeStateCategory::ExternalSideEffects,
             .disposition = RuntimeStateDisposition::NotApplicable,
             .owner_id = "native.side-effect-outbox",
             .schema_id = "echelon_forge.runtime_state.side_effect_outbox.v1",
             .unknown_field_policy = RuntimeStateUnknownFieldPolicy::Reject,
             .replay_policy = RuntimeStateReplayPolicy::Reject,
             .migration_sha256 =
                 "ce084f5eb8fb333b0437e6f7a66badd5fb5ae2f192df859e4cb9b7fb07f79a92"},
            {.category = RuntimeStateCategory::DiagnosticsTelemetry,
             .disposition = RuntimeStateDisposition::Rederive,
             .owner_id = "native.telemetry-owner",
             .schema_id = "echelon_forge.runtime_state.telemetry.v1",
             .unknown_field_policy = RuntimeStateUnknownFieldPolicy::IgnoreDerived,
             .replay_policy = RuntimeStateReplayPolicy::Rederive,
             .migration_sha256 =
                 "3f205d207034c8f48dc00408a8836da76bd0a7cfe4e82b24e4c80a3ad5ccfd66"},
        }};
    return matrix;
}

const RuntimeStateDecoderReplayRule *
runtime_state_decoder_replay_rule(RuntimeStateCategory category) noexcept {
    const auto index = static_cast<std::size_t>(category);
    if (index >= kRuntimeStateCategoryCount) {
        return nullptr;
    }
    return &runtime_state_decoder_replay_matrix()[index];
}

RuntimeStateTransferProfile runtime_state_transfer_profile_from_decoder_matrix(
    std::string profile_id, std::uint32_t profile_generation, std::string source_plan_sha256,
    std::string target_plan_sha256) {
    RuntimeStateTransferProfile profile{
        .profile_id = std::move(profile_id),
        .profile_generation = profile_generation,
        .source_plan_sha256 = std::move(source_plan_sha256),
        .target_plan_sha256 = std::move(target_plan_sha256),
    };
    profile.rows.reserve(kRuntimeStateCategoryCount);
    for (const RuntimeStateDecoderReplayRule &rule : runtime_state_decoder_replay_matrix()) {
        profile.rows.push_back({
            .category = rule.category,
            .disposition = rule.disposition,
            .owner_id = std::string(rule.owner_id),
            .schema_id = std::string(rule.schema_id),
            .minimum_schema_generation = rule.previous_schema_generation,
            .maximum_schema_generation = rule.current_schema_generation,
            .truth_affecting = category_requires_truth_schema(rule.category),
        });
    }
    return profile;
}

std::string runtime_state_payload_sha256(const std::vector<std::uint8_t> &payload) {
    return sha256_hex(
        std::string_view(reinterpret_cast<const char *>(payload.data()), payload.size()));
}

std::vector<std::uint8_t> runtime_state_canonical_payload(const RuntimeStateCensusEntry &entry) {
    std::string output("echelon_forge.runtime_state_payload.v1\n");
    append_text(output, "category", runtime_state_category_name(entry.category));
    append_text(output, "owner_id", entry.owner_id);
    append_text(output, "schema_id", entry.schema_id);
    append_number(output, "schema_generation", entry.schema_generation);
    append_text(output, "state_content_sha256", entry.state_content_sha256);
    append_number(output, "item_count", entry.item_count);
    append_number(output, "settled_item_count", entry.settled_item_count);
    append_number(output, "sequence_high_watermark", entry.sequence_high_watermark);
    append_number(output, "rng_draw_position", entry.rng_draw_position);
    append_number(output, "simulation_tick", entry.simulation_tick);
    append_number(output, "step_sequence", entry.step_sequence);
    append_number(output, "barrier_sequence", entry.barrier_sequence);
    return {output.begin(), output.end()};
}

std::string runtime_state_census_entry_sha256(const RuntimeStateCensusEntry &entry) {
    return sha256_hex(canonical_state_entry_bytes(entry));
}

std::string
canonical_episode_transition_receipt_bytes(const RuntimeEpisodeTransitionReceipt &receipt) {
    std::string output("echelon_forge.runtime_episode_transition_receipt.v1\n");
    append_number(output, "protocol_generation", receipt.protocol_generation);
    append_number(output, "kind", static_cast<std::uint8_t>(receipt.kind));
    append_identity(output, "idempotency_key", receipt.idempotency_key);
    append_episode(output, "episode_before", receipt.episode_before);
    append_episode(output, "episode_after", receipt.episode_after);
    append_number(output, "previous_step_sequence", receipt.previous_step_sequence);
    append_number(output, "resulting_step_sequence", receipt.resulting_step_sequence);
    append_number(output, "resulting_phase", static_cast<std::uint8_t>(receipt.resulting_phase));
    append_number(output, "terminal", receipt.terminal ? 1 : 0);
    append_number(output, "reset_applied", receipt.reset_applied ? 1 : 0);
    append_identity(output, "snapshot_id", receipt.snapshot_id);
    append_text(output, "snapshot_sha256", receipt.snapshot_sha256);
    append_number(output, "barrier_sequence", receipt.barrier_sequence);
    return output;
}

std::string
canonical_episode_transition_intent_bytes(const RuntimeEpisodeTransitionIntent &intent) {
    std::string output("echelon_forge.runtime_episode_transition_intent.v1\n");
    append_number(output, "protocol_generation", intent.protocol_generation);
    append_number(output, "kind", static_cast<std::uint8_t>(intent.kind));
    append_episode(output, "expected", intent.expected_episode);
    append_number(output, "expected_step_sequence", intent.expected_step_sequence);
    append_identity(output, "idempotency_key", intent.idempotency_key);
    append_text(output, "payload_sha256", intent.payload_sha256);
    append_number(output, "production_authorized", intent.production_authorized ? 1 : 0);
    return output;
}

bool RuntimeEpisodeTransitionReceipt::well_formed() const noexcept {
    try {
        return protocol_generation == kRuntimeEpisodeHandshakeGeneration &&
               supported_intent(kind) && idempotency_key.well_formed() &&
               episode_before.well_formed() && episode_after.well_formed() &&
               snapshot_id.well_formed() && is_lower_hex_sha256(snapshot_sha256) &&
               is_lower_hex_sha256(receipt_sha256) &&
               sha256_hex(canonical_episode_transition_receipt_bytes(*this)) == receipt_sha256;
    } catch (...) {
        return false;
    }
}

RuntimeEpisodeCoordinatorCreateResult
RuntimeEpisodeCoordinatorCandidate::create(const RuntimeEpisodeCoordinatorConfig &config) {
    if (config.production_authorized) {
        return {.status = failure(RuntimeStateTransferError::ProductionAuthorityForbidden,
                                  "P4-B coordinator is dark/shadow only"),
                .coordinator = {}};
    }
    if (config.initial_phase != RuntimeEpisodePhase::Running &&
        config.initial_phase != RuntimeEpisodePhase::Terminal) {
        return {.status = failure(RuntimeStateTransferError::InvalidArgument,
                                  "initial coordinator phase must be running or terminal"),
                .coordinator = {}};
    }
    if (!config.initial_episode.well_formed() || !config.initial_snapshot_id.well_formed() ||
        !is_lower_hex_sha256(config.initial_snapshot_sha256)) {
        return {.status = failure(RuntimeStateTransferError::InvalidArgument,
                                  "initial episode coordinator state is malformed"),
                .coordinator = {}};
    }
    if (!reserve_world(config.initial_episode.world)) {
        return {.status = failure(RuntimeStateTransferError::DuplicateCoordinator,
                                  "the world already has a native episode coordinator"),
                .coordinator = {}};
    }
    try {
        auto state = std::make_shared<RuntimeEpisodeCoordinatorState>(config);
        return {.status = success(),
                .coordinator = std::unique_ptr<RuntimeEpisodeCoordinatorCandidate>(
                    new RuntimeEpisodeCoordinatorCandidate(std::move(state)))};
    } catch (...) {
        release_world(config.initial_episode.world);
        return {.status = failure(RuntimeStateTransferError::InvalidArgument,
                                  "episode coordinator allocation failed"),
                .coordinator = {}};
    }
}

RuntimeEpisodeCoordinatorCandidate::RuntimeEpisodeCoordinatorCandidate(
    std::shared_ptr<RuntimeEpisodeCoordinatorState> state) noexcept
    : state_(std::move(state)) {}

RuntimeEpisodeCoordinatorCandidate::~RuntimeEpisodeCoordinatorCandidate() = default;

RuntimeEpisodeTransitionResult
RuntimeEpisodeCoordinatorCandidate::submit(const RuntimeEpisodeTransitionIntent &intent,
                                           RuntimeNativeEpisodeControl &control) {
    std::unique_lock<std::mutex> lock(state_->mutex);
    if (intent.production_authorized) {
        return {.status = failure(RuntimeStateTransferError::ProductionAuthorityForbidden,
                                  "P4-B transition intent is dark/shadow only")};
    }
    if (intent.protocol_generation != kRuntimeEpisodeHandshakeGeneration ||
        !supported_intent(intent.kind) || !intent.expected_episode.well_formed() ||
        !intent.idempotency_key.well_formed() || !is_lower_hex_sha256(intent.payload_sha256)) {
        return {.status = failure(RuntimeStateTransferError::InvalidArgument,
                                  "episode transition intent is malformed")};
    }
    const std::string fingerprint = intent_fingerprint(intent);
    const auto existing =
        std::find_if(state_->receipts.begin(), state_->receipts.end(), [&](const auto &record) {
            return record.idempotency_key == intent.idempotency_key;
        });
    if (existing != state_->receipts.end()) {
        if (existing->intent_fingerprint != fingerprint) {
            return {.status = failure(RuntimeStateTransferError::IdempotencyConflict,
                                      "idempotency key was reused for a different intent")};
        }
        return {.status = success(), .receipt = existing->receipt, .replayed = true};
    }
    if (intent.expected_step_sequence < state_->compacted_step_sequence) {
        return {.status = failure(RuntimeStateTransferError::ReceiptResyncRequired,
                                  "intent is older than the acknowledged receipt window")};
    }
    if (state_->receipts.size() >= kMaxTransitionReceipts) {
        return {.status = failure(RuntimeStateTransferError::ReceiptBudgetExhausted,
                                  "transition receipt retention budget is exhausted")};
    }
    if (state_->mutation_in_progress) {
        return {.status = failure(RuntimeStateTransferError::ConcurrentMutation,
                                  "a native episode mutation is already in progress")};
    }
    if (!same_episode(intent.expected_episode, state_->episode) ||
        intent.expected_step_sequence != state_->step_sequence) {
        return {.status = failure(RuntimeStateTransferError::StaleIntent,
                                  "episode identity or step sequence is stale")};
    }
    if ((intent.kind == RuntimeEpisodeIntentKind::Action &&
         state_->phase != RuntimeEpisodePhase::Running) ||
        (intent.kind == RuntimeEpisodeIntentKind::Reset &&
         state_->phase != RuntimeEpisodePhase::Terminal)) {
        return {.status = failure(RuntimeStateTransferError::AdmissionClosed,
                                  "intent is not legal in the current native episode phase")};
    }
    const RuntimeEpisodeRef episode_before = state_->episode;
    const RuntimeEpisodePhase phase_before = state_->phase;
    const std::uint64_t step_before = state_->step_sequence;
    RuntimeNativeEpisodeCommand command{.intent = intent,
                                        .authorized_episode_after = episode_before,
                                        .authorized_resulting_step_sequence = step_before};
    bool reset_world_reserved = false;
    if (intent.kind == RuntimeEpisodeIntentKind::Action) {
        if (step_before == std::numeric_limits<std::uint64_t>::max()) {
            return {.status = failure(RuntimeStateTransferError::SequenceExhausted,
                                      "action step sequence is exhausted")};
        }
        command.authorized_resulting_step_sequence = step_before + 1;
    } else {
        if (state_->episode.episode_generation == std::numeric_limits<std::uint64_t>::max() ||
            state_->episode.world.world_generation == std::numeric_limits<std::uint64_t>::max() ||
            state_->barrier_sequence == std::numeric_limits<std::uint64_t>::max()) {
            return {.status = failure(RuntimeStateTransferError::SequenceExhausted,
                                      "reset episode or barrier sequence is exhausted")};
        }
        command.authorized_episode_after = state_->episode;
        command.authorized_episode_after.episode_id = mint_nonce();
        ++command.authorized_episode_after.episode_generation;
        ++command.authorized_episode_after.world.world_generation;
        command.authorized_resulting_step_sequence = 0;
        if (!reserve_world(command.authorized_episode_after.world)) {
            return {.status = failure(RuntimeStateTransferError::DuplicateCoordinator,
                                      "reset target world generation is already owned")};
        }
        reset_world_reserved = true;
    }
    state_->mutation_in_progress = true;
    lock.unlock();
    RuntimeNativeEpisodeMutation mutation;
    try {
        mutation = control.apply(command);
    } catch (...) {
        mutation = {};
    }
    lock.lock();
    state_->mutation_in_progress = false;
    if (!mutation.applied) {
        if (reset_world_reserved) {
            release_world(command.authorized_episode_after.world);
        }
        return {.status = failure(RuntimeStateTransferError::NativeMutationFailed,
                                  "native mutation was not applied")};
    }
    if (!mutation.snapshot_id.well_formed() || !is_lower_hex_sha256(mutation.snapshot_sha256) ||
        (intent.kind == RuntimeEpisodeIntentKind::Reset && mutation.terminal)) {
        if (reset_world_reserved) {
            release_world(state_->episode.world);
            state_->episode = command.authorized_episode_after;
        }
        state_->phase = RuntimeEpisodePhase::FailStopped;
        return {.status = failure(RuntimeStateTransferError::NativeMutationFailed,
                                  "applied native mutation violated its coordinator command")};
    }
    if (!same_episode(state_->episode, episode_before) || state_->phase != phase_before ||
        state_->step_sequence != step_before) {
        if (reset_world_reserved) {
            release_world(command.authorized_episode_after.world);
        }
        state_->phase = RuntimeEpisodePhase::FailStopped;
        return {.status = failure(RuntimeStateTransferError::ConcurrentMutation,
                                  "coordinator state changed after an applied native mutation")};
    }

    bool truth_state_advanced = false;
    try {
        RuntimeEpisodeTransitionReceipt receipt{
            .protocol_generation = kRuntimeEpisodeHandshakeGeneration,
            .kind = intent.kind,
            .idempotency_key = intent.idempotency_key,
            .episode_before = episode_before,
            .episode_after = episode_before,
            .previous_step_sequence = step_before,
            .resulting_step_sequence = step_before,
            .resulting_phase = phase_before,
            .terminal = false,
            .reset_applied = false,
            .snapshot_id = mutation.snapshot_id,
            .snapshot_sha256 = mutation.snapshot_sha256,
            .barrier_sequence = state_->barrier_sequence,
        };
        if (intent.kind == RuntimeEpisodeIntentKind::Action) {
            state_->step_sequence = command.authorized_resulting_step_sequence;
            state_->phase =
                mutation.terminal ? RuntimeEpisodePhase::Terminal : RuntimeEpisodePhase::Running;
            receipt.resulting_step_sequence = state_->step_sequence;
            receipt.resulting_phase = state_->phase;
            receipt.terminal = mutation.terminal;
        } else {
            release_world(state_->episode.world);
            ++state_->barrier_sequence;
            state_->episode = command.authorized_episode_after;
            state_->step_sequence = command.authorized_resulting_step_sequence;
            state_->phase = RuntimeEpisodePhase::Running;
            receipt.episode_after = state_->episode;
            receipt.resulting_step_sequence = 0;
            receipt.resulting_phase = state_->phase;
            receipt.reset_applied = true;
            receipt.barrier_sequence = state_->barrier_sequence;
        }
        state_->snapshot_id = mutation.snapshot_id;
        state_->snapshot_sha256 = mutation.snapshot_sha256;
        truth_state_advanced = true;
        receipt.receipt_sha256 = sha256_hex(canonical_episode_transition_receipt_bytes(receipt));
        state_->receipts.push_back({.idempotency_key = intent.idempotency_key,
                                    .intent_fingerprint = fingerprint,
                                    .receipt = receipt});
        return {.status = success(), .receipt = receipt, .replayed = false};
    } catch (...) {
        // The native mutation already happened, but a durable receipt could
        // not be constructed or retained.  Fail-stop the coordinator rather
        // than exposing a truth state that can be advanced without an
        // idempotent replay record.  If reset bookkeeping had not committed,
        // release its reserved target world before returning.
        if (reset_world_reserved && !truth_state_advanced) {
            release_world(command.authorized_episode_after.world);
        }
        state_->phase = RuntimeEpisodePhase::FailStopped;
        return {.status = failure(RuntimeStateTransferError::NativeMutationFailed,
                                  "native truth advanced without a durable transition receipt")};
    }
}

RuntimeStateTransferStatus RuntimeEpisodeCoordinatorCandidate::acknowledge_receipt(
    const RuntimeEpisodeTransitionReceipt &receipt) {
    if (!receipt.well_formed()) {
        return failure(RuntimeStateTransferError::ReceiptAcknowledgementInvalid,
                       "receipt acknowledgement is not a valid native receipt");
    }
    std::lock_guard<std::mutex> lock(state_->mutex);
    if (state_->mutation_in_progress) {
        return failure(RuntimeStateTransferError::ConcurrentMutation,
                       "receipt acknowledgement cannot race a native episode mutation");
    }
    const auto found =
        std::find_if(state_->receipts.begin(), state_->receipts.end(), [&](const auto &record) {
            return record.idempotency_key == receipt.idempotency_key && record.receipt == receipt;
        });
    if (found == state_->receipts.end()) {
        if (receipt.resulting_step_sequence <= state_->compacted_step_sequence &&
            receipt.barrier_sequence <= state_->compacted_barrier_sequence &&
            receipt.receipt_sha256 == state_->compacted_receipt_sha256) {
            return success();
        }
        return failure(RuntimeStateTransferError::ReceiptAcknowledgementInvalid,
                       "receipt acknowledgement is unknown to this coordinator");
    }
    state_->compacted_step_sequence =
        std::max(state_->compacted_step_sequence, receipt.resulting_step_sequence);
    state_->compacted_barrier_sequence =
        std::max(state_->compacted_barrier_sequence, receipt.barrier_sequence);
    state_->compacted_receipt_sha256 = receipt.receipt_sha256;
    state_->receipts.erase(std::remove_if(state_->receipts.begin(), state_->receipts.end(),
                                          [&](const auto &record) {
                                              return record.receipt.resulting_step_sequence <=
                                                         state_->compacted_step_sequence &&
                                                     record.receipt.barrier_sequence <=
                                                         state_->compacted_barrier_sequence;
                                          }),
                           state_->receipts.end());
    return success();
}

RuntimeEpisodeBarrierAdmission RuntimeEpisodeCoordinatorCandidate::open_replacement_barrier(
    const RuntimeEpisodeRef &expected_episode, std::uint64_t expected_step_sequence) {
    std::lock_guard<std::mutex> lock(state_->mutex);
    if (!same_episode(expected_episode, state_->episode) ||
        expected_step_sequence != state_->step_sequence) {
        return {.status = failure(RuntimeStateTransferError::StaleIntent,
                                  "replacement barrier expectation is stale")};
    }
    if (state_->phase != RuntimeEpisodePhase::Terminal || state_->mutation_in_progress) {
        return {.status = failure(RuntimeStateTransferError::BarrierRequired,
                                  "replacement requires the terminal native episode barrier")};
    }
    if (state_->barrier_sequence == std::numeric_limits<std::uint64_t>::max()) {
        return {.status = failure(RuntimeStateTransferError::SequenceExhausted,
                                  "episode barrier sequence is exhausted")};
    }
    ++state_->barrier_sequence;
    state_->phase = RuntimeEpisodePhase::ReplacementBarrier;
    state_->open_barrier_nonce = mint_nonce();
    RuntimeEpisodeCoordinatorSnapshot snapshot{
        .episode = state_->episode,
        .phase = state_->phase,
        .step_sequence = state_->step_sequence,
        .barrier_sequence = state_->barrier_sequence,
        .snapshot_id = state_->snapshot_id,
        .snapshot_sha256 = state_->snapshot_sha256,
    };
    auto token = std::make_shared<RuntimeEpisodeBarrierToken>();
    token->coordinator = state_;
    token->coordinator_nonce = state_->coordinator_nonce;
    token->barrier_nonce = state_->open_barrier_nonce;
    token->snapshot = snapshot;
    return {.status = success(), .capability = RuntimeEpisodeBarrierCapability(std::move(token))};
}

RuntimeNativeEpisodeAdmission RuntimeEpisodeCoordinatorCandidate::issue_episode_capability() {
    std::lock_guard<std::mutex> lock(state_->mutex);
    // A terminal episode still needs a host-bound capability so the native
    // coordinator can accept the explicit Reset intent. The submit path keeps
    // Action admission closed in Terminal; capability issuance alone does not
    // authorize a second truth mutation.
    if ((state_->phase != RuntimeEpisodePhase::Running &&
         state_->phase != RuntimeEpisodePhase::Terminal) ||
        state_->mutation_in_progress) {
        return {.status = failure(RuntimeStateTransferError::AdmissionClosed,
                                  "native episode is not admitting shadow work"),
                .capability = {}};
    }
    auto token = std::make_shared<RuntimeNativeEpisodeToken>();
    token->coordinator = state_;
    token->coordinator_nonce = state_->coordinator_nonce;
    token->episode = state_->episode;
    token->step_sequence = state_->step_sequence;
    return {.status = success(), .capability = RuntimeNativeEpisodeCapability(std::move(token))};
}

RuntimeIdentity128 RuntimeEpisodeCoordinatorCandidate::coordinator_nonce() const noexcept {
    if (state_ == nullptr) {
        return {};
    }
    std::lock_guard<std::mutex> lock(state_->mutex);
    return state_->coordinator_nonce;
}

RuntimeStateTransferStatus RuntimeEpisodeCoordinatorCandidate::abort_replacement_barrier(
    RuntimeEpisodeBarrierCapability &&capability) {
    if (capability.token_ == nullptr) {
        return failure(RuntimeStateTransferError::InvalidArgument,
                       "replacement barrier capability is empty");
    }
    const auto token = std::move(capability.token_);
    std::lock_guard<std::mutex> token_lock(token->mutex);
    if (token->claimed || token->released) {
        return failure(RuntimeStateTransferError::BarrierReplay,
                       "replacement barrier capability is already claimed");
    }
    const auto coordinator = token->coordinator.lock();
    if (coordinator != state_) {
        return failure(RuntimeStateTransferError::StaleIntent,
                       "replacement barrier belongs to another coordinator");
    }
    std::lock_guard<std::mutex> coordinator_lock(state_->mutex);
    if (state_->phase != RuntimeEpisodePhase::ReplacementBarrier ||
        state_->open_barrier_nonce != token->barrier_nonce ||
        state_->barrier_sequence != token->snapshot.barrier_sequence) {
        return failure(RuntimeStateTransferError::StaleIntent,
                       "replacement barrier is no longer current");
    }
    state_->phase = RuntimeEpisodePhase::Terminal;
    state_->open_barrier_nonce = {};
    token->released = true;
    return success();
}

RuntimeEpisodeCoordinatorSnapshot RuntimeEpisodeCoordinatorCandidate::snapshot() const {
    std::lock_guard<std::mutex> lock(state_->mutex);
    return {.episode = state_->episode,
            .phase = state_->phase,
            .step_sequence = state_->step_sequence,
            .barrier_sequence = state_->barrier_sequence,
            .snapshot_id = state_->snapshot_id,
            .snapshot_sha256 = state_->snapshot_sha256};
}

RuntimeNativeEpisodeCapability::RuntimeNativeEpisodeCapability(
    std::shared_ptr<RuntimeNativeEpisodeToken> token) noexcept
    : token_(std::move(token)) {}

RuntimeNativeEpisodeCapability::RuntimeNativeEpisodeCapability(
    RuntimeNativeEpisodeCapability &&other) noexcept
    : token_(std::move(other.token_)) {}

RuntimeNativeEpisodeCapability &
RuntimeNativeEpisodeCapability::operator=(RuntimeNativeEpisodeCapability &&other) noexcept {
    if (this != &other) {
        token_ = std::move(other.token_);
    }
    return *this;
}

bool RuntimeNativeEpisodeCapability::valid() const noexcept {
    if (token_ == nullptr) {
        return false;
    }
    try {
        std::lock_guard<std::mutex> token_lock(token_->mutex);
        if (token_->host_claimed) {
            return false;
        }
        const auto coordinator = token_->coordinator.lock();
        if (coordinator == nullptr) {
            return false;
        }
        std::lock_guard<std::mutex> coordinator_lock(coordinator->mutex);
        return coordinator->coordinator_nonce == token_->coordinator_nonce &&
               (coordinator->phase == RuntimeEpisodePhase::Running ||
                coordinator->phase == RuntimeEpisodePhase::Terminal) &&
               coordinator->episode == token_->episode &&
               coordinator->step_sequence == token_->step_sequence;
    } catch (...) {
        return false;
    }
}

RuntimeEpisodeRef RuntimeNativeEpisodeCapability::episode() const noexcept {
    return token_ == nullptr ? RuntimeEpisodeRef{} : token_->episode;
}

std::uint64_t RuntimeNativeEpisodeCapability::step_sequence() const noexcept {
    return token_ == nullptr ? 0 : token_->step_sequence;
}

RuntimeIdentity128 RuntimeNativeEpisodeCapability::coordinator_nonce() const noexcept {
    return token_ == nullptr ? RuntimeIdentity128{} : token_->coordinator_nonce;
}

RuntimeStateTransferStatus
RuntimeNativeEpisodeCapability::consume_for_host(const RuntimeIncarnationRef &expected_source) {
    if (token_ == nullptr) {
        return failure(RuntimeStateTransferError::InvalidArgument,
                       "native episode capability is empty");
    }
    std::lock_guard<std::mutex> token_lock(token_->mutex);
    if (token_->host_claimed) {
        return failure(RuntimeStateTransferError::BarrierReplay,
                       "native episode capability was already consumed");
    }
    const auto coordinator = token_->coordinator.lock();
    if (coordinator == nullptr) {
        return failure(RuntimeStateTransferError::StaleIntent,
                       "native episode coordinator no longer exists");
    }
    std::lock_guard<std::mutex> coordinator_lock(coordinator->mutex);
    if (coordinator->mutation_in_progress) {
        return failure(RuntimeStateTransferError::ConcurrentMutation,
                       "native episode mutation is in progress");
    }
    if (token_->episode.world.incarnation != expected_source ||
        coordinator->coordinator_nonce != token_->coordinator_nonce ||
        (coordinator->phase != RuntimeEpisodePhase::Running &&
         coordinator->phase != RuntimeEpisodePhase::Terminal) ||
        coordinator->episode != token_->episode ||
        coordinator->step_sequence != token_->step_sequence) {
        return failure(RuntimeStateTransferError::StaleIntent,
                       "native episode capability is stale or belongs to another slot");
    }
    token_->host_claimed = true;
    token_->coordinator_owner = coordinator;
    return success();
}

RuntimeStateTransferStatus RuntimeNativeEpisodeCapability::validate_for_host(
    const RuntimeIncarnationRef &expected_source) const {
    if (token_ == nullptr) {
        return failure(RuntimeStateTransferError::InvalidArgument,
                       "native episode capability is empty");
    }
    std::lock_guard<std::mutex> token_lock(token_->mutex);
    if (!token_->host_claimed) {
        return failure(RuntimeStateTransferError::BarrierRequired,
                       "native episode capability was not claimed by the host");
    }
    const auto coordinator = token_->coordinator_owner != nullptr ? token_->coordinator_owner
                                                                  : token_->coordinator.lock();
    if (coordinator == nullptr) {
        return failure(RuntimeStateTransferError::StaleIntent,
                       "native episode coordinator no longer exists");
    }
    std::lock_guard<std::mutex> coordinator_lock(coordinator->mutex);
    if (coordinator->mutation_in_progress) {
        return failure(RuntimeStateTransferError::ConcurrentMutation,
                       "native episode mutation is in progress");
    }
    if (token_->episode.world.incarnation != expected_source ||
        coordinator->coordinator_nonce != token_->coordinator_nonce ||
        (coordinator->phase != RuntimeEpisodePhase::Running &&
         coordinator->phase != RuntimeEpisodePhase::Terminal) ||
        coordinator->episode != token_->episode ||
        coordinator->step_sequence != token_->step_sequence) {
        return failure(RuntimeStateTransferError::StaleIntent,
                       "host-bound native episode capability is stale");
    }
    return success();
}

RuntimeEpisodeBarrierCapability::RuntimeEpisodeBarrierCapability(
    std::shared_ptr<RuntimeEpisodeBarrierToken> token) noexcept
    : token_(std::move(token)) {}

RuntimeEpisodeBarrierCapability::RuntimeEpisodeBarrierCapability(
    RuntimeEpisodeBarrierCapability &&other) noexcept
    : token_(std::move(other.token_)) {}

RuntimeEpisodeBarrierCapability &
RuntimeEpisodeBarrierCapability::operator=(RuntimeEpisodeBarrierCapability &&other) noexcept {
    if (this != &other) {
        release_unclaimed_barrier(token_);
        token_ = std::move(other.token_);
    }
    return *this;
}

RuntimeEpisodeBarrierCapability::~RuntimeEpisodeBarrierCapability() {
    release_unclaimed_barrier(token_);
}

bool RuntimeEpisodeBarrierCapability::valid() const noexcept {
    if (token_ == nullptr) {
        return false;
    }
    try {
        std::lock_guard<std::mutex> token_lock(token_->mutex);
        if (token_->claimed || token_->released) {
            return false;
        }
        const auto coordinator = token_->coordinator.lock();
        if (coordinator == nullptr) {
            return false;
        }
        std::lock_guard<std::mutex> coordinator_lock(coordinator->mutex);
        return coordinator->phase == RuntimeEpisodePhase::ReplacementBarrier &&
               coordinator->coordinator_nonce == token_->coordinator_nonce &&
               coordinator->open_barrier_nonce == token_->barrier_nonce &&
               coordinator->barrier_sequence == token_->snapshot.barrier_sequence;
    } catch (...) {
        return false;
    }
}

RuntimeEpisodeCoordinatorSnapshot RuntimeEpisodeBarrierCapability::snapshot() const noexcept {
    return token_ == nullptr ? RuntimeEpisodeCoordinatorSnapshot{} : token_->snapshot;
}

RuntimeIdentity128 RuntimeEpisodeBarrierCapability::coordinator_nonce() const noexcept {
    return token_ == nullptr ? RuntimeIdentity128{} : token_->coordinator_nonce;
}

RuntimeStateTransferStatus
RuntimeEpisodeBarrierCapability::bind_for_host(const RuntimeIdentity128 &host_instance_nonce,
                                               std::uint64_t world_slot) noexcept {
    if (token_ == nullptr || !host_instance_nonce.well_formed()) {
        return failure(RuntimeStateTransferError::InvalidArgument,
                       "cannot bind an empty episode barrier to a host");
    }
    try {
        std::lock_guard<std::mutex> lock(token_->mutex);
        if (token_->claimed || token_->released || token_->host_bound ||
            token_->snapshot.episode.world.world_slot != world_slot) {
            return failure(RuntimeStateTransferError::BarrierReplay,
                           "episode barrier is already bound or consumed");
        }
        token_->host_instance_nonce = host_instance_nonce;
        token_->world_slot = world_slot;
        token_->host_bound = true;
        return success();
    } catch (...) {
        return failure(RuntimeStateTransferError::InvalidArgument,
                       "episode barrier host binding failed");
    }
}

RuntimeHostQuiescenceCapability::RuntimeHostQuiescenceCapability(
    std::shared_ptr<RuntimeHostQuiescenceToken> token) noexcept
    : token_(std::move(token)) {}

RuntimeHostQuiescenceCapability::RuntimeHostQuiescenceCapability(
    RuntimeHostQuiescenceCapability &&other) noexcept
    : token_(std::move(other.token_)) {}

RuntimeHostQuiescenceCapability &
RuntimeHostQuiescenceCapability::operator=(RuntimeHostQuiescenceCapability &&other) noexcept {
    if (this != &other) {
        release_unclaimed_quiescence(token_);
        token_ = std::move(other.token_);
    }
    return *this;
}

RuntimeHostQuiescenceCapability::~RuntimeHostQuiescenceCapability() {
    release_unclaimed_quiescence(token_);
}

RuntimeHostQuiescenceCapability RuntimeHostQuiescenceCapability::mint_for_host(
    const RuntimeIncarnationRef &source_slot, std::string source_plan_sha256,
    std::string target_plan_sha256, RuntimeIdentity128 source_resource_identity,
    RuntimeIdentity128 candidate_resource_identity,
    std::shared_ptr<RuntimeStateTransferOwnerRegistry> source_owner_registry,
    std::shared_ptr<RuntimeStateTransferOwnerRegistry> target_owner_registry,
    const RuntimeIdentity128 &host_instance_nonce, std::function<bool()> host_revalidate,
    std::function<void()> host_rollback, std::function<bool()> host_begin_transfer,
    std::function<bool()> host_claim_transfer, std::function<void()> host_end_transfer,
    std::uint64_t lifecycle_ticket, std::uint64_t candidate_sequence,
    std::uint64_t mutation_fence_sequence, std::size_t source_read_only_result_leases,
    bool cooperative_cancellation_acknowledged) {
    auto token = std::make_shared<RuntimeHostQuiescenceToken>();
    token->source_slot = source_slot;
    token->source_plan_sha256 = std::move(source_plan_sha256);
    token->target_plan_sha256 = std::move(target_plan_sha256);
    token->source_resource_identity = source_resource_identity;
    token->candidate_resource_identity = candidate_resource_identity;
    token->source_owner_registry = std::move(source_owner_registry);
    token->target_owner_registry = std::move(target_owner_registry);
    token->host_instance_nonce = host_instance_nonce;
    token->host_revalidate = std::move(host_revalidate);
    token->host_rollback = std::move(host_rollback);
    token->host_begin_transfer = std::move(host_begin_transfer);
    token->host_claim_transfer = std::move(host_claim_transfer);
    token->host_end_transfer = std::move(host_end_transfer);
    token->lifecycle_ticket = lifecycle_ticket;
    token->candidate_sequence = candidate_sequence;
    token->mutation_fence_sequence = mutation_fence_sequence;
    token->source_read_only_result_leases = source_read_only_result_leases;
    token->cooperative_cancellation_acknowledged = cooperative_cancellation_acknowledged;
    return RuntimeHostQuiescenceCapability(std::move(token));
}

bool RuntimeHostQuiescenceCapability::valid() const noexcept {
    if (token_ == nullptr) {
        return false;
    }
    try {
        std::lock_guard<std::mutex> lock(token_->mutex);
        return !token_->claimed && !token_->released && token_->source_slot.well_formed() &&
               is_lower_hex_sha256(token_->source_plan_sha256) &&
               is_lower_hex_sha256(token_->target_plan_sha256) &&
               token_->source_resource_identity.well_formed() &&
               token_->candidate_resource_identity.well_formed() &&
               token_->source_owner_registry != nullptr &&
               token_->target_owner_registry != nullptr &&
               token_->host_instance_nonce.well_formed() &&
               static_cast<bool>(token_->host_revalidate) &&
               static_cast<bool>(token_->host_begin_transfer) &&
               static_cast<bool>(token_->host_claim_transfer) &&
               static_cast<bool>(token_->host_end_transfer) && token_->lifecycle_ticket != 0 &&
               token_->candidate_sequence != 0 && token_->mutation_fence_sequence != 0 &&
               token_->cooperative_cancellation_acknowledged;
    } catch (...) {
        return false;
    }
}

RuntimeIncarnationRef RuntimeHostQuiescenceCapability::source_slot() const noexcept {
    return token_ == nullptr ? RuntimeIncarnationRef{} : token_->source_slot;
}

std::uint64_t RuntimeHostQuiescenceCapability::mutation_fence_sequence() const noexcept {
    return token_ == nullptr ? 0 : token_->mutation_fence_sequence;
}

RuntimeIdentity128 RuntimeHostQuiescenceCapability::candidate_resource_identity() const noexcept {
    return token_ == nullptr ? RuntimeIdentity128{} : token_->candidate_resource_identity;
}

RuntimeStateTransferValidationResult
RuntimeStateTransferValidator::validate(RuntimeStateTransferValidationRequest &&request) {
    RuntimeStateTransferStatus status = validate_profile(request.profile);
    if (!status) {
        return {.status = status, .transfer = {}};
    }
    if (request.evidence.production_authorized) {
        return {.status = failure(RuntimeStateTransferError::ProductionAuthorityForbidden,
                                  "P4-B state transfer is dark/shadow only"),
                .transfer = {}};
    }
    if (!request.host_quiescence.valid()) {
        return {.status = failure(RuntimeStateTransferError::BarrierRequired,
                                  "state transfer requires a live host quiescence fence"),
                .transfer = {}};
    }
    const auto quiescence_token = request.host_quiescence.token_;
    if (quiescence_token->source_owner_registry == nullptr ||
        quiescence_token->target_owner_registry == nullptr) {
        return {.status = failure(
                    RuntimeStateTransferError::SemanticEvidenceMissing,
                    "state transfer requires host-bound source and target owner registries"),
                .transfer = {}};
    }
    if (quiescence_token->source_owner_registry == quiescence_token->target_owner_registry) {
        return {.status =
                    failure(RuntimeStateTransferError::SemanticEvidenceMissing,
                            "state transfer requires distinct source and target owner registries"),
                .transfer = {}};
    }
    const RuntimeIdentity128 source_bound_resource =
        quiescence_token->source_owner_registry->bound_resource_identity();
    const RuntimeIdentity128 target_bound_resource =
        quiescence_token->target_owner_registry->bound_resource_identity();
    if (!source_bound_resource.well_formed() || !target_bound_resource.well_formed() ||
        source_bound_resource != quiescence_token->source_resource_identity ||
        target_bound_resource != quiescence_token->candidate_resource_identity) {
        return {.status = failure(
                    RuntimeStateTransferError::SemanticEvidenceMissing,
                    "owner registry is not bound to the admitted source or target resource"),
                .transfer = {}};
    }
    const void *source_binding = quiescence_token->source_owner_registry->owner_binding_token();
    const void *target_binding = quiescence_token->target_owner_registry->owner_binding_token();
    if (source_binding != nullptr && target_binding != nullptr &&
        source_binding == target_binding) {
        return {.status =
                    failure(RuntimeStateTransferError::SemanticEvidenceMissing,
                            "source and target owner registries capture the same owner instance"),
                .transfer = {}};
    }
    if ((request.census.contract_generation != kRuntimeStateTransferContractGeneration &&
         request.census.contract_generation != kRuntimeStateTransferPreviousGeneration) ||
        request.census.profile_id != request.profile.profile_id ||
        request.census.profile_generation != request.profile.profile_generation ||
        !request.census.source_slot.well_formed() ||
        request.census.source_plan_sha256 != request.profile.source_plan_sha256 ||
        request.census.target_plan_sha256 != request.profile.target_plan_sha256 ||
        request.evidence.source_final_mutation_fence_sequence == 0) {
        return {.status = failure(RuntimeStateTransferError::InvalidArgument,
                                  "state census or transfer evidence is malformed"),
                .transfer = {}};
    }
    {
        std::lock_guard<std::mutex> quiescence_lock(quiescence_token->mutex);
        if (quiescence_token->claimed || quiescence_token->released ||
            quiescence_token->source_slot != request.census.source_slot ||
            quiescence_token->source_plan_sha256 != request.profile.source_plan_sha256 ||
            quiescence_token->target_plan_sha256 != request.profile.target_plan_sha256 ||
            quiescence_token->mutation_fence_sequence !=
                request.evidence.source_final_mutation_fence_sequence) {
            return {.status =
                        failure(RuntimeStateTransferError::StaleIntent,
                                "state census does not bind the current host quiescence fence"),
                    .transfer = {}};
        }
    }
    if (!request.episode_barrier.valid()) {
        return {.status = failure(RuntimeStateTransferError::BarrierRequired,
                                  "state transfer requires a live native episode barrier"),
                .transfer = {}};
    }
    const auto barrier_token = request.episode_barrier.token_;
    {
        std::scoped_lock authority_locks(barrier_token->mutex, quiescence_token->mutex);
        if (!barrier_token->host_bound ||
            barrier_token->host_instance_nonce != quiescence_token->host_instance_nonce ||
            barrier_token->world_slot != barrier_token->snapshot.episode.world.world_slot) {
            return {.status =
                        failure(RuntimeStateTransferError::StaleIntent,
                                "episode barrier is not bound to the quiesced host authority"),
                    .transfer = {}};
        }
    }
    const RuntimeEpisodeCoordinatorSnapshot barrier_snapshot = request.episode_barrier.snapshot();
    if (barrier_snapshot.phase != RuntimeEpisodePhase::ReplacementBarrier ||
        barrier_snapshot.episode.world.incarnation != request.census.source_slot) {
        return {.status = failure(RuntimeStateTransferError::StaleIntent,
                                  "state census does not bind the current source barrier"),
                .transfer = {}};
    }

    // Pin the host/candidate before asking any owner to read source truth.  A
    // blocking export/import callback must not race candidate reclamation.
    HostTransferReservationGuard transfer_reservation;
    if (!quiescence_token->host_begin_transfer || !quiescence_token->host_begin_transfer()) {
        return {.status = failure(RuntimeStateTransferError::StaleIntent,
                                  "host transfer reservation was revoked before source export"),
                .transfer = {}};
    }
    transfer_reservation.release = quiescence_token->host_end_transfer;
    transfer_reservation.active = true;

    std::array<const RuntimeStateCensusEntry *, kRuntimeStateCategoryCount> entries{};
    for (const RuntimeStateCensusEntry &entry : request.census.entries) {
        if (!supported_category(entry.category)) {
            return {.status = failure(RuntimeStateTransferError::InvalidArgument,
                                      "state census contains an unsupported category"),
                    .transfer = {}};
        }
        const std::size_t index = static_cast<std::size_t>(entry.category);
        if (entries[index] != nullptr) {
            return {.status = failure(RuntimeStateTransferError::DuplicateCategory,
                                      "state census contains a duplicate category"),
                    .transfer = {}};
        }
        entries[index] = &entry;
    }
    for (std::size_t index = 0; index < entries.size(); ++index) {
        if (entries[index] == nullptr) {
            return {.status = failure(RuntimeStateTransferError::MissingCategory,
                                      "state census omits a required category"),
                    .transfer = {}};
        }
    }
    for (const RuntimeStateCensusRowPolicy &policy : request.profile.rows) {
        status = validate_entry(policy, *entries[static_cast<std::size_t>(policy.category)],
                                barrier_snapshot);
        if (!status) {
            return {.status = status, .transfer = {}};
        }
    }

    RuntimeStateOwnerExport source_export = quiescence_token->source_owner_registry->export_source(
        request.profile, request.census.source_slot,
        RuntimeStateOwnerExportContext{
            .barrier_snapshot = barrier_snapshot,
            .source_read_only_result_leases = quiescence_token->source_read_only_result_leases,
            .cooperative_cancellation_acknowledged =
                quiescence_token->cooperative_cancellation_acknowledged,
        });
    if (!source_export.status) {
        return {.status = source_export.status, .transfer = {}};
    }
    if (source_export.source_slot != request.census.source_slot ||
        !same_source_census(request.census, source_export.census)) {
        return {.status = failure(RuntimeStateTransferError::SemanticEvidenceMissing,
                                  "owner source export does not match the requested census"),
                .transfer = {}};
    }
    status = validate_source_artifacts(request.profile, request.census, source_export);
    if (!status) {
        return {.status = status, .transfer = {}};
    }

    RuntimeStateOwnerImportReceipt owner_receipt =
        quiescence_token->target_owner_registry->import_and_observe(
            request.profile, source_export, request.host_quiescence.candidate_resource_identity());
    ImportTransactionAbortGuard import_abort{
        .transaction = owner_receipt.transaction,
        .active = owner_receipt.transaction != nullptr,
    };
    if (!owner_receipt.status) {
        return {.status = owner_receipt.status, .transfer = {}};
    }
    if (owner_receipt.transaction == nullptr) {
        return {.status = failure(RuntimeStateTransferError::SemanticEvidenceMissing,
                                  "owner import did not return a rollback-capable transaction"),
                .transfer = {}};
    }
    const RuntimeStateOwnerImportTransactionStatus transaction_status =
        owner_receipt.transaction->status();
    if (transaction_status.error != RuntimeStateTransferError::None ||
        transaction_status.phase != RuntimeStateOwnerImportTransactionPhase::Prepared) {
        return {.status = failure(RuntimeStateTransferError::ImportTransactionStateInvalid,
                                  "owner import transaction is not in the prepared state"),
                .transfer = {}};
    }
    if (owner_receipt.candidate_resource_identity !=
            request.host_quiescence.candidate_resource_identity() ||
        owner_receipt.observations.size() != kRuntimeStateCategoryCount) {
        return {.status = failure(RuntimeStateTransferError::SemanticEvidenceMissing,
                                  "owner receipt is not bound to the complete candidate import"),
                .transfer = {}};
    }
    std::array<const RuntimeStateOwnerObservation *, kRuntimeStateCategoryCount> observations{};
    for (const RuntimeStateOwnerObservation &observation : owner_receipt.observations) {
        if (!supported_category(observation.category)) {
            return {.status = failure(RuntimeStateTransferError::SchemaMismatch,
                                      "owner receipt contains an unsupported category"),
                    .transfer = {}};
        }
        const std::size_t index = static_cast<std::size_t>(observation.category);
        if (observations[index] != nullptr) {
            return {.status = failure(RuntimeStateTransferError::DuplicateCategory,
                                      "owner receipt contains a duplicate category"),
                    .transfer = {}};
        }
        observations[index] = &observation;
    }
    for (const RuntimeStateCensusRowPolicy &policy : request.profile.rows) {
        const RuntimeStateCensusEntry &entry = *entries[static_cast<std::size_t>(policy.category)];
        const RuntimeStateOwnerObservation &observation =
            *observations[static_cast<std::size_t>(policy.category)];
        const auto artifact =
            std::find_if(source_export.artifacts.begin(), source_export.artifacts.end(),
                         [&](const RuntimeStateOwnerArtifact &candidate) {
                             return candidate.category == policy.category;
                         });
        if (artifact == source_export.artifacts.end()) {
            return {.status = failure(RuntimeStateTransferError::MissingCategory,
                                      "owner receipt has no source artifact"),
                    .transfer = {}};
        }
        RuntimeStateCensusEntry normalized_entry = entry;
        normalized_entry.schema_generation = kRuntimeStateTransferContractGeneration;
        if (entry.schema_generation != kRuntimeStateTransferContractGeneration) {
            normalized_entry.canonical_payload = runtime_state_canonical_payload(normalized_entry);
            normalized_entry.canonical_payload_sha256 =
                runtime_state_payload_sha256(normalized_entry.canonical_payload);
        }
        if (observation.owner_id != policy.owner_id || observation.schema_id != policy.schema_id ||
            observation.source_schema_generation != entry.schema_generation ||
            observation.schema_generation != kRuntimeStateTransferContractGeneration ||
            observation.candidate_resource_identity !=
                request.host_quiescence.candidate_resource_identity() ||
            !observation.exact_schema_decoded || observation.contains_unknown_truth_fields ||
            observation.contains_raw_process_handle || observation.item_count != entry.item_count ||
            observation.settled_item_count != entry.settled_item_count ||
            observation.source_entry_sha256 != runtime_state_census_entry_sha256(entry) ||
            observation.source_artifact_payload_sha256 != artifact->payload_sha256 ||
            !is_lower_hex_sha256(observation.candidate_artifact_payload_sha256) ||
            (entry.schema_generation == kRuntimeStateTransferContractGeneration &&
             observation.candidate_artifact_payload_sha256 != artifact->payload_sha256) ||
            observation.candidate_entry_sha256 !=
                runtime_state_census_entry_sha256(normalized_entry) ||
            observation.semantic_replay_sha256 != entry.semantic_evidence_sha256) {
            return {.status =
                        failure(RuntimeStateTransferError::SemanticEvidenceMissing,
                                "owner receipt does not prove exact source/import/replay equality"),
                    .transfer = {}};
        }
    }
    if (!quiescence_token->host_revalidate || !quiescence_token->host_revalidate()) {
        return {.status = failure(RuntimeStateTransferError::StaleIntent,
                                  "host quiescence was revoked during owner import"),
                .transfer = {}};
    }

    try {
        auto state = std::make_shared<RuntimeValidatedStateTransferState>();
        state->source_slot = request.census.source_slot;
        state->source_plan_sha256 = request.profile.source_plan_sha256;
        state->target_plan_sha256 = request.profile.target_plan_sha256;
        state->state_bundle_sha256 = sha256_hex(
            canonical_state_bundle_bytes(request.profile, request.census, source_export.artifacts,
                                         request.evidence, barrier_snapshot));
        state->transfer_fence_sequence = request.evidence.source_final_mutation_fence_sequence;
        state->episode_barrier_sequence = barrier_snapshot.barrier_sequence;
        state->source_barrier_snapshot = barrier_snapshot;
        state->lifecycle_ticket = quiescence_token->lifecycle_ticket;
        state->candidate_sequence = quiescence_token->candidate_sequence;
        state->candidate_resource_identity = quiescence_token->candidate_resource_identity;
        state->quiescence_token = quiescence_token;
        state->barrier_token = barrier_token;
        state->coordinator_owner = barrier_token->coordinator.lock();
        state->import_transaction = owner_receipt.transaction;
        if (!quiescence_token->host_claim_transfer || !quiescence_token->host_claim_transfer()) {
            return {.status = failure(RuntimeStateTransferError::StaleIntent,
                                      "host transfer changed before capability claim"),
                    .transfer = {}};
        }
        {
            std::scoped_lock capability_locks(quiescence_token->mutex, barrier_token->mutex);
            if (quiescence_token->claimed || quiescence_token->released || barrier_token->claimed ||
                barrier_token->released) {
                return {.status = failure(RuntimeStateTransferError::BarrierReplay,
                                          "host or episode barrier was already consumed"),
                        .transfer = {}};
            }
            quiescence_token->claimed = true;
            barrier_token->claimed = true;
        }
        state->host_end_transfer = transfer_reservation.disarm();
        import_abort.disarm();
        return {.status = success(), .transfer = RuntimeValidatedStateTransfer(std::move(state))};
    } catch (...) {
        return {.status = failure(RuntimeStateTransferError::InvalidArgument,
                                  "state-transfer capability allocation failed"),
                .transfer = {}};
    }
}

RuntimeValidatedStateTransfer::RuntimeValidatedStateTransfer(
    std::shared_ptr<RuntimeValidatedStateTransferState> state) noexcept
    : state_(std::move(state)) {}

RuntimeValidatedStateTransfer::RuntimeValidatedStateTransfer(
    RuntimeValidatedStateTransfer &&other) noexcept
    : state_(std::move(other.state_)) {}

RuntimeValidatedStateTransfer &
RuntimeValidatedStateTransfer::operator=(RuntimeValidatedStateTransfer &&other) noexcept {
    if (this != &other) {
        abort_for_host();
        state_ = std::move(other.state_);
    }
    return *this;
}

RuntimeValidatedStateTransfer::~RuntimeValidatedStateTransfer() {
    abort_for_host();
}

bool RuntimeValidatedStateTransfer::valid() const noexcept {
    if (state_ == nullptr) {
        return false;
    }
    try {
        std::lock_guard<std::mutex> lock(state_->mutex);
        return state_->lifecycle == RuntimeValidatedTransferLifecycle::Ready ||
               state_->lifecycle == RuntimeValidatedTransferLifecycle::Prepared;
    } catch (...) {
        return false;
    }
}

bool RuntimeValidatedStateTransfer::committed() const noexcept {
    if (state_ == nullptr) {
        return false;
    }
    try {
        std::lock_guard<std::mutex> lock(state_->mutex);
        return state_->lifecycle == RuntimeValidatedTransferLifecycle::Committed;
    } catch (...) {
        return false;
    }
}

bool RuntimeValidatedStateTransfer::aborted() const noexcept {
    if (state_ == nullptr) {
        return false;
    }
    try {
        std::lock_guard<std::mutex> lock(state_->mutex);
        return state_->lifecycle == RuntimeValidatedTransferLifecycle::Aborted;
    } catch (...) {
        return false;
    }
}

bool RuntimeValidatedStateTransfer::ambiguous() const noexcept {
    if (state_ == nullptr) {
        return false;
    }
    try {
        std::lock_guard<std::mutex> lock(state_->mutex);
        return state_->lifecycle == RuntimeValidatedTransferLifecycle::Ambiguous ||
               state_->lifecycle == RuntimeValidatedTransferLifecycle::Committing ||
               state_->lifecycle == RuntimeValidatedTransferLifecycle::Aborting;
    } catch (...) {
        return false;
    }
}

RuntimeIncarnationRef RuntimeValidatedStateTransfer::source_slot() const noexcept {
    return state_ == nullptr ? RuntimeIncarnationRef{} : state_->source_slot;
}

std::string_view RuntimeValidatedStateTransfer::target_plan_sha256() const noexcept {
    return state_ == nullptr ? std::string_view{} : std::string_view(state_->target_plan_sha256);
}

std::string_view RuntimeValidatedStateTransfer::state_bundle_sha256() const noexcept {
    return state_ == nullptr ? std::string_view{} : std::string_view(state_->state_bundle_sha256);
}

std::uint64_t RuntimeValidatedStateTransfer::transfer_fence_sequence() const noexcept {
    return state_ == nullptr ? 0 : state_->transfer_fence_sequence;
}

std::uint64_t RuntimeValidatedStateTransfer::episode_barrier_sequence() const noexcept {
    return state_ == nullptr ? 0 : state_->episode_barrier_sequence;
}

RuntimeEpisodeCoordinatorSnapshot
RuntimeValidatedStateTransfer::source_barrier_snapshot() const noexcept {
    return state_ == nullptr ? RuntimeEpisodeCoordinatorSnapshot{}
                             : state_->source_barrier_snapshot;
}

void RuntimeValidatedStateTransfer::abandon() noexcept {
    abort_for_host();
}

RuntimeStateTransferStatus RuntimeValidatedStateTransfer::prepare_for_host(
    const RuntimeIncarnationRef &expected_source, std::string_view expected_source_plan_sha256,
    std::string_view expected_target_plan_sha256,
    const RuntimeIdentity128 &expected_candidate_resource_identity,
    std::uint64_t expected_lifecycle_ticket, std::uint64_t expected_candidate_sequence,
    std::uint64_t expected_mutation_fence_sequence) {
    if (state_ == nullptr) {
        return failure(RuntimeStateTransferError::InvalidArgument,
                       "validated state transfer is empty");
    }
    std::lock_guard<std::mutex> state_lock(state_->mutex);
    if (state_->lifecycle != RuntimeValidatedTransferLifecycle::Ready) {
        return failure(RuntimeStateTransferError::TransferAlreadyConsumed,
                       "validated state transfer is not ready");
    }
    if (state_->source_slot != expected_source ||
        state_->source_plan_sha256 != expected_source_plan_sha256 ||
        state_->target_plan_sha256 != expected_target_plan_sha256 ||
        state_->candidate_resource_identity != expected_candidate_resource_identity ||
        state_->lifecycle_ticket != expected_lifecycle_ticket ||
        state_->candidate_sequence != expected_candidate_sequence ||
        state_->transfer_fence_sequence != expected_mutation_fence_sequence) {
        return failure(RuntimeStateTransferError::PlanMismatch,
                       "validated state transfer source or target plan is stale");
    }
    const auto token = state_->barrier_token;
    if (token == nullptr) {
        return failure(RuntimeStateTransferError::BarrierRequired,
                       "validated state transfer lost its native barrier");
    }
    std::lock_guard<std::mutex> token_lock(token->mutex);
    const auto coordinator = token->coordinator.lock();
    if (!token->claimed || token->released || coordinator == nullptr) {
        return failure(RuntimeStateTransferError::BarrierReplay,
                       "validated native barrier is no longer live");
    }
    std::lock_guard<std::mutex> coordinator_lock(coordinator->mutex);
    if (coordinator->phase != RuntimeEpisodePhase::ReplacementBarrier ||
        coordinator->coordinator_nonce != token->coordinator_nonce ||
        coordinator->open_barrier_nonce != token->barrier_nonce ||
        coordinator->barrier_sequence != state_->episode_barrier_sequence) {
        return failure(RuntimeStateTransferError::StaleIntent,
                       "native replacement barrier changed before host preparation");
    }
    state_->lifecycle = RuntimeValidatedTransferLifecycle::Prepared;
    return success();
}

RuntimeStateTransferStatus
RuntimeValidatedStateTransfer::commit_for_host(std::uint64_t now_tick,
                                               std::uint64_t deadline_tick) noexcept {
    if (state_ == nullptr) {
        return failure(RuntimeStateTransferError::InvalidArgument,
                       "validated state transfer is empty");
    }
    try {
        std::shared_ptr<RuntimeStateOwnerImportTransaction> import_transaction;
        {
            std::lock_guard<std::mutex> state_lock(state_->mutex);
            if (state_->lifecycle != RuntimeValidatedTransferLifecycle::Prepared) {
                return failure(RuntimeStateTransferError::TransferAlreadyConsumed,
                               "validated state transfer is not prepared");
            }
            state_->lifecycle = RuntimeValidatedTransferLifecycle::Committing;
            import_transaction = std::move(state_->import_transaction);
        }
        RuntimeStateOwnerImportTransactionStatus transaction_status;
        if (import_transaction != nullptr) {
            // Owner callbacks run outside both the host and transfer mutexes;
            // they are allowed to inspect their own resource but cannot
            // re-enter this transfer while it is Committing.
            transaction_status = import_transaction->commit_with_deadline(now_tick, deadline_tick);
        } else {
            transaction_status = {.phase = RuntimeStateOwnerImportTransactionPhase::Ambiguous,
                                  .error = RuntimeStateTransferError::ImportTransactionStateInvalid,
                                  .journal_sequence = 0,
                                  .durable = false};
        }
        const bool durable_commit =
            transaction_status.phase == RuntimeStateOwnerImportTransactionPhase::Committed &&
            transaction_status.durable && transaction_status.journal_sequence != 0;
        if (!transaction_status || !durable_commit) {
            const bool ambiguous =
                transaction_status.phase == RuntimeStateOwnerImportTransactionPhase::Committing ||
                transaction_status.phase == RuntimeStateOwnerImportTransactionPhase::Aborting ||
                transaction_status.phase == RuntimeStateOwnerImportTransactionPhase::Ambiguous ||
                transaction_status.phase == RuntimeStateOwnerImportTransactionPhase::Committed;
            {
                std::lock_guard<std::mutex> state_lock(state_->mutex);
                if (state_->lifecycle == RuntimeValidatedTransferLifecycle::Committing) {
                    state_->import_transaction = std::move(import_transaction);
                    state_->lifecycle = ambiguous ? RuntimeValidatedTransferLifecycle::Ambiguous
                                                  : RuntimeValidatedTransferLifecycle::Ready;
                }
            }
            if (!ambiguous) {
                abort_for_host();
            }
            const RuntimeStateTransferError error =
                ambiguous && transaction_status.error == RuntimeStateTransferError::None
                    ? RuntimeStateTransferError::ImportTransactionAmbiguous
                    : (transaction_status.error == RuntimeStateTransferError::None
                           ? RuntimeStateTransferError::ImportTransactionStateInvalid
                           : transaction_status.error);
            return failure(error, "owner import transaction did not commit");
        }
        {
            std::lock_guard<std::mutex> state_lock(state_->mutex);
            if (state_->lifecycle != RuntimeValidatedTransferLifecycle::Committing) {
                return failure(RuntimeStateTransferError::TransferAlreadyConsumed,
                               "validated state transfer was consumed while committing");
            }
            const auto token = state_->barrier_token;
            if (token != nullptr) {
                std::lock_guard<std::mutex> token_lock(token->mutex);
                const auto coordinator = token->coordinator.lock();
                if (coordinator != nullptr) {
                    std::lock_guard<std::mutex> coordinator_lock(coordinator->mutex);
                    if (coordinator->phase == RuntimeEpisodePhase::ReplacementBarrier &&
                        coordinator->open_barrier_nonce == token->barrier_nonce) {
                        coordinator->phase = RuntimeEpisodePhase::TransferCommitted;
                        coordinator->open_barrier_nonce = {};
                    }
                }
                token->released = true;
            }
            state_->lifecycle = RuntimeValidatedTransferLifecycle::Committed;
            if (state_->quiescence_token != nullptr) {
                std::lock_guard<std::mutex> quiescence_lock(state_->quiescence_token->mutex);
                state_->quiescence_token->released = true;
                state_->quiescence_token->host_rollback = {};
            }
            state_->coordinator_owner.reset();
        }
        return success();
    } catch (...) {
        std::terminate();
    }
}

RuntimeStateTransferStatus
RuntimeValidatedStateTransfer::recover_for_host(std::uint64_t now_tick,
                                                std::uint64_t deadline_tick) noexcept {
    if (state_ == nullptr) {
        return failure(RuntimeStateTransferError::InvalidArgument,
                       "validated state transfer is empty");
    }
    try {
        std::shared_ptr<RuntimeStateOwnerImportTransaction> import_transaction;
        {
            std::lock_guard<std::mutex> state_lock(state_->mutex);
            if (state_->lifecycle == RuntimeValidatedTransferLifecycle::Committed ||
                state_->lifecycle == RuntimeValidatedTransferLifecycle::Aborted) {
                return success();
            }
            if (state_->lifecycle != RuntimeValidatedTransferLifecycle::Ambiguous &&
                state_->lifecycle != RuntimeValidatedTransferLifecycle::Committing &&
                state_->lifecycle != RuntimeValidatedTransferLifecycle::Aborting) {
                return failure(RuntimeStateTransferError::TransferAlreadyConsumed,
                               "validated state transfer is not recoverable");
            }
            import_transaction = state_->import_transaction;
        }
        if (import_transaction == nullptr) {
            return failure(RuntimeStateTransferError::ImportTransactionStateInvalid,
                           "ambiguous transfer has no owner transaction");
        }
        const auto recovered = import_transaction->recover_with_deadline(now_tick, deadline_tick);
        const bool committed =
            recovered.phase == RuntimeStateOwnerImportTransactionPhase::Committed &&
            recovered.error == RuntimeStateTransferError::None && recovered.durable &&
            recovered.journal_sequence != 0;
        const bool aborted = recovered.phase == RuntimeStateOwnerImportTransactionPhase::Aborted &&
                             recovered.error == RuntimeStateTransferError::None &&
                             recovered.durable && recovered.journal_sequence != 0;
        if (!committed && !aborted) {
            std::lock_guard<std::mutex> state_lock(state_->mutex);
            state_->lifecycle = RuntimeValidatedTransferLifecycle::Ambiguous;
            return failure(recovered.error == RuntimeStateTransferError::None
                               ? RuntimeStateTransferError::ImportTransactionAmbiguous
                               : recovered.error,
                           "owner import outcome remains ambiguous after recovery");
        }

        std::function<void()> rollback;
        {
            std::lock_guard<std::mutex> state_lock(state_->mutex);
            state_->import_transaction.reset();
            const auto token = state_->barrier_token;
            if (token != nullptr) {
                std::lock_guard<std::mutex> token_lock(token->mutex);
                const auto coordinator = token->coordinator.lock();
                if (coordinator != nullptr) {
                    std::lock_guard<std::mutex> coordinator_lock(coordinator->mutex);
                    if (coordinator->phase == RuntimeEpisodePhase::ReplacementBarrier &&
                        coordinator->open_barrier_nonce == token->barrier_nonce) {
                        coordinator->phase = committed ? RuntimeEpisodePhase::TransferCommitted
                                                       : RuntimeEpisodePhase::Terminal;
                        coordinator->open_barrier_nonce = {};
                    }
                }
                token->released = true;
            }
            if (committed) {
                state_->lifecycle = RuntimeValidatedTransferLifecycle::Committed;
                if (state_->quiescence_token != nullptr) {
                    std::lock_guard<std::mutex> quiescence_lock(state_->quiescence_token->mutex);
                    state_->quiescence_token->released = true;
                    state_->quiescence_token->host_rollback = {};
                }
            } else {
                state_->lifecycle = RuntimeValidatedTransferLifecycle::Aborted;
                if (state_->quiescence_token != nullptr) {
                    std::lock_guard<std::mutex> quiescence_lock(state_->quiescence_token->mutex);
                    state_->quiescence_token->released = true;
                    rollback = std::move(state_->quiescence_token->host_rollback);
                }
            }
            state_->coordinator_owner.reset();
        }
        if (rollback) {
            rollback();
        }
        return success();
    } catch (...) {
        return failure(RuntimeStateTransferError::ImportTransactionAmbiguous,
                       "exception while recovering owner import transaction");
    }
}

void RuntimeValidatedStateTransfer::release_host_transfer_fence() noexcept {
    if (state_ == nullptr) {
        return;
    }
    try {
        std::function<void()> end_transfer;
        {
            std::lock_guard<std::mutex> state_lock(state_->mutex);
            end_transfer = std::move(state_->host_end_transfer);
        }
        if (end_transfer) {
            end_transfer();
        }
    } catch (...) {
        std::terminate();
    }
}

void RuntimeValidatedStateTransfer::abort_for_host() noexcept {
    if (state_ == nullptr) {
        return;
    }
    try {
        std::function<void()> rollback;
        std::function<void()> end_transfer;
        std::shared_ptr<RuntimeStateOwnerImportTransaction> import_transaction;
        bool needs_recovery = false;
        bool already_terminal = false;
        {
            std::lock_guard<std::mutex> state_lock(state_->mutex);
            if (state_->lifecycle == RuntimeValidatedTransferLifecycle::Committed ||
                state_->lifecycle == RuntimeValidatedTransferLifecycle::Aborted) {
                end_transfer = std::move(state_->host_end_transfer);
                already_terminal = true;
            } else {
                needs_recovery =
                    state_->lifecycle == RuntimeValidatedTransferLifecycle::Ambiguous ||
                    state_->lifecycle == RuntimeValidatedTransferLifecycle::Committing ||
                    state_->lifecycle == RuntimeValidatedTransferLifecycle::Aborting;
                if (!needs_recovery) {
                    state_->lifecycle = RuntimeValidatedTransferLifecycle::Aborting;
                    import_transaction = std::move(state_->import_transaction);
                }
            }
        }
        if (already_terminal) {
            if (end_transfer) {
                end_transfer();
            }
            return;
        }
        if (needs_recovery) {
            // Never discard an ambiguous transaction silently.  Recovery is
            // deliberately best-effort here because this destructor has no
            // trusted clock; the host's explicit recovery path remains the
            // authoritative retry mechanism.
            (void)recover_for_host(0, 0);
            return;
        }
        RuntimeStateOwnerImportTransactionStatus abort_status;
        if (import_transaction != nullptr) {
            // Abort provisional target state before reopening the source, and
            // do so without holding either the transfer or host mutex.
            abort_status = import_transaction->abort_with_deadline(0, 0);
        } else {
            abort_status = {.phase = RuntimeStateOwnerImportTransactionPhase::Ambiguous,
                            .error = RuntimeStateTransferError::ImportTransactionStateInvalid,
                            .journal_sequence = 0,
                            .durable = false};
        }
        if (!abort_status ||
            abort_status.phase != RuntimeStateOwnerImportTransactionPhase::Aborted) {
            std::lock_guard<std::mutex> state_lock(state_->mutex);
            if (state_->lifecycle == RuntimeValidatedTransferLifecycle::Aborting) {
                state_->import_transaction = std::move(import_transaction);
                state_->lifecycle = RuntimeValidatedTransferLifecycle::Ambiguous;
            }
            return;
        }
        {
            std::lock_guard<std::mutex> state_lock(state_->mutex);
            if (state_->lifecycle != RuntimeValidatedTransferLifecycle::Aborting) {
                return;
            }
            const auto token = state_->barrier_token;
            if (token != nullptr) {
                std::lock_guard<std::mutex> token_lock(token->mutex);
                const auto coordinator = token->coordinator.lock();
                if (coordinator != nullptr) {
                    std::lock_guard<std::mutex> coordinator_lock(coordinator->mutex);
                    if (coordinator->phase == RuntimeEpisodePhase::ReplacementBarrier &&
                        coordinator->open_barrier_nonce == token->barrier_nonce) {
                        coordinator->phase = RuntimeEpisodePhase::Terminal;
                        coordinator->open_barrier_nonce = {};
                    }
                }
                token->released = true;
            }
            state_->lifecycle = RuntimeValidatedTransferLifecycle::Aborted;
            if (state_->quiescence_token != nullptr) {
                std::lock_guard<std::mutex> quiescence_lock(state_->quiescence_token->mutex);
                state_->quiescence_token->released = true;
                rollback = std::move(state_->quiescence_token->host_rollback);
            }
            state_->coordinator_owner.reset();
            end_transfer = std::move(state_->host_end_transfer);
        }
        if (rollback) {
            rollback();
        }
        if (end_transfer) {
            end_transfer();
        }
    } catch (...) {
        std::terminate();
    }
}

} // namespace runtime::host
