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
    assert.strictEqual(config.build.frontendDist, "../frontend/dist");
  });

  // The configured entry URL is pinned verbatim so any drift fails loudly. The
  // query is additionally parsed because the cold-start UNKNOWN state is the
  // contract being tested: without a separate assertion, re-pinning this string
  // for an unrelated edit (a new param, a theme change) could silently drop
  // mode=UNKNOWN and still pass. shell=tauri is how the frameless shell declares
  // itself to the frontend, which has no other deterministic way to know it is
  // not a plain-browser entry.
  function query(url) {
    return new URL(url, "http://tauri.localhost").searchParams;
  }

  test("main window starts UNKNOWN and uses an opaque desktop canvas", () => {
    assert.strictEqual(windows.main.url, "index.html?view=full&mode=UNKNOWN&theme=dark&shell=tauri");
    assert.strictEqual(query(windows.main.url).get("mode"), "UNKNOWN");
    assert.strictEqual(query(windows.main.url).get("view"), "full");
    assert.strictEqual(windows.main.decorations, false);
    assert.strictEqual(windows.main.transparent, false);
  });

  test("panel window is a fixed compact component entry", () => {
    assert.strictEqual(windows.panel.url, "index.html?view=compact&mode=UNKNOWN&theme=dark&shell=tauri");
    assert.strictEqual(query(windows.panel.url).get("mode"), "UNKNOWN");
    assert.strictEqual(query(windows.panel.url).get("view"), "compact");
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
