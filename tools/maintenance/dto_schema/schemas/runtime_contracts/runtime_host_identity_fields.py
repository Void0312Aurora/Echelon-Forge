"""Schema for the stable public v1 runtime host identity."""

from tools.maintenance.dto_schema.model import DtoSchema, Field
from tools.maintenance.dto_schema.schemas.runtime_contracts import (
  ASCII_FILE_HEADER,
  validate_public_runtime_contract_schema,
)


SCHEMA = validate_public_runtime_contract_schema(DtoSchema(
  name="runtime_host_identity",
  output_path=(
    "include/echelon_forge/runtime_contracts/detail/"
    "runtime_host_identity_fields.inc"
  ),
  fields=(
    Field("host_id", "RuntimeIdentity128", "{}", "EF_RUNTIME_HOST_IDENTITY_FIELD"),
    Field("boot_id", "RuntimeIdentity128", "{}", "EF_RUNTIME_HOST_IDENTITY_FIELD"),
  ),
  file_header=ASCII_FILE_HEADER,
  file_footer="\n#undef EF_RUNTIME_HOST_IDENTITY_FIELD\n",
))
