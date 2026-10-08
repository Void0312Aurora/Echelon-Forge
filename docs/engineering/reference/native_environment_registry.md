# Native process environment registry

Language: English canonical; [Chinese companion](native_environment_registry.zh.md).

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/engineering/reference/native_environment_registry.md`
Owner: `engineering`, with physics/control model owners
Last verified: `2026-10-08`

## Fixed builtin physics contract

The maintained builtin runtime asserts `builtin.default_physics.v1`: these
values are immutable defaults. The seven legacy environment overrides below
are refused at `SimulationKernel` construction, before composition admission
or execution. The facade constructs the same kernel and enforces that refusal.
Any defined value, including empty, invalid or default-valued text, is an error;
unset the variable. Custom physics requires an explicitly owned/versioned model
profile. No separate environment-driven configuration resolver is introduced.

| Refused legacy variable | Fixed value | Owner / former range policy |
| --- | --- | --- |
| `CMO_ROT_MAX_RATE_CROSS_RAD_S` | 50 rad/s | rotational integration; floor 1 |
| `CMO_ROT_MAX_TORQUE_NM` | 5,000,000 N m | rotational integration; floor 10,000 |
| `CMO_ROT_MAX_ANG_ACCEL_RAD_S2` | 10,000 rad/s² | rotational integration; floor 10 |
| `CMO_ROT_MAX_RATE_RAD_S` | 6 rad/s | rotational integration; floor 0.1 |
| `CMO_ROT_SINGULARITY_MIN_PITCH_DEG` | 85 degrees, applied as cosine guard | rotational integration; clamp 70–89.9 |
| `CMO_ROT_PITCH_LIMIT_DEG` | 89 degrees | rotational integration; clamp 70–89.9 |
| `CMO_FBW_PROTECTION_MODE` | strict | default Air control; strict/relaxed/off aliases |

The implementation owners remain `rotational_system.h` and
`default_control_model.cpp`. Their original default numerical values and strict
control branches are unchanged. They no longer read environment at first use.
A late environment change cannot alter an existing world's dynamics or reset
settings; another world constructed while a variable is defined is refused.
No new component or alternate settings mechanism is added.

## Identity, replay and migration

The default composition identity admits only these fixed values. An override
cannot silently execute while presenting that identity: bootstrap fails before
runtime evidence or a trajectory exists. The existing executable graph hash
remains a contribution identity, not a numerical trajectory hash. Historical
override-dependent recordings need their original build and external settings;
an old seed/hash alone cannot prove reproducible replay. Do not silently migrate
them to the fixed default profile.

A pre-fix fresh-process probe used seed 17, generic Aircraft at pitch 88 degrees,
calm wind and one 1/60-second step. Default pitch was 87.63375811076725 degrees;
`CMO_ROT_PITCH_LIMIT_DEG=70` produced 70.0. Both reported graph hash
`6c35e313f5a67ce7d6e76824a2652fc90319b0d8788723cb90ff5270297e3399`.
This was observed clamp-active divergence across OS processes.
`test_fixed_physics_environment.py` now covers independent-process refusal,
default replay, reset, multiple worlds and a late environment change.

## Inventory boundary

The `src` process-environment call-site inventory found these seven truth knobs
and `EF_P7_PARITY_REPORT` in a native test. The latter selects a report output
path and remains diagnostic only. Python build/logging settings such as
`CMO_BUILD_DIR` and `CMO_SIM_LOG_LEVEL` keep their existing owners. This inventory
does not classify variables interpreted by third-party libraries or launchers.
