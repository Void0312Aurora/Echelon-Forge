import { createHash } from 'node:crypto';

export const AUTHORITY_CANONICALIZATION = 'echelon_forge.canonical_json.v2';
export const AUTHORITY_ENVELOPE_VERSION = 'echelon_forge.authority_envelope.v1';
const DOMAIN_SEPARATOR = Buffer.from('echelon-forge-authority-v1\0', 'utf8');
const MAX_SAFE_INTEGER = Number.MAX_SAFE_INTEGER;

function utf16Compare(left, right) {
  const leftUnits = [...left].flatMap((char) => {
    const code = char.codePointAt(0);
    return code > 0xffff ? [0xd800 + ((code - 0x10000) >> 10), 0xdc00 + ((code - 0x10000) & 0x3ff)] : [code];
  });
  const rightUnits = [...right].flatMap((char) => {
    const code = char.codePointAt(0);
    return code > 0xffff ? [0xd800 + ((code - 0x10000) >> 10), 0xdc00 + ((code - 0x10000) & 0x3ff)] : [code];
  });
  const length = Math.min(leftUnits.length, rightUnits.length);
  for (let index = 0; index < length; index += 1) {
    if (leftUnits[index] !== rightUnits[index]) return leftUnits[index] - rightUnits[index];
  }
  return leftUnits.length - rightUnits.length;
}

function validateString(value, path) {
  for (const char of value) {
    const code = char.codePointAt(0);
    if (code >= 0xd800 && code <= 0xdfff) throw new TypeError(`${path}: lone UTF-16 surrogate`);
  }
}

function encodeValue(value, path = '$') {
  if (value === null) return 'null';
  if (typeof value === 'boolean') return value ? 'true' : 'false';
  if (typeof value === 'string') {
    validateString(value, path);
    return JSON.stringify(value);
  }
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) throw new TypeError(`${path}: non-finite number`);
    if (!Number.isSafeInteger(value) && Number.isInteger(value)) {
      throw new TypeError(`${path}: integer outside exact cross-language range must be a decimal string`);
    }
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) {
    return `[${value.map((nested, index) => encodeValue(nested, `${path}[${index}]`)).join(',')}]`;
  }
  if (typeof value === 'object') {
    const entries = Object.entries(value).sort(([left], [right]) => utf16Compare(left, right));
    return `{${entries.map(([key, nested]) => {
      validateString(key, `${path}.<key>`);
      return `${JSON.stringify(key)}:${encodeValue(nested, `${path}.${key}`)}`;
    }).join(',')}}`;
  }
  throw new TypeError(`${path}: unsupported JSON value`);
}

function sortKeys(value) {
  if (Array.isArray(value)) return value.map(sortKeys);
  if (!value || typeof value !== 'object') return value;
  return Object.fromEntries(Object.entries(value)
    .sort(([left], [right]) => utf16Compare(left, right))
    .map(([key, nested]) => [key, sortKeys(nested)]));
}

export function canonicalAuthorityJson(value) {
  return encodeValue(value);
}

export function authorityDigestHex(domain, mediaType, payloadBytes) {
  if (typeof domain !== 'string' || typeof mediaType !== 'string' || typeof payloadBytes !== 'string' ||
      !domain || domain.includes('\0') || !mediaType || mediaType.includes('\0')) {
    throw new TypeError('domain and media type must be non-empty and NUL-free');
  }
  validateString(domain, 'domain');
  validateString(mediaType, 'media_type');
  validateString(payloadBytes, 'payload_bytes');
  return createHash('sha256')
    .update(Buffer.concat([DOMAIN_SEPARATOR, Buffer.from(domain), Buffer.from('\0'), Buffer.from(mediaType), Buffer.from('\0'), Buffer.from(payloadBytes)]))
    .digest('hex');
}

function buildAuthorityEnvelope({ domain, mediaType, payload, signatures = [] }) {
  const canonicalPayload = canonicalAuthorityJson(payload);
  return sortKeys({
    canonicalization: AUTHORITY_CANONICALIZATION,
    domain,
    envelope_version: AUTHORITY_ENVELOPE_VERSION,
    media_type: mediaType,
    payload: JSON.parse(canonicalPayload),
    payload_sha256: authorityDigestHex(domain, mediaType, canonicalPayload),
    signatures,
  });
}

const RELEASE_FIELDS = new Set([
  'authority_kind', 'contract_version', 'package_set', 'provenance_sha256',
  'reader_generation_max', 'reader_generation_min', 'release_id', 'sbom_sha256',
  'schema_version', 'source_revision', 'supported_rows', 'toolchain_identity',
  'writer_generation', 'writer_role', 'compatibility_generation', 'minimum_reader_generation',
  'state_schema_generation', 'rollback_policy',
]);

