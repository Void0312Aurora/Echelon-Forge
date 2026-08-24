import { DEFAULT_PROFILE } from '../profiles/default-compatibility.mjs';
import { TextDecoder } from 'node:util';
import {
  canonicalJson,
  lowerDefaultProfile,
  produceDefaultRequest,
  sha256Bytes,
  sha256Hex,
  sortKeys,
} from './producer.mjs';

export const PACKAGE_SCHEMA_VERSION = 'echelon_forge.cordis_runtime_package.v1';
export const OVERLAY_SCHEMA_VERSION =
  'echelon_forge.cordis_runtime_configuration_overlay.v1';
export const PROVENANCE_SCHEMA_VERSION =
  'echelon_forge.cordis_runtime_package_provenance.v1';
export const DIAGNOSTICS_SCHEMA_VERSION =
  'echelon_forge.cordis_runtime_package_diagnostics.v1';
export const PRODUCER_PACKAGE_NAME = '@echelon-forge/cordis-runtime';
export const PRODUCER_PACKAGE_VERSION = '0.1.0';

const RESOLVED_PACKAGE_SCHEMA_VERSION =
  'echelon_forge.cordis_runtime_resolved_package.v1';
const SEMVER = /^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?$/;
const SHA256 = /^[0-9a-f]{64}$/;
const ABSOLUTE_OR_TRAVERSAL = /^(?:\/|[A-Za-z]:)|(?:^|\/)\.\.(?:\/|$)/;
const UTF8_DECODER = new TextDecoder('utf-8', { fatal: true });

function utf8Compare(left, right) {
  return Buffer.compare(Buffer.from(left, 'utf8'), Buffer.from(right, 'utf8'));
}

function assertObject(value, label) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new TypeError(`${label} must be an object`);
  }
}

function assertExactKeys(value, expected, label) {
  assertObject(value, label);
  const actual = Object.keys(value).sort(utf8Compare);
  const wanted = [...expected].sort(utf8Compare);
  if (canonicalJson(actual) !== canonicalJson(wanted)) {
    throw new Error(`${label} has unsupported fields`);
  }
}

function assertAscii(value, label) {
  if (typeof value !== 'string' || value.length === 0 || /[^\x00-\x7f]/.test(value)) {
    throw new Error(`${label} must be a non-empty ASCII string`);
  }
}

function assertSemver(value, label) {
  if (typeof value !== 'string' || !SEMVER.test(value)) {
    throw new Error(`${label} must be semantic version text`);
  }
}

function assertSha256(value, label) {
  if (typeof value !== 'string' || !SHA256.test(value)) {
    throw new Error(`${label} must be a lowercase SHA-256 identity`);
  }
}

function assertRelativePath(value, label) {
  assertAscii(value, label);
  if (value.includes('\\') || ABSOLUTE_OR_TRAVERSAL.test(value)) {
    throw new Error(`${label} must remain relative to the package root`);
  }
}

function assertUniqueAscii(values, label) {
  if (!Array.isArray(values)) throw new TypeError(`${label} must be an array`);
  const seen = new Set();
  for (const value of values) {
    assertAscii(value, `${label} entry`);
    if (seen.has(value)) throw new Error(`${label} contains a duplicate: ${value}`);
    seen.add(value);
  }
}

function cloneJson(value) {
  return JSON.parse(JSON.stringify(value));
}

function deepFreeze(value) {
  if (!value || typeof value !== 'object' || Object.isFrozen(value)) return value;
  Object.freeze(value);
  for (const nested of Object.values(value)) deepFreeze(nested);
  return value;
}

function asBuffer(value, label) {
  if (!(value instanceof Uint8Array) || value.byteLength === 0) {
    throw new TypeError(`${label} must contain non-empty bytes`);
  }
  return Buffer.from(value);
}

function parseJsonBytes(bytes, label) {
  try {
    return JSON.parse(UTF8_DECODER.decode(asBuffer(bytes, label)));
  } catch (error) {
    throw new Error(`${label} is not valid UTF-8 JSON: ${error.message}`);
  }
}

