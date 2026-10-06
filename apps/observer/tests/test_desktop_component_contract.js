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

  // Tauri v2 denies every mutating window/webview command by default:
  // core:default carries only readers (is-maximized, inner-size, title…), so a
  // caption button that calls close() against an ungranted ACL rejects
  // asynchronously and the user just sees a dead button. Deriving the called
  // set from the shipped source is what keeps that from recurring — an
  // un-mapped new call, or a dropped grant, fails here rather than on someone's
  // desktop.
  const NATIVE_CALL_PERMISSIONS = {
    minimize: "core:window:allow-minimize",
    toggleMaximize: "core:window:allow-toggle-maximize",
    close: "core:window:allow-close",
    startDragging: "core:window:allow-start-dragging",
    setZoom: "core:webview:allow-set-webview-zoom",
  };

  function nativeCallsInFrontend() {
    const srcRoot = path.join(ROOT, "frontend", "src");
    const calls = new Map();
    const walk = (dir) => {
      for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
        const fp = path.join(dir, entry.name);
        if (entry.isDirectory()) { walk(fp); continue; }
        if (!/\.(ts|tsx)$/.test(entry.name)) continue;
        const src = fs.readFileSync(fp, "utf8");
        const found = [
          ...[...src.matchAll(/\(await win\(\)\)\.(\w+)\(/g)].map((m) => m[1]),
          ...[...src.matchAll(/getCurrentWebview\(\)\.(\w+)\(/g)].map((m) => m[1]),
          ...( /data-tauri-drag-region/.test(src) ? ["startDragging"] : []),
        ];
        for (const c of found) {
          if (!calls.has(c)) calls.set(c, path.relative(ROOT, fp));
        }
      }
    };
    walk(srcRoot);
    return calls;
  }

  const nativeCalls = nativeCallsInFrontend();

  test("every native call the frontend makes maps to an ACL identifier", () => {
    const unmapped = [...nativeCalls.keys()].filter(
      (c) => !Object.prototype.hasOwnProperty.call(NATIVE_CALL_PERMISSIONS, c));
    assert.deepStrictEqual(unmapped, [],
      "add the permission identifier for: " + unmapped.join(", "));
  });

  test("the capability grants every native call the frontend makes", () => {
    const granted = new Set(caps.permissions || []);
    const missing = [...nativeCalls].filter(
      ([call, file]) => !granted.has(NATIVE_CALL_PERMISSIONS[call]))
      .map(([call, file]) => `${call} (${file}) → ${NATIVE_CALL_PERMISSIONS[call]}`);
    assert.deepStrictEqual(missing, [],
      "capability does not grant:\n        " + missing.join("\n        "));
  });

  // Both windows are frameless, so the top of the layout IS the edge of the OS
  // window: a rule with no vertical clearance puts content directly against the
  // border, which is exactly what the owner found by eye after a visual audit
  // that only ever measured overflow to the right and bottom. These assertions
  // keep the measured clearance from being zeroed again.
  const SHELL_CSS = fs.readFileSync(
    path.join(ROOT, "frontend", "src", "skins", "l10b-shell.css"), "utf8");

  function px(property, where) {
    const block = SHELL_CSS.match(where);
    if (!block) return null;
    const found = new RegExp(property + ":\\s*(-?[\\d.]+)px").exec(block[0]);
    return found ? parseFloat(found[1]) : null;
  }

  test("the frameless shell keeps the top row clear of the window edge", () => {
    const fixedCluster = /\.winctl\s*\{[^}]*position:\s*fixed[^}]*\}/;
    const top = px("padding-top", /\.topbar\s*\{[^}]*padding-top[^}]*\}/);
    const bottom = px("padding-bottom", /\.topbar\s*\{[^}]*padding-bottom[^}]*\}/);
    const clusterTop = px("top", fixedCluster);
    const clusterRight = px("right", fixedCluster);
    for (const [name, value] of [[".topbar padding-top", top],
                                 [".topbar padding-bottom", bottom],
                                 [".winctl top", clusterTop],
                                 [".winctl right", clusterRight]]) {
      assert(typeof value === "number", `${name} is not declared in px`);
      assert(value >= 10, `${name} = ${value}px gives a frameless window no clearance`);
    }
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
