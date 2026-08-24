import { Context, Service } from 'cordis';
import { createHash } from 'node:crypto';
import { DEFAULT_PROFILE } from '../profiles/default-compatibility.mjs';

export const REQUEST_SCHEMA_VERSION = 'echelon_forge.runtime_composition_request.v1';

class CatalogLockService extends Service {
  static provide = 'catalogLock';

  constructor(ctx, config) {
    super(ctx, 'catalogLock');
    this.lock = config;
  }
}

function utf8Compare(left, right) {
  return Buffer.compare(Buffer.from(left, 'utf8'), Buffer.from(right, 'utf8'));
}

function sortKeys(value) {
  if (Array.isArray(value)) return value.map(sortKeys);
  if (!value || typeof value !== 'object') return value;
  return Object.fromEntries(
    Object.entries(value)
      .sort(([left], [right]) => utf8Compare(left, right))
      .map(([key, nested]) => [key, sortKeys(nested)]),
  );
}

function sortedUnique(values) {
  return [...new Set(values)].sort(utf8Compare);
}

export function lowerDefaultProfile(profile = DEFAULT_PROFILE) {
  if (!profile || typeof profile !== 'object') {
    throw new TypeError('profile must be an object');
  }
  if (profile.profile_id !== DEFAULT_PROFILE.profile_id ||
      profile.profile_version !== DEFAULT_PROFILE.profile_version) {
    throw new Error(`unsupported profile: ${profile.profile_id}@${profile.profile_version}`);
  }
  if (canonicalJson(profile) !== canonicalJson(DEFAULT_PROFILE)) {
    throw new Error('unsupported profile bundle contents');
  }
  return sortKeys({
    schema_version: REQUEST_SCHEMA_VERSION,
    request_id: profile.request_id,
    request_version: profile.request_version,
    contract_versions: profile.contract_versions,
    intent: profile.intent,
    requested_profile: {
      profile_id: profile.profile_id,
      profile_version: profile.profile_version,
    },
    required_capabilities: sortedUnique(profile.required_capabilities),
    required_policies: sortedUnique(profile.required_policies),
    configuration: profile.configuration,
  });
}

export function canonicalJson(value) {
  return JSON.stringify(sortKeys(value));
}

export function sha256Hex(value) {
  return createHash('sha256').update(canonicalJson(value), 'utf8').digest('hex');
}

export function sha256Bytes(value) {
  return createHash('sha256').update(value).digest('hex');
}

export function lowerDefaultManifest(request, manifestTemplate) {
  if (!request || request.requested_profile?.profile_id !== DEFAULT_PROFILE.profile_id ||
      request.requested_profile?.profile_version !== DEFAULT_PROFILE.profile_version) {
    throw new Error('unsupported request profile for low-level manifest lowering');
  }
  if (!manifestTemplate || typeof manifestTemplate !== 'object' ||
      manifestTemplate.composition_id !== request.requested_profile.profile_id ||
      manifestTemplate.requested_profile?.profile_id !== request.requested_profile.profile_id ||
      manifestTemplate.requested_profile?.profile_version !== request.requested_profile.profile_version) {
    throw new Error('low-level manifest template does not match the admitted request profile');
  }
  return sortKeys({
    ...manifestTemplate,
    composition_id: request.requested_profile.profile_id,
    contract_versions: request.contract_versions,
    requested_profile: request.requested_profile,
  });
}

/**
 * Join a compatibility profile to the owner-admitted catalog and the native
 * resolved graph.  The profile remains an alias for capabilities/policies;
 * contribution identities are copied from the native artifact and cannot be
 * supplied by the producer as an independent package graph.
 */
