#pragma once

struct Score {
    double total_reward; // Accumulated Reward (for RL)
    
    // Discrete events counter for diagnostics
    int missiles_fired;
    int hits_landed;
    int kills_confirmed;
};
