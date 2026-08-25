"""Schema for the public v1 runtime entity reference."""

from tools.maintenance.dto_schema.model import DtoSchema, Field
from tools.maintenance.dto_schema.schemas.runtime_contracts import (
  ASCII_FILE_HEADER,
  validate_public_runtime_contract_schema,
)


SCHEMA = validate_public_runtime_contract_schema(DtoSchema(
  name="runtime_entity_ref",
  output_path=(
    "include/echelon_forge/runtime_contracts/detail/runtime_entity_ref_fields.inc"
  ),
  fields=(
    Field("world", "RuntimeWorldRef", "{}", "EF_RUNTIME_ENTITY_REF_FIELD"),
    Field("entity_id", "std::uint64_t", "0", "EF_RUNTIME_ENTITY_REF_FIELD"),
    Field(
      "entity_generation",
      "std::uint64_t",
      "kInvalidRuntimeGeneration",
      "EF_RUNTIME_ENTITY_REF_FIELD",
    ),
  ),
  file_header=ASCII_FILE_HEADER,
  file_footer="\n#undef EF_RUNTIME_ENTITY_REF_FIELD\n",
))
