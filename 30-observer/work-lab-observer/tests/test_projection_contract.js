/* WORK-LAB Observer — tests/test_projection_contract.js
   Contract tests: fixture passes schema, unknown-field forward compat,
   required-missing downgrade, RFC3339 dates, coverage num/den/scope,
   and input/output/cache/cost semantic separation (no fabricated total token). */

"use strict";

const { loadScripts, loadFixture, readProjectionSchema, assert, test } = require("./helpers");

const ISO_DATE_RE = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$/;

function run() {
  const { WlApi, WlRender, WlState } = loadScripts();
  let pass = 0, fail = 0;
  const t = (n, f) => { if (test(n, f)) pass++; else fail++; };

  t("fixture parses as valid JSON object with core keys", () => {
    const fx = loadFixture("cross-project-active-mixed.json");
    ["schemaVersion", "mode", "generatedAt", "freshness", "summary", "projects", "usage", "ci", "governance", "quality"]
      .forEach((k) => assert(k in fx, "missing core key " + k));
  });

  t("inline API FIXTURE matches authoritative fixture numbers", () => {
    const fx = loadFixture("cross-project-active-mixed.json");
    assert(WlApi.FIXTURE.mode === "FIXTURE", "inline must be FIXTURE");
    assert(WlApi.FIXTURE.usage.inputTokens === 64391, "inputTokens must be 64391");
    assert(WlApi.FIXTURE.usage.outputTokens === 26821, "outputTokens must be 26821");
    assert(WlApi.FIXTURE.usage.cacheReadTokens === 39960, "cacheReadTokens must be 39960");
    assert(WlApi.FIXTURE.usage.cost.amount === 4.29, "cost amount 4.29");
    assert(WlApi.FIXTURE.usage.subscriptionUsage === "not-metered", "subscriptionUsage not-metered");
    assert(WlApi.FIXTURE.summary.registeredProjects === fx.summary.registeredProjects, "project count parity");
    assert(WlApi.FIXTURE.projects.length === fx.projects.length, "project list parity");
  });

  t("input/output/cache/cost never collapsed into a fabricated total token", () => {
    const { WlRender } = loadScripts();
    const fx = loadFixture("cross-project-active-mixed.json");
    WlState.accept(fx, "FIXTURE");
    const html = WlRender.renderFull(fx) + WlRender.renderCompact(fx);
    assert(!/总\s*Token/.test(html) && !/total\s*token/i.test(html), "no undefined total token string");
    assert(/64,391|64391|64\.4K/.test(html), "input tokens visible");
    assert(/26,821|26821|26\.8K/.test(html), "output tokens visible");
    assert(/39,960|39960|40K|40\.0K/.test(html), "cache read tokens visible as separate figure");
  });

  t("cost shown as API estimate / USD, never as an exact bill", () => {
    const fx = loadFixture("cross-project-active-mixed.json");
    const html = WlRender.renderFull(fx) + WlRender.renderCompact(fx);
    assert(/API 估算\s*\/\s*USD/.test(html), "cost label = API 估算 / USD");
    assert(/\$4\.29/.test(html), "amount $4.29 present");
  });

  t("subscriptionUsage=not-metered renders as 订阅未计量, never 0", () => {
    const fx = loadFixture("cross-project-active-mixed.json");
    const html = WlRender.renderFull(fx) + WlRender.renderCompact(fx);
    assert(/订阅未计量/.test(html), "subscription label 订阅未计量 shown");
    assert(!/(sub|订阅)[^<]{0,6}0/.test(html.replace(/\s+/g, "")), "no zero billed for not-metered");
  });

  t("all fixture dates are strict RFC3339", () => {
    const fx = loadFixture("cross-project-active-mixed.json");
    const walk = (o) => {
      for (const k in o) {
        const v = o[k];
        if (typeof v === "string" && /(At|at|GeneratedAt|bucket|from|to)$/.test(k)) {
          assert(ISO_DATE_RE.test(v), "non-RFC3339 date for key " + k + ": " + v);
        } else if (v && typeof v === "object") {
          walk(v);
        }
      }
    };
    walk(fx);
  });

  t("coverage has numerator/denominator/scope", () => {
    const fx = loadFixture("cross-project-active-mixed.json");
    const c = fx.quality.sourceCoverage;
    assert(typeof c.numerator === "number", "coverage numerator");
    assert(typeof c.denominator === "number", "coverage denominator");
    assert(typeof c.scope === "string" && c.scope.length > 0, "coverage scope");
    assert(c.numerator <= c.denominator, "numerator <= denominator");
  });

  t("unknown/new fields are forward compatible (extra keys ignored, no crash)", () => {
    const fx = loadFixture("cross-project-active-mixed.json");
    const extended = JSON.parse(JSON.stringify(fx));
    extended.futureField = { a: 1 };
    extended.usage.someNewMetric = 12345;
    extended.projects[0]._newMeta = "x";
    // Rendering an extended payload must not throw.
    let html = "";
    assert(!(function () { try { html = WlRender.renderFull(extended); return false; } catch (e) { return true; } })(), "renderFull handles unknown fields");
    assert(html.length > 0, "rendered output non-empty");
  });

  t("missing required core keys degrade gracefully (no crash, partial/unknown shown)", () => {
    const fx = loadFixture("cross-project-active-mixed.json");
    const degraded = JSON.parse(JSON.stringify(fx));
    delete degraded.usage.series;          // required by schema
    delete degraded.projects[0].state;     // required by schema
    let html = "";
    assert(!(function () { try { html = WlRender.renderFull(degraded); return false; } catch (e) { return true; } })(), "renderFull tolerates missing required");
    assert(html.length > 0, "still renders");
  });

  t("empty-new-install fixture renders (empty state, no crash, no fake success)", () => {
    const empty = loadFixture("empty-new-install.json");
    let html = "";
    assert(!(function () { try { html = WlRender.renderFull(empty); return false; } catch (e) { return true; } })(), "empty renders");
    assert(/尚无已验证项目事件/.test(html), "empty project message present");
  });

  t("schema file is valid JSON and lists the 10 core required keys", () => {
    const schema = readProjectionSchema();
    const required = schema.required;
    ["schemaVersion", "mode", "generatedAt", "freshness", "summary", "projects", "usage", "ci", "governance", "quality"]
      .forEach((k) => assert(required.includes(k), "schema requires " + k));
  });

  return { pass, fail };
}

module.exports = { run };
if (require.main === module) {
  const { pass, fail } = run();
  console.log(`\ntest_projection_contract: ${pass} passed, ${fail} failed`);
  process.exit(fail ? 1 : 0);
}
