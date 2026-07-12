import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';
import { resolve } from 'node:path';

const root = resolve(import.meta.dirname, '..');

test('generated Douyin bundle boots against the tt Canvas contract', () => {
  execFileSync(process.execPath, ['build.js', 'douyin'], { cwd: root, stdio: 'pipe' });
  const bundle = readFileSync(resolve(root, 'douyin-minigame', 'game.js'), 'utf8');
  const text = [];
  const imageSources = [];
  let drawImageCalls = 0;
  const gradient = { addColorStop() {} };
  const ctx = new Proxy({
    measureText(value) { return { width: String(value).length * 16 }; },
    fillText(value) { text.push(String(value)); },
    drawImage() { drawImageCalls += 1; },
    createLinearGradient() { return gradient; },
    createRadialGradient() { return gradient; },
  }, {
    get(target, key) {
      if (key in target) return target[key];
      return () => {};
    },
    set(target, key, value) {
      target[key] = value;
      return true;
    },
  });
  const canvas = { width: 0, height: 0, getContext: () => ctx };
  let onTouchStart;
  let onHide;
  let onShow;
  let sidebarOptions;
  let nextFrame;
  let now = 1_000;
  const tt = {
    createCanvas: () => canvas,
    getSystemInfoSync: () => ({ windowWidth: 390, windowHeight: 844, safeArea: { top: 47 } }),
    requestAnimationFrame(callback) { nextFrame = callback; return 1; },
    onTouchStart(callback) { onTouchStart = callback; },
    onHide(callback) { onHide = callback; },
    onShow: fn => { onShow = fn; },
    checkScene: options => options.success?.({ isExist: true }),
    navigateToScene: options => { sidebarOptions = options; options.success?.({}); },
    createImage() {
      const image = { onload: null, onerror: null, _src: '' };
      Object.defineProperty(image, 'src', {
        set(value) { image._src = value; imageSources.push(value); image.onload?.(); },
        get() { return image._src; },
      });
      return image;
    },
    createInnerAudioContext() {
      return { play() {}, stop() {}, seek() {}, destroy() {} };
    },
  };
  const sandbox = vm.createContext({
    tt,
    console,
    Date: { now: () => now },
    Promise,
    setTimeout,
    clearTimeout,
  });
  vm.runInContext(bundle, sandbox, { filename: 'douyin-minigame/game.js' });

  assert.equal(canvas.width, 750);
  assert.ok(canvas.height > 1623 && canvas.height < 1624);
  assert.equal(typeof onTouchStart, 'function');
  assert.equal(typeof onHide, 'function');
  assert.equal(typeof onShow, 'function');
  assert.equal(typeof nextFrame, 'function');
  assert.ok(text.includes('等待接管异常电梯'));
  assert.ok(text.includes('开始接管'));
  assert.ok(text.includes('侧边栏入口'));
  assert.equal(imageSources.length, 38, 'all shipped Canvas visual assets should preload');
  assert.ok(imageSources.includes('visual/cctv/00_idle_closed_mobile.png'));
  assert.ok(imageSources.includes('visual/buttons/btn_stop_danger.png'));
  assert.ok(drawImageCalls >= 2, 'the first render should draw the CCTV state and its dynamic inspection overlay');

  onTouchStart({ touches: [{ screenX: 570 * 390 / 750, screenY: 930 * 844 / canvas.height }] });
  assert.equal(sidebarOptions?.scene, 'sidebar');
  onTouchStart({ touches: [{ screenX: 275 * 390 / 750, screenY: 930 * 844 / canvas.height }] });
  now += 8_000;
  nextFrame();
  assert.ok(text.includes('报告异常'), 'first anomaly should expose a real classify decision');
  assert.ok(text.includes('判为正常'), 'normal/anomaly choices should stay paired');
  onHide();
  onShow({ scene: '021036' });
});

test('generated Douyin bundle settles rewarded-ad completion, cancellation, error and stale guards safely', async () => {
  execFileSync(process.execPath, ['build.js', 'douyin'], { cwd: root, stdio: 'pipe' });
  const rawBundle = readFileSync(resolve(root, 'douyin-minigame', 'game.js'), 'utf8');
  assert.match(rawBundle, /function shouldApplyReward\s*\(/, 'reward guard must be present in the generated bundle');
  const bundle = rawBundle.replace(
    'startMiniGame();\n})();',
    'globalThis.__bundleTest = { createMiniGameRewardedAd, shouldApplyReward };\n})();',
  );
  const sandbox = vm.createContext({ console, Promise, setTimeout, clearTimeout });
  vm.runInContext(bundle, sandbox, { filename: 'douyin-minigame/game.js' });
  const { createMiniGameRewardedAd, shouldApplyReward } = sandbox.__bundleTest;

  const ads = [];
  const api = {
    createRewardedVideoAd() {
      const ad = {
        onClose(handler) { ad.close = handler; },
        onError(handler) { ad.error = handler; },
        offClose() {}, offError() {}, destroy() {},
        show: () => Promise.resolve(),
        load: () => Promise.resolve(),
      };
      ads.push(ad);
      return ad;
    },
  };
  let rewards = 0;
  let errors = 0;
  let starts = 0;
  let settlements = 0;
  const show = createMiniGameRewardedAd(api, 'adunit-real', {
    releaseMode: true,
    onReward: () => { rewards += 1; },
    onError: () => { errors += 1; },
    onStart: () => { starts += 1; },
    onSettled: () => { settlements += 1; },
  });

  await show({ runToken: 1 });
  ads[0].close({ isEnded: false });
  await show({ runToken: 2 });
  ads[1].close({ isEnded: true });
  ads[1].close({ isEnded: true });
  await show({ runToken: 3 });
  ads[2].error(new Error('ad failed'));

  assert.deepEqual({ rewards, errors, starts, settlements }, {
    rewards: 1, errors: 1, starts: 3, settlements: 3,
  });
  assert.equal(shouldApplyReward(
    { context: { runToken: 7 } }, 7, 'revive', { gameOver: true, result: 'failure' },
  ), true);
  assert.equal(shouldApplyReward(
    { context: { runToken: 6 } }, 7, 'revive', { gameOver: true, result: 'failure' },
  ), false, 'stale run callbacks must not apply rewards');
});
