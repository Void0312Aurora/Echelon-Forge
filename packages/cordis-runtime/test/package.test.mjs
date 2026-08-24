import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { DEFAULT_PROFILE } from '../profiles/default-compatibility.mjs';
import {
  buildRuntimePackageDiagnostics,
  buildRuntimePackageProvenance,
  canonicalJson,
  defineConfigurationOverlay,
  defineRuntimePackage,
  produceRuntimePackageRequest,
  resolveRuntimePackage,
  sha256Bytes,
  sha256Hex,
} from '../src/index.mjs';

const PACKAGE_ROOT = new URL('../', import.meta.url);
const FIXTURES = new URL('../../../tests/architecture/composition/fixtures/', import.meta.url);

function bytes(path) {
  return readFileSync(new URL(path, PACKAGE_ROOT));
}

function json(path) {
  return JSON.parse(bytes(path).toString('utf8'));
}

function fixture(name) {
  return JSON.parse(readFileSync(new URL(name, FIXTURES), 'utf8'));
}

function jsonBytes(value) {
  return Buffer.from(`${JSON.stringify(value, null, 2)}\n`, 'utf8');
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function inputs() {
  const descriptor = json('packages/default-compatibility.package.json');
  const overlay = json('overlays/default-compatibility.default.v1.json');
  return {
    descriptor,
    descriptorBytes: bytes('packages/default-compatibility.package.json'),
    profile: DEFAULT_PROFILE,
    profileModuleBytes: bytes('profiles/default-compatibility.mjs'),
    profileBundle: json('profiles/default-compatibility.bundle.json'),
    profileBundleBytes: bytes('profiles/default-compatibility.bundle.json'),
    overlays: [{ overlay, bytes: bytes('overlays/default-compatibility.default.v1.json') }],
    cordisVersion: '4.0.0-rc.8',
    packageLockBytes: bytes('package-lock.json'),
  };
}

function resolved() {
  return resolveRuntimePackage(inputs());
}

test('Cordis runtime package resolves the repository-owned dependency graph deterministically', () => {
  const first = resolved();
  const second = resolved();
  assert.deepEqual(first, second);
  assert.equal(first.descriptor.package_id, 'builtin.default_compatibility.package');
  assert.deepEqual(first.dependency_graph.order, [
    'cordis.runtime',
    'profile.module',
    'profile.bundle',
    'builtin.default_compatibility.overlay.default',
  ]);
  assert.deepEqual(first.effective_profile, DEFAULT_PROFILE);
  assert.deepEqual(first.configuration_overlays, [{
    overlay_id: 'builtin.default_compatibility.overlay.default',
    overlay_version: '1.0.0',
    precedence: 0,
    sha256: '2ab04cf6d5f2e377e343949641058fe05fd9f3024891aa3892a1eb43ff00603e',
  }]);
  assert.equal(first.profile_bundle_sha256, sha256Bytes(inputs().profileBundleBytes));
  assert(Object.isFrozen(first));
});

test('Cordis runtime package rejects missing dependencies and dependency cycles', () => {
  const missing = inputs();
  missing.descriptor = clone(missing.descriptor);
  missing.descriptor.dependencies[2].requires = ['missing.dependency'];
  missing.descriptorBytes = jsonBytes(missing.descriptor);
  assert.throws(() => resolveRuntimePackage(missing), /dependency is missing/);

  const cycle = inputs();
  cycle.descriptor = clone(cycle.descriptor);
  cycle.descriptor.dependencies[0].requires = ['profile.bundle'];
  cycle.descriptorBytes = jsonBytes(cycle.descriptor);
  assert.throws(() => resolveRuntimePackage(cycle), /dependency cycle/);

  const duplicate = inputs();
  duplicate.descriptor = clone(duplicate.descriptor);
  duplicate.descriptor.overlays[0].overlay_id = 'profile.bundle';
  duplicate.descriptorBytes = jsonBytes(duplicate.descriptor);
  assert.throws(() => resolveRuntimePackage(duplicate), /contains a duplicate/);
});

test('Cordis runtime package dependency identity is discovery-order stable', () => {
  const original = resolved();
  const permuted = inputs();
  permuted.descriptor = clone(permuted.descriptor);
  permuted.descriptor.dependencies.reverse();
  permuted.descriptor.overlays.reverse();
  permuted.descriptorBytes = jsonBytes(permuted.descriptor);
  const reordered = resolveRuntimePackage(permuted);
  assert.deepEqual(reordered.dependency_graph.order, original.dependency_graph.order);
  assert.equal(reordered.dependency_graph.graph_sha256, original.dependency_graph.graph_sha256);
});

test('Cordis runtime package rejects unpinned artifacts, Cordis versions, and lockfiles', () => {
  const bundle = inputs();
  bundle.profileBundleBytes = Buffer.concat([bundle.profileBundleBytes, Buffer.from('\n')]);
  assert.throws(() => resolveRuntimePackage(bundle), /profile bundle hash mismatch/);

  const module = inputs();
  module.profileModuleBytes = Buffer.concat([module.profileModuleBytes, Buffer.from('\n')]);
  assert.throws(() => resolveRuntimePackage(module), /profile module hash mismatch/);

  const cordis = inputs();
  cordis.cordisVersion = '4.0.0-rc.7';
  assert.throws(() => resolveRuntimePackage(cordis), /package-lock does not pin/);

  const lock = inputs();
  const parsedLock = JSON.parse(lock.packageLockBytes.toString('utf8'));
  parsedLock.packages['node_modules/cordis'].version = '4.0.0-rc.7';
  lock.packageLockBytes = jsonBytes(parsedLock);
  assert.throws(() => resolveRuntimePackage(lock), /package-lock does not pin/);

  const producer = inputs();
  const producerLock = JSON.parse(producer.packageLockBytes.toString('utf8'));
  producerLock.version = '9.9.9';
  producerLock.packages[''].version = '9.9.9';
  producer.packageLockBytes = jsonBytes(producerLock);
  assert.throws(() => resolveRuntimePackage(producer), /package-lock does not pin/);

  const invalidUtf8 = inputs();
  invalidUtf8.descriptorBytes = Buffer.from([0xff]);
  assert.throws(() => resolveRuntimePackage(invalidUtf8), /not valid UTF-8 JSON/);
});

test('Cordis runtime package rejects unsafe paths and non-ASCII identities', () => {
  const traversal = inputs();
  traversal.descriptor = clone(traversal.descriptor);
  traversal.descriptor.dependencies[1].path = '../outside.mjs';
  traversal.descriptorBytes = jsonBytes(traversal.descriptor);
  assert.throws(() => resolveRuntimePackage(traversal), /must remain relative/);

  const nonAscii = inputs();
  nonAscii.descriptor = clone(nonAscii.descriptor);
  nonAscii.descriptor.package_id = 'builtin.默认.package';
  nonAscii.descriptorBytes = jsonBytes(nonAscii.descriptor);
  assert.throws(() => resolveRuntimePackage(nonAscii), /ASCII string/);
});

test('Cordis runtime package overlays cannot change admitted truth or introduce keys', () => {
  const changed = inputs();
  changed.descriptor = clone(changed.descriptor);
  const changedOverlay = clone(changed.overlays[0].overlay);
  changedOverlay.configuration_patch.seed = 999;
  const changedBytes = jsonBytes(changedOverlay);
  changed.descriptor.overlays[0].sha256 = sha256Bytes(changedBytes);
  changed.descriptorBytes = jsonBytes(changed.descriptor);
  changed.overlays = [{ overlay: changedOverlay, bytes: changedBytes }];
  assert.throws(() => resolveRuntimePackage(changed), /unsupported profile bundle contents/);

  const introduced = clone(changedOverlay);
  introduced.configuration_patch = { attacker_key: 1 };
  const introducedBytes = jsonBytes(introduced);
  changed.descriptor.overlays[0].sha256 = sha256Bytes(introducedBytes);
  changed.descriptorBytes = jsonBytes(changed.descriptor);
  changed.overlays = [{ overlay: introduced, bytes: introducedBytes }];
  assert.throws(() => resolveRuntimePackage(changed), /introduces an unowned key/);
});

test('Cordis runtime package rejects undeclared and same-precedence overlay conflicts', () => {
  const conflict = inputs();
  conflict.descriptor = clone(conflict.descriptor);
  const secondOverlay = clone(conflict.overlays[0].overlay);
  secondOverlay.overlay_id = 'builtin.default_compatibility.overlay.conflict';
  const secondBytes = jsonBytes(secondOverlay);
  conflict.descriptor.overlays.push({
    overlay_id: secondOverlay.overlay_id,
    path: 'overlays/conflict.v1.json',
    sha256: sha256Bytes(secondBytes),
    required: true,
    requires: ['profile.bundle'],
  });
  conflict.descriptorBytes = jsonBytes(conflict.descriptor);
  conflict.overlays.push({ overlay: secondOverlay, bytes: secondBytes });
  assert.throws(() => resolveRuntimePackage(conflict), /precedence conflict/);

  const undeclared = inputs();
  const attacker = clone(undeclared.overlays[0].overlay);
  attacker.overlay_id = 'attacker.overlay';
  undeclared.overlays.push({ overlay: attacker, bytes: jsonBytes(attacker) });
  assert.throws(() => resolveRuntimePackage(undeclared), /undeclared configuration overlay/);
});

test('Cordis runtime package descriptor and overlay definitions are immutable SDK values', () => {
  const runtimePackage = defineRuntimePackage(inputs().descriptor);
  const overlay = defineConfigurationOverlay(inputs().overlays[0].overlay);
  assert(Object.isFrozen(runtimePackage));
  assert(Object.isFrozen(runtimePackage.profile));
  assert(Object.isFrozen(overlay));
  assert(Object.isFrozen(overlay.configuration_patch));
  assert.throws(() => { runtimePackage.profile.profile_id = 'attacker.profile'; }, TypeError);
  assert.throws(() => { overlay.configuration_patch.seed = 999; }, TypeError);
});

test('Cordis runtime package public export exposes the supported SDK', async () => {
  const sdk = await import('@echelon-forge/cordis-runtime');
  for (const name of [
    'defineRuntimePackage',
    'defineConfigurationOverlay',
    'resolveRuntimePackage',
    'produceRuntimePackageRequest',
    'buildRuntimePackageProvenance',
    'buildRuntimePackageDiagnostics',
  ]) {
    assert.equal(typeof sdk[name], 'function', `${name} must be a public SDK function`);
  }
});

test('Cordis runtime package emits stable sealed provenance and path-free diagnostics', async () => {
  const packageResolution = resolved();
  const lock = fixture('default_admitted_catalog_lock.v1.json');
  const request = await produceRuntimePackageRequest(packageResolution, lock);
  const profileProjection = fixture('default_runtime_profile_projection.v1.json');
  const provenance = buildRuntimePackageProvenance(packageResolution, {
    request,
    catalogLock: lock,
    profileProjection,
  });
  const runtimeArtifacts = { request, catalogLock: lock, profileProjection };
  const repeated = buildRuntimePackageProvenance(packageResolution, {
    request,
    catalogLock: lock,
    profileProjection,
  });
  assert.deepEqual(provenance, repeated);
  assert.equal(provenance.runtime_artifacts.request_sha256, lock.request_sha256);
  assert.equal(provenance.runtime_artifacts.lock_sha256, lock.lock_sha256);
  assert.equal(provenance.configuration_overlays.length, 1);

  const diagnostics = buildRuntimePackageDiagnostics(
    packageResolution,
    provenance,
    runtimeArtifacts,
  );
  assert.equal(diagnostics.status, 'ready_for_native_validation');
  assert.equal(diagnostics.summary.request_lock_binding, 'validated');
  assert.equal(diagnostics.summary.provenance_sha256, provenance.provenance_sha256);
  assert(!/[A-Za-z]:\\|\/(?:home|Users|tmp)\//.test(JSON.stringify(diagnostics)));

  const identityTamper = clone(provenance);
  identityTamper.runtime_artifacts.lock_sha256 = '0'.repeat(64);
  assert.throws(
    () => buildRuntimePackageDiagnostics(packageResolution, identityTamper, runtimeArtifacts),
    /sealed identity is invalid/,
  );

  const resolutionTamper = clone(provenance);
  resolutionTamper.dependency_resolution.graph_sha256 = '0'.repeat(64);
  const payload = Object.fromEntries(
    Object.entries(resolutionTamper)
      .filter(([key]) => key !== 'canonical_json' && key !== 'provenance_sha256'),
  );
  resolutionTamper.canonical_json = canonicalJson(payload);
  resolutionTamper.provenance_sha256 = sha256Hex(payload);
  assert.throws(
    () => buildRuntimePackageDiagnostics(packageResolution, resolutionTamper, runtimeArtifacts),
    /does not match package resolution/,
  );

  const artifactTamper = clone(provenance);
  artifactTamper.runtime_artifacts = {
    request_sha256: '0'.repeat(64),
    lock_sha256: '1'.repeat(64),
    profile_projection_sha256: '2'.repeat(64),
  };
  const artifactPayload = Object.fromEntries(
    Object.entries(artifactTamper)
      .filter(([key]) => key !== 'canonical_json' && key !== 'provenance_sha256'),
  );
  artifactTamper.canonical_json = canonicalJson(artifactPayload);
  artifactTamper.provenance_sha256 = sha256Hex(artifactPayload);
  assert.throws(
    () => buildRuntimePackageDiagnostics(packageResolution, artifactTamper, runtimeArtifacts),
    /does not match runtime artifacts/,
  );

  const extraField = clone(provenance);
  extraField.attacker_claim = true;
  const extraPayload = Object.fromEntries(
    Object.entries(extraField)
      .filter(([key]) => key !== 'canonical_json' && key !== 'provenance_sha256'),
  );
  extraField.canonical_json = canonicalJson(extraPayload);
  extraField.provenance_sha256 = sha256Hex(extraPayload);
  assert.throws(
    () => buildRuntimePackageDiagnostics(packageResolution, extraField, runtimeArtifacts),
    /unsupported fields/,
  );

  const producerVersionTamper = clone(provenance);
  producerVersionTamper.producer.package_version = '9.9.9';
  const producerPayload = Object.fromEntries(
    Object.entries(producerVersionTamper)
      .filter(([key]) => key !== 'canonical_json' && key !== 'provenance_sha256'),
  );
  producerVersionTamper.canonical_json = canonicalJson(producerPayload);
  producerVersionTamper.provenance_sha256 = sha256Hex(producerPayload);
  assert.throws(
    () => buildRuntimePackageDiagnostics(
      packageResolution,
      producerVersionTamper,
      runtimeArtifacts,
    ),
    /does not match package resolution/,
  );
});

test('Cordis runtime package provenance rejects unbound artifacts', async () => {
  const packageResolution = resolved();
  const lock = fixture('default_admitted_catalog_lock.v1.json');
  const request = await produceRuntimePackageRequest(packageResolution, lock);
  const projection = fixture('default_runtime_profile_projection.v1.json');
  projection.request_sha256 = '0'.repeat(64);
  assert.throws(
    () => buildRuntimePackageProvenance(packageResolution, {
      request,
      catalogLock: lock,
      profileProjection: projection,
    }),
    /not identity-bound/,
  );

  const tamperedLock = clone(lock);
  tamperedLock.lock_version = '2.0.0';
  assert.throws(
    () => buildRuntimePackageProvenance(packageResolution, {
      request,
      catalogLock: tamperedLock,
      profileProjection: fixture('default_runtime_profile_projection.v1.json'),
    }),
    /sealed identity is invalid/,
  );
});
