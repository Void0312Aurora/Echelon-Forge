#pragma once

#include <vector>
#include <cstdint>

#include "components/command/common/comm_message.h"

struct CommPacket {
    uint64_t sender_id;
    uint64_t target_receiver_id; // 0 = Broadcast to Net
    CommMsgType type;
    
    // Payload
    uint64_t entity_ref; // Related entity (Target ID)
    uint64_t track_ref = 0; // Related tactical track ID
    double location_x;   // Optional coords
    double location_y;
    double location_z;
    double velocity_x = 0.0;
    double velocity_y = 0.0;
    double velocity_z = 0.0;
    double value;        // Generic value (fuel %, heading, etc)
    double quality = 0.0; // Track/report confidence
    int status_code;     // Specific codes (Joker/Bingo enum etc)
    
    double timestamp;
};

struct CommQueue {
    std::vector<CommPacket> inbox;
};
