<!-- Machine-translated draft generated on 2026-05-18 from docs/plan/exact_runtime/gpu_resident_state_implementation_plan.zh.md. Review before treating this file as authoritative. -->

<!-- Machine-translated draft generated on 2026-05-18 from docs/plan/exact_runtime/gpu_resident_state_implementation_plan.md. Review before treating this file as authoritative. -->

# GPU Resident State Implementation Plan

## Goal

Eliminate the write_back bottleneck (currently 79% of time) by keeping state on the GPU and only synchronizing the observation fields required for training.

## Current Bottleneck Analysis

```
Total time = GPU kernel (11.7%) + write_back (79.1%) + overhead (8.1%)
```

write_back requires:
1. D2H transfer of full state (20+ components)
2. Applying each component to the Flecs ECS world
3. Each `entity.set<Component>()` triggers internal state updates

## Implementation Plan

### Phase E1: Minimal Observation Synchronization

**Goal**: Only synchronize fields needed for training, not the full state

**Required observation fields**:
- Transform (position, orientation)
- Velocity
- InstrumentState (needed for training reward)
- GroundState (needed for termination conditions)

**Implementation**:
1. Create `GpuResidentObservationSync` structure
2. Implement `sync_observations_only()` method
3. Only synchronize the above fields to CPU

**Expected Benefit**: 60-70% reduction in write_back time

### Phase E2: Device Resident Stepping Loop

**Goal**: Keep state on GPU, execute multiple steps

**Implementation**:
1. Modify `step_batch()` to support device resident mode
2. Add `set_resident_mode(bool)` method
3. In resident mode:
   - Initially upload state to GPU
   - Execute N GPU steps
   - Only synchronize observation fields at the end

**Expected Benefit**: Eliminate H2D/D2H overhead per step

### Phase E3: Training Loop Integration

**Goal**: Modify training loop to support device resident mode

**Implementation**:
1. Add GPU resident mode for `WorldBatchVecEnv`
2. Modify observation extraction path
3. Modify reward calculation path

## File Modification List

| File | Modification |
|------|--------------|
| `src/gpu/gpu_resident_state.h` | New: device resident state management |
| `src/gpu/gpu_resident_state.cu` | New: CUDA implementation |
| `src/core/engine/world_batch_runtime.h` | Modify: add resident mode support |
| `src/core/engine/world_batch_runtime.cpp` | Modify: implement resident stepping |
| `python/rl/world_batch_vec_env.py` | Modify: support GPU resident mode |

## Risks

1. **Semantic equivalence**: Need to verify that observation synchronization does not affect training results
2. **Memory usage**: GPU resident mode requires additional memory to hold state
3. **Complexity**: Increases code path complexity

## Timeline

| Phase | Estimated Time |
|-------|----------------|
| E1: Minimal observation synchronization | 1 day |
| E2: Device resident stepping | 1-2 days |
| E3: Training loop integration | 1 day |
| Testing and validation | 1 day |
| **Total** | **4-5 days** |
