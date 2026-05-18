# Standards Documentation Overview

This directory defines the standardized modeling baseline the project intends to use going forward.

Language migration note:

- `docs/standards/` is being migrated to a bilingual layout in which English `.md` files are canonical and Chinese `.zh.md` files are companion documents.
- See [bilingual_documentation_policy.md](bilingual_documentation_policy.md) for the governing rule set.
- Until the English counterparts are fully in place, the legacy Chinese source documents may still be used as transitional input, but they are not the desired steady state.

Since `2026-03-23`, the standards documentation is no longer organized around an "air-combat-first, generalize later" line. It now follows:

1. `joint`: shared templates for the joint layer
2. `services`: service/domain profiles
3. `air/*`: air-combat-specific supplemental standards for platform or mission layers
4. `naval/*`: early placeholders and minimal mission-structure baselines for naval work

The reason is straightforward:

- The U.S. joint layer has shared command and authority relationships.
- But the Air Force, Army, Navy, and Marine Corps use different tactical organizations and control vocabularies.
- What is actually reusable is therefore not one fully unified command chain, but rather
  `joint/common core + service profile + platform/task specialization`

## 1. Recommended Reading Order

1. [Joint Standards Overview](joint/README.md)
2. [Joint Command Relationships and Modeling Baseline](joint/command_and_modeling_baseline.md)
3. [Service Standards Overview](services/README.md)
4. [USAF Profile](services/air_force.md)
5. [US Army Profile](services/army.md)
6. [US Navy Profile](services/navy.md)
7. [US Marine Corps Profile](services/marine_corps.md)
8. [Document Alignment Map](document_alignment_map.md)
9. [Air Platform Specialization Overview](air/README.md)
10. [Naval Standards Placeholder](naval/README.md)

## 2. Relationship to Older Documents

The following legacy documents are still retained, but are now treated as `ARCHIVED`:

- `docs/Archive/air_first_standards/com/*.md`
- `docs/Archive/air_first_standards/com/two_ship/*.md`
- `docs/Archive/architecture/*.md`
- `docs/Archive/architecture/layers/*.md`

They are still useful for understanding the project's historical evolution, but they are no longer the primary basis for current standardized modeling.

## 3. Current Modeling Conclusion

If the project continues to use publicly available U.S. military material as its real-world baseline, it should model along these three layers:

- `Joint/Common Layer`
  - command relationships
  - authority scope
  - task organization
  - commander intent / order / report
- `Service Profile Layer`
  - USAF
  - Army
  - Navy
  - Marine Corps
- `Platform/Task Layer`
  - air vehicle
  - naval platform
  - land platform
  - domain-specific recovery / route / sensor / weapon semantics

## 4. Research Baseline

This refactor uses only official or officially hosted public sources. The priority order is:

- Joint Chiefs of Staff
- USAF doctrine
- U.S. Army official doctrine or doctrine-related official pages
- U.S. Navy official doctrine, fleet, or training pages
- U.S. Marine Corps official doctrine

Current key sources:

- [Joint Chiefs Service Publications](https://www.jcs.mil/Doctrine/Service-Publications/)
- [CJCSM 3150.13C, Joint Reporting Structure](https://www.jcs.mil/Portals/36/Documents/Library/Manuals/m315013.pdf)
- [AFDP 3-0.1, Command and Control](https://www.doctrine.af.mil/Portals/61/documents/AFDP_3-0_1/AFDP3-0.1CommandandControl.pdf)
- [Army MCCoE](https://usacac.army.mil/Organizations/Centers-of-Excellence-CoE/MCCoE)
- [Army doctrinal references page](https://www.ikn.army.mil/apps/IKNHostedWebsites/Home/LoadPublishedPage?PageUID=30c204aa-de54-471a-8252-2df7d9f5a5cc)
- [Army force structure reference](https://www.army.mil/core/support/best-practices/ap/ap_stylebook_quick_reference.html)
- [U.S. 7th Fleet, CTF 71 establishment](https://www.c7f.navy.mil/Media/News/Display/Article/2641477/ctf-71-establishment-enhances-readiness-in-7th-fleet/)
- [TTGP Warfare Commanders Conference I](https://www.ttgp.navy.mil/OFRP-Syllabus/Warfare-Commanders-Conference-I/)
- [NAVIFOR, IW Has a Seat at the Table](https://www.navifor.usff.navy.mil/Press-Room/News-Stories/Article/2395110/iw-has-a-seat-at-the-table/)
- [COMPHIBRON 5 About](https://www.surfpac.navy.mil/Ships/Amphibious-Squadron-COMPHIBRON-5/About/)
- [MCDP 1-0 w/ CH 1-3](https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/1323621/mcdp-1-0-w-ch-1-3/)

## 5. Alignment Principles

From this round forward, standards documents use the following status categories:

- `Authoritative`
  - The primary basis for current standardized modeling.
- `Specialization`
  - A service-specific or platform-specific supplemental standard.
- `Archived`
  - Historical designs and retired lines that are retained but no longer primary.

Current status mapping:

- `joint/*.md`: `Authoritative`
- `services/*.md`: `Authoritative`
- `air/obs.md`, `air/act.md`, `air/aim.md`, `air/rep.md`: `Specialization`
- `naval/*.md`: `Specialization (early-stage)`
- `docs/Archive/air_first_standards/com/*.md`, `docs/Archive/air_first_standards/com/two_ship/*.md`: `Archived`
- `docs/Archive/architecture/*.md`: `Archived`
