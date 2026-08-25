"""Schema for the public v1 runtime world reference."""

from tools.maintenance.dto_schema.model import DtoSchema, Field
from tools.maintenance.dto_schema.schemas.runtime_contracts import (
  ASCII_FILE_HEADER,
  validate_public_runtime_contract_schema,
)


SCHEMA = validate_public_runtime_contract_schema(DtoSchema(
  name="runtime_world_ref",
  output_path=(
    "include/echelon_forge/runtime_contracts/detail/runtime_world_ref_fields.inc"
  ),
  fields=(
    Field("incarnation", "RuntimeIncarnationRef", "{}", "EF_RUNTIME_WORLD_REF_FIELD"),
    Field("world_slot", "std::uint64_t", "0", "EF_RUNTIME_WORLD_REF_FIELD"),
    Field(
      "world_generation",
      "std::uint64_t",
      "kInvalidRuntimeGeneration",
      "EF_RUNTIME_WORLD_REF_FIELD",
    ),
  ),
  file_header=ASCII_FILE_HEADER,
  file_footer="\n#undef EF_RUNTIME_WORLD_REF_FIELD\n",
))
