import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import {
  authorityDigestHex,
  buildReleaseManifestShell,
  canonicalAuthorityJson,
  parseCanonicalAuthorityJson,
} from '../src/authority.mjs';

const vector = JSON.parse(readFileSync(new URL('../../../tests/architecture/composition/fixtures/authority_cross_language_vector.v1.json', import.meta.url), 'utf8'));
const authorityVectors = [
  JSON.parse(readFileSync(new URL('../../../tests/architecture/composition/fixtures/authority_resolved_composition_plan.v1.json', import.meta.url), 'utf8')),
  JSON.parse(readFileSync(new URL('../../../tests/architecture/composition/fixtures/authority_resolved_composition_plan.generation2.v1.json', import.meta.url), 'utf8')),
  vector,
  JSON.parse(readFileSync(new URL('../../../tests/architecture/composition/fixtures/authority_rollout_decision.v1.json', import.meta.url), 'utf8')),
  JSON.parse(readFileSync(new URL('../../../tests/architecture/composition/fixtures/authority_state_checkpoint.v1.json', import.meta.url), 'utf8')),
];

test('authority vector is byte and digest stable in Cordis lane', () => {
  assert.equal(canonicalAuthorityJson(JSON.parse(vector.canonical_payload_bytes)), vector.canonical_payload_bytes);
  assert.equal(authorityDigestHex(vector.domain, vector.media_type, vector.canonical_payload_bytes), vector.payload_sha256);
  assert.deepEqual(parseCanonicalAuthorityJson(Buffer.from(vector.canonical_payload_bytes)), JSON.parse(vector.canonical_payload_bytes));
});

test('Cordis consumes every checked-in authority vector without reserialization', () => {
  for (const candidate of authorityVectors) {
    assert.equal(canonicalAuthorityJson(JSON.parse(candidate.canonical_payload_bytes)), candidate.canonical_payload_bytes);
    assert.equal(authorityDigestHex(candidate.domain, candidate.media_type, candidate.canonical_payload_bytes), candidate.payload_sha256);
    assert.equal(JSON.stringify(JSON.parse(candidate.envelope_json)), candidate.envelope_json);
  }
});

test('authority parser rejects invalid UTF-8, surrogate, BOM, duplicate, and noncanonical input', () => {
  assert.throws(() => parseCanonicalAuthorityJson(Buffer.from([0x7b, 0x22, 0x78, 0x22, 0x3a, 0xff, 0x7d])), /encoding|UTF/);
  assert.throws(() => parseCanonicalAuthorityJson(Buffer.from('{"x":"\\ud800"}')), /surrogate/);
  assert.throws(() => parseCanonicalAuthorityJson(Buffer.from('\ufeff{}')), /BOM/);
  assert.throws(() => parseCanonicalAuthorityJson(Buffer.from('{"a":1,"a":1}')), /canonical/);
  assert.throws(() => parseCanonicalAuthorityJson(Buffer.from('{ "a": 1 }')), /canonical/);
  assert.equal(canonicalAuthorityJson({ '10': 1, '2': 2 }), '{"10":1,"2":2}');
  assert.throws(() => authorityDigestHex('\ud800', vector.media_type, vector.canonical_payload_bytes), /surrogate/);
  assert.throws(() => authorityDigestHex(vector.domain, vector.media_type, '\ud800'), /surrogate/);
});

test('Cordis release shell is owner-scoped and typed', () => {
  const payload = JSON.parse(vector.canonical_payload_bytes);
  const envelope = buildReleaseManifestShell(payload);
  assert.equal(envelope.payload_sha256, vector.payload_sha256);
  assert.throws(() => buildReleaseManifestShell({ ...payload, writer_role: 'operator' }), /owner/);
  assert.throws(() => buildReleaseManifestShell({ ...payload, supported_rows: [] }), /non-empty/);
  assert.throws(() => buildReleaseManifestShell({ ...payload, package_set: [{ name: 'z', sha256: 'a'.repeat(64) }, { name: 'a', sha256: 'b'.repeat(64) }] }), /sorted/);
});
