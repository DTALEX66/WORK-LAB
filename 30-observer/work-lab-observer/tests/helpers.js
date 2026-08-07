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
  const WlA11y = require(path.join(WEB, "scripts", "accessibility.js")).WlA11y;
  global.WlA11y = WlA11y;
  return { WlFormat, WlApi, WlState, WlCharts, WlRender, WlA11y };
}

function loadFixture(name) {
  const p = path.join(FIXTURES, name);
  return JSON.parse(fs.readFileSync(p, "utf-8"));
}

function readProjectionSchema() {
  const p = path.resolve(__dirname, "..", "..", "..", ".hermes",
    "task-artifacts", "observer-ui-deepseek-r1",
    "WORK-LAB-OBSERVER-UI-DEEPSEEK-PACK-R1-2026-08-07",
    "contracts", "dashboard-projection.schema.json");
  return JSON.parse(fs.readFileSync(p, "utf-8"));
}

function assert(cond, msg) {
  if (!cond) throw new Error("ASSERT FAILED: " + msg);
}

function test(name, fn) {
  try {
    fn();
    console.log("  PASS  " + name);
    return true;
  } catch (e) {
    console.error("  FAIL  " + name);
    console.error("        " + e.message);
    return false;
  }
}

module.exports = { WEB, FIXTURES, loadScripts, loadFixture, readProjectionSchema, assert, test };
