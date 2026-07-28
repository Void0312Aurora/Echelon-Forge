"""Declarative DTO schema for the scenario-generation request lineage vocabulary.

Shared schema owner (T10 census VA-6) for the parallel lineage vocabularies:

- C++ face: ``ScenarioGenerationRequestMetadata`` in
  src/runtime/contracts/counterfactual_replay_contract_types.h
- Python face: ``ScenarioGenerationRequest`` in
  python/scenario/compiler/generation_request.py

Field ORDER below is the C++ member order (ABI: additive/append-only) and is
also the serialization key order of the Python face's ``to_metadata()``. Both
faces are gated against this schema by
tests/architecture/governance/test_scenario_generation_lineage_parity.py.

SEAM STATUS (this iteration): the C++ header includes the generated .inc at
its original seam, so the compiled member list IS this schema's rendering;
the parity gate verifies the seam adoption plus schema==.inc field equality
instead of parsing hand-written members. The Python dataclass stays
hand-written because python/scenario must not import gym_envs at runtime (no
new runtime import direction); its metadata projection is gated to this
schema.

HELD VERDICTS (codec escape hatches observed while unifying; recorded, not
forced):

1. ``has_deterministic_seed`` is a C++-only presence flag with no Python
   counterpart: the Python dataclass encodes presence structurally by making
   ``deterministic_seed`` a required constructor argument, and its
   ``to_metadata()`` intentionally emits no ``has_deterministic_seed`` key.
   HELD: do not add the flag to the Python face or serialization, and do not
   remove it from the C++ face; the parity gate pins this exact projection
   (schema field set minus ``has_deterministic_seed``).
2. Python constructor parameter order deviates from the ABI member order
   because dataclasses require defaulted parameters last; the serialization
   order (``to_metadata`` key order) follows the ABI order recorded here.
   HELD: the constructor permutation is pinned by the parity gate rather
   than reordered (reordering keyword-capable parameters would be a public
   API behavior change).
3. The Python face normalizes values in ``__post_init__`` (strip, dedupe +
   sort ``capability_refs``, sort ``evidence_refs``, dict coercion); the C++
   face stores values verbatim. This is Python-face codec behavior outside
   the vocabulary this schema owns. HELD: not represented in the schema.
"""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of ScenarioGenerationRequestMetadata fields.\n'
    '//\n'
    '// Consumers define EF_SCENARIO_GENERATION_REQUEST_METADATA_FIELD(type,\n'
    '// name, default_value) before including this file; the macro is\n'
    '// #undef\'d here after expansion. The contract_version default requires\n'
    '// counterfactual_replay_contract_constants.h and the evidence_refs\n'
    '// element type requires ScenarioGenerationEvidenceMetadataRef to be\n'
    '// declared before expansion.\n'
    '//\n'
    '// counterfactual_replay_contract_types.h includes this file at the\n'
    '// struct\'s original seam, so this list is the single C++ member-order\n'
    '// owner (ABI: additive/append-only); the cross-language gate is\n'
    '// tests/architecture/governance/test_scenario_generation_lineage_parity.py.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_SCENARIO_GENERATION_REQUEST_METADATA_FIELD\n'
)


SCHEMA = DtoSchema(
    name='scenario_generation_request_metadata',
    output_path='src/runtime/contracts/detail/scenario_generation_request_metadata.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='request_id', cpp_type='std::string', default='""', group='EF_SCENARIO_GENERATION_REQUEST_METADATA_FIELD'),
        Field(name='request_version', cpp_type='std::string', default='"1"', group='EF_SCENARIO_GENERATION_REQUEST_METADATA_FIELD'),
        Field(name='contract_version', cpp_type='std::string', default='std::string(kScenarioGenerationContractVersionRequestV1)', group='EF_SCENARIO_GENERATION_REQUEST_METADATA_FIELD'),
        Field(name='generation_kind', cpp_type='std::string', default='""', group='EF_SCENARIO_GENERATION_REQUEST_METADATA_FIELD'),
        Field(name='source', cpp_type='std::string', default='""', group='EF_SCENARIO_GENERATION_REQUEST_METADATA_FIELD'),
        Field(name='generator_version', cpp_type='std::string', default='""', group='EF_SCENARIO_GENERATION_REQUEST_METADATA_FIELD'),
        # C++-only presence flag; the Python face has no counterpart (held
        # verdict 1 in the module docstring).
        Field(name='has_deterministic_seed', cpp_type='bool', default='false', group='EF_SCENARIO_GENERATION_REQUEST_METADATA_FIELD'),
        Field(name='deterministic_seed', cpp_type='std::uint64_t', default='0', group='EF_SCENARIO_GENERATION_REQUEST_METADATA_FIELD'),
        Field(name='baseline_scenario_ref', cpp_type='std::string', default='""', group='EF_SCENARIO_GENERATION_REQUEST_METADATA_FIELD'),
        Field(name='replay_envelope_ref', cpp_type='std::string', default='""', group='EF_SCENARIO_GENERATION_REQUEST_METADATA_FIELD'),
        Field(name='branch_point_ref', cpp_type='std::string', default='""', group='EF_SCENARIO_GENERATION_REQUEST_METADATA_FIELD'),
        Field(name='capability_refs', cpp_type='std::vector<std::string>', default='{}', group='EF_SCENARIO_GENERATION_REQUEST_METADATA_FIELD'),
        Field(name='evidence_refs', cpp_type='std::vector<ScenarioGenerationEvidenceMetadataRef>', default='{}', group='EF_SCENARIO_GENERATION_REQUEST_METADATA_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
