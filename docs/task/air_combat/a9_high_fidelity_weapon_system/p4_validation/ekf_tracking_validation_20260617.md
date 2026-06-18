# A9 EKF Tracking Validation - 2026-06-17

Status: R2 closed by focused C++ regression coverage.

## Scope

This record covers the A9 R2 residual: quantitative validation for the
Kalman-filter seeker path. It does not promote the EKF path to a stock-weapon
truth model, does not claim Pk authority, and does not tune weapon-specific
constants.

## Test Surface

Focused test file:

- `src/tests/test_kalman_seeker.cpp`

Focused test case added:

- `tracking_covariance_converges_and_weaving_track_is_continuous`

The test runs deterministic synthetic seeker observations against three
non-weapon-specific target profiles:

| Scenario | Gate |
|----------|------|
| constant velocity | position covariance trace converges from 300 to less than 30% of initial; final velocity/acceleration covariance traces remain bounded |
| dropout/reacquire | position covariance expands during a 2s observation dropout and recovers to less than 30% of initial after reacquisition |
| weaving target | final position covariance trace remains below 35% of initial; maximum estimate step is below 20m; maximum frame-to-frame error jump is below 15m; RMSE remains below 40m |

## Verification Command

```bash
cmake --build build --target ef_test -j2
./build/ef_test --test-suite=kalman_seeker
```

Observed result:

```text
test cases:     3 |     3 passed | 0 failed | 55 skipped
assertions: 17423 | 17423 passed | 0 failed
```

## Acceptance Decision

R2 is closed for the bounded A9 acceptance scope. The EKF branch remains opt-in
(`use_kalman_seeker = false` by default), and IMM banks, adaptive process noise,
ECM/EW degradation, and weapon-specific tuning remain outside this subproject.
