import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const root = resolve(import.meta.dirname, '..');
const templatePath = resolve(root, 'templates/skin-template.json');
const guidePath = resolve(root, 'docs/SKIN_AUTHORING_GUIDE.md');
const schemaPath = resolve(root, 'schemas/skin.schema.json');

function validate(instance, subschema, path = '$', failures = []) {
  const allowedTypes = Array.isArray(subschema.type) ? subschema.type : [subschema.type];
  if (allowedTypes.includes('object')) {
    if (typeof instance !== 'object' || instance === null || Array.isArray(instance)) {
      failures.push(`${path}: expected object`);
      return failures;
    }
    for (const key of subschema.required || []) {
      if (!(key in instance)) failures.push(`${path}: missing ${key}`);
    }
    for (const [key, propSchema] of Object.entries(subschema.properties || {})) {
      if (key in instance) validate(instance[key], propSchema, `${path}.${key}`, failures);
    }
    if (subschema.minProperties !== undefined && Object.keys(instance).length < subschema.minProperties) {
      failures.push(`${path}: expected at least ${subschema.minProperties} properties`);
    }
  } else if (allowedTypes.includes('array')) {
    if (!Array.isArray(instance)) {
      failures.push(`${path}: expected array`);
      return failures;
    }
    if (subschema.minItems !== undefined && instance.length < subschema.minItems) {
      failures.push(`${path}: expected at least ${subschema.minItems} items`);
    }
    for (let i = 0; i < instance.length; i++) {
      validate(instance[i], subschema.items || {}, `${path}[${i}]`, failures);
    }
  } else if (allowedTypes.includes('integer') && typeof instance === 'number') {
    if (!Number.isInteger(instance)) failures.push(`${path}: expected integer`);
  } else if (allowedTypes.includes('string')) {
    if (typeof instance !== 'string') failures.push(`${path}: expected string`);
    if (subschema.minLength !== undefined && typeof instance === 'string' && instance.length < subschema.minLength) {
      failures.push(`${path}: too short`);
    }
  } else if (allowedTypes.includes('integer')) {
    if (!(typeof instance === 'number' && Number.isInteger(instance))) failures.push(`${path}: expected integer`);
  }
  return failures;
}

test('skin authoring template is valid JSON and satisfies the skin schema', () => {
  const template = JSON.parse(readFileSync(templatePath, 'utf8'));
  const schema = JSON.parse(readFileSync(schemaPath, 'utf8'));
  const failures = validate(template, schema);

  assert.deepEqual(failures, []);
  assert.equal(template.meta.id, 'skin-template');
  assert.ok(template.anomalies.length >= 12);
  for (const anomaly of template.anomalies) {
    assert.ok(template.hiddenLogs[anomaly.id], `${anomaly.id} should have a matching hidden log`);
  }
});

test('skin authoring guide documents the repeatable production workflow', () => {
  const guide = readFileSync(guidePath, 'utf8');

  for (const required of [
    'templates/skin-template.json',
    'src/skins/<skin-id>/skin.json',
    'npm run skins:check',
    'npm test',
    'node build.js wechat',
    'meta.id',
    'actionLabels',
    'canvasLabels',
    'anomalies',
    'hiddenLogs',
    '12',
    '地铁末班调度室',
  ]) {
    assert.match(guide, new RegExp(required.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
  }
});
