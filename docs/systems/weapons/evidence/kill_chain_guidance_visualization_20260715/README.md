# Kill-Chain Guidance Calibration Visualization Evidence

Status: accepted bounded visualization evidence assembled on `2026-09-16`
from source reports generated on `2026-07-15`.

## Supported Claim

The retained unsmoothed heatmaps support keeping `nav_gain=4.0` as the held
engineering baseline: the stage-4 main grid contains `N/M/O = 146/32/69`, the
60-degree robust-hit interval is `8-14 km`, and all stage-5 state changes remain
near the baseline hit boundary. Non-baseline candidates move the angular
boundary by `5 deg`, above the preregistered `2.5 deg` limit.

| View | Retained output |
| --- | --- |
| Stage-4 launch class | [launch_class.png](launch_class.png) |
| Stage-4 conservative `log10(rho_edge)` | [rho_edge.png](rho_edge.png) |
| Stage-5 changes relative to `nav_gain=4.0` | [state_changes.png](state_changes.png) |

## Non-Claims

This package does not promote a new default, authorize maneuver/APN behavior,
rerun simulation, interpolate unsampled cells, or establish real weapon
performance, target vulnerability, or Pk authority. Promotion remains `held`.

## Provenance And Retention

- Producer: `tools/diagnostics/kill_chain_guidance_calibration_visualize.py`.
- Source-report date: `2026-07-15`; package assembly date: `2026-09-16`.
- Inputs and output hashes: [manifest.json](manifest.json).
- Consumer: kill-chain guidance baseline review and the associated diagnostic
  tools; no dated review page is rewritten to point at this package.
- Retention reason: preserve three human-readable decision surfaces without
  retaining the multi-megabyte raw experiment directory in Git.
- Rights boundary: repository-internal synthetic engineering evidence; no
  third-party data or separately licensed assets are included.
- Raw CSV, SVG, and report inputs remain outside Git under the ignored
  `artifacts/` surface; recorded identities do not imply repository
  availability.

Accepted evidence is immutable. Corrections require a new dated package that
marks this package superseded or archived.
