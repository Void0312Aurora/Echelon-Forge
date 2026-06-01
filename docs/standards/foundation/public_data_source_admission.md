# Public Data Source Admission Standard

Language:
- English canonical: `foundation/public_data_source_admission.md`
- Chinese companion: [public_data_source_admission.zh.md](public_data_source_admission.zh.md)

Status: `2026-06-01` authoritative foundation rule for public-source admission, research candidate data, and runtime authority gates.

This standard defines how public data, papers, standards, reports, generated
benchmarks, and source ledgers may enter the project. It applies across air,
naval, ground, joint command, sensors, weapons, damage models, visualization,
and future domains.

The central rule is:

> A source may support documentation, method design, benchmarks, or residual
> tracking before it can support runtime authority. Runtime authority requires
> an explicit gate with scope, provenance, rights, validation, and residual
> closeout.
>
> In many high-realism simulation domains, official or authoritative
> calibration data is usually unavailable. Third-party, community, and
> open-source material may enter the candidate pool, but it must be explicitly
> labeled with its tier, provenance, rights status, reasonableness assessment,
> and residuals. It must not be cited as official or calibrated authority unless
> it later passes the relevant authority gate.

## Repository License Boundary

The repository is licensed under Apache-2.0 for project code and maintained
documentation. That project license does not grant rights to third-party
inputs.

Public papers, datasets, vendor materials, community code, visualization
assets, retained source payloads, and generated artifacts that depend on those
inputs must still record their own source, license, copyright, export,
redistribution, and attribution status. If an external input cannot be copied,
redistributed, or used to generate retained outputs under its own terms, the
repository-level Apache-2.0 license does not cure that gap.

## Source Tiers

| Tier | Acceptable sources | Allowed use | Limit |
| --- | --- | --- | --- |
| `Tier A / official-standard` | Public standards, official public documents, government reports, public textbooks, peer-reviewed papers, public validation methods | Method references, validation criteria, reproducible benchmark design, public policy or terminology baseline | Still requires scope match, rights checks, and reproducibility records |
| `Tier B / public-engineering` | Public vendor materials, public audit/congressional files, public course material, marketing or product factsheets with identifiable holders, third-party engineering material with traceable authorship/version/license | Engineering magnitude, platform/weapon/sensor family candidates, geometry or component layout candidates, non-authoritative parameter candidates | Must be marked approximate and third-party; cannot stand alone as model truth |
| `Tier C / sanity-check` | Community databases, open-source configs, traceable community datasets, forum compilations, encyclopedic secondary sources | Keyword discovery, sign/unit sanity checks, rough magnitude cross-checks, candidate hypothesis generation | Must be marked community/secondary with a reasonableness assessment; cannot independently grant calibrated authority |
| `rejected` | Restricted, non-redistributable, unstable, provenance-missing, suspect, leaked, rights-unclear, or scope-mismatched sources | Rejection record only | Cannot enter descriptor rows, generated benchmarks, or runtime data |

## Required Ledger Fields

Every source ledger row must record:

- `source_id`;
- source tier and category;
- stable `source_ref`, such as DOI, URL, report number, official catalog entry,
  archive reference, ISBN, code commit, or benchmark manifest;
- publisher, holder, or responsible organization;
- public availability, license, copyright, export, or redistribution limits;
- provenance summary, including how the data or method is obtained, processed,
  retained, and bounded;
- scope match, including relevant target, platform, weapon family, aspect,
  closure, range, miss-distance, mechanism, sensor, component, terrain, or
  command-role axes;
- cross-validation status, especially whether a Tier A/B source confirms it or
  whether it is only Tier C sanity check;
- reasonableness assessment: numeric range, units, internal consistency, and
  conflicts with public physics/engineering context or other sources;
- ingest status: `pending`, `acquired`, `rejected`, or `superseded`;
- authority status, defaulting to `non-authoritative`;
- residual risks that remain after admission.

If a row lacks stable `source_ref`, rights, scope, provenance, or residual
status, it may be kept as a search lead but must not become an input source.

## Research / Candidate Profile Admission

A research-grade candidate model is not the same thing as industrial or
release-grade authority. When a task explicitly declares its current target as
`research`, `candidate`, `non-authoritative`, or `authority_opt_in_only`, it may
use `Tier B`, `Tier C`, community material, open-source configuration,
multi-source derived estimates, or hash-only restricted references without
waiting for official or industrial-grade data, provided that:

- each data item records source tier, data class, scope, rights or
  redistribution notes, uncertainty or confidence, cross-check notes, and a
  replacement rule;
- `Tier C`, community, and secondary sources may form sanity envelopes,
  candidate hypotheses, parameter ranges, or derived estimates, but cannot
  independently become calibrated truth;
- copyrighted or redistribution-limited material is not copied into the
  repository as long prose, tables, images, or raw selected values; locators,
  hashes, short summaries, review records, and derived parameters may be
  retained instead;
- research-profile residuals may be marked `research_closed` or
  `research_out_of_scope`, but missing authority evidence must still be retained
  as `authority_blocked`, `authority_fail_closed`, or
  `authority_boundary_deferred`;
- any runtime descriptor, stock row, or release-grade claim still requires the
  task-specific authority gate to pass.

In short, research high fidelity may first make the model runnable, auditable,
and replaceable with reasonable traceable data. It must not describe that data
as official, calibrated, or industrial authority.

