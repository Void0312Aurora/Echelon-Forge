#pragma once

/**
 * ForceAccumulator Component
 * 
 * Accumulates all forces acting on a rigid body in world frame.
 * Used by ForceSystem to compute net force, then by IntegrationSystem
 * to update velocity and position using Leapfrog (symplectic) integration.
 */
struct ForceAccumulator {
    // Linear forces in world frame (Newtons)
    double fx = 0.0;
    double fy = 0.0;
    double fz = 0.0;
    
    // Angular torques in body frame (Newton-meters) - for future use
    double torque_roll = 0.0;
    double torque_pitch = 0.0;
    double torque_yaw = 0.0;
    
    void clear() {
        fx = fy = fz = 0.0;
        torque_roll = torque_pitch = torque_yaw = 0.0;
    }
    
    void add_force(double x, double y, double z) {
        fx += x;
        fy += y;
        fz += z;
    }
    
    void add_torque(double roll, double pitch, double yaw) {
        torque_roll += roll;
        torque_pitch += pitch;
        torque_yaw += yaw;
    }
};

struct Inertia {
    double ixx = 10000.0;
    double iyy = 10000.0;
    double izz = 10000.0;
    // Cross products (Ixy etc) ignored for MVP
};

struct AngularVelocity {
    double p = 0.0; // Roll Rate (rad/s)
    double q = 0.0; // Pitch Rate (rad/s)
    double r = 0.0; // Yaw Rate (rad/s)
};

/**
 * AeroState Component
 * 
 * Cached aerodynamic quantities computed each frame.
 */
struct AeroState {
    double dynamic_pressure = 0.0;    // q = 0.5 * rho * V^2
    double angle_of_attack = 0.0;     // alpha (degrees)
    double sideslip_angle = 0.0;      // beta (degrees)
    double mach_number = 0.0;
    double lift_coefficient = 0.0;    // Cl
    double drag_coefficient = 0.0;    // Cd
};

