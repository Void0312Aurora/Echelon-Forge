"""Declarative DTO schema for PilotReportMaintainedBatchContract fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of PilotReportMaintainedBatchContract fields.\n'
    '//\n'
    '// Consumers define EF_PILOT_REPORT_MAINTAINED_BATCH_CONTRACT_FIELD(\n'
    '// type, name, default_value) before including this file; the macro is\n'
    "// #undef'd here after expansion.\n"
    '//\n'
    '// NOTE(I35): the trailing ground_static_status field has never been\n'
    '// bound to Python (pre-existing binding-surface omission). I35\n'
    '// preserves that omission as-is instead of newly exposing the field;\n'
    '// see bindings_runtime.cpp for the held hand-written binding.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_PILOT_REPORT_MAINTAINED_BATCH_CONTRACT_FIELD\n'
)


SCHEMA = DtoSchema(
    name='pilot_report_maintained_batch_contract',
    output_path='src/runtime/contracts/detail/pilot_report_maintained_batch_contract.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='shared_core', cpp_type='shared_core_type', default='{}', group='EF_PILOT_REPORT_MAINTAINED_BATCH_CONTRACT_FIELD'),
        Field(name='air', cpp_type='air_owner_slice_type', default='{}', group='EF_PILOT_REPORT_MAINTAINED_BATCH_CONTRACT_FIELD'),
        Field(name='naval_command_authority', cpp_type='naval_command_authority_type', default='{}', group='EF_PILOT_REPORT_MAINTAINED_BATCH_CONTRACT_FIELD'),
        Field(name='ground_static_status', cpp_type='ground_static_status_type', default='{}', group='EF_PILOT_REPORT_MAINTAINED_BATCH_CONTRACT_FIELD', hidden=True),
    ),
    file_footer=FILE_FOOTER,
)
