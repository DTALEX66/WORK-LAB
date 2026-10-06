/* WORK-LAB Observer — production-surface static contracts (U03 cutover step 1).
   The legacy tree guarded these properties with tests/test_read_only_surface.js and
   tests/test_responsive_contract.js, which read web/index.html and web/styles/*.css.
   The production surfaces are frontend/index.html plus frontend/src/skins/*.css and
   frontend/src/**, so the same guarantees have to be pinned there before apps/observer/web
   can be retired — otherwise deleting the legacy UI deletes the only assertions that hold
   the read-only and no-fabrication rules. Static checks, runnable without a browser. */

"use strict";

const fs = require("fs");
const path = require("path");

const FRONTEND = path.join(__dirname, "..", "frontend");
const SRC = path.join(FRONTEND, "src");

let pass = 0, fail = 0;
function t(name, fn) {
  try { fn(); console.log("  PASS  " + name); pass += 1; }
  catch (err) { console.log("  FAIL  " + name); console.log("        " + err.message); fail += 1; }
}
function assert(cond, msg) { if (!cond) throw new Error(msg); }
function read(rel) { return fs.readFileSync(path.join(FRONTEND, rel), "utf-8"); }

function walk(dir, out = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) { if (entry.name !== "node_modules") walk(full, out); }
    else out.push(full);
  }
  return out;
}

