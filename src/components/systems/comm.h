#pragma once

#include <vector>
#include <cstdint>

enum class CommMsgType {
    None,
    ReportContact, // "I see X"
    AssignTask,    // "Attack X"
    StatusUpdate,  // "I am engaging X"
    RequestSupport // "Help me with X"
};

struct CommPacket {
    uint64_t sender_id;
    uint64_t target_receiver_id; // 0 = Broadcast to Net
    CommMsgType type;
    uint64_t entity_ref; // Related entity (Target ID)
    double location_x;   // Optional coords
    double location_y;
    double location_z;
    double timestamp;
};

struct CommQueue {
    std::vector<CommPacket> inbox;
};
