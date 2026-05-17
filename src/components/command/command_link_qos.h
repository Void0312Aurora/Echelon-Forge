#pragma once

#include <array>
#include <cstddef>

#include "components/command/command_link.h"

inline constexpr std::size_t kMissionCommandPendingQueueCapacity = 4;

enum class MissionCommandEnqueueResult {
    Accepted,
    ReplacedQueuedCommand,
    Dropped,
};

struct MissionCommandQueueEntry {
    MissionCommand command{};
    double deliver_time = 0.0;
};

struct MissionCommandPendingQueue {
    std::array<MissionCommandQueueEntry, kMissionCommandPendingQueueCapacity> entries{};
    std::size_t size = 0;
};

inline MissionCommandPendingQueue make_mission_command_pending_queue() {
    return {};
}

inline bool mission_command_pending_queue_empty(const MissionCommandPendingQueue& queue) {
    return queue.size == 0;
}

inline bool mission_command_pending_queue_full(const MissionCommandPendingQueue& queue) {
    return queue.size >= queue.entries.size();
}

inline double mission_command_pending_queue_tail_deliver_time(
    const PendingMissionCommand& pending,
    const MissionCommandPendingQueue& queue,
    double current_time
) {
    if (!mission_command_pending_queue_empty(queue)) {
        return queue.entries[queue.size - 1].deliver_time;
    }
    if (pending.active) {
        return pending.deliver_time;
    }
    return current_time;
}

inline int mission_command_queue_priority(const MissionCommand& command) {
    switch (command.command_code) {
    case kMissionCommandCodeNavalAutoCloseInDefense:
    case kMissionCommandCodeNavalSurfaceEngage:
        return 2;
    default:
        break;
    }
    if (command.authorization_to_fire || command.assigned_target_id != 0) {
        return 1;
    }
    return 0;
}

inline std::size_t mission_command_queue_insert_index(
    const MissionCommandPendingQueue& queue,
    const MissionCommand& command
) {
    const int next_priority = mission_command_queue_priority(command);
    std::size_t index = 0;
    while (index < queue.size &&
           mission_command_queue_priority(queue.entries[index].command) >= next_priority) {
        ++index;
    }
    return index;
}

inline void recompute_mission_command_queue_deliver_times(
    const PendingMissionCommand& pending,
    MissionCommandPendingQueue& queue,
    double current_time,
    double latency_s
) {
    double deliver_time = pending.active ? pending.deliver_time : current_time;
    for (std::size_t i = 0; i < queue.size; ++i) {
        deliver_time += latency_s;
        queue.entries[i].deliver_time = deliver_time;
    }
}

inline MissionCommandEnqueueResult enqueue_pending_mission_command(
    PendingMissionCommand& pending,
    MissionCommandPendingQueue& queue,
    const MissionCommand& command,
    double current_time,
    double latency_s
) {
    MissionCommand next = command;
    next.active = true;

    if (!pending.active) {
        pending.command = next;
        pending.deliver_time = current_time + latency_s;
        pending.active = true;
        return MissionCommandEnqueueResult::Accepted;
    }

    const std::size_t insert_index = mission_command_queue_insert_index(queue, next);
    if (mission_command_pending_queue_full(queue)) {
        if (insert_index >= queue.size) {
            return MissionCommandEnqueueResult::Dropped;
        }
        for (std::size_t i = queue.size - 1; i > insert_index; --i) {
            queue.entries[i] = queue.entries[i - 1];
        }
        queue.entries[insert_index] = {next, 0.0};
        recompute_mission_command_queue_deliver_times(pending, queue, current_time, latency_s);
        return MissionCommandEnqueueResult::ReplacedQueuedCommand;
    }

    for (std::size_t i = queue.size; i > insert_index; --i) {
        queue.entries[i] = queue.entries[i - 1];
    }
    queue.entries[insert_index] = {next, 0.0};
    ++queue.size;
    recompute_mission_command_queue_deliver_times(pending, queue, current_time, latency_s);
    return MissionCommandEnqueueResult::Accepted;
}

inline bool promote_next_pending_mission_command(
    PendingMissionCommand& pending,
    MissionCommandPendingQueue& queue
) {
    if (mission_command_pending_queue_empty(queue)) {
        pending.active = false;
        return false;
    }

    pending.command = queue.entries[0].command;
    pending.deliver_time = queue.entries[0].deliver_time;
    pending.active = true;

    for (std::size_t i = 1; i < queue.size; ++i) {
        queue.entries[i - 1] = queue.entries[i];
    }
    queue.entries[queue.size - 1] = MissionCommandQueueEntry{};
    --queue.size;
    return true;
}