function assertJsonBytesMatch(bytes, value, label) {
  const parsed = parseJsonBytes(bytes, label);
  if (canonicalJson(parsed) !== canonicalJson(value)) {
    throw new Error(`${label} bytes do not match the supplied object`);
  }
}

function validateDependency(dependency, index) {
  const label = `dependencies[${index}]`;
  assertObject(dependency, label);
  assertAscii(dependency.dependency_id, `${label}.dependency_id`);
  assertUniqueAscii(dependency.requires, `${label}.requires`);
  if (dependency.kind === 'npm_package') {
    assertExactKeys(
      dependency,
      ['dependency_id', 'kind', 'package_name', 'version', 'requires'],
      label,
    );
    assertAscii(dependency.package_name, `${label}.package_name`);
    assertSemver(dependency.version, `${label}.version`);
    return;
  }
  if (dependency.kind === 'repository_artifact') {
    assertExactKeys(
      dependency,
      ['dependency_id', 'kind', 'path', 'sha256', 'requires'],
      label,
    );
    assertRelativePath(dependency.path, `${label}.path`);
    assertSha256(dependency.sha256, `${label}.sha256`);
    return;
  }
  throw new Error(`${label}.kind is unsupported`);
}

function validateOverlayReference(reference, index) {
  const label = `overlays[${index}]`;
  assertExactKeys(reference, ['overlay_id', 'path', 'sha256', 'required', 'requires'], label);
  assertAscii(reference.overlay_id, `${label}.overlay_id`);
  assertRelativePath(reference.path, `${label}.path`);
  assertSha256(reference.sha256, `${label}.sha256`);
  if (reference.required !== true) throw new Error(`${label}.required must be true`);
  assertUniqueAscii(reference.requires, `${label}.requires`);
}

export function defineRuntimePackage(candidate) {
  assertExactKeys(
    candidate,
    [
      'schema_version',
      'package_id',
      'package_version',
      'profile',
      'cordis_dependency_id',
      'dependencies',
      'overlays',
      'provenance_policy',
      'diagnostics_policy',
    ],
    'runtime package',
  );
  if (candidate.schema_version !== PACKAGE_SCHEMA_VERSION) {
    throw new Error('runtime package schema version is unsupported');
  }
  assertAscii(candidate.package_id, 'runtime package.package_id');
  assertSemver(candidate.package_version, 'runtime package.package_version');
  assertExactKeys(
    candidate.profile,
    ['profile_id', 'profile_version', 'module_dependency_id', 'bundle_dependency_id'],
    'runtime package.profile',
  );
  assertAscii(candidate.profile.profile_id, 'runtime package.profile.profile_id');
  assertSemver(candidate.profile.profile_version, 'runtime package.profile.profile_version');
  assertAscii(
    candidate.profile.module_dependency_id,
    'runtime package.profile.module_dependency_id',
  );
  assertAscii(
    candidate.profile.bundle_dependency_id,
    'runtime package.profile.bundle_dependency_id',
  );
  assertAscii(candidate.cordis_dependency_id, 'runtime package.cordis_dependency_id');
  if (!Array.isArray(candidate.dependencies) || candidate.dependencies.length === 0) {
    throw new Error('runtime package.dependencies must not be empty');
  }
  candidate.dependencies.forEach(validateDependency);
  if (!Array.isArray(candidate.overlays)) throw new TypeError('runtime package.overlays must be an array');
  candidate.overlays.forEach(validateOverlayReference);
  const nodeIds = [
    ...candidate.dependencies.map(({ dependency_id }) => dependency_id),
    ...candidate.overlays.map(({ overlay_id }) => overlay_id),
  ];
  assertUniqueAscii(nodeIds, 'runtime package dependency node identities');

  assertExactKeys(
    candidate.provenance_policy,
    ['require_package_lock', 'require_artifact_hashes'],
    'runtime package.provenance_policy',
  );
  if (candidate.provenance_policy.require_package_lock !== true ||
      candidate.provenance_policy.require_artifact_hashes !== true) {
    throw new Error('runtime package provenance policy must require lock and artifact hashes');
  }
  assertExactKeys(
    candidate.diagnostics_policy,
    ['schema_version', 'redact_absolute_paths'],
    'runtime package.diagnostics_policy',
  );
  if (candidate.diagnostics_policy.schema_version !== DIAGNOSTICS_SCHEMA_VERSION ||
      candidate.diagnostics_policy.redact_absolute_paths !== true) {
    throw new Error('runtime package diagnostics policy is unsupported');
  }

  const dependencies = new Map(
    candidate.dependencies.map((dependency) => [dependency.dependency_id, dependency]),
  );
  const cordis = dependencies.get(candidate.cordis_dependency_id);
  if (!cordis || cordis.kind !== 'npm_package' || cordis.package_name !== 'cordis') {
    throw new Error('runtime package must name its exact Cordis npm dependency');
  }
  for (const dependencyId of [
    candidate.profile.module_dependency_id,
    candidate.profile.bundle_dependency_id,
  ]) {
    if (dependencies.get(dependencyId)?.kind !== 'repository_artifact') {
      throw new Error(`runtime package profile dependency is not a repository artifact: ${dependencyId}`);
    }
  }
  return deepFreeze(sortKeys(cloneJson(candidate)));
}

