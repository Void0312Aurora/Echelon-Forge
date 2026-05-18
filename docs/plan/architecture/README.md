# `architecture/`

Language:
- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

This directory holds the active architecture plan, performance follow-up
research, and archived `src/` layering records.

Recommended reading order:

1. [system_layering_and_engine_encapsulation_plan.md](system_layering_and_engine_encapsulation_plan.md)
2. [system_layering_and_engine_encapsulation_plan.zh.md](system_layering_and_engine_encapsulation_plan.zh.md)
3. [architecture_and_performance_research_followup.zh.md](architecture_and_performance_research_followup.zh.md)
4. [archive/src_layered_refactor_freeze.zh.md](../archive/src_layered_refactor_freeze.zh.md)

Usage rules:

- The target steady state for this directory is English canonical `.md` files
  with optional Chinese `.zh.md` companions.
- During migration, some long-form plan/freeze docs still exist only as
  `.zh.md`; treat them as transitional sources until the English peer is added.
- Research docs provide rationale and option ordering; they do not authorize
  implementation by themselves.
- Completed freeze records are execution records. New scope should be frozen
  separately.
