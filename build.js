/**
 * build.js — 小游戏构建脚本
 *
 * 将 src/ 下的 ES module 源码打包为单个文件，
 * 供微信/抖音小游戏使用（小游戏不支持 ESM）。
 *
 * 用法：node build.js [platform]
 *   platform: wechat (默认) | douyin | browser
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = __dirname;

// ── 需要打包的入口模块 ──
// 顺序重要：依赖在前
const ENTRY_MODULES = [
  'src/gameConfig.js',
  'src/feedback.js',
  'src/skinManager.js',
  'src/skins/elevator/skin.json',
  'src/audio.js',
  'src/state.js',
  'src/events.js',
  'src/actions.js',
  'src/game.js',
];

/**
 * 简易打包：将所有模块拼接为一个 IIFE
 * 注意：这假设模块间没有循环依赖，且所有 export 被入口使用
 */
function bundle(target) {
  let output = `/**
 * MINIGAME - ${target} 小游戏构建
 * 构建时间: ${new Date().toISOString()}
 * 请勿手动修改此文件
 */\n\n`;

  // 注入平台 polyfill
  output += `(function() {\n'use strict';\n\n`;

  // 读取并拼接所有模块
  for (const modPath of ENTRY_MODULES) {
    const fullPath = path.join(ROOT, modPath);
    if (!fs.existsSync(fullPath)) {
      console.warn(`[build] 警告: ${modPath} 不存在，跳过`);
      continue;
    }

    let content = fs.readFileSync(fullPath, 'utf-8');

    // 处理 skin.json - 转为 JS 对象赋值
    if (modPath.endsWith('.json')) {
      content = `const SKIN_DATA = ${content.trim()};\n`;
    } else {
      // 移除 ESM import/export 语句
      content = content
        .replace(/^import .+ from\s+['"].+['"];?\s*$/gm, '')  // 移除 import
        .replace(/^export (default |const |function |let |var )/gm, '$1')  // 移除 export
        .replace(/^export \{.+};?\s*$/gm, '');  // 移除 export { ... }
    }

    output += `// --- ${modPath} ---\n${content}\n\n`;
  }

  // 添加启动代码
  output += `
// ── 启动游戏 ──
const canvas = typeof wx !== 'undefined' ? wx.createCanvas() : document.querySelector('canvas');
if (canvas) {
  const { init, render } = window.__MINIGAME_RENDERER__ || {};
  if (init) init(canvas);

  // 每帧渲染
  function gameLoop() {
    render(state);
    requestAnimationFrame(gameLoop);
  }
  gameLoop();
} else {
  // DOM 模式 - game.js 已经处理
  console.log('[MINIGAME] Running in DOM mode');
}
`;

  output += `\n})();\n`;
  return output;
}

// ── 写入输出 ──
const target = process.argv[2] || 'wechat';
const outputDir = path.join(ROOT, `${target}-minigame`);
fs.mkdirSync(outputDir, { recursive: true });

const bundled = bundle(target);
const outPath = path.join(outputDir, 'game.js');
fs.writeFileSync(outPath, bundled, 'utf-8');

console.log(`[build] ✅ ${target} 构建完成`);
console.log(`[build]   输出: ${outPath}`);
console.log(`[build]   大小: ${(bundled.length / 1024).toFixed(1)} KB`);

// ── 创建 project.config.json ──
if (!fs.existsSync(path.join(outputDir, 'project.config.json'))) {
  const projConfig = {
    description: 'MINIGAME - 异常系统模拟类小游戏',
    setting: {
      urlCheck: true,
      es6: true,
      postcss: true,
      minified: true,
      enhance: true,
      condition: false,
    },
    compileType: 'game',
    libVersion: 'latest',
    appid: '请替换为你的微信小游戏 AppID',
    projectname: 'MINIGAME',
    condition: {},
  };
  fs.writeFileSync(
    path.join(outputDir, 'project.config.json'),
    JSON.stringify(projConfig, null, 2),
    'utf-8'
  );
  console.log('[build] ✅ project.config.json 已创建（请替换 appid）');
}

// ── 创建 game.json ──
if (!fs.existsSync(path.join(outputDir, 'game.json'))) {
  const gameConfig = {
    deviceOrientation: 'portrait',
    showStatusBar: false,
    networkTimeout: { request: 5000, connectSocket: 5000 },
    workers: null,
  };
  fs.writeFileSync(
    path.join(outputDir, 'game.json'),
    JSON.stringify(gameConfig, null, 2),
    'utf-8'
  );
  console.log('[build] ✅ game.json 已创建');
}