function run() {
  const html = read("index.html");
  const shell = read("src/skins/l10b-shell.css");
  const base10 = read("src/skins/b10.css");
  const skins = shell + base10;
  const sources = walk(SRC).filter((p) => /\.(ts|tsx)$/.test(p) && !/\.test\.(ts|tsx)$/.test(p));
  const appCode = sources.map((p) => fs.readFileSync(p, "utf-8")).join("\n");
  // The editor lane persists a canvas model locally and is the one sanctioned
  // storage user. Paths come back with the platform separator, so normalise
  // before matching — an un-normalised test excluded nothing and reported the
  // editor's own four uses as a violation of a rule it never broke.
  const isEditor = (p) => /views[/\\]WorkflowEditorView/.test(p);
  const uiCode = sources.filter((p) => !isEditor(p))
    .map((p) => fs.readFileSync(p, "utf-8")).join("\n");

  console.log("\n==== WORK-LAB Observer production-surface static contracts ====");

  t("the production entry loads no remote runtime, framework or CDN", () => {
    const remote = [...html.matchAll(/(?:src|href)\s*=\s*["']([^"']+)["']/g)]
      .map((m) => m[1]).filter((u) => /^https?:\/\//i.test(u));
    assert(remote.length === 0, "remote references in index.html: " + remote.join(", "));
  });

  t("the skins never reach out to the network", () => {
    const urls = skins.match(/url\(\s*["']?https?:\/\//gi) || [];
    assert(urls.length === 0, urls.length + " remote url() references in the skins");
    const imports = skins.match(/@import\s+["']?https?:/gi) || [];
    assert(imports.length === 0, "remote @import in the skins");
  });

  t("read-only: no write request leaves the UI layer", () => {
    const mutating = appCode.match(/method\s*:\s*["'](POST|PUT|PATCH|DELETE)["']/gi) || [];
    assert(mutating.length === 0, "mutating HTTP methods in src: " + mutating.join(", "));
    const verbs = appCode.match(/\bfetch\s*\(\s*[^)]*,\s*\{[^}]*\bmethod\b/gi) || [];
    assert(verbs.length === 0, "fetch call with an options object found — re-check its method");
  });

  t("read-only: no credential, auth store or env read in the UI layer", () => {
    const hits = [];
    for (const pattern of [/process\.env/, /\bauthorization\b/i, /\bbearer\s+[A-Za-z0-9._-]{6,}/,
                           /\bapi[_-]?key\b/i, /\bcookie\b/i, /auth\.json/i]) {
      if (pattern.test(uiCode)) hits.push(String(pattern));
    }
    assert(hits.length === 0, "forbidden reads present: " + hits.join(", "));
  });

  t("theme and layout state never persist to web storage", () => {
    const storage = uiCode.match(/localStorage|sessionStorage/gi) || [];
    assert(storage.length === 0, storage.length + " web-storage uses outside the editor lane");
  });

  t("responsive: horizontal page overflow is suppressed by construction", () => {
    assert(/overflow-x:\s*hidden/.test(shell) || /min-width:\s*0/.test(shell),
      "the shell neither hides horizontal overflow nor gives flex children min-width:0");
    assert(/\.main\s*\{\s*min-width:\s*0/.test(shell) || /min-width:\s*0/.test(shell),
      "the content column can be widened past the viewport by an unshrinkable child");
  });

  t("responsive: numeric columns use tabular numerals", () => {
    assert(/font-variant-numeric:\s*[^;]*tabular-nums|tabular-nums/.test(skins),
      "no tabular-nums in the production skins, so numbers jitter between rows");
  });

  t("responsive: long CJK, SHA and token strings wrap instead of overflowing", () => {
    assert(/overflow-wrap:\s*(anywhere|break-word)|word-break:\s*break-all/.test(shell),
      "no wrapping rule for long unbroken strings");
  });

  t("motion: a reduced-motion preference is honoured", () => {
    assert(/prefers-reduced-motion/.test(skins),
      "neither skin reacts to prefers-reduced-motion");
  });

  t("legibility: no rule sets the page or lane base text below 12px", () => {
    // The skins inherit the UA base (16px) and never shrink it; what the rule
    // has to catch is a future `body{font-size:10px}` or a container that drops
    // the reading level of real content.
    const offenders = [];
    for (const [, selector, body] of skins.matchAll(/([^{}]+)\{([^}]*)\}/g)) {
      const m = /font-size:\s*(\d+(?:\.\d+)?)px/.exec(body);
      if (!m) continue;
      if (/^\s*(?:html|body)\s*$/.test(selector.trim()) && parseFloat(m[1]) < 12) {
        offenders.push(selector.trim() + " { " + m[0] + " }");
      }
    }
    assert(offenders.length === 0, "base text under 12px: " + offenders.join(", "));
    const bodyDeclared = /(?:^|\})\s*(?:html|body)[^{}]*\{[^}]*font-size/.test(skins);
    assert(!bodyDeclared || parseFloat(/(?:html|body)[^{}]*\{[^}]*font-size:\s*(\d+(?:\.\d+)?)/
      .exec(skins)[1]) >= 12, "body base font-size dropped below 12px");
  });

  t("legibility: every sub-12px declaration is a named micro role", () => {
    // Small type is allowed only where it is a chrome glyph or a spaced label:
    // the window-control zoom percentage, the transient first-frame strip, the
    // brand lockup caption and status chips. Any new 10px paragraph of real
    // content fails here even though the base rule above would still pass.
    const ALLOWED = [/\.winctl-zoom/, /\.load-strip/, /\.brand\s+small/,
                     /\.tag\b/, /\.badge\b/, /\.kpi\s+small\b/];
    const offenders = [];
    for (const [, selector, body] of skins.matchAll(/([^{}]+)\{([^}]*)\}/g)) {
      const m = /font-size:\s*(\d+(?:\.\d+)?)px/.exec(body);
      if (!m || parseFloat(m[1]) >= 12) continue;
      const clean = selector.replace(/\s+/g, " ").trim();
      if (!ALLOWED.some((re) => re.test(clean))) offenders.push(clean + " → " + m[1] + "px");
    }
    assert(offenders.length === 0,
      "small text outside the micro roles:\n        " + offenders.join("\n        "));
  });

  // --- file-level halves of the projection-truth ports (U03 step 1b) ---
  // The behavior halves are in frontend/src/lib/projectionTruthContract.test.ts;
  // these three need the disk, which the frontend tsconfig (no @types/node) must
  // not do from a test.
  t("the typed front model declares the v3 core keys, with `software` the only optional", () => {
    const types = fs.readFileSync(path.join(SRC, "types.ts"), "utf-8");
    const block = /export interface SnapshotV3 \{([\s\S]*?)\n\}/.exec(types);
    assert(block, "types.ts must declare SnapshotV3");
    const declared = [...block[1].matchAll(/^\s+(\w+)(\??):/gm)]
      .map((m) => ({ name: m[1], optional: m[2] === "?" }));
    const CORE = ["schemaVersion", "revision", "generatedAt", "sourceWatermark", "transport",
                  "coverage", "governance", "workspace", "projects", "executions", "tasks",
                  "tokenSummary", "git", "ci", "sourceRefs"];
    for (const k of CORE) {
      assert(declared.some((d) => d.name === k && !d.optional), "types.ts must declare required " + k);
    }
    const optional = declared.filter((d) => d.optional).map((d) => d.name);
    assert(optional.length === 1 && optional[0] === "software",
      "only `software` may be optional, got " + (optional.join(", ") || "none"));
  });

  t("no v3 snapshot literal is embedded in the production source", () => {
    // The legacy front hard-coded WlApi.FIXTURE and pinned its numbers to the
    // real fixture; the production front's only data source is the sidecar.
    const typesPath = path.resolve(SRC, "types.ts");
    const hits = sources
      .filter((p) => path.resolve(p) !== typesPath)
      .filter((p) => /workflow\/snapshot\/v3/.test(fs.readFileSync(p, "utf-8")))
      .map((p) => path.relative(SRC, p));
    assert(hits.length === 0, "files embedding a v3 snapshot literal: " + hits.join(", "));
  });

  t("the production tree renders no currency amount and no subscription wording", () => {
    // Port of "cost shown as API estimate / USD, never as an exact bill" and
    // "subscriptionUsage=not-metered renders as 订阅未计量, never 0". v3 has no
    // monetary field at all, so the ported rule is stronger: money never appears.
    // The needle is a bill SHAPE, not a bare `$` — api.ts legitimately contains
    // `$1` inside a URL replacement.
    const money = /(?:US?\$|RMB|¥|￥)\s?\d|\$\s?\d+\.\d|\bUSD\b|人民币|账单|订阅/;
    const hits = sources.filter((p) => money.test(fs.readFileSync(p, "utf-8")))
      .map((p) => path.relative(SRC, p));
    const inMarkup = [];
    if (money.test(html)) inMarkup.push("index.html");
    if (money.test(skins)) inMarkup.push("skins");
    assert(hits.length === 0 && inMarkup.length === 0,
      "currency/subscription wording in: " + [...hits, ...inMarkup].join(", "));
  });

  console.log(`TOTAL: ${pass} passed, ${fail} failed`);
  return { pass, fail };
}

if (require.main === module) {
  if (run().fail) process.exitCode = 1;
}

module.exports = { run };
