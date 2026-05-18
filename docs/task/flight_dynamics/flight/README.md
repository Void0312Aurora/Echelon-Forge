# Flight Dynamics Subproject

Language:
- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Status: `2026-05-17` with the `P0/P1` document skeleton already formed. Further
realism work for this slice continues under this directory.

This subproject collects flight dynamics, propulsion, aerodynamic parameters,
stall/high-AoA recovery, and their related acceptance-framing documents.

## Document Entry Points

- [flight-dynamics realism analysis and air-combat prerequisite gates](flight_dynamics_realism_analysis_20260516.zh.md)
  - Frozen record of current distortion points, air-combat prerequisite gates,
    and analysis basis.
- [flight-dynamics realism P0 implementation package](flight_dynamics_realism_p0_implementation_package_20260516.zh.md)
  - Records the first implementation scope for the minimal aerodynamics,
    propulsion, and stall skeleton.
- [flight-dynamics realism P1 implementation package](flight_dynamics_realism_p1_implementation_package_20260517.zh.md)
  - Carries the follow-on work for database-driven behavior, propulsion
    transients, compressibility, and high-AoA semantics.

## Current Reading Order

1. Start with `analysis` to confirm the defects and acceptance gates.
2. Then read `P0` to understand the landed skeleton.
3. Finish with `P1` to confirm the current realism/data closeout backlog.

## Maintenance Conventions

1. New flight-dynamics research, calibration notes, and data-source notes
   should land in this directory first.
2. If more specific aircraft-model or data subprojects are split later, keep
   layering them under `flight/` rather than flattening them back to the parent
   directory.
