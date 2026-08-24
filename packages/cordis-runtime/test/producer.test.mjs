import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import {
  produceDefaultRequest,
  lowerDefaultManifest,
  lowerDefaultProfile,
  lowerDefaultProfileProjection,
  sha256Hex,
} from '../src/producer.mjs';

const FIXTURES = new URL('../../../tests/architecture/composition/fixtures/', import.meta.url);

function fixture(name) {
  return JSON.parse(readFileSync(new URL(name, FIXTURES), 'utf8'));
}

test('Cordis producer lowers the default profile into the frozen request', async () => {
  const request = await produceDefaultRequest(undefined, { lock_id: 'default.admitted_catalog' });
  assert.equal(request.schema_version, 'echelon_forge.runtime_composition_request.v1');
  assert.equal(request.requested_profile.profile_id, 'builtin.default_compatibility');
  assert.deepEqual(request.required_capabilities, [
    'deterministic.step',
    'runtime.world_batch.cpu',
  ]);
  assert.deepEqual(request.configuration, { seed: 42, time_step_ns: 16666667 });
  assert.equal(sha256Hex(request), '5c2954d6d04c77fe803130db14d7e5b56391dcf51e482c73ac8cd96877698d6f');
});

test('Cordis producer rejects an unadmitted profile before native handoff', () => {
  assert.throws(
    () => lowerDefaultProfile({ profile_id: 'attacker.profile', profile_version: '1.0.0' }),
    /unsupported profile/,
  );
});

test('Cordis producer requires a catalog-lock artifact', async () => {
  await assert.rejects(
    produceDefaultRequest(undefined, null),
    /requires an admitted catalog-lock artifact/,
  );
});

test('Cordis producer rejects a same-identity profile with altered configuration', () => {
  assert.throws(
    () => lowerDefaultProfile({
      profile_id: 'builtin.default_compatibility',
      profile_version: '1.0.0',
      request_id: 'default.experiment',
      request_version: '1.0.0',
      contract_versions: { composition: '1.0.0', content: '1.0.0', runtime: '1.0.0', stage: '1.0.0' },
      intent: { evaluation_id: 'default.evaluation', policy_id: 'default.policy', simulation_id: 'default.simulation' },
      required_capabilities: ['deterministic.step', 'runtime.world_batch.cpu'],
      required_policies: ['native_step_authority', 'no_mid_episode_truth_reconfiguration'],
      configuration: { seed: 999, time_step_ns: 16666667 },
    }),
    /unsupported profile bundle contents/,
  );
});

test('Cordis producer disposes its effect when lowering fails', async () => {
  await assert.rejects(
    produceDefaultRequest({ profile_id: 'attacker.profile', profile_version: '1.0.0' }, {
      lock_id: 'default.admitted_catalog',
    }),
    /unsupported profile/,
  );
});

test('Cordis producer rejects a low-level template for another profile', async () => {
  const request = await produceDefaultRequest(undefined, { lock_id: 'default.admitted_catalog' });
  assert.throws(
    () => lowerDefaultManifest(request, {
      composition_id: 'attacker.profile',
      requested_profile: { profile_id: 'attacker.profile', profile_version: '1.0.0' },
    }),
    /template does not match/,
  );
});

test('Cordis producer derives the frozen owner-admitted profile projection', () => {
  const projection = lowerDefaultProfileProjection(
    fixture('default_runtime_composition_request.v1.json'),
    fixture('default_admitted_catalog_lock.v1.json'),
    fixture('default_compatibility_manifest.requested.json'),
    fixture('default_compatibility_manifest.resolved.json'),
  );
  assert.deepEqual(projection, fixture('default_runtime_profile_projection.v1.json'));
  assert.equal(
    projection.projection_sha256,
    'a6983836e82df80805ac3f0f4f4a6975edccf3024d8ff231a67009a596a28c09',
  );
});

test('Cordis profile projection identity is catalog permutation stable', () => {
  const lock = fixture('default_admitted_catalog_lock.v1.json');
  lock.entries.reverse();
  for (const entry of lock.entries) entry.capabilities.reverse();
  const projection = lowerDefaultProfileProjection(
    fixture('default_runtime_composition_request.v1.json'),
    lock,
    fixture('default_compatibility_manifest.requested.json'),
    fixture('default_compatibility_manifest.resolved.json'),
  );
  assert.deepEqual(projection, fixture('default_runtime_profile_projection.v1.json'));
});

test('Cordis profile projection rejects a request outside its admitted capability alias', () => {
  const request = fixture('default_runtime_composition_request.v1.json');
  request.required_capabilities = ['attacker.capability'];
  assert.throws(
    () => lowerDefaultProfileProjection(
      request,
      fixture('default_admitted_catalog_lock.v1.json'),
      fixture('default_compatibility_manifest.requested.json'),
      fixture('default_compatibility_manifest.resolved.json'),
    ),
    /request is not bound|capability\/policy set mismatch/,
  );
});
