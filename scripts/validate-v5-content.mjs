import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = relative => JSON.parse(fs.readFileSync(path.join(ROOT, relative), 'utf8'));
const errors = [];
const fail = (path, message) => errors.push(`${path}: ${message}`);

const pairs = [
  ['src/content/protocols.json', 'schemas/protocol.schema.json'],
  ['src/content/normalShifts.json', 'schemas/normal-shift.schema.json'],
  ['src/content/anomalies.json', 'schemas/anomaly-content.schema.json'],
  ['src/content/eventChains.json', 'schemas/event-chain.schema.json'],
  ['src/content/passengers.json', 'schemas/passenger.schema.json'],
  ['src/content/endings.json', 'schemas/ending.schema.json'],
];

function matchesType(value, expected) {
  if (Array.isArray(expected)) return expected.some(type => matchesType(value, type));
  if (expected === 'array') return Array.isArray(value);
  if (expected === 'object') return value !== null && typeof value === 'object' && !Array.isArray(value);
  if (expected === 'integer') return Number.isInteger(value);
  if (expected === 'null') return value === null;
  return typeof value === expected;
}

function validateEntry(entry, schema, location) {
  if (!matchesType(entry, schema.type)) return fail(location, `expected ${schema.type}`);
  for (const field of schema.required || []) {
    if (!(field in entry)) fail(location, `missing required field ${field}`);
  }
  if (schema.additionalProperties === false) {
    for (const field of Object.keys(entry)) {
      if (!(field in (schema.properties || {}))) fail(location, `unknown field ${field}`);
    }
  }
  for (const [field, rule] of Object.entries(schema.properties || {})) {
    if (!(field in entry)) continue;
    const value = entry[field];
    if (rule.type && !matchesType(value, rule.type)) fail(`${location}.${field}`, `expected ${JSON.stringify(rule.type)}`);
    if (rule.enum && !rule.enum.includes(value)) fail(`${location}.${field}`, `must be one of ${rule.enum.join(', ')}`);
    if ('const' in rule && value !== rule.const) fail(`${location}.${field}`, `must equal ${rule.const}`);
    if (typeof value === 'string' && rule.maxLength && value.length > rule.maxLength) fail(`${location}.${field}`, `exceeds ${rule.maxLength} chars`);
    if (Array.isArray(value) && rule.minItems && value.length < rule.minItems) fail(`${location}.${field}`, `requires ${rule.minItems} items`);
  }
}

for (const [contentPath, schemaPath] of pairs) {
  const content = read(contentPath);
  const schema = read(schemaPath);
  if (!Array.isArray(content)) {
    fail(contentPath, 'content root must be an array');
    continue;
  }
  content.forEach((entry, index) => validateEntry(entry, schema, `${contentPath}[${index}]`));
  console.log(`[v5-content] ${contentPath}: ${content.length} entries`);
}

if (errors.length) {
  console.error(errors.map(error => `- ${error}`).join('\n'));
  process.exit(1);
}
console.log('[v5-content] ✅ schemas and content containers valid');
