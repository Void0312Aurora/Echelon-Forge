"""Declarative DTO schema for the scenario-generation evidence-ref lineage vocabulary.

Shared schema owner (T10 census VA-6) for the evidence-ref face of the
scenario-generation lineage vocabulary:

- C++ face: ``ScenarioGenerationEvidenceMetadataRef`` in
  src/runtime/contracts/counterfactual_replay_contract_types.h
- Python face: ``ScenarioGenerationEvidenceRef`` in
  python/scenario/compiler/generation_request.py

Both faces are gated against this schema by
tests/architecture/governance/test_scenario_generation_lineage_parity.py.

SEAM STATUS (this iteration): the C++ header includes the generated .inc at
its original seam, so the compiled member list IS this schema's rendering;
the parity gate verifies the seam adoption plus schema==.inc field equality
instead of parsing hand-written members. The Python dataclass stays hand-written
because python/scenario must not import gym_envs at runtime (no new runtime
import direction); its serialization (to_metadata) key order is gated to
this schema's field order.
"""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of ScenarioGenerationEvidenceMetadataRef fields.\n'
    '//\n'
    '// Consumers define EF_SCENARIO_GENERATION_EVIDENCE_REF_FIELD(type, name,\n'
    '// default_value) before including this file; the macro is #undef\'d here\n'
    '// after expansion.\n'
    '//\n'
    '// counterfactual_replay_contract_types.h includes this file at the\n'
    '// struct\'s original seam, so this list is the single C++ member-order\n'
    '// owner (ABI: additive/append-only); the cross-language gate is\n'
    '// tests/architecture/governance/test_scenario_generation_lineage_parity.py.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_SCENARIO_GENERATION_EVIDENCE_REF_FIELD\n'
)


SCHEMA = DtoSchema(
    name='scenario_generation_evidence_ref',
    output_path='src/runtime/contracts/detail/scenario/scenario_generation_evidence_ref.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='ref_id', cpp_type='std::string', default='""', group='EF_SCENARIO_GENERATION_EVIDENCE_REF_FIELD'),
        Field(name='evidence_kind', cpp_type='std::string', default='""', group='EF_SCENARIO_GENERATION_EVIDENCE_REF_FIELD'),
        Field(name='provenance_label', cpp_type='std::string', default='""', group='EF_SCENARIO_GENERATION_EVIDENCE_REF_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
