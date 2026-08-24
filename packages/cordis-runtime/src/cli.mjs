import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { dirname, isAbsolute, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { DEFAULT_PROFILE } from '../profiles/default-compatibility.mjs';
import {
  buildRuntimePackageDiagnostics,
  buildRuntimePackageProvenance,
  defineRuntimePackage,
  lowerDefaultManifest,
  lowerDefaultProfileProjection,
  PRODUCER_PACKAGE_NAME,
  PRODUCER_PACKAGE_VERSION,
  produceRuntimePackageRequest,
  resolveRuntimePackage,
  sha256Bytes,
  sha256Hex,
} from './index.mjs';

const PACKAGE_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const REPO_ROOT = resolve(PACKAGE_ROOT, '..', '..');

function argument(name) {
  const index = process.argv.indexOf(name);
  return index < 0 ? undefined : process.argv[index + 1];
}

function resolveWithin(root, relativePath, label) {
  const candidate = resolve(root, relativePath);
  const relation = relative(root, candidate);
  if (relation === '' || relation.startsWith('..') || isAbsolute(relation)) {
    throw new Error(`${label} escapes its repository root`);
  }
  return candidate;
}

async function main() {
  if (process.argv[2] !== 'produce') {
    throw new Error('usage: node src/cli.mjs produce --out <directory>');
  }
  const output = resolve(argument('--out') ?? resolve(PACKAGE_ROOT, 'build', 'default-profile'));
  const descriptorPath = resolve(PACKAGE_ROOT, 'packages', 'default-compatibility.package.json');
  const descriptorBytes = await readFile(descriptorPath);
  const descriptor = defineRuntimePackage(JSON.parse(descriptorBytes.toString('utf8')));
  const dependencies = new Map(
    descriptor.dependencies.map((dependency) => [dependency.dependency_id, dependency]),
  );
  const moduleDescriptor = dependencies.get(descriptor.profile.module_dependency_id);
  const bundleDescriptor = dependencies.get(descriptor.profile.bundle_dependency_id);
  const profileModuleBytes = await readFile(
    resolveWithin(PACKAGE_ROOT, moduleDescriptor.path, 'profile module path'),
  );
  const bundleBytes = await readFile(
    resolveWithin(PACKAGE_ROOT, bundleDescriptor.path, 'profile bundle path'),
  );
  const bundle = JSON.parse(bundleBytes.toString('utf8'));
  const overlayInputs = await Promise.all(descriptor.overlays.map(async (reference) => {
    const bytes = await readFile(
      resolveWithin(PACKAGE_ROOT, reference.path, `overlay path ${reference.overlay_id}`),
    );
    return { overlay: JSON.parse(bytes.toString('utf8')), bytes };
  }));
  const packageLockBytes = await readFile(resolve(PACKAGE_ROOT, 'package-lock.json'));
  const packageManifest = JSON.parse(
    await readFile(resolve(PACKAGE_ROOT, 'package.json'), 'utf8'),
  );
  if (packageManifest.name !== PRODUCER_PACKAGE_NAME ||
      packageManifest.version !== PRODUCER_PACKAGE_VERSION) {
    throw new Error('Cordis producer package manifest identity mismatch');
  }
  const cordisManifest = JSON.parse(
    await readFile(resolve(PACKAGE_ROOT, 'node_modules', 'cordis', 'package.json'), 'utf8'),
  );
  const resolvedPackage = resolveRuntimePackage({
    descriptor,
    descriptorBytes,
    profile: DEFAULT_PROFILE,
    profileModuleBytes,
    profileBundle: bundle,
    profileBundleBytes: bundleBytes,
    overlays: overlayInputs,
    cordisVersion: cordisManifest.version,
    packageLockBytes,
  });
  async function readBundleArtifact(name) {
    const descriptor = bundle.artifacts[name];
    const bytes = await readFile(
      resolveWithin(REPO_ROOT, descriptor.path, `bundle artifact path ${name}`),
    );
    const actualSha256 = sha256Bytes(bytes);
    if (actualSha256 !== descriptor.sha256) {
      throw new Error(`bundle artifact hash mismatch: ${name}`);
    }
    return JSON.parse(bytes.toString('utf8'));
  }
  const lock = await readBundleArtifact('catalog_lock');
  const request = await produceRuntimePackageRequest(resolvedPackage, lock);
  const requestSha256 = sha256Hex(request);
  if (requestSha256 !== lock.request_sha256) {
    throw new Error(`Cordis request does not match admitted catalog lock: ${requestSha256}`);
  }
  const authority = await readBundleArtifact('authority_registry');
  const lowLevelManifestTemplate = await readBundleArtifact('requested_manifest');
  const lowLevelManifest = lowerDefaultManifest(request, lowLevelManifestTemplate);
  const resolvedManifest = await readBundleArtifact('resolved_manifest');
  const profileProjectionFixture = await readBundleArtifact('profile_projection');
  const profileProjection = lowerDefaultProfileProjection(
    request,
    lock,
    lowLevelManifest,
    resolvedManifest,
  );
  if (JSON.stringify(profileProjection) !== JSON.stringify(profileProjectionFixture)) {
    throw new Error('profile projection does not match the owner-derived fixture');
  }
  const packageProvenance = buildRuntimePackageProvenance(resolvedPackage, {
    request,
    catalogLock: lock,
    profileProjection,
  });
  const packageDiagnostics = buildRuntimePackageDiagnostics(
    resolvedPackage,
    packageProvenance,
    { request, catalogLock: lock, profileProjection },
  );
  await mkdir(output, { recursive: true });
  await Promise.all([
    writeFile(resolve(output, 'runtime_composition_request.v1.json'), `${JSON.stringify(request, null, 2)}\n`),
    writeFile(resolve(output, 'admitted_catalog_lock.v1.json'), `${JSON.stringify(lock, null, 2)}\n`),
    writeFile(resolve(output, 'owner_authority_registry.v1.json'), `${JSON.stringify(authority, null, 2)}\n`),
    writeFile(resolve(output, 'runtime_profile_projection.v1.json'), `${JSON.stringify(profileProjection, null, 2)}\n`),
    writeFile(resolve(output, 'default_compatibility_manifest.requested.json'), `${JSON.stringify(lowLevelManifest, null, 2)}\n`),
    writeFile(resolve(output, 'default_compatibility_manifest.resolved.json'), `${JSON.stringify(resolvedManifest, null, 2)}\n`),
    writeFile(resolve(output, 'runtime_package_provenance.v1.json'), `${JSON.stringify(packageProvenance, null, 2)}\n`),
    writeFile(resolve(output, 'runtime_package_diagnostics.v1.json'), `${JSON.stringify(packageDiagnostics, null, 2)}\n`),
    writeFile(resolve(output, 'producer_metadata.json'), `${JSON.stringify({
      producer: 'cordis',
      package: '@echelon-forge/cordis-runtime',
      profile_id: request.requested_profile.profile_id,
      request_sha256: requestSha256,
      lock_sha256: lock.lock_sha256,
      profile_projection_sha256: profileProjection.projection_sha256,
      request_lock_binding: 'validated',
      cordis_version: resolvedPackage.cordis_version,
      package_lock_sha256: resolvedPackage.package_lock_sha256,
      runtime_package_id: resolvedPackage.descriptor.package_id,
      runtime_package_version: resolvedPackage.descriptor.package_version,
      runtime_package_descriptor_sha256: resolvedPackage.descriptor_sha256,
      runtime_package_dependency_graph_sha256: resolvedPackage.dependency_graph.graph_sha256,
      runtime_package_provenance_sha256: packageProvenance.provenance_sha256,
      applied_configuration_overlays: resolvedPackage.configuration_overlays.map(
        ({ overlay_id }) => overlay_id,
      ),
      profile_module_sha256: resolvedPackage.profile_module_sha256,
      profile_bundle_sha256: resolvedPackage.profile_bundle_sha256,
      artifact_source: bundle.artifact_source,
      low_level_manifest_fixture: 'default_compatibility_manifest.requested.json',
      resolved_manifest_fixture: 'default_compatibility_manifest.resolved.json',
    }, null, 2)}\n`),
  ]);
  process.stdout.write(`${output}\n`);
}

main().catch((error) => {
  console.error(error.stack || error.message || String(error));
  process.exitCode = 1;
});