export function lowerDefaultProfileProjection(request, lock, requestedManifest, resolvedManifest) {
  if (!request || request.requested_profile?.profile_id !== DEFAULT_PROFILE.profile_id ||
      request.requested_profile?.profile_version !== DEFAULT_PROFILE.profile_version) {
    throw new Error('unsupported request profile for profile projection');
  }
  if (!lock || request.requested_profile.profile_id !== DEFAULT_PROFILE.profile_id ||
      lock.request_sha256 !== sha256Hex(request)) {
    throw new Error('profile projection request is not bound to the admitted catalog lock');
  }
  if (canonicalJson(request.required_capabilities) !== canonicalJson(DEFAULT_PROFILE.required_capabilities) ||
      canonicalJson(request.required_policies) !== canonicalJson(DEFAULT_PROFILE.required_policies)) {
    throw new Error('profile projection capability/policy set mismatch');
  }
  const resolved = resolvedManifest?.manifest ?? resolvedManifest;
  const requested = requestedManifest?.manifest ?? requestedManifest;
  if (canonicalJson(resolved) !== canonicalJson(requested)) {
    throw new Error('profile projection requested and resolved manifests differ');
  }
  const categories = ['backend', 'domain', 'evidence', 'model', 'security', 'system'];
  const entries = categories.map((category) => {
    const matches = lock.entries.filter((entry) => entry.category === category);
    if (matches.length !== 1) throw new Error(`profile projection requires one admitted ${category} entry`);
    const entry = matches[0];
    return {
      category: entry.category,
      owner_id: entry.owner_id,
      descriptor_id: entry.descriptor_id,
      capabilities: [...entry.capabilities].sort(utf8Compare),
    };
  });
  const components = [...(resolved.component_contributions ?? [])]
    .sort((left, right) => utf8Compare(left.component_id, right.component_id))
    .map(({ component_id, registration_id }) => ({ component_id, registration_id }));
  const systemOrder = [...(resolvedManifest.system_registration_order ?? [])];
  const systems = systemOrder.map((contribution_id, stage_order) => ({ contribution_id, stage_order }));
  const payload = sortKeys({
    schema_version: 'echelon_forge.runtime_profile_projection.v1',
    projection_id: `${DEFAULT_PROFILE.profile_id}.projection`,
    projection_version: '1.0.0',
    requested_profile: request.requested_profile,
    request_sha256: sha256Hex(request),
    lock_sha256: lock.lock_sha256,
    authority_registry_sha256: lock.authority_registry_sha256,
    required_capabilities: [...request.required_capabilities].sort(utf8Compare),
    required_policies: [...request.required_policies].sort(utf8Compare),
    catalog_entries: entries,
    component_contributions: components,
    system_contributions: systems,
    compatibility_claims: [...(resolved.compatibility_claims ?? [])].sort(utf8Compare),
    canonicalization: 'echelon_forge.sorted_utf8_json.v1',
    hash_algorithm: 'sha256',
  });
  const canonical_json = canonicalJson(payload);
  return sortKeys({
    ...payload,
    canonical_json,
    projection_sha256: sha256Hex(payload),
  });
}

/**
 * Produce one request through Cordis Context/plugin/fiber lifecycle.
 * The profile bundle owns authoring; native code remains the validator and
 * realization authority after this producer returns.
 */
export async function produceDefaultRequest(profile = DEFAULT_PROFILE, catalogLock = null) {
  if (!catalogLock || typeof catalogLock !== 'object' ||
      typeof catalogLock.lock_id !== 'string' || catalogLock.lock_id.length === 0) {
    throw new Error('Cordis producer requires an admitted catalog-lock artifact');
  }
  const root = new Context();
  let produced;
  let disposed = false;
  root.effect(() => () => {
    disposed = true;
  }, 'cordis-runtime-producer');
  const profileProducer = Object.assign((ctx) => {
    ctx.on('runtime/compose', (candidate) => {
      if (!ctx.catalogLock) throw new Error('Cordis catalog-lock service is unavailable');
      produced = lowerDefaultProfile(candidate);
    });
  }, { inject: ['catalogLock'] });

  try {
    await root.plugin(CatalogLockService, catalogLock);
    await root.plugin(profileProducer);
    root.emit('runtime/compose', profile);
  } finally {
    await root.fiber.dispose();
  }
  if (!disposed) throw new Error('Cordis producer effect did not dispose');
  if (!produced) throw new Error('Cordis producer emitted no request');
  return produced;
}

export { sortKeys };
