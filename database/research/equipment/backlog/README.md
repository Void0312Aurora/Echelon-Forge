# Research Backlog

Language: English canonical. Chinese companion: not established.

Document kind: \`reference\`
Lifecycle: \`draft\`
Canonical: \`database/research/equipment/backlog/README.md\`
Owner: \`database/equipment-data\`
Last verified: \`not established\`
Content status: Operational research queue. A queued row is not verified equipment data.

## Responsibility

Owns the candidate list and processing status for equipment research. Catalog records remain the authoritative equipment documents.

## State Model

- \`queued\`: discovered candidate, source work has not started.
- \`source_search\`: searching Tier A/B sources.
- \`source_acquired\`: at least one source package exists.
- \`extracted\`: parameters and identity have been extracted.
- \`cross_checked\`: conflicting sources have been compared.
- \`cataloged\`: a concrete draft leaf record exists in \`catalog/\`; completeness is not implied.
- \`parameter_complete\`: every declared target field has a cited value or a bounded, explicitly labelled estimate; no target field remains \`unknown\`.
- \`held\`: source scarcity or ambiguity blocks cataloging.

## Queue

- [Air queue](air.csv)
- [Ground queue](ground.csv)
- [Naval queue](naval.csv)
- [Weapon queue](weapon.csv)
- [Module queue](module.csv)
- [Cross-domain coverage queue](../coverage/coverage.csv)

The coverage queue is a discovery list for current, post-Cold-War, and Cold-War candidates. It is not verified equipment data. Candidates enter the domain queues only after a concrete variant and source package are selected.

`cataloged` only means that a draft leaf exists. It does not mean that the parameter set is complete, cross-checked, calibrated, or suitable for runtime use. A leaf must reach `parameter_complete` and then `cross_checked` before it can be treated as a complete research result; unresolved source scarcity should be recorded as `held` rather than hidden behind `unknown`.
