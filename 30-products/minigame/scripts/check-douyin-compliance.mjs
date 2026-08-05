import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { resolve } from 'node:path';

const root = resolve(import.meta.dirname, '..');
const assetsDir = resolve(process.env.DOUYIN_RELEASE_ASSETS_DIR || resolve(root, 'release-assets', 'douyin'));
const bundlePath = resolve(process.env.DOUYIN_BUNDLE_PATH || resolve(root, 'douyin-minigame', 'game.js'));
const strict = process.argv.includes('--strict');
const checks = [];

function add(id, ok, level, message, detail = '') {
  checks.push({ id, ok, level, message, detail });
}

const required = [
  'PRIVACY_POLICY_TEMPLATE.md',
  'DATA_AND_SDK_INVENTORY.md',
  'AGE_RATING.md',
  'STORE_LISTING.md',
  'REVIEW_NOTES.md',
  'icon-512.png',
  'icon-1024.png',
];
for (const file of required) {
  add(`asset:${file}`, existsSync(resolve(assetsDir, file)), 'blocker', `${file} exists`);
}
const screenshotsDir = resolve(assetsDir, 'screenshots');
const screenshots = existsSync(screenshotsDir)
  ? readdirSync(screenshotsDir).filter(name => /\.png$/i.test(name))
  : [];
const screenshotMeta = screenshots.map((name) => {
  const data = readFileSync(resolve(screenshotsDir, name));
  const validPng = data.length >= 24 && data.subarray(1, 4).toString('ascii') === 'PNG';
  return {
    name,
    width: validPng ? data.readUInt32BE(16) : 0,
    height: validPng ? data.readUInt32BE(20) : 0,
  };
});
const screenshotsValid = screenshotMeta.length >= 3
  && screenshotMeta.every(item => item.width === 1080 && item.height === 1920);
add(
  'screenshots',
  screenshotsValid,
  'blocker',
  'at least three 1080x1920 review screenshots exist',
  screenshotMeta.map(item => `${item.name}=${item.width}x${item.height}`).join(', '),
);

const bundle = existsSync(bundlePath) ? readFileSync(bundlePath, 'utf8') : '';
const sensitiveApis = [
  'getUserProfile', 'getLocation', 'chooseLocation', 'getPhoneNumber', 'chooseAddress',
  'getClipboardData', 'chooseImage', 'chooseVideo', 'getFuzzyLocation', 'startRecord',
];
const usedSensitiveApis = sensitiveApis.filter(name => new RegExp(`\\.${name}\\s*\\(`).test(bundle));
add(
  'sensitiveApis',
  usedSensitiveApis.length === 0,
  'blocker',
  'bundle does not call undeclared sensitive APIs',
  usedSensitiveApis.join(', '),
);
add('noNetworkUpload', !/\.(request|uploadFile|connectSocket)\s*\(/.test(bundle), 'blocker', 'bundle has no self-hosted network upload path');
add('localPreferenceOnly', /minigame_audio_muted_v1/.test(bundle), 'blocker', 'documented local storage is limited to audio preference');
add('rewardedOnly', /createRewardedVideoAd/.test(bundle) && !/createInterstitialAd|createBannerAd/.test(bundle), 'blocker', 'monetization uses only voluntary rewarded video');

const privacyPath = resolve(assetsDir, 'PRIVACY_POLICY_TEMPLATE.md');
const privacy = existsSync(privacyPath) ? readFileSync(privacyPath, 'utf8') : '';
add('operatorName', !privacy.includes('[需替换为抖音开放平台认证主体全称]'), 'external', 'certified operator name must be filled in the console policy');
add('privacyEmail', !privacy.includes('[需替换为该主体可用的隐私联系邮箱]'), 'external', 'a working privacy contact email must be supplied');

const agePath = resolve(assetsDir, 'AGE_RATING.md');
const ageRating = existsSync(agePath) ? readFileSync(agePath, 'utf8') : '';
add(
  'ageRating16Plus',
  /16\s*(?:周岁以上|\+)/.test(ageRating) && !/建议\s*12\s*周岁以上/.test(ageRating),
  'blocker',
  'suspense content is declared for the stricter 16+ age segment',
);

const listingPath = resolve(assetsDir, 'STORE_LISTING.md');
const listing = existsSync(listingPath) ? readFileSync(listingPath, 'utf8') : '';
add('listingNoHorrorMismatch', !/工业恐怖/.test(listing), 'blocker', 'store positioning is consistent with the declared industrial suspense presentation');

const reviewNotesPath = resolve(assetsDir, 'REVIEW_NOTES.md');
const reviewNotes = existsSync(reviewNotesPath) ? readFileSync(reviewNotesPath, 'utf8') : '';
add(
  'reviewAdPaths',
  ['revive', 'decode', 'truth'].every(id => reviewNotes.includes(id)) && /无需|不包含自建账号/.test(reviewNotes),
  'blocker',
  'review notes document all rewarded-ad paths and test-account requirements',
);

const failed = checks.filter(check => !check.ok);
const blockers = failed.filter(check => check.level === 'blocker');
const external = failed.filter(check => check.level === 'external');
for (const check of checks) {
  const marker = check.ok ? 'PASS' : check.level.toUpperCase();
  console.log(`[${marker}] ${check.id}: ${check.message}`);
  if (!check.ok && check.detail) console.log(`  ${check.detail}`);
}
console.log(`summary: ${checks.length - failed.length}/${checks.length} pass, external placeholder(s): ${external.length}, code blocker(s): ${blockers.length}`);
if (strict && blockers.length > 0) process.exitCode = 1;
