/* WORK-LAB Observer — tests/run_all_tests.js
   Runs every test_*.js suite and reports a combined pass/fail exit code. */

"use strict";

const suites = [
  "./test_projection_contract.js",
  "./test_read_only_surface.js",
  "./test_responsive_contract.js",
  "./test_visual_assets_r2.js",
  "./test_desktop_component_contract.js",
  "./test_render_v3.js",
];

let totalPass = 0, totalFail = 0;

for (const s of suites) {
  const mod = require(s);
  const result = mod.run();
  totalPass += result.pass;
  totalFail += result.fail;
}

console.log(`\n==== WORK-LAB Observer UI contract tests ====`);
console.log(`TOTAL: ${totalPass} passed, ${totalFail} failed`);
process.exit(totalFail ? 1 : 0);
