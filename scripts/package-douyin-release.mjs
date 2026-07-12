import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs';
import { dirname, relative, resolve } from 'node:path';
import { deflateRawSync } from 'node:zlib';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const projectDir = resolve(root, 'douyin-minigame');
const distDir = resolve(root, 'dist');
const zipPath = resolve(distDir, 'douyin-minigame-release.zip');

execFileSync(process.execPath, ['scripts/check-release-readiness.mjs', '--target=douyin'], {
  cwd: root,
  stdio: 'inherit',
});
execFileSync(process.execPath, ['scripts/check-douyin-bundle.mjs', '--strict'], {
  cwd: root,
  stdio: 'inherit',
});
execFileSync(process.execPath, ['scripts/check-douyin-compliance.mjs', '--strict'], {
  cwd: root,
  stdio: 'inherit',
});

function walk(dir) {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    if (entry.name.startsWith('.') || entry.name === 'node_modules') return [];
    const path = resolve(dir, entry.name);
    if (entry.isDirectory() && existsSync(resolve(path, '.douyin-local-workspace'))) return [];
    return entry.isDirectory() ? walk(path) : [path];
  });
}

const crcTable = Array.from({ length: 256 }, (_, index) => {
  let value = index;
  for (let bit = 0; bit < 8; bit += 1) value = (value & 1) ? (0xedb88320 ^ (value >>> 1)) : (value >>> 1);
  return value >>> 0;
});

function crc32(buffer) {
  let value = 0xffffffff;
  for (const byte of buffer) value = crcTable[(value ^ byte) & 0xff] ^ (value >>> 8);
  return (value ^ 0xffffffff) >>> 0;
}

function dosDateTime() {
  return { time: 0, date: 33 }; // 1980-01-01 00:00:00, deterministic package metadata.
}

function createZip(entries) {
  const localParts = [];
  const centralParts = [];
  let offset = 0;
  const { time, date } = dosDateTime();

  for (const entry of entries) {
    const name = Buffer.from(entry.name.replaceAll('\\', '/'));
    const source = entry.data;
    const compressed = deflateRawSync(source, { level: 9 });
    const crc = crc32(source);

    const local = Buffer.alloc(30);
    local.writeUInt32LE(0x04034b50, 0);
    local.writeUInt16LE(20, 4);
    local.writeUInt16LE(0x0800, 6);
    local.writeUInt16LE(8, 8);
    local.writeUInt16LE(time, 10);
    local.writeUInt16LE(date, 12);
    local.writeUInt32LE(crc, 14);
    local.writeUInt32LE(compressed.length, 18);
    local.writeUInt32LE(source.length, 22);
    local.writeUInt16LE(name.length, 26);
    local.writeUInt16LE(0, 28);
    localParts.push(local, name, compressed);

    const central = Buffer.alloc(46);
    central.writeUInt32LE(0x02014b50, 0);
    central.writeUInt16LE(20, 4);
    central.writeUInt16LE(20, 6);
    central.writeUInt16LE(0x0800, 8);
    central.writeUInt16LE(8, 10);
    central.writeUInt16LE(time, 12);
    central.writeUInt16LE(date, 14);
    central.writeUInt32LE(crc, 16);
    central.writeUInt32LE(compressed.length, 20);
    central.writeUInt32LE(source.length, 24);
    central.writeUInt16LE(name.length, 28);
    central.writeUInt16LE(0, 30);
    central.writeUInt16LE(0, 32);
    central.writeUInt16LE(0, 34);
    central.writeUInt16LE(0, 36);
    central.writeUInt32LE(0, 38);
    central.writeUInt32LE(offset, 42);
    centralParts.push(central, name);
    offset += local.length + name.length + compressed.length;
  }

  const centralBuffer = Buffer.concat(centralParts);
  const end = Buffer.alloc(22);
  end.writeUInt32LE(0x06054b50, 0);
  end.writeUInt16LE(0, 4);
  end.writeUInt16LE(0, 6);
  end.writeUInt16LE(entries.length, 8);
  end.writeUInt16LE(entries.length, 10);
  end.writeUInt32LE(centralBuffer.length, 12);
  end.writeUInt32LE(offset, 16);
  end.writeUInt16LE(0, 20);
  return Buffer.concat([...localParts, centralBuffer, end]);
}

if (!existsSync(projectDir)) throw new Error('douyin-minigame directory is missing');
const entries = walk(projectDir)
  .map(path => ({ name: relative(projectDir, path).replaceAll('\\', '/'), data: readFileSync(path) }))
  .sort((a, b) => a.name.localeCompare(b.name));

const privateConfigEntry = entries.find(entry => entry.name === 'project.private.config.json');
const projectConfigEntry = entries.find(entry => entry.name === 'project.config.json');
if (!privateConfigEntry || !projectConfigEntry) {
  throw new Error('release package requires both project.config.json and project.private.config.json');
}
const privateConfig = JSON.parse(privateConfigEntry.data.toString('utf8'));
const projectConfig = JSON.parse(projectConfigEntry.data.toString('utf8'));
if (!privateConfig.appid || privateConfig.appid === 'touristappid') {
  throw new Error('release package requires a real Douyin appid');
}
projectConfig.appid = privateConfig.appid;
projectConfigEntry.data = Buffer.from(`${JSON.stringify(projectConfig, null, 2)}\n`);

mkdirSync(distDir, { recursive: true });
const zip = createZip(entries);
writeFileSync(zipPath, zip);
const sha256 = createHash('sha256').update(zip).digest('hex');
const manifest = {
  generatedBy: 'npm run douyin:package',
  artifact: 'douyin-minigame-release.zip',
  bytes: zip.length,
  sha256,
  files: entries.map(entry => ({ name: entry.name, bytes: entry.data.length })),
};
writeFileSync(resolve(distDir, 'douyin-minigame-release.manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`);
console.log(`[douyin-package] ${zipPath}`);
console.log(`[douyin-package] bytes=${zip.length} sha256=${sha256}`);
