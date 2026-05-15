# Sensor and Situational Awareness Plan

This document records the roadmap for sensor realism and the derived situation
picture (tracks, memory, uncertainty).

## Current Features Implemented
- Scan cycle: `scan_period` and `last_scan_time` gate scanning.
- Detection probability: `detection_prob` with range attenuation (`range_power`).
- Measurement noise: `bearing_noise_std` (deg), `range_noise_std` (m).
- Track memory: `track_memory_s` retains contacts if a scan misses them.
- Target aspect influence: `aspect_influence` scales detection with target heading.

## Sensor Parameters (Per Unit)
- `max_range`: maximum detection range (m).
- `fov_deg`: total field of view (deg, NAV).
- `scan_period`: seconds between scans.
- `detection_prob`: baseline detection probability [0,1].
- `range_power`: exponent for range attenuation.
- `bearing_noise_std`: bearing noise std-dev (deg).
- `range_noise_std`: range noise std-dev (m).
- `track_memory_s`: contact retention time (s).
- `aspect_influence`: [0,1] weight for aspect-based detection.

## Detection Model (Summary)
1) Range and FOV gating.
2) Probability = detection_prob * range_factor * aspect_factor.
3) If detected: apply Gaussian noise to bearing/range.
4) Merge with track memory to avoid hard drops.

## Situation Picture Notes
- `ContactList` currently holds point detections (no filters).
- Track memory provides short-term persistence but no full tracking filter.
- Noise and dropouts are deterministic per scan with seeded hashing.

## Planned Extensions
- Track filter: alpha-beta or Kalman filter with per-track covariance.
- Track IDs and quality scores (confidence, age, last update time).
- Multi-sensor fusion: combine radar/EO tracks with priority rules.
- Elevation/bearing noise separation and 3D line-of-sight angles.
- Jamming/ECM: detection probability reduction by target state.
- Seeker limits for missiles (boresight angle, lock time).

## Action Items
- Expose sensor parameters in unit JSON schema.
- Add track metadata to logs (probability, noise used, memory age).
- Create sensor regression tests for determinism and dropouts.
