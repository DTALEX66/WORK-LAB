/* WORK-LAB Observer — fixed portable desktop component contract. */

"use strict";

const assert = require("assert");
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const CONFIG = path.join(ROOT, "src-tauri", "tauri.conf.json");
const CAPABILITIES = path.join(ROOT, "src-tauri", "capabilities", "default.json");

function run() {
  const config = JSON.parse(fs.readFileSync(CONFIG, "utf8"));
  const caps = JSON.parse(fs.readFileSync(CAPABILITIES, "utf8"));
  const windows = Object.fromEntries((config.app && config.app.windows || []).map((w) => [w.label, w]));
  let pass = 0;
  let fail = 0;

  function test(name, fn) {
    try {
      fn();
      console.log("  PASS  " + name);
      pass += 1;
    } catch (err) {
      console.log("  FAIL  " + name);
      console.log("        " + err.message);
      fail += 1;
    }
  }

  test("frontendDist points to the embedded local web frontend", () => {
    assert.strictEqual(config.build.frontendDist, "../web");
  });

  test("main window is a fixed full LIVE entry", () => {
    assert.strictEqual(windows.main.url, "index.html?view=full&mode=LIVE&theme=dark");
    assert.strictEqual(windows.main.decorations, false);
    assert.strictEqual(windows.main.transparent, true);
  });

  test("panel window is a fixed compact component entry", () => {
    assert.strictEqual(windows.panel.url, "index.html?view=compact&mode=LIVE&theme=dark");
    assert.strictEqual(windows.panel.width, 440);
    assert.strictEqual(windows.panel.height, 780);
    assert.strictEqual(windows.panel.minWidth, 440);
    assert.strictEqual(windows.panel.minHeight, 780);
    assert.strictEqual(windows.panel.resizable, false);
    assert.strictEqual(windows.panel.alwaysOnTop, true);
    assert.strictEqual(windows.panel.skipTaskbar, true);
    assert.strictEqual(windows.panel.visible, false);
  });

  test("portable bundle remains active without updater or mutation capability", () => {
    assert.strictEqual(config.bundle.active, true);
    assert(!JSON.stringify(config).match(/updater|createUpdaterArtifacts/i));
    const permissions = JSON.stringify(caps.permissions || []);
    assert(!permissions.match(/shell|process|fs:allow|http:allow|os:allow/i));
  });

  console.log("\n==== WORK-LAB desktop component contract tests ====");
  console.log(`TOTAL: ${pass} passed, ${fail} failed`);
  return { pass, fail };
}

if (require.main === module) {
  const result = run();
  if (result.fail) process.exitCode = 1;
}

module.exports = { run };
