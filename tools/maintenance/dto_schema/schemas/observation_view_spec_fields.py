"""Declarative DTO schema for ObservationViewSpec fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of ObservationViewSpec fields.\n'
    '//\n'
    '// Consumers define EF_OBSERVATION_VIEW_SPEC_FIELD(type, name,\n'
    '// default_value) before including this file; the macro is #undef\'d here\n'
    '// after expansion.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_OBSERVATION_VIEW_SPEC_FIELD\n'
)


SCHEMA = DtoSchema(
    name='observation_view_spec',
    output_path='src/runtime/contracts/detail/observation_view_spec.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='schema_version', cpp_type='std::string', default='"1.0"', group='EF_OBSERVATION_VIEW_SPEC_FIELD'),
        Field(name='required_fields', cpp_type='std::vector<std::string>', default='{}', group='EF_OBSERVATION_VIEW_SPEC_FIELD'),
        Field(name='optional_fields', cpp_type='std::vector<std::string>', default='{}', group='EF_OBSERVATION_VIEW_SPEC_FIELD'),
        Field(name='reject_major_mismatch', cpp_type='bool', default='true', group='EF_OBSERVATION_VIEW_SPEC_FIELD'),
        Field(name='allow_minor_version_drift', cpp_type='bool', default='true', group='EF_OBSERVATION_VIEW_SPEC_FIELD'),
        Field(name='allow_unknown_optional_fields', cpp_type='bool', default='true', group='EF_OBSERVATION_VIEW_SPEC_FIELD'),
        Field(name='allow_missing_optional_fields', cpp_type='bool', default='true', group='EF_OBSERVATION_VIEW_SPEC_FIELD'),
        # T8 fourth slice (I60): additive structural-fact declaration of the maintained
        # observation view at the TL13 seam. Appended after the checkpoint-compatibility
        # fields (member order ABI: append-only). These carry the layer/stage/view-id
        # STRUCTURAL facts mirrored from the Python registry (gym_envs.observation_view /
        # python.architecture.information_layer); the detailed observation field list
        # stays Python-owned to avoid dual-source drift, and a G4 architecture test gates
        # C++ export == Python registry. Empty by default so every existing default-
        # constructed ObservationViewSpec (checkpoint-compat consumers) is unchanged.
        Field(name='view_id', cpp_type='std::string', default='""', group='EF_OBSERVATION_VIEW_SPEC_FIELD'),
        Field(name='information_layer_produced', cpp_type='std::vector<std::string>', default='{}', group='EF_OBSERVATION_VIEW_SPEC_FIELD'),
        Field(name='information_layer_consumed', cpp_type='std::vector<std::string>', default='{}', group='EF_OBSERVATION_VIEW_SPEC_FIELD'),
        Field(name='semantic_stage', cpp_type='std::vector<std::string>', default='{}', group='EF_OBSERVATION_VIEW_SPEC_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
