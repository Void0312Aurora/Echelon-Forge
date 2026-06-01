# Simulation Architecture Archive

Historical, accepted, blocked, superseded, or closed architecture work packages
kept for traceability. The current architecture entry remains
[../README.md](../README.md).

## Closed / Frozen Lanes

- [WP22 Legacy Compatibility Retirement And Architecture Hardening](wp22_legacy_compatibility_retirement/legacy_compatibility_retirement_wp22_20260522.md):
  owner-rejected and frozen stream superseded by WP23; its dispatch queue is
  historical only.
- [WP23 Legacy Retirement Recovery And Reset](wp23_legacy_retirement_recovery/legacy_retirement_recovery_wp23_20260523.md):
  controlled blocked recovery record after WP22 was frozen.
- [WP24 TaskOrder Maintained Business Migration](wp24_taskorder_maintained_business_migration/taskorder_maintained_business_migration_wp24_20260524.md):
  accepted replacement-backed TaskOrder business migration with canonical
  acceptance review.
- [TM01 Architecture Closure Remediation](tm01_architecture_closure_remediation/README.md):
  audited-slice remediation closed on `2026-05-25`; later TM02/TM03 lanes closed
  its two explicit ledgered gaps.
- [TM02 WP24 Acceptance Closure](tm02_wp24_acceptance_closure/README.md):
  temporary closure lane that published the canonical WP24 acceptance review and
  index sync.
- [TM03 Launch Bridge Boundary](tm03_launch_bridge_boundary/README.md):
  temporary closure lane that closed the two explicit launch-helper
  `systems -> SimulationKernel` bridges through `IWeaponReleaseService`.

## Older WP Records

The remaining `wp*` archive directories hold prior work-package packets and
acceptance records. Prefer the parent
[simulation architecture README](../README.md) for the curated reading order and
only open these archived packets when provenance is needed.
