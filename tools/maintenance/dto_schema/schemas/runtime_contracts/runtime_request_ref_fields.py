"""Schema for the public v1 runtime request reference."""

from tools.maintenance.dto_schema.model import DtoSchema, Field
from tools.maintenance.dto_schema.schemas.runtime_contracts import (
  ASCII_FILE_HEADER,
  validate_public_runtime_contract_schema,
)


SCHEMA = validate_public_runtime_contract_schema(DtoSchema(
  name="runtime_request_ref",
  output_path=(
    "include/echelon_forge/runtime_contracts/detail/runtime_request_ref_fields.inc"
  ),
  fields=(
    Field("episode", "RuntimeEpisodeRef", "{}", "EF_RUNTIME_REQUEST_REF_FIELD"),
    Field("request_sequence", "std::uint64_t", "0", "EF_RUNTIME_REQUEST_REF_FIELD"),
  ),
  file_header=ASCII_FILE_HEADER,
  file_footer="\n#undef EF_RUNTIME_REQUEST_REF_FIELD\n",
))
