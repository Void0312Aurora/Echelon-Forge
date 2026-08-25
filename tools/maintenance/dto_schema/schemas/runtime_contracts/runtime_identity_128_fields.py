"""Schema for the public v1 opaque 128-bit identity value."""

from tools.maintenance.dto_schema.model import DtoSchema, Field
from tools.maintenance.dto_schema.schemas.runtime_contracts import (
  ASCII_FILE_HEADER,
  validate_public_runtime_contract_schema,
)


SCHEMA = validate_public_runtime_contract_schema(DtoSchema(
  name="runtime_identity_128",
  output_path=(
    "include/echelon_forge/runtime_contracts/detail/"
    "runtime_identity_128_fields.inc"
  ),
  fields=(
    Field("high", "std::uint64_t", "0", "EF_RUNTIME_IDENTITY_128_FIELD"),
    Field("low", "std::uint64_t", "0", "EF_RUNTIME_IDENTITY_128_FIELD"),
  ),
  file_header=ASCII_FILE_HEADER,
  file_footer="\n#undef EF_RUNTIME_IDENTITY_128_FIELD\n",
))
