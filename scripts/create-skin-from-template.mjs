#!/usr/bin/env node
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const templatePath = resolve(root, 'templates/skin-template.json');
const skinsRoot = resolve(root, 'src/skins');
const [skinId, ...nameParts] = process.argv.slice(2);

function usage() {
  console.error('Usage: npm run skin:new -- <skin-id> [display-name]');
  console.error('Example: npm run skin:new -- hospital 深夜医院值班台');
}

if (!skinId) {
  usage();
  process.exit(1);
}

if (!/^[a-z][a-z0-9_-]*$/.test(skinId)) {
  console.error(`[skin:new] invalid skin id: ${skinId}`);
  console.error('[skin:new] use lowercase letters, numbers, hyphen, or underscore; start with a letter.');
  process.exit(1);
}

if (!existsSync(templatePath)) {
  console.error(`[skin:new] template not found: ${templatePath}`);
  process.exit(1);
}

const skinDir = resolve(skinsRoot, skinId);
const skinPath = resolve(skinDir, 'skin.json');
if (existsSync(skinPath)) {
  console.error(`[skin:new] skin already exists: ${skinPath}`);
  process.exit(1);
}

const template = JSON.parse(readFileSync(templatePath, 'utf8'));
template.meta.id = skinId;
template.meta.name = nameParts.join(' ').trim() || skinId;
template.meta.subtitle = template.meta.subtitle || 'MINIGAME · ANOMALY SYSTEM SIM';

mkdirSync(skinDir, { recursive: true });
writeFileSync(skinPath, `${JSON.stringify(template, null, 2)}\n`, 'utf8');

console.log(`[skin:new] created ${skinPath}`);
console.log('[skin:new] next steps:');
console.log(`  1. Edit src/skins/${skinId}/skin.json`);
console.log('  2. Replace template copy with the new theme');
console.log('  3. Run npm run skins:check');
console.log('  4. Run npm test');