## Artifact Rules

Generated data, validation runs, model outputs, and benchmark outputs are
artifacts, not sources by themselves.

An artifact may be cited only when it has:

- stable artifact reference or retention location;
- generation script, config, and code version;
- environment or container notes when relevant;
- random seed policy;
- metric definitions;
- checksum or hash for retained outputs;
- rights and redistribution status of all inputs;
- source ledger references for every external input;
- residual and out-of-scope notes.

Transient workspace paths, local temporary files, untracked notebooks, and
ad-hoc screenshots are not long-term provenance.

## Authority Gates

A task-specific runtime authority gate must name its allowed `source_kind`
values and required manifest fields. Until that gate is defined and passed,
all admitted sources remain documentation or benchmark candidates.

A runtime authority gate must fail closed when any of the following are missing:

- current schema version;
- non-empty `source_ref`;
- non-empty provenance;
- rights or redistribution status;
- scope axes required by the domain;
- calibration or validation status;
- validation artifact reference, when the source is a surrogate;
- artifact checksum or reproducibility manifest, when generated outputs are
  consumed;
- row-level `row_id`, `source_ref`, and provenance for consumable rows;
- explicit per-authority grants.

Authority is per field. A source that can support geometry does not thereby
support vulnerability. A source that can support a benchmark does not thereby
support Pk. A source that can support a method does not thereby support
deterministic trigger behavior.

## Source-Kind Boundary

Task schemas may define their own `source_kind` values, but the standard split
is:

- `external_calibration_dataset`: a public or rights-cleared dataset with
  scope, uncertainty, provenance, and redistribution terms sufficient for the
  domain gate;
- `validated_physics_surrogate`: a model or generated benchmark package with a
  complete validation manifest, scope match, versioned code/config, metrics,
  acceptance criteria, artifacts, and residual closeout;
- `method_reference`: a source that supports formulas, terminology, or modeling
  structure only;
- `validation_criteria_reference`: a source that supports what should be
  checked, not the checked result;
- `benchmark_design_reference`: a source that supports a reproducible benchmark
  design, not runtime authority;
- `sanity_check_only`: a source used only for unit, sign, magnitude, naming,
  candidate hypotheses, or edge-case checks;
- `rejected`: a source that must not be used as data.

Only domain schemas may decide which source kinds can enter runtime authority.
Documentation must not imply authority for kinds outside that allow-list.

## Rejected Sources

The following source types must be rejected or held at `sanity_check_only`
unless a task-specific owner explicitly proves public rights, provenance, scope,
and reasonableness:

- restricted, proprietary, leaked, FOUO, CUI, ITAR, EAR, or export-controlled
  material;
- unauthorized manuals, technical orders, IPB/parts catalogs, maintenance
  manuals, training decks, contractor attachments, or file-share mirrors;
- no-provenance game, commercial simulation, forum, anonymous database, or
  community balancing parameters;
- screenshots, social posts, unsourced tables, one-line Pk curves, anonymous
  hit probability charts, or unattributed parameter lists;
- unofficial mirrors when an official publisher, DOI, NTRS, NTIS, standards
  catalog, or archive entry is available;
- source names for controlled tools or databases when only the name is public
  and the underlying data is not.

Rejected source categories may be recorded to prevent future accidental reuse.
They must not be copied, summarized into parameters, or used to tune runtime
behavior.

Traceable third-party or community sources must not be rejected merely because
they are unofficial. They may enter the source ledger as `Tier B` or `Tier C`
candidates, but citations must preserve labels such as
`third_party_candidate`, `community_sanity_check`, `open_source_config_candidate`,
or `non-authoritative_estimate`, and must state why the data is or is not
reasonable for the current scope.

## Claim Rules

Documentation, training reports, task plans, and evaluation summaries must:

1. Distinguish source collection, method design, benchmark generation,
   validation, calibration, and runtime authority.
2. State the highest claim supported by the weakest unresolved residual.
3. Keep synthetic fixtures, engineering scaffolds, and schema examples
   explicitly non-authoritative.
4. Avoid converting public formulas, examples, or textbook methods directly
   into calibrated runtime rows.
5. Avoid using reward, score, or scenario terminal logic to define physical
   authority.
6. For third-party, community, or open-source material, state the source nature,
   reasonableness assessment, and unsupported claims in both prose and tables.

Passing a data-shape test only proves the data path. Passing a benchmark only
proves the benchmark's stated scope. Neither implies a higher realism or
authority claim.

## Task Documentation Rules

Task-level data collection folders should contain:

- a README with scope, status, authority boundary, and related standards;
- a source ledger;
- optional benchmark matrix, schema mapping, residual register, or validation
  manifest drafts;
- a rejection list;
- a gate mapping that explains what each source may and may not support.

When a task creates a domain-specific admission rule, that rule should link
back to this standard and then state only the task-specific schema fields and
authority gates.

## Relation To Gradient Realism

This standard supports [Gradient Realism Principles](gradient_realism_principles.md).
A scenario or domain model cannot claim a realism gradient that depends on data
or validation unless the relevant source admission and authority gates have
passed.

For example, a weapon-release scenario can be `G5` functionally connected while
its lethality model remains non-authoritative. It may not claim calibrated
damage or deterministic fuze realism until the data source, validation, and
authority gates for those claims pass.