export function defineConfigurationOverlay(candidate) {
  assertExactKeys(
    candidate,
    [
      'schema_version',
      'overlay_id',
      'overlay_version',
      'target_profile',
      'precedence',
      'configuration_patch',
    ],
    'configuration overlay',
  );
  if (candidate.schema_version !== OVERLAY_SCHEMA_VERSION) {
    throw new Error('configuration overlay schema version is unsupported');
  }
  assertAscii(candidate.overlay_id, 'configuration overlay.overlay_id');
  assertSemver(candidate.overlay_version, 'configuration overlay.overlay_version');
  assertExactKeys(
    candidate.target_profile,
    ['profile_id', 'profile_version'],
    'configuration overlay.target_profile',
  );
  assertAscii(candidate.target_profile.profile_id, 'configuration overlay target profile id');
  assertSemver(
    candidate.target_profile.profile_version,
    'configuration overlay target profile version',
  );
  if (!Number.isSafeInteger(candidate.precedence) || candidate.precedence < 0) {
    throw new Error('configuration overlay.precedence must be a non-negative safe integer');
  }
  assertObject(candidate.configuration_patch, 'configuration overlay.configuration_patch');
  const entries = Object.entries(candidate.configuration_patch);
  if (entries.length === 0) throw new Error('configuration overlay patch must not be empty');
  for (const [key, value] of entries) {
    assertAscii(key, 'configuration overlay patch key');
    if (!['boolean', 'number', 'string'].includes(typeof value) ||
        (typeof value === 'number' && !Number.isFinite(value)) ||
        (Number.isInteger(value) && !Number.isSafeInteger(value))) {
      throw new Error(`configuration overlay patch value is unsupported: ${key}`);
    }
  }
  return deepFreeze(sortKeys(cloneJson(candidate)));
}

export function applyConfigurationOverlays(profile, overlays) {
  assertObject(profile, 'profile');
  if (!Array.isArray(overlays)) throw new TypeError('overlays must be an array');
  const admitted = overlays
    .map(defineConfigurationOverlay)
    .sort((left, right) => left.precedence - right.precedence ||
      utf8Compare(left.overlay_id, right.overlay_id));
  const effective = cloneJson(profile);
  assertObject(effective.configuration, 'profile.configuration');
  const writes = new Map();
  for (const overlay of admitted) {
    if (overlay.target_profile.profile_id !== profile.profile_id ||
        overlay.target_profile.profile_version !== profile.profile_version) {
      throw new Error(`configuration overlay targets another profile: ${overlay.overlay_id}`);
    }
    for (const [key, value] of Object.entries(overlay.configuration_patch)) {
      if (!Object.hasOwn(effective.configuration, key)) {
        throw new Error(`configuration overlay introduces an unowned key: ${key}`);
      }
      const previous = writes.get(key);
      if (previous?.precedence === overlay.precedence) {
        throw new Error(`configuration overlay precedence conflict for key: ${key}`);
      }
      if (typeof effective.configuration[key] !== typeof value ||
          (Number.isInteger(effective.configuration[key]) && !Number.isSafeInteger(value))) {
        throw new Error(`configuration overlay changes the type of key: ${key}`);
      }
      effective.configuration[key] = value;
      writes.set(key, { overlay_id: overlay.overlay_id, precedence: overlay.precedence });
    }
  }
  return deepFreeze(sortKeys(effective));
}

