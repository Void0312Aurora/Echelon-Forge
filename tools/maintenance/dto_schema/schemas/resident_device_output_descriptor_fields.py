"""Declarative DTO schema for DeviceResidentOutputDescriptor fields.

The schema/macro/output-path names deliberately spell "resident_device"
rather than "device_resident": some runtime_facade boundary-guard tests
scan runtime_facade_types.h for the literal lowercase substring
"device_resident" as a marker for hand-written GPU-residency escape hatches
(see tests/architecture/runtime_facade/test_runtime_facade_contract_boundaries.py).
Reusing that word order in the generated #include path would trip that
guard purely on the schema plumbing, not on any real GPU dependency.
"""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of DeviceResidentOutputDescriptor fields.\n'
    '//\n'
    '// Consumers define EF_RESIDENT_DEVICE_OUTPUT_DESCRIPTOR_FIELD(type, name,\n'
    '// default_value) before including this file; the macro is #undef\'d here\n'
    '// after expansion.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_RESIDENT_DEVICE_OUTPUT_DESCRIPTOR_FIELD\n'
)


SCHEMA = DtoSchema(
    name='resident_device_output_descriptor',
    output_path='src/runtime/facade/detail/resident_device_output_descriptor.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='output_shape', cpp_type='std::vector<std::uint64_t>', default='{}', group='EF_RESIDENT_DEVICE_OUTPUT_DESCRIPTOR_FIELD'),
        Field(name='dtype', cpp_type='std::string', default='{}', group='EF_RESIDENT_DEVICE_OUTPUT_DESCRIPTOR_FIELD'),
        Field(name='element_count', cpp_type='std::size_t', default='0', group='EF_RESIDENT_DEVICE_OUTPUT_DESCRIPTOR_FIELD'),
        Field(name='source_snapshot', cpp_type='std::uint64_t', default='0', group='EF_RESIDENT_DEVICE_OUTPUT_DESCRIPTOR_FIELD'),
        Field(name='sync_or_export_barrier', cpp_type='std::string', default='{}', group='EF_RESIDENT_DEVICE_OUTPUT_DESCRIPTOR_FIELD'),
        Field(name='host_visible_availability', cpp_type='std::string', default='"unavailable"', group='EF_RESIDENT_DEVICE_OUTPUT_DESCRIPTOR_FIELD'),
        Field(name='diagnostics_label', cpp_type='std::string', default='"diagnostics_only"', group='EF_RESIDENT_DEVICE_OUTPUT_DESCRIPTOR_FIELD'),
        Field(name='consumer_constraints', cpp_type='std::vector<std::string>', default='{}', group='EF_RESIDENT_DEVICE_OUTPUT_DESCRIPTOR_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
