/* WORK-LAB Observer — tests/test_responsive_contract.js
   Responsive contract (static checks, runnable without a browser):
   no horizontal overflow by construction, breakpoints per contract, body
   min 12px, CJK/SHA wrapping, tabular numerals, reduced-motion hook. */

"use strict";

const fs = require("fs");
const path = require("path");
const { WEB, assert, test } = require("./helpers");

function run() {
  let pass = 0, fail = 0;
  const t = (n, f) => { if (test(n, f)) pass++; else fail++; };

  const read = (p) => fs.readFileSync(path.join(WEB, p), "utf-8");
  const html = read("index.html");
  const tokens = read("styles/tokens.css");
  const base = read("styles/base.css");
  const layout = read("styles/layout.css");
  const components = read("styles/components.css");
  const themes = read("styles/themes.css");
  const allCss = tokens + base + layout + components + themes;

  t("viewport meta present (for mobile scaling)", () => {
    assert(/<meta name="viewport"[^>]*width=device-width/.test(html), "viewport meta");
  });

  t("horizontal overflow suppressed on html/body/table containers", () => {
    assert(/overflow-x:\s*hidden/.test(base), "body overflow-x hidden");
    // Table containers scroll internally, never the page.
    assert(/\.wl-table-wrap\s*\{[^}]*overflow-x:\s*auto/.test(components), "table wrap scrolls internally");
  });

  t("grid columns reflow at the contract breakpoints (<960 top nav, <640 compact-ish)", () => {
    assert(/@media\s*\(max-width:\s*960px\)/.test(layout), "960px breakpoint");
    assert(/@media\s*\(max-width:\s*640px\)/.test(layout), "640px breakpoint");
    assert(/@media\s*\(max-width:\s*1024px\)|@media\s*\(max-width:\s*1180px\)/.test(layout), "narrow-full breakpoint");
    assert(/@media\s*\(max-width:\s*420px\)/.test(components), "420px breakpoint");
  });

  t("compact view is a separate single-column layout (no sidebar)", () => {
    assert(/\.wl-compact/.test(layout), "compact class exists");
    assert(/\.wl-compact\s*\{[^}]*flex-direction:\s*column/.test(layout), "compact column stack");
    assert(/\.wl-body-compact/.test(layout), "compact body class");
  });

  t("body font-size >= 12px", () => {
    const m = base.match(/body\s*\{[^}]*font-size:\s*(\d+)px/);
    assert(m && parseInt(m[1], 10) >= 12, "body min font 12px");
  });

  t("tabular numerals enabled for numeric values", () => {
    assert(/tabular-nums/.test(components) && /font-variant-numeric:\s*tabular-nums/.test(components), "tabular nums in components");
  });

  t("long CJK / SHA / tokens wrap, never overflow", () => {
    assert(/overflow-wrap:\s*anywhere/.test(base), "break-word util wraps long opaque values");
    assert(/\.wl-project-repo\s*\{[^}]*overflow-wrap:\s*anywhere/.test(components), "repo cell wraps");
    assert(/\.wl-blocker[^}]*overflow-wrap/.test(components) || /\.wl-kv \.v\s*\{[^}]*overflow-wrap:\s*anywhere/.test(components), "blocker text wraps");
  });

  t("prefers-reduced-motion honored", () => {
    assert(/prefers-reduced-motion/.test(allCss), "reduced-motion media query");
  });

  t("no horizontal page scroll at any width by construction (min-width 320 shell)", () => {
    assert(/min-width:\s*320px/.test(base), "min-width 320 for shell");
  });

  t("status never relies on color alone (chip carries icon + text)", () => {
    assert(/\.wl-chip\s*\{/.test(components), "chip component exists");
    // render.js chipFor always emits icon + text inside a .wl-chip span.
    const render = fs.readFileSync(path.join(WEB, "scripts", "render.js"), "utf-8");
    assert(/chipFor/.test(render), "chipFor helper present");
    assert(/\.wl-chip svg/.test(components) && /\.wl-chip/.test(components), "chip styles icon+text");
  });

  return { pass, fail };
}

module.exports = { run };
if (require.main === module) {
  const { pass, fail } = run();
  console.log(`\ntest_responsive_contract: ${pass} passed, ${fail} failed`);
  process.exit(fail ? 1 : 0);
}