function dependencyGraph(runtimePackage) {
  const nodes = [
    ...runtimePackage.dependencies.map((dependency) => ({
      node_id: dependency.dependency_id,
      kind: dependency.kind,
      requires: [...dependency.requires].sort(utf8Compare),
      ...(dependency.kind === 'npm_package'
        ? { package_name: dependency.package_name, version: dependency.version }
        : { path: dependency.path, sha256: dependency.sha256 }),
    })),
    ...runtimePackage.overlays.map((overlay) => ({
      node_id: overlay.overlay_id,
      kind: 'configuration_overlay',
      path: overlay.path,
      sha256: overlay.sha256,
      requires: [...overlay.requires].sort(utf8Compare),
    })),
  ].sort((left, right) => utf8Compare(left.node_id, right.node_id));
  const byId = new Map(nodes.map((node) => [node.node_id, node]));
  const indegree = new Map(nodes.map((node) => [node.node_id, node.requires.length]));
  const dependents = new Map(nodes.map((node) => [node.node_id, []]));
  for (const node of nodes) {
    for (const required of node.requires) {
      if (!byId.has(required)) {
        throw new Error(`runtime package dependency is missing: ${node.node_id} requires ${required}`);
      }
      dependents.get(required).push(node.node_id);
    }
  }
  for (const values of dependents.values()) values.sort(utf8Compare);
  const ready = nodes.filter((node) => indegree.get(node.node_id) === 0)
    .map((node) => node.node_id)
    .sort(utf8Compare);
  const order = [];
  while (ready.length > 0) {
    const current = ready.shift();
    order.push(current);
    for (const dependent of dependents.get(current)) {
      const next = indegree.get(dependent) - 1;
      indegree.set(dependent, next);
      if (next === 0) {
        ready.push(dependent);
        ready.sort(utf8Compare);
      }
    }
  }
  if (order.length !== nodes.length) {
    const cycle = nodes.filter((node) => indegree.get(node.node_id) > 0)
      .map((node) => node.node_id)
      .sort(utf8Compare);
    throw new Error(`runtime package dependency cycle: ${cycle.join(', ')}`);
  }
  const payload = sortKeys({ nodes });
  return deepFreeze({
    nodes: deepFreeze(nodes),
    order: deepFreeze(order),
    graph_sha256: sha256Hex(payload),
  });
}

function verifyPackageLock(packageLockBytes, cordisVersion) {
  const lock = parseJsonBytes(packageLockBytes, 'package-lock');
  if (lock.name !== PRODUCER_PACKAGE_NAME ||
      lock.version !== PRODUCER_PACKAGE_VERSION ||
      lock.packages?.['']?.name !== PRODUCER_PACKAGE_NAME ||
      lock.packages?.['']?.version !== PRODUCER_PACKAGE_VERSION ||
      lock.packages?.['']?.dependencies?.cordis !== cordisVersion ||
      lock.packages?.['node_modules/cordis']?.version !== cordisVersion) {
    throw new Error('package-lock does not pin the admitted producer and Cordis versions');
  }
}

