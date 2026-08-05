#!/usr/bin/env node
// validate-skins.mjs — structural schema checker for skin JSON files.
// Validates every src/skins/*/skin.json against schemas/skin.schema.json
// using a lightweight built-in walker. No npm install required.
import { readFileSync, readdirSync, statSync, existsSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const schemaPath = resolve(root, 'schemas', 'skin.schema.json');
const skinsDir = resolve(root, 'src', 'skins');

let failures = 0;

function fail(msg) {
  process.stderr.write(`[skin-schema] FAIL: ${msg}\n`);
  failures++;
}

function pass(msg) {
  process.stdout.write(`[skin-schema] PASS: ${msg}\n`);
}

// ---- Schema loader ----
if (!existsSync(schemaPath)) {
  fail(`schema not found at ${schemaPath}`);
  process.exit(1);
}
const schema = JSON.parse(readFileSync(schemaPath, 'utf8'));

// ---- Recursive validator ----
function validate(instance, subschema, path) {
  if (subschema.type === 'object') {
    if (typeof instance !== 'object' || instance === null || Array.isArray(instance)) {
      fail(`${path}: expected object, got ${typeof instance}`);
      return;
    }
    if (subschema.required) {
      for (const key of subschema.required) {
        if (!(key in instance)) {
          fail(`${path}: missing required key "${key}"`);
        }
      }
    }
    if (subschema.minProperties !== undefined) {
      const count = Object.keys(instance).length;
      if (count < subschema.minProperties) {
        fail(`${path}: expected at least ${subschema.minProperties} properties, got ${count}`);
      }
    }
    if (subschema.properties) {
      for (const [key, propSchema] of Object.entries(subschema.properties)) {
        if (key in instance) {
          validate(instance[key], propSchema, `${path}.${key}`);
        }
      }
    }
    if (subschema.additionalProperties) {
      for (const [key, value] of Object.entries(instance)) {
        if (subschema.properties && key in subschema.properties) continue;
        validate(value, subschema.additionalProperties, `${path}.${key}`);
      }
    }
    if (subschema.additionalProperties === false) {
      for (const key of Object.keys(instance)) {
        if (subschema.properties && !(key in subschema.properties)) {
          fail(`${path}: unexpected key "${key}"`);
        }
      }
    }
  } else if (subschema.type === 'array') {
    if (!Array.isArray(instance)) {
      fail(`${path}: expected array, got ${typeof instance}`);
      return;
    }
    if (subschema.minItems !== undefined && instance.length < subschema.minItems) {
      fail(`${path}: expected at least ${subschema.minItems} items, got ${instance.length}`);
    }
    if (subschema.items) {
      for (let i = 0; i < instance.length; i++) {
        validate(instance[i], subschema.items, `${path}[${i}]`);
      }
    }
  } else if (subschema.type === 'string') {
    if (typeof instance !== 'string') {
      fail(`${path}: expected string, got ${typeof instance}`);
    } else if (subschema.minLength !== undefined && instance.length < subschema.minLength) {
      fail(`${path}: expected string length >= ${subschema.minLength}, got ${instance.length}`);
    }
  } else if (subschema.type === 'integer' || (Array.isArray(subschema.type) && subschema.type.includes('integer'))) {
    if (typeof instance === 'number' && Number.isInteger(instance)) {
      if (subschema.minimum !== undefined && instance < subschema.minimum) {
        fail(`${path}: expected >= ${subschema.minimum}, got ${instance}`);
      }
      if (subschema.maximum !== undefined && instance > subschema.maximum) {
        fail(`${path}: expected <= ${subschema.maximum}, got ${instance}`);
      }
    } else if (Array.isArray(subschema.type) && subschema.type.includes('string') && typeof instance === 'string') {
      // floor can be "+4" — string is allowed when schema says ["integer","string"]
    } else {
      fail(`${path}: expected integer, got ${typeof instance}`);
    }
  }
}

// ---- Discover skins ----
const skinFolders = readdirSync(skinsDir).filter(name => {
  const full = resolve(skinsDir, name);
  return statSync(full).isDirectory() && existsSync(resolve(full, 'skin.json'));
});

if (skinFolders.length === 0) {
  fail('no skin folders found');
  process.exit(1);
}

console.log(`[skin-schema] Found ${skinFolders.length} skin(s): ${skinFolders.join(', ')}`);
console.log('');

// ---- Validate each skin ----
for (const folder of skinFolders) {
  const skinPath = resolve(skinsDir, folder, 'skin.json');
  let skin;
  try {
    skin = JSON.parse(readFileSync(skinPath, 'utf8'));
  } catch (e) {
    fail(`${folder}: invalid JSON — ${e.message}`);
    continue;
  }

  validate(skin, schema, `${folder}`);

  // Cross-reference: every anomaly must have a matching hiddenLog
  if (Array.isArray(skin.anomalies) && Array.isArray(skin.hiddenLogs)) {
    const anomalyIds = new Set(skin.anomalies.map(a => a.id));
    const hiddenLogIds = new Set(skin.hiddenLogs.map(h => h.id));
    const missingLogs = [...anomalyIds].filter(id => !hiddenLogIds.has(id));
    const orphanLogs = [...hiddenLogIds].filter(id => !anomalyIds.has(id));
    if (missingLogs.length) {
      fail(`${folder}: ${missingLogs.length} anomaly(ies) have no matching hiddenLog: ${missingLogs.join(', ')}`);
    }
    if (orphanLogs.length) {
      fail(`${folder}: ${orphanLogs.length} hiddenLog(s) have no matching anomaly: ${orphanLogs.join(', ')}`);
    }
    if (missingLogs.length === 0 && orphanLogs.length === 0) {
      pass(`${folder}: anomaly↔hiddenLog mapping is 1:1 (${anomalyIds.size})`);
    }
  }

  pass(`${folder}: structural schema check complete`);
  console.log('');
}

// ---- Result ----
if (failures > 0) {
  console.log(`[skin-schema] ${failures} failure(s) — skins are NOT valid`);
  process.exit(1);
}

console.log(`[skin-schema] all ${skinFolders.length} skin(s) valid ✓`);
