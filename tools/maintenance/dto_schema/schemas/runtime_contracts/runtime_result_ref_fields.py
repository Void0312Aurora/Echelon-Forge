"""Schema for the public v1 terminal result reference."""

from tools.maintenance.dto_schema.model import DtoSchema, Field
from tools.maintenance.dto_schema.schemas.runtime_contracts import (
  ASCII_FILE_HEADER,
  validate_public_runtime_contract_schema,
)


SCHEMA = validate_public_runtime_contract_schema(DtoSchema(
  name="runtime_result_ref",
  output_path=(
    "include/echelon_forge/runtime_contracts/detail/runtime_result_ref_fields.inc"
  ),
  fields=(
    Field("request", "RuntimeRequestRef", "{}", "EF_RUNTIME_RESULT_REF_FIELD"),
  ),
  file_header=ASCII_FILE_HEADER,
  file_footer="\n#undef EF_RUNTIME_RESULT_REF_FIELD\n",
))