export function resolveRuntimePackage({
  descriptor,
  descriptorBytes,
  profile = DEFAULT_PROFILE,
  profileModuleBytes,
  profileBundle,
  profileBundleBytes,
  overlays,
  cordisVersion,
  packageLockBytes,
}) {
  const runtimePackage = defineRuntimePackage(descriptor);
  assertJsonBytesMatch(descriptorBytes, runtimePackage, 'runtime package descriptor');
  assertSemver(cordisVersion, 'installed Cordis version');
  verifyPackageLock(packageLockBytes, cordisVersion);
  const graph = dependencyGraph(runtimePackage);
  const dependencies = new Map(
    runtimePackage.dependencies.map((dependency) => [dependency.dependency_id, dependency]),
  );
  const cordis = dependencies.get(runtimePackage.cordis_dependency_id);
  if (cordis.version !== cordisVersion) {
    throw new Error(`installed Cordis version is not admitted: ${cordisVersion}`);
  }

  const moduleDependency = dependencies.get(runtimePackage.profile.module_dependency_id);
  const moduleBytes = asBuffer(profileModuleBytes, 'profile module');
  if (sha256Bytes(moduleBytes) !== moduleDependency.sha256) {
    throw new Error('profile module hash mismatch');
  }
  const bundleDependency = dependencies.get(runtimePackage.profile.bundle_dependency_id);
  const bundleBytes = asBuffer(profileBundleBytes, 'profile bundle');
  assertJsonBytesMatch(bundleBytes, profileBundle, 'profile bundle');
  if (sha256Bytes(bundleBytes) !== bundleDependency.sha256) {
    throw new Error('profile bundle hash mismatch');
  }
  if (profile.profile_id !== runtimePackage.profile.profile_id ||
      profile.profile_version !== runtimePackage.profile.profile_version ||
      profileBundle.profile_id !== runtimePackage.profile.profile_id ||
      profileBundle.profile_version !== runtimePackage.profile.profile_version) {
    throw new Error('runtime package profile identity mismatch');
  }
  lowerDefaultProfile(profile);

  if (!Array.isArray(overlays)) throw new TypeError('resolved overlays must be an array');
  const supplied = new Map();
  for (const item of overlays) {
    assertExactKeys(item, ['overlay', 'bytes'], 'resolved overlay item');
    const overlay = defineConfigurationOverlay(item.overlay);
    if (supplied.has(overlay.overlay_id)) {
      throw new Error(`resolved overlay is duplicated: ${overlay.overlay_id}`);
    }
    supplied.set(overlay.overlay_id, { overlay, bytes: asBuffer(item.bytes, 'overlay bytes') });
  }
  const resolvedOverlays = runtimePackage.overlays.map((reference) => {
    const item = supplied.get(reference.overlay_id);
    if (!item) throw new Error(`required configuration overlay is missing: ${reference.overlay_id}`);
    assertJsonBytesMatch(item.bytes, item.overlay, `configuration overlay ${reference.overlay_id}`);
    const actualSha256 = sha256Bytes(item.bytes);
    if (actualSha256 !== reference.sha256) {
      throw new Error(`configuration overlay hash mismatch: ${reference.overlay_id}`);
    }
    if (item.overlay.overlay_id !== reference.overlay_id) {
      throw new Error(`configuration overlay identity mismatch: ${reference.overlay_id}`);
    }
    return deepFreeze({
      overlay: item.overlay,
      sha256: actualSha256,
      path: reference.path,
    });
  });
  if (supplied.size !== resolvedOverlays.length) {
    throw new Error('runtime package received an undeclared configuration overlay');
  }
  const effectiveProfile = applyConfigurationOverlays(
    profile,
    resolvedOverlays.map(({ overlay }) => overlay),
  );
  lowerDefaultProfile(effectiveProfile);

  return deepFreeze(sortKeys({
    schema_version: RESOLVED_PACKAGE_SCHEMA_VERSION,
    descriptor: runtimePackage,
    descriptor_sha256: sha256Bytes(asBuffer(descriptorBytes, 'runtime package descriptor')),
    profile_module_sha256: sha256Bytes(moduleBytes),
    profile_bundle: cloneJson(profileBundle),
    profile_bundle_sha256: sha256Bytes(bundleBytes),
    effective_profile: cloneJson(effectiveProfile),
    dependency_graph: cloneJson(graph),
    configuration_overlays: resolvedOverlays.map(({ overlay, sha256 }) => ({
      overlay_id: overlay.overlay_id,
      overlay_version: overlay.overlay_version,
      precedence: overlay.precedence,
      sha256,
    })),
    cordis_version: cordisVersion,
    producer_package_version: PRODUCER_PACKAGE_VERSION,
    package_lock_sha256: sha256Bytes(asBuffer(packageLockBytes, 'package-lock')),
  }));
}

