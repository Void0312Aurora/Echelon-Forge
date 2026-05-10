#pragma once

#include <vector>
#include <cstdint>

#include "components/tasking/pilot_report.h"

struct CommPacket {
    uint64_t sender_id;
    uint64_t target_receiver_id; // 0 = Broadcast to Net
    CommMsgType type;
    
    // Payload
    uint64_t entity_ref; // Related entity (Target ID)
    double location_x;   // Optional coords
    double location_y;
    double location_z;
    double value;        // Generic value (fuel %, heading, etc)
    int status_code;     // Specific codes (Joker/Bingo enum etc)
    
    double timestamp;
};

struct CommQueue {
    std::vector<CommPacket> inbox;
};
