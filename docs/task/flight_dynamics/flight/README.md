# Flight Dynamics Subproject

Language:
- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Status: `2026-05-18` with the `P0/P1` document skeleton already formed. The
current framing is taken from the analysis doc closure markers, not
`program/` or `archive/`.

This subproject collects flight dynamics, propulsion, aerodynamic parameters,
stall/high-AoA recovery, and their related acceptance-framing documents.

## Document Entry Points

- [flight-dynamics realism analysis and air-combat prerequisite gates](flight_dynamics_realism_analysis_20260516.zh.md)
  - Frozen record of current distortion points, air-combat prerequisite gates,
    and analysis basis.
- [archived flight-dynamics realism P0 implementation package](../archive/flight/flight_dynamics_realism_p0_implementation_package_20260516.md)
  - Archived first implementation scope for the minimal aerodynamics,
    propulsion, and stall skeleton.
- [archived flight-dynamics realism P1 implementation package](../archive/flight/flight_dynamics_realism_p1_implementation_package_20260517.md)
  - Archived follow-on work for database-driven behavior, propulsion
    transients, compressibility, and high-AoA semantics.

## Current Reading Order

1. Start with the analysis doc and its `2026-05-18` closure marker.
2. Use the body of the analysis only when you need the historical rationale or original acceptance framing.

## Maintenance Conventions

1. New flight-dynamics research, calibration notes, and data-source notes
   should land in this directory first.
2. If more specific aircraft-model or data subprojects are split later, keep
   layering them under `flight/` rather than flattening them back to the parent
   directory.