function assertResolvedPackage(resolvedPackage) {
  assertObject(resolvedPackage, 'resolved runtime package');
  if (resolvedPackage.schema_version !== RESOLVED_PACKAGE_SCHEMA_VERSION) {
    throw new Error('resolved runtime package schema version is unsupported');
  }
  assertSha256(resolvedPackage.descriptor_sha256, 'resolved package descriptor hash');
  assertSha256(resolvedPackage.dependency_graph?.graph_sha256, 'resolved dependency graph hash');
  if (resolvedPackage.producer_package_version !== PRODUCER_PACKAGE_VERSION) {
    throw new Error('resolved runtime package producer version is unsupported');
  }
}

function assertSealedIdentity(value, identityKey, label) {
  assertObject(value, label);
  assertSha256(value[identityKey], `${label}.${identityKey}`);
  if (typeof value.canonical_json !== 'string') {
    throw new Error(`${label} has no canonical payload`);
  }
  const payload = Object.fromEntries(
    Object.entries(value)
      .filter(([key]) => key !== 'canonical_json' && key !== identityKey),
  );
  if (canonicalJson(payload) !== value.canonical_json ||
      sha256Hex(payload) !== value[identityKey]) {
    throw new Error(`${label} sealed identity is invalid`);
  }
}

function assertRuntimePackageProvenanceShape(provenance) {
  assertExactKeys(
    provenance,
    [
      'schema_version',
      'package',
      'profile',
      'dependency_resolution',
      'configuration_overlays',
      'producer',
      'runtime_artifacts',
      'canonicalization',
      'hash_algorithm',
      'canonical_json',
      'provenance_sha256',
    ],
    'runtime package provenance',
  );
  if (provenance.schema_version !== PROVENANCE_SCHEMA_VERSION ||
      provenance.canonicalization !== 'echelon_forge.sorted_utf8_json.v1' ||
      provenance.hash_algorithm !== 'sha256') {
    throw new Error('runtime package provenance contract is unsupported');
  }
  assertExactKeys(
    provenance.package,
    ['package_id', 'package_version', 'descriptor_sha256'],
    'runtime package provenance.package',
  );
  assertAscii(provenance.package.package_id, 'runtime package provenance package id');
  assertSemver(provenance.package.package_version, 'runtime package provenance package version');
  assertSha256(provenance.package.descriptor_sha256, 'runtime package provenance descriptor hash');
  assertExactKeys(
    provenance.profile,
    ['profile_id', 'profile_version', 'module_sha256', 'bundle_sha256'],
    'runtime package provenance.profile',
  );
  assertAscii(provenance.profile.profile_id, 'runtime package provenance profile id');
  assertSemver(provenance.profile.profile_version, 'runtime package provenance profile version');
  assertSha256(provenance.profile.module_sha256, 'runtime package provenance profile module hash');
  assertSha256(provenance.profile.bundle_sha256, 'runtime package provenance profile bundle hash');
  assertExactKeys(
    provenance.dependency_resolution,
    ['order', 'graph_sha256'],
    'runtime package provenance.dependency_resolution',
  );
  assertUniqueAscii(
    provenance.dependency_resolution.order,
    'runtime package provenance dependency order',
  );
  assertSha256(
    provenance.dependency_resolution.graph_sha256,
    'runtime package provenance dependency graph hash',
  );
  if (!Array.isArray(provenance.configuration_overlays)) {
    throw new TypeError('runtime package provenance configuration overlays must be an array');
  }
  provenance.configuration_overlays.forEach((overlay, index) => {
    const label = `runtime package provenance.configuration_overlays[${index}]`;
    assertExactKeys(
      overlay,
      ['overlay_id', 'overlay_version', 'precedence', 'sha256'],
      label,
    );
    assertAscii(overlay.overlay_id, `${label}.overlay_id`);
    assertSemver(overlay.overlay_version, `${label}.overlay_version`);
    if (!Number.isSafeInteger(overlay.precedence) || overlay.precedence < 0) {
      throw new Error(`${label}.precedence must be a non-negative safe integer`);
    }
    assertSha256(overlay.sha256, `${label}.sha256`);
  });
  assertExactKeys(
    provenance.producer,
    ['package_name', 'package_version', 'cordis_version', 'package_lock_sha256'],
    'runtime package provenance.producer',
  );
  if (provenance.producer.package_name !== PRODUCER_PACKAGE_NAME) {
    throw new Error('runtime package provenance producer is unsupported');
  }
  assertSemver(provenance.producer.package_version, 'runtime package provenance producer version');
  assertSemver(provenance.producer.cordis_version, 'runtime package provenance Cordis version');
  assertSha256(
    provenance.producer.package_lock_sha256,
    'runtime package provenance package-lock hash',
  );
  assertExactKeys(
    provenance.runtime_artifacts,
    ['request_sha256', 'lock_sha256', 'profile_projection_sha256'],
    'runtime package provenance.runtime_artifacts',
  );
  for (const [key, value] of Object.entries(provenance.runtime_artifacts)) {
    assertSha256(value, `runtime package provenance.runtime_artifacts.${key}`);
  }
}

