# Weapon And Guidance Subproject

Language:
- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Status: `2026-05-17` with `P0/P1` implementation packages already formed. The
current code has already passed seeker-only guidance, minimal
`3DoF`/`PN-autopilot` surrogate, shared missile tuning, and launch/runtime
guard tests. Treat the latest checked conclusions in the `P1` package as the
source of truth for any still-open items mentioned elsewhere.

This subproject collects documents for the weapon chain, seekers, guidance
loops, proximity fuzes/damage, and their reference-data plans.

## Document Entry Points

- [weapon-system and guidance-loop realism analysis](weapon_guidance_realism_analysis_20260516.zh.md)
  - Frozen record of the main current distortion points in the weapon chain and
    missile guidance behavior.
- [weapon-system and guidance-loop realism verification and landing plan](weapon_guidance_realism_verification_and_plan_20260516.zh.md)
  - Verifies the research conclusions and organizes implementable plans plus
    data sources.
- [weapon/guidance realism P0 implementation package](weapon_guidance_realism_p0_implementation_package_20260516.zh.md)
  - Records the first implementation scope for seeker-only guidance, minimal
    `3DoF` energetics, and the `PN/autopilot` surrogate.
- [weapon/guidance realism P1 implementation package](weapon_guidance_realism_p1_implementation_package_20260517.zh.md)
  - Carries follow-on work for shared closeout, data integration,
    fuze/damage deepening, and config exposure.

## Maintenance Conventions

1. Future weapon-parameter reference tables, seeker calibration notes, and
   external data-source notes should land here first.
2. If missile-database or fuze-specific subtracks are split out later, keep
   layering them under this directory instead of moving back to the
   `flight_dynamics/` top level.
