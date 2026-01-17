#pragma once
#include "components/basic/common.h"
#include <string>
#include <vector>

struct UnitData {
    uint64_t id;
    int side;       // 0=Blue, 1=Red
    int type;       // 0=Aircraft, 1=Missile, etc.
    double x, y, z;
    double heading; // Degrees (NAV: 0=North, CW)
};
