#pragma once

#include <array>
#include <cstddef>

#include "components/command/command_link.h"

inline constexpr std::size_t kMissionCommandPendingQueueCapacity = 4;

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

inline bool enqueue_pending_mission_command(
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
        return true;
    }

    if (mission_command_pending_queue_full(queue)) {
        return false;
    }

    queue.entries[queue.size++] = {
        next,
        mission_command_pending_queue_tail_deliver_time(pending, queue, current_time) + latency_s,
    };
    return true;
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
