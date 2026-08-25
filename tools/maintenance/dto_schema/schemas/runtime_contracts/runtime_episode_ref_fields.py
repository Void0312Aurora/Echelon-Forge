"""Schema for the public v1 runtime episode reference."""

from tools.maintenance.dto_schema.model import DtoSchema, Field
from tools.maintenance.dto_schema.schemas.runtime_contracts import (
  ASCII_FILE_HEADER,
  validate_public_runtime_contract_schema,
)


SCHEMA = validate_public_runtime_contract_schema(DtoSchema(
  name="runtime_episode_ref",
  output_path=(
    "include/echelon_forge/runtime_contracts/detail/runtime_episode_ref_fields.inc"
  ),
  fields=(
    Field("world", "RuntimeWorldRef", "{}", "EF_RUNTIME_EPISODE_REF_FIELD"),
    Field("episode_id", "RuntimeIdentity128", "{}", "EF_RUNTIME_EPISODE_REF_FIELD"),
    Field(
      "episode_generation",
      "std::uint64_t",
      "kInvalidRuntimeGeneration",
      "EF_RUNTIME_EPISODE_REF_FIELD",
    ),
  ),
  file_header=ASCII_FILE_HEADER,
  file_footer="\n#undef EF_RUNTIME_EPISODE_REF_FIELD\n",
))