function assertRuntimeArtifactBindings(
  provenance,
  { request, catalogLock, profileProjection },
) {
  assertObject(request, 'runtime package diagnostics request');
  assertSealedIdentity(catalogLock, 'lock_sha256', 'catalog lock');
  assertSealedIdentity(profileProjection, 'projection_sha256', 'profile projection');
  const requestSha256 = sha256Hex(request);
  const actual = {
    request_sha256: requestSha256,
    lock_sha256: catalogLock.lock_sha256,
    profile_projection_sha256: profileProjection.projection_sha256,
  };
  if (canonicalJson(provenance.runtime_artifacts) !== canonicalJson(actual) ||
      catalogLock.request_sha256 !== requestSha256 ||
      profileProjection.request_sha256 !== requestSha256 ||
      profileProjection.lock_sha256 !== catalogLock.lock_sha256) {
    throw new Error('runtime package diagnostics provenance does not match runtime artifacts');
  }
}

export async function produceRuntimePackageRequest(resolvedPackage, catalogLock) {
  assertResolvedPackage(resolvedPackage);
  const request = await produceDefaultRequest(resolvedPackage.effective_profile, catalogLock);
  const requestSha256 = sha256Hex(request);
  if (requestSha256 !== catalogLock?.request_sha256) {
    throw new Error(`Cordis package request does not match the admitted catalog lock: ${requestSha256}`);
  }
  return request;
}

export function buildRuntimePackageProvenance(
  resolvedPackage,
  { request, catalogLock, profileProjection },
) {
  assertResolvedPackage(resolvedPackage);
  const requestSha256 = sha256Hex(request);
  if (requestSha256 !== catalogLock?.request_sha256 ||
      requestSha256 !== profileProjection?.request_sha256 ||
      catalogLock?.lock_sha256 !== profileProjection?.lock_sha256) {
    throw new Error('runtime package provenance artifacts are not identity-bound');
  }
  assertSealedIdentity(catalogLock, 'lock_sha256', 'catalog lock');
  assertSealedIdentity(profileProjection, 'projection_sha256', 'profile projection');
  const descriptor = resolvedPackage.descriptor;
  const payload = sortKeys({
    schema_version: PROVENANCE_SCHEMA_VERSION,
    package: {
      package_id: descriptor.package_id,
      package_version: descriptor.package_version,
      descriptor_sha256: resolvedPackage.descriptor_sha256,
    },
    profile: {
      profile_id: descriptor.profile.profile_id,
      profile_version: descriptor.profile.profile_version,
      module_sha256: resolvedPackage.profile_module_sha256,
      bundle_sha256: resolvedPackage.profile_bundle_sha256,
    },
    dependency_resolution: {
      order: [...resolvedPackage.dependency_graph.order],
      graph_sha256: resolvedPackage.dependency_graph.graph_sha256,
    },
    configuration_overlays: cloneJson(resolvedPackage.configuration_overlays),
    producer: {
      package_name: PRODUCER_PACKAGE_NAME,
      package_version: resolvedPackage.producer_package_version,
      cordis_version: resolvedPackage.cordis_version,
      package_lock_sha256: resolvedPackage.package_lock_sha256,
    },
    runtime_artifacts: {
      request_sha256: requestSha256,
      lock_sha256: catalogLock.lock_sha256,
      profile_projection_sha256: profileProjection.projection_sha256,
    },
    canonicalization: 'echelon_forge.sorted_utf8_json.v1',
    hash_algorithm: 'sha256',
  });
  return deepFreeze(sortKeys({
    ...payload,
    canonical_json: canonicalJson(payload),
    provenance_sha256: sha256Hex(payload),
  }));
}

