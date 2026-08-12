"""Declarative DTO schema for RuntimeCapabilities fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of RuntimeCapabilities fields.\n'
    '//\n'
    '// Consumers define EF_RUNTIME_CAPABILITIES_FIELD(type, name, default_value)\n'
    "// before including this file; the macro is #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_RUNTIME_CAPABILITIES_FIELD\n'
)


SCHEMA = DtoSchema(
    name='runtime_capabilities',
    output_path='src/runtime/facade/detail/runtime/runtime_capabilities.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='supports_batch_runtime', cpp_type='bool', default='false', group='EF_RUNTIME_CAPABILITIES_FIELD'),
        Field(name='supports_compiled_episode_controller', cpp_type='bool', default='false', group='EF_RUNTIME_CAPABILITIES_FIELD'),
        Field(name='supports_compiled_execution_step', cpp_type='bool', default='false', group='EF_RUNTIME_CAPABILITIES_FIELD'),
        Field(name='supports_gpu_visual', cpp_type='bool', default='false', group='EF_RUNTIME_CAPABILITIES_FIELD'),
        Field(name='supports_gpu_observation', cpp_type='bool', default='false', group='EF_RUNTIME_CAPABILITIES_FIELD'),
        Field(name='supports_gpu_flight_shaping', cpp_type='bool', default='false', group='EF_RUNTIME_CAPABILITIES_FIELD'),
        Field(name='supports_device_observation_view', cpp_type='bool', default='false', group='EF_RUNTIME_CAPABILITIES_FIELD'),
        Field(name='supports_resident_state', cpp_type='bool', default='false', group='EF_RUNTIME_CAPABILITIES_FIELD'),
        Field(name='supports_exact_gpu_backend', cpp_type='bool', default='false', group='EF_RUNTIME_CAPABILITIES_FIELD'),
        Field(name='supports_shadow_compare', cpp_type='bool', default='false', group='EF_RUNTIME_CAPABILITIES_FIELD'),
        Field(name='maintained_baseline_backend_profile_id', cpp_type='std::string', default='{}', group='EF_RUNTIME_CAPABILITIES_FIELD'),
        Field(name='maintained_baseline_parity_budget_ref', cpp_type='std::string', default='{}', group='EF_RUNTIME_CAPABILITIES_FIELD'),
        Field(name='maintained_baseline_profile_status', cpp_type='std::string', default='{}', group='EF_RUNTIME_CAPABILITIES_FIELD'),
        Field(name='device_observation_view_candidate_profile_id', cpp_type='std::string', default='{}', group='EF_RUNTIME_CAPABILITIES_FIELD'),
        Field(name='device_observation_view_rejection_reason', cpp_type='std::string', default='{}', group='EF_RUNTIME_CAPABILITIES_FIELD'),
        Field(name='exact_gpu_backend_candidate_profile_id', cpp_type='std::string', default='{}', group='EF_RUNTIME_CAPABILITIES_FIELD'),
        Field(name='exact_gpu_backend_rejection_reason', cpp_type='std::string', default='{}', group='EF_RUNTIME_CAPABILITIES_FIELD'),
        Field(name='resident_state_candidate_profile_id', cpp_type='std::string', default='{}', group='EF_RUNTIME_CAPABILITIES_FIELD'),
        Field(name='resident_state_candidate_parity_budget_ref', cpp_type='std::string', default='{}', group='EF_RUNTIME_CAPABILITIES_FIELD'),
        Field(name='resident_state_rejection_reason', cpp_type='std::string', default='{}', group='EF_RUNTIME_CAPABILITIES_FIELD'),
        Field(name='shadow_compare_candidate_profile_id', cpp_type='std::string', default='{}', group='EF_RUNTIME_CAPABILITIES_FIELD'),
        Field(name='shadow_compare_candidate_parity_budget_ref', cpp_type='std::string', default='{}', group='EF_RUNTIME_CAPABILITIES_FIELD'),
        Field(name='shadow_compare_rejection_reason', cpp_type='std::string', default='{}', group='EF_RUNTIME_CAPABILITIES_FIELD'),
        Field(name='multi_fidelity_rejection_reason', cpp_type='std::string', default='{}', group='EF_RUNTIME_CAPABILITIES_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
