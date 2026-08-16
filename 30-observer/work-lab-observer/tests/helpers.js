/* WORK-LAB Observer — tests/helpers.js
   Shared test harness. Loads web/ scripts as CommonJS modules and reads
   fixture JSON from tests/fixtures/. Pure Node, no external deps. */

"use strict";

const fs = require("fs");
const path = require("path");

const WEB = path.resolve(__dirname, "..", "web");
const FIXTURES = path.resolve(__dirname, "fixtures");

function loadScripts() {
  // The web scripts reference each other as globals (they run as plain <script>
  // tags in the browser). Mirror that in Node by exposing each module's namespace
  // on global before the dependent modules load.
  const WlFormat = require(path.join(WEB, "scripts", "formatters.js")).WlFormat;
  global.WlFormat = WlFormat;
  const WlApi = require(path.join(WEB, "scripts", "api.js")).WlApi;
  global.WlApi = WlApi;
  const WlState = require(path.join(WEB, "scripts", "state.js")).WlState;
  global.WlState = WlState;
  const WlCharts = require(path.join(WEB, "scripts", "charts.js")).WlCharts;
  global.WlCharts = WlCharts;
  const WlRender = require(path.join(WEB, "scripts", "render.js")).WlRender;
  global.WlRender = WlRender;
  const WlRenderV3 = require(path.join(WEB, "scripts", "render-v3.js")).WlRenderV3;
  global.WlRenderV3 = WlRenderV3;
  const WlA11y = require(path.join(WEB, "scripts", "accessibility.js")).WlA11y;
  global.WlA11y = WlA11y;
  const WlFusionV3 = require(path.join(WEB, "scripts", "fusion-v3.js")).WlFusionV3;
  global.WlFusionV3 = WlFusionV3;
  return { WlFormat, WlApi, WlState, WlCharts, WlRender, WlRenderV3, WlA11y, WlFusionV3 };
}

function loadFixture(name) {
  const p = path.join(FIXTURES, name);
  return JSON.parse(fs.readFileSync(p, "utf-8"));
}

function readProjectionSchema() {
  const p = path.resolve(__dirname, "..", "schemas", "dashboard-projection.schema.json");
  return JSON.parse(fs.readFileSync(p, "utf-8"));
}

function assert(cond, msg) {
  if (!cond) throw new Error("ASSERT FAILED: " + msg);
}

function test(name, fn) {
  try {
    const result = fn();
    if (result && typeof result.then === "function") {
      throw new Error("async test passed to synchronous harness; use asyncTest");
    }
    console.log("  PASS  " + name);
    return true;
  } catch (e) {
    console.error("  FAIL  " + name);
    console.error("        " + e.message);
    return false;
  }
}

async function asyncTest(name, fn) {
  try {
    await fn();
    console.log("  PASS  " + name);
    return true;
  } catch (e) {
    console.error("  FAIL  " + name);
    console.error("        " + e.message);
    return false;
  }
}

module.exports = { WEB, FIXTURES, loadScripts, loadFixture, readProjectionSchema, assert, test, asyncTest };
