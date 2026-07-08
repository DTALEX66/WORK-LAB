import { copyFileSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, '..');
const appRoot = resolve(root, 'android-webview');
const assetsDir = resolve(appRoot, 'app/src/main/assets');
const generatedAssetsDir = resolve(assetsDir, 'assets/generated');

const GENERATED_ASSETS = [
  'cctv-elevator-corridor-clear.png',
  'cctv-elevator-corridor-warp.png',
  'cctv-elevator-corridor-figure.png',
  'cctv-hospital-ward-real.png',
  'cctv-security-room-real.png',
  'cctv-factory-real.png',
  'cctv-subway-platform-real.png',
  'cctv-hotel-lobby-real.png',
  'texture-control-panel.png',
  'texture-hud-glass.png',
  'overlay-cctv-noise.png',
  'overlay-signal-tear.png',
];

rmSync(assetsDir, { recursive: true, force: true });
mkdirSync(assetsDir, { recursive: true });
mkdirSync(generatedAssetsDir, { recursive: true });

execFileSync(process.execPath, ['build.js', 'android'], { cwd: root, stdio: 'pipe' });
copyFileSync(resolve(root, 'android-minigame/game.js'), resolve(assetsDir, 'game.js'));
copyFileSync(resolve(root, 'styles.css'), resolve(assetsDir, 'styles.css'));
for (const asset of GENERATED_ASSETS) {
  copyFileSync(resolve(root, 'assets/generated', asset), resolve(generatedAssetsDir, asset));
}

let html = readFileSync(resolve(root, 'index.html'), 'utf8');
html = html.replace('<script type="module" src="src/game.js"></script>', '<script src="game.js"></script>');
html = html.replace('<meta name="viewport" content="width=device-width, initial-scale=1.0" />', '<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover, user-scalable=no" />');
writeFileSync(resolve(assetsDir, 'index.html'), html, 'utf8');

const files = [
  'settings.gradle',
  'build.gradle',
  'app/build.gradle',
  'app/src/main/AndroidManifest.xml',
  'app/src/main/java/com/dtalex/minigame/MainActivity.java',
  'app/src/main/assets/index.html',
  'app/src/main/assets/styles.css',
  'app/src/main/assets/game.js',
  ...GENERATED_ASSETS.map((asset) => `app/src/main/assets/assets/generated/${asset}`),
];

for (const file of files) {
  const full = resolve(appRoot, file);
  mkdirSync(dirname(full), { recursive: true });
}

console.log(`[android] WebView assets prepared at ${assetsDir}`);
console.log('[android] Entry: android-webview/app/src/main/assets/index.html');
