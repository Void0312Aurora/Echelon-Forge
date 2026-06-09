# A2 High-Fidelity Damage Model

Status: `2026-06-02` archived pointer. The full project package was moved to
[archive/a2_high_fidelity_damage_model](../archive/a2_high_fidelity_damage_model/README.md).

This path is retained only as a lightweight work statement for navigation.

The archived A2 package closed the research/candidate profile for the
air-combat high-fidelity damage-model line. It retains non-authoritative
blast-fragmentation evidence, accepted G1-G5 research packets, and a structured
aircraft damage/effects runtime record. It does not release stock authority,
Pk authority, deterministic fuze authority, or broader weapon-outcome
authority.

Current A2 follow-ons:

- [damage_consequence_reward_surface/README.md](damage_consequence_reward_surface/README.md):
  bounded training feedback for damage consequences rather than a single kill
  flag.
- [missile_lethality_model_foundation/README.md](missile_lethality_model_foundation/README.md):
  archived MLF-1 chain-contract foundation, retained as field and boundary
  evidence for later stages.
- [missile_lethality_geometry_fuze/README.md](missile_lethality_geometry_fuze/README.md):
  archived MLF-2 evidence package for missile approach geometry and fuze
  evaluation; it proves that nearest point, fuze evaluation, and detonation
  handoff are observable, but it does not implement fragmentation, structural
  breakup, Pk, or weapon-specific kill conclusions.
- [missile_lethality_warhead_effects/README.md](missile_lethality_warhead_effects/README.md):
  MLF-3 planning subproject for post-detonation generic warhead effects,
  fragment/blast loads, spatial coverage, and component load; it does not
  implement continuous rod, structural breakup, debris/wreck, Pk, or
  weapon-specific kill conclusions.

Follow-on warhead effects, breakup/debris, Pk, or weapon-specific calibration
need a separate `docs/agent` subproject and must not continue inside the
archived MLF-2 package.
MLF-3 is a new follow-on; it does not reopen the sealed A2 package.

These follow-ons do not reopen the sealed A2 package or create A9.

Reopen this line only through an explicit authority-promotion or new research
request. Default air-combat work continues from [../README.md](../README.md).
