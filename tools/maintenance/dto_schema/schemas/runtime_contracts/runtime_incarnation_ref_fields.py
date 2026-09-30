"""Schema for the public v1 published runtime incarnation reference."""

from tools.maintenance.dto_schema.model import DtoSchema, Field
from tools.maintenance.dto_schema.schemas.runtime_contracts import (
  ASCII_FILE_HEADER,
  validate_public_runtime_contract_schema,
)


SCHEMA = validate_public_runtime_contract_schema(DtoSchema(
  name="runtime_incarnation_ref",
  output_path=(
    "include/echelon_forge/runtime_contracts/detail/"
    "runtime_incarnation_ref_fields.inc"
  ),
  fields=(
    Field("host", "RuntimeHostIdentity", "{}", "EF_RUNTIME_INCARNATION_REF_FIELD"),
    Field(
      "incarnation_epoch",
      "std::uint64_t",
      "kInvalidRuntimeGeneration",
      "EF_RUNTIME_INCARNATION_REF_FIELD",
    ),
  ),
  file_header=ASCII_FILE_HEADER,
  file_footer="\n#undef EF_RUNTIME_INCARNATION_REF_FIELD\n",
))