export function buildRuntimePackageDiagnostics(resolvedPackage, provenance, runtimeArtifacts) {
  assertResolvedPackage(resolvedPackage);
  assertRuntimePackageProvenanceShape(provenance);
  if (provenance.package.descriptor_sha256 !== resolvedPackage.descriptor_sha256) {
    throw new Error('runtime package diagnostics require matching sealed provenance');
  }
  assertSealedIdentity(provenance, 'provenance_sha256', 'runtime package provenance');
  assertRuntimeArtifactBindings(provenance, runtimeArtifacts);
  const descriptor = resolvedPackage.descriptor;
  if (provenance.package.package_id !== descriptor.package_id ||
      provenance.package.package_version !== descriptor.package_version ||
      provenance.profile?.profile_id !== descriptor.profile.profile_id ||
      provenance.profile?.profile_version !== descriptor.profile.profile_version ||
      provenance.profile?.module_sha256 !== resolvedPackage.profile_module_sha256 ||
      provenance.profile?.bundle_sha256 !== resolvedPackage.profile_bundle_sha256 ||
      provenance.dependency_resolution?.graph_sha256 !==
        resolvedPackage.dependency_graph.graph_sha256 ||
      canonicalJson(provenance.dependency_resolution?.order) !==
        canonicalJson(resolvedPackage.dependency_graph.order) ||
      canonicalJson(provenance.configuration_overlays) !==
        canonicalJson(resolvedPackage.configuration_overlays) ||
      provenance.producer?.package_name !== PRODUCER_PACKAGE_NAME ||
      provenance.producer?.package_version !== resolvedPackage.producer_package_version ||
      provenance.producer?.cordis_version !== resolvedPackage.cordis_version ||
      provenance.producer?.package_lock_sha256 !== resolvedPackage.package_lock_sha256) {
    throw new Error('runtime package diagnostics provenance does not match package resolution');
  }
  const events = [
    {
      code: 'package.descriptor.validated',
      severity: 'info',
      subject_id: resolvedPackage.descriptor.package_id,
    },
    {
      code: 'dependency.graph.resolved',
      severity: 'info',
      subject_id: resolvedPackage.dependency_graph.graph_sha256,
    },
    ...resolvedPackage.configuration_overlays.map((overlay) => ({
      code: 'configuration.overlay.applied',
      severity: 'info',
      subject_id: overlay.overlay_id,
    })),
    {
      code: 'runtime.request_lock.bound',
      severity: 'info',
      subject_id: provenance.runtime_artifacts.lock_sha256,
    },
    {
      code: 'runtime.profile_projection.bound',
      severity: 'info',
      subject_id: provenance.runtime_artifacts.profile_projection_sha256,
    },
    {
      code: 'package.provenance.sealed',
      severity: 'info',
      subject_id: provenance.provenance_sha256,
    },
  ];
  return deepFreeze(sortKeys({
    schema_version: DIAGNOSTICS_SCHEMA_VERSION,
    status: 'ready_for_native_validation',
    package_id: resolvedPackage.descriptor.package_id,
    package_version: resolvedPackage.descriptor.package_version,
    events,
    summary: {
      dependency_count: resolvedPackage.dependency_graph.order.length,
      overlay_count: resolvedPackage.configuration_overlays.length,
      request_lock_binding: 'validated',
      provenance_sha256: provenance.provenance_sha256,
    },
  }));
}
