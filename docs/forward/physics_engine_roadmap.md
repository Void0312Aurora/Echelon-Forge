# Physics Engine Upgrade Roadmap

> **Status**: Planning  
> **Author**: Development Team  
> **Last Updated**: 2026-01-20

## Executive Summary

This document outlines the roadmap for upgrading the Echelon Forge physics engine from its current ad-hoc procedural model to a rigorous force-based system with symplectic integration, enabling future extensions like weapon separation and ejection dynamics.

---

## Current Architecture Issues

| Component | Issue |
|-----------|-------|
| `src/models/air/default_control_model.cpp` | Ground path is still kinematic (writes `Velocity` directly) and crash logic hard-stops state (not force-based) |
| `src/systems/physics/leapfrog_system.h` | Single force evaluation per frame (not full Velocity-Verlet); accuracy depends on dt |
| `src/systems/physics/aerodynamics_system.h` | Lift/drag is a placeholder model (no aero moments/damping; stall curve is simplistic) |
| `src/core/engine/simulation_kernel.cpp` | Pipeline ordering must guarantee Control/Rotation → AeroState/Forces → Integration (fixed in current implementation) |

---

## Theoretical Framework

### 混合架构 (Hybrid Approach)

```
┌─────────────────────────────────────────────────────────┐
│                    Physics Engine v2.0                  │
├─────────────────────────────────────────────────────────┤
│  Layer 1: 辛积分器 (Symplectic Integrator)              │
│  ├─ Leapfrog/Störmer-Verlet for (q, p)                 │
│  └─ Guarantees bounded energy error                     │
├─────────────────────────────────────────────────────────┤
│  Layer 2: Force Models (Newtonian)                      │
│  ├─ Gravity, Thrust, Drag, Lift                         │
│  └─ Intuitive, extensible, tunable                      │
├─────────────────────────────────────────────────────────┤
│  Layer 3: Constraint Dynamics (On-demand)               │
│  ├─ Lagrange multipliers for equality constraints       │
│  └─ LCP for inequality constraints (ground/collision)   │
├─────────────────────────────────────────────────────────┤
│  Layer 4: Multi-Body Extensions (Future)                │
│  ├─ Weapon separation: constraint release               │
│  └─ Ejection seat: impulse + new rigid body             │
└─────────────────────────────────────────────────────────┘
```

### 为什么选择辛积分器

| 积分方法 | 能量误差 | 长期稳定性 |
|----------|----------|------------|
| Euler | O(dt) 累积 | ❌ 发散 |
| RK4 | O(dt⁴) 累积 | ⚠️ 缓慢发散 |
| **Leapfrog** | O(dt²) **有界振荡** | ✅ 稳定 |

```cpp
// Leapfrog Algorithm (辛积分, 2阶精度)
p_half = p + F(q) * dt/2;        // 动量半步
q_new  = q + (p_half/m) * dt;    // 位置全步
p_new  = p_half + F(q_new) * dt/2; // 动量半步
```

---

## Implementation Phases

### Phase 1: Force-Based Refactor with Symplectic Integration
**Estimated Time**: 2-3 hours

1. Create `ForceAccumulator` component
2. Refactor `DefaultControlModel` to populate forces
3. Implement gravity: `F_z = -m * g`
4. Implement drag: `F_drag = -0.5 * ρ * v² * Cd * S * v̂`
5. Implement thrust: `F_thrust = throttle * T_max * n̂`
6. Replace Euler position update with kick-drift-kick integration (`LeapfrogIntegrationSystem`)
7. **Verify**: Aircraft falls under gravity when stationary

#### Files to Modify
| File | Action |
|------|--------|
| `components/physics/forces.h` | [NEW] ForceAccumulator |
| `models/air/default_control_model.cpp` | Refactor to force-based |
| `systems/physics/leapfrog_system.h` | Kick-drift-kick integration |
| `core/engine/simulation_kernel.cpp` | Ensure system ordering |

---

### Phase 2: Lift Model & Stall Dynamics
**Estimated Time**: 1-2 hours

1. Implement Angle of Attack (AoA) calculation
2. Implement lift coefficient curve: `Cl = f(α)`
3. Implement stall: `Cl_max` at critical AoA, then drops
4. **Verify**: Aircraft maintains altitude at cruise speed

---

### Phase 3: Constraint Dynamics (Future)
**Estimated Time**: 3-4 hours

1. Ground contact as unilateral constraint (LCP)
2. Lagrange multipliers for weapon pylons
3. **Verify**: Weapon separation trajectory correct

---

### Phase 4: Multi-Body Dynamics (Future)
**Estimated Time**: 5+ hours

1. Ejection seat dynamics (impulse + new body)
2. Flexible structure modes (optional)
3. Geometric mechanics extensions (SE(3) Lie group)

---

## Verification Plan

| Test | Expected Result |
|------|-----------------|
| Free Fall | 100m drop, throttle=0 → a ≈ 9.8 m/s² |
| Level Flight | At cruise speed, altitude stable |
| Stall | Speed < V_stall → altitude decreases |
| Ground Contact | No penetration, correct friction |

---

## Future Considerations: Geometric Mechanics

For advanced multi-body applications, consider:

1. **Lie Group Integrators**: SE(3) for rigid body motion  
2. **Variational Integrators**: Discrete mechanics, structure-preserving  
3. **Port-Hamiltonian**: Energy-based modeling for complex systems  

These provide a mathematically rigorous foundation for extensions like:
- Chaotic dynamics analysis (Lyapunov exponents)
- Energy budgeting in RL reward design
- Multi-body constraint handling via fiber bundles

---

## Alternative: JSBSim Integration Analysis
> **Status**: Rejected (Data Starvation)

The question of embedding [JSBSim](https://github.com/JSBSim-Team/jsbsim) (an open-source, data-driven FDM) was considered.

### Pros
1.  **Industry Standard**: Used in FlightGear, academic research, and real-world simulations.
2.  **Validated Physics**: 6DOF equations of motion are verified against NASA data.
3.  **Configurable**: Aircraft defined via XML files (mass, aero, propulsion).

### Cons (Why we chose Custom ECS Physics)
1.  **Data Starvation**: JSBSim requires fully populated aerodynamic tables ($C_L(\alpha, \delta_e, M)$, etc.). We currently lack this data. Without it, JSBSim is just an empty shell.
2.  **Integration Complexity**: JSBSim is a compiled C++ library object. Interfacing it with `flecs` ECS requires complex bridging (copying state back and forth every frame).
3.  **Overkill**: For "Digital Pilot" RL training, we need a *consistent* environment, not necessarily a *valid* one. As long as the physics are plausible (Phase 2), the AI can learn.

### Future Compatibility
The current architecture (Action -> Instrument) is **FDM-Agnostic**.
*   **Today**: `Action` -> `ForceSystem` (Internal) -> `Instrument`
*   **Future**: `Action` -> `JSBSimBridgeSystem` -> `Instrument`

If we acquire high-fidelity F-16/F-35 XML models in the future, we can swap the backend without changing the Agent's code.

---

## References

1. Hairer, Lubich, Wanner - *Geometric Numerical Integration* (2006)
2. Marsden, Ratiu - *Introduction to Mechanics and Symmetry* (1999)
3. Stevens, Lewis - *Aircraft Control and Simulation* (2015)