function requireSha(value, field) {
  if (typeof value !== 'string' || !/^[0-9a-f]{64}$/.test(value)) throw new TypeError(`${field}: SHA-256 is required`);
}

function requireString(value, field) {
  if (typeof value !== 'string' || value.length === 0) throw new TypeError(`${field}: non-empty string required`);
}

function requireIdentifier(value, field) {
  requireString(value, field);
  if (!/^[A-Za-z][A-Za-z0-9._:-]{0,127}$/.test(value)) throw new TypeError(`${field}: bounded identifier required`);
}

function requireGeneration(value, field) {
  if (typeof value !== 'string' || !/^(?:0|[1-9][0-9]*)$/.test(value)) throw new TypeError(`${field}: generation is not canonical`);
}

function generationAtMost(left, right) {
  return left.length < right.length || (left.length === right.length && left <= right);
}

export function buildReleaseManifestShell(payload) {
  if (!payload || typeof payload !== 'object' || [...RELEASE_FIELDS].some((field) => !(field in payload)) || Object.keys(payload).some((field) => !RELEASE_FIELDS.has(field))) {
    throw new TypeError('release manifest payload fields are not exact');
  }
  if (payload.authority_kind !== 'release_manifest' || payload.schema_version !== 'echelon_forge.release_manifest.v1' ||
      payload.contract_version !== 'echelon_forge.release_manifest_contract.v1' || payload.writer_role !== 'release_artifact_pipeline') {
    throw new TypeError('release manifest owner or version mismatch');
  }
  requireIdentifier(payload.release_id, 'release_id');
  ['source_revision', 'toolchain_identity'].forEach((field) => requireString(payload[field], field));
  ['writer_generation', 'reader_generation_min', 'reader_generation_max'].forEach((field) => requireGeneration(payload[field], field));
  ['compatibility_generation', 'minimum_reader_generation', 'state_schema_generation'].forEach((field) => requireGeneration(payload[field], field));
  requireString(payload.rollback_policy, 'rollback_policy');
  if (!['checkpoint-recovery', 'package-restart'].includes(payload.rollback_policy)) throw new TypeError('release rollback policy is not admitted');
  if (!generationAtMost(payload.reader_generation_min, payload.reader_generation_max)) throw new TypeError('release reader generation window is inverted');
  ['provenance_sha256', 'sbom_sha256'].forEach((field) => requireSha(payload[field], field));
  if (!Array.isArray(payload.package_set) || payload.package_set.length === 0 || payload.package_set.some((item) => !item || Object.keys(item).length !== 2 || typeof item.name !== 'string' || !item.name || typeof item.sha256 !== 'string')) {
    throw new TypeError('release package_set is not typed');
  }
  payload.package_set.forEach((item) => requireSha(item.sha256, 'package_set.sha256'));
  const names = payload.package_set.map((item) => item.name);
  if (names.some((name, index) => name !== [...names].sort(utf16Compare)[index]) || new Set(names).size !== names.length) throw new TypeError('release package_set must be sorted and unique');
  if (!Array.isArray(payload.supported_rows) || payload.supported_rows.length === 0 || payload.supported_rows.some((row) => typeof row !== 'string' || !row) || [...payload.supported_rows].sort(utf16Compare).join('\0') !== payload.supported_rows.join('\0') || new Set(payload.supported_rows).size !== payload.supported_rows.length) throw new TypeError('release supported_rows must be non-empty, sorted, and unique');
  return buildAuthorityEnvelope({
    domain: 'release.manifest',
    mediaType: 'application/vnd.echelon-forge.release-manifest.v1+json',
    payload,
  });
}

export function parseCanonicalAuthorityJson(bytes) {
  const raw = Buffer.from(bytes);
  if (raw.subarray(0, 3).equals(Buffer.from([0xef, 0xbb, 0xbf]))) throw new TypeError('UTF-8 BOM is forbidden');
  const text = new TextDecoder('utf-8', { fatal: true }).decode(raw);
  if (text.charCodeAt(0) === 0xfeff) throw new TypeError('UTF-8 BOM is forbidden');
  const parsed = JSON.parse(text);
  if (!parsed || Array.isArray(parsed) || typeof parsed !== 'object') throw new TypeError('authority payload must be an object');
  if (canonicalAuthorityJson(parsed) !== text) throw new TypeError('payload is not canonical JSON v2');
  return parsed;
}
