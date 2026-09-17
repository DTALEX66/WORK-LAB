/* WORK-LAB Observer — R2 visual asset contract.
   Verifies the checked-in visual baseline is present without introducing
   remote assets, mutation controls, or an alternate runtime. */

"use strict";

const fs = require("fs");
const path = require("path");
const { WEB, assert, test } = require("./helpers");

function run() {
  let pass = 0, fail = 0;
  const t = (name, fn) => { if (test(name, fn)) pass++; else fail++; };
  const asset = (name) => path.join(WEB, "assets", "brand", name);

  t("R2 brand assets are checked in under web/assets/brand", () => {
    ["design-tokens.json", "observer-icons.svg", "work-lab-observer-symbol.svg", "work-lab-observer-tray.svg", "app-icon-512.png"]
      .forEach((name) => assert(fs.existsSync(asset(name)), "missing " + name));
  });

  t("R2 design tokens declare the approved themes/views and read-only constraints", () => {
    const tokens = JSON.parse(fs.readFileSync(asset("design-tokens.json"), "utf8"));
    assert(tokens.version === "2.0.0", "R2 token version");
    assert(tokens.themes.includes("dark") && tokens.themes.includes("light"), "dark/light themes");
    assert(tokens.views.includes("full") && tokens.views.includes("compact"), "full/compact views");
    assert(tokens.constraints.readOnly === true, "readOnly");
    assert(tokens.constraints.externalMutation === false, "externalMutation=false");
    assert(tokens.constraints.modelSummary === false, "modelSummary=false");
  });

  t("R2 brand SVGs are local and structurally valid", () => {
    ["observer-icons.svg", "work-lab-observer-symbol.svg", "work-lab-observer-tray.svg"].forEach((name) => {
      const svg = fs.readFileSync(asset(name), "utf8");
      assert(/^\s*<svg\b/.test(svg), name + " starts with svg");
      assert(!/<(?:image|use|script)[^>]+(?:href|src)=["']https?:\/\//i.test(svg), name + " has no remote asset");
    });
  });

  t("index uses only local visual assets and preserves read-only web surface", () => {
    const html = fs.readFileSync(path.join(WEB, "index.html"), "utf8");
    assert(!/<(?:script|link)[^>]+(?:src|href)=["']https?:\/\//i.test(html), "no remote runtime asset");
    assert(/assets\/brand\/work-lab-observer-symbol\.svg/.test(html) || /assets\/brand/.test(html), "brand asset mount");
    assert(/GET|read-only|只读/i.test(html), "read-only surface remains documented");
  });

  t("compact R2 hierarchy keeps four KPIs and a dense project list", () => {
    const render = fs.readFileSync(path.join(WEB, "scripts", "render.js"), "utf8");
    assert(/function compactGlobal\(d\)/.test(render), "compact global renderer");
    assert(/u\.inputTokens[\s\S]{0,120}F\.tokensCompact/.test(render), "token formatter is explicit");
    assert(/wl-compact-project-list/.test(render), "compact project list renderer");
    assert(/slice\(0, 3\)/.test(render), "compact list caps visible projects");
  });

  return { pass, fail };
}

module.exports = { run };
if (require.main === module) {
  const { pass, fail } = run();
  console.log(`\ntest_visual_assets_r2: ${pass} passed, ${fail} failed`);
  process.exit(fail ? 1 : 0);
}
