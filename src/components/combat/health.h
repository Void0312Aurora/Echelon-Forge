#pragma once

struct Health {
    double current_hp;
    double max_hp;
    bool mission_kill = false;
    bool mobility_kill = false;
    bool sensor_kill = false;
};
