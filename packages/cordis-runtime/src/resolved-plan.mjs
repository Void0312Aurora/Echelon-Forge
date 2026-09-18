import { createHash } from 'node:crypto';
import {
  AUTHORITY_CANONICALIZATION,
  AUTHORITY_ENVELOPE_VERSION,
  authorityDigestHex,
  canonicalAuthorityJson,
} from './authority.mjs';
import { canonicalJson, sha256Bytes, sortKeys } from './producer.mjs';

export const RESOLVED_EXECUTION_PLAN_SCHEMA_VERSION = 'echelon_forge.resolved_execution_plan.v1';
export const RESOLVED_EXECUTION_PLAN_CONTRACT_VERSION = '1.0.0';

function digest(value) {
  return sha256Bytes(Buffer.from(canonicalJson(value), 'utf8'));
}

function exactBackend(lock, backendRequest) {
  const entries = lock.entries.filter((entry) => entry.category === 'backend');
  if (entries.length !== 1) throw new Error('closed plan requires exactly one admitted backend entry');
  const entry = entries[0];
  if (entry.descriptor_id !== backendRequest.provider_id ||
      entry.implementation_version !== backendRequest.provider_implementation_version ||
      entry.trust_decision !== 'admitted') {
    throw new Error('backend request is not bound to the admitted catalog backend entry');
  }
  return entry;
}

export function buildResolvedExecutionPlan({
  request,
  catalogLock,
  profileProjection,
  backendRequest,
  requestedManifest,
  resolvedManifest,
  planId = 'plan-default-closed',
  writerGeneration = '1',
  readerGenerationMin = '1',
  readerGenerationMax = '1',
}) {
  const backendEntry = exactBackend(catalogLock, backendRequest);
  const manifest = resolvedManifest.manifest ?? resolvedManifest;
  const requested = requestedManifest.manifest ?? requestedManifest;
  if (canonicalJson(manifest) !== canonicalJson(requested)) {
    throw new Error('closed plan requested and resolved manifests differ');
  }
  if (manifest.backend_request.provider_id !== backendRequest.provider_id ||
      manifest.backend_request.backend_profile_id !== backendRequest.backend_profile_id ||
      !manifest.providers.some((provider) => provider.provider_id === backendRequest.provider_id &&
        provider.implementation_version === backendRequest.provider_implementation_version)) {
    throw new Error('backend request does not match the resolved manifest provider');
  }
  const inputBindings = {
    request_sha256: digest(request),
    catalog_lock_sha256: catalogLock.lock_sha256,
    profile_projection_sha256: profileProjection.projection_sha256,
    backend_request_sha256: digest(backendRequest),
    requested_manifest_sha256: digest(requestedManifest),
    resolved_manifest_sha256: resolvedManifest.resolved_manifest_sha256,
  };
  const ownerJoin = {
    composition_id: manifest.composition_id,
    requested_profile: manifest.requested_profile,
    backend_provider_id: backendRequest.provider_id,
    backend_profile_id: backendRequest.backend_profile_id,
    backend_implementation_version: backendRequest.provider_implementation_version,
    catalog_backend_owner_id: backendEntry.owner_id,
    catalog_backend_implementation_id: backendEntry.implementation_id,
    catalog_backend_provenance: backendEntry.provenance,
    catalog_backend_capabilities: [...backendEntry.capabilities].sort(),
    resolver_contract_version: resolvedManifest.resolver_contract_version,
  };
  const authorityPayload = {
    authority_kind: 'resolved_execution_plan',
    schema_version: RESOLVED_EXECUTION_PLAN_SCHEMA_VERSION,
    contract_version: `echelon_forge.resolved_execution_plan_contract.v1`,
    writer_role: 'plan_compiler',
    plan_id: planId,
    writer_generation: writerGeneration,
    reader_generation_min: readerGenerationMin,
    reader_generation_max: readerGenerationMax,
    ...inputBindings,
    composition_id: ownerJoin.composition_id,
    requested_profile: ownerJoin.requested_profile,
    backend: {
      provider_id: ownerJoin.backend_provider_id,
      profile_id: ownerJoin.backend_profile_id,
      implementation_version: ownerJoin.backend_implementation_version,
      required_capabilities: backendRequest.required_capabilities,
    },
    provider_versions: manifest.providers.map(({ provider_id, implementation_version }) => ({ provider_id, implementation_version })),
    resolved_manifest: resolvedManifest,
  };
  const authorityPayloadBytes = canonicalAuthorityJson(authorityPayload);
  const authorityEnvelope = sortKeys({
    canonicalization: AUTHORITY_CANONICALIZATION,
    domain: 'composition.execution-plan',
    envelope_version: AUTHORITY_ENVELOPE_VERSION,
    media_type: 'application/vnd.echelon-forge.resolved-execution-plan.v1+json',
    payload: JSON.parse(authorityPayloadBytes),
    payload_sha256: authorityDigestHex('composition.execution-plan', 'application/vnd.echelon-forge.resolved-execution-plan.v1+json', authorityPayloadBytes),
    signatures: [],
  });
  const body = {
    schema_version: RESOLVED_EXECUTION_PLAN_SCHEMA_VERSION,
    plan_contract_version: RESOLVED_EXECUTION_PLAN_CONTRACT_VERSION,
    plan_id: planId,
    writer_role: 'plan_compiler',
    writer_generation: writerGeneration,
    reader_generation_min: readerGenerationMin,
    reader_generation_max: readerGenerationMax,
    authority_envelope_json: JSON.stringify(authorityEnvelope),
    authority_payload_bytes: JSON.parse(authorityPayloadBytes),
    owner_inputs: { request, catalog_lock: catalogLock, profile_projection: profileProjection, backend_request: backendRequest, requested_manifest: requestedManifest, resolved_manifest: resolvedManifest },
    input_bindings: inputBindings,
    owner_join: ownerJoin,
    canonicalization: 'echelon_forge.sorted_utf8_json.v1',
    hash_algorithm: 'sha256',
  };
  const canonical = canonicalJson(body);
  return sortKeys({ ...body, canonical_json: canonical, plan_sha256: createHash('sha256').update(canonical, 'utf8').digest('hex') });
}
