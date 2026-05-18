# `architecture/`

Language:
- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

This directory holds the strict simulation-system architecture baseline, the
active architecture plan, performance follow-up research, and archived `src/`
layering records.

Recommended reading order:

1. [simulation_system_architecture_design.md](simulation_system_architecture_design.md)
2. [simulation_system_architecture_design.zh.md](simulation_system_architecture_design.zh.md)
3. [system_layering_and_engine_encapsulation_plan.md](system_layering_and_engine_encapsulation_plan.md)
4. [system_layering_and_engine_encapsulation_plan.zh.md](system_layering_and_engine_encapsulation_plan.zh.md)
5. [architecture_and_performance_research_followup.md](architecture_and_performance_research_followup.md)
6. [architecture_and_performance_research_followup.zh.md](architecture_and_performance_research_followup.zh.md)
7. [archive/src_layered_refactor_freeze.zh.md](../archive/architecture/src_layered_refactor_freeze.zh.md)

Usage rules:

- The target steady state for this directory is English canonical `.md` files
  with optional Chinese `.zh.md` companions.
- During migration, some long-form plan/freeze docs still exist only as
  `.zh.md`; treat them as transitional sources until the English peer is added.
- Research docs provide rationale and option ordering; they do not authorize
  implementation by themselves.
- Completed freeze records are execution records. New scope should be frozen
  separately.
- The simulation-system design is the current strict architecture baseline.
  Turn broad implementation work into scoped task sheets under
  [docs/task/simulation_architecture/](../../task/simulation_architecture/README.md).
