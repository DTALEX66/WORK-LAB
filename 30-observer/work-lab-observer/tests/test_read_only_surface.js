/* WORK-LAB Observer — tests/test_read_only_surface.js
   Read-only contract: no execution/retry/approve/submit/push/merge/publish/
   switch buttons in the rendered DOM, no POST/PUT/PATCH/DELETE success path in
   the API layer, no credentials/session/prompt access, theme switch is
   memory-only, and GET /api/dashboard is the only network read. */

"use strict";

const fs = require("fs");
const path = require("path");
const { loadScripts, loadFixture, WEB, assert, test } = require("./helpers");

// Words that would imply a mutating control. Blocker/evidence card must NOT offer retry.
const FORBIDDEN_BUTTON_WORDS = [
  "执行", "暂停", "重试", "取消", "批准", "提交", "推送", "合并", "发布",
  "切换 Agent", "切换模型", "切换账号", "同步数据", "同步",
];
const FORBIDDEN_BUTTON_EN = [
  "execute", "retry", "approve", "submit", "push", "merge", "publish", "deploy", "sync",
];
const FORBIDDEN_WRITE_METHODS = ["POST", "PUT", "PATCH", "DELETE"];

function run() {
  const { WlApi, WlRender, WlState } = loadScripts();
  let pass = 0, fail = 0;
  const t = (n, f) => { if (test(n, f)) pass++; else fail++; };

  t("api layer exposes no success path for POST/PUT/PATCH/DELETE", async () => {
    // rejectNonGet is the negative control; every non-GET must reject.
    const results = await Promise.all(
      FORBIDDEN_WRITE_METHODS.map((m) =>
        WlApi.rejectNonGet(m).then(
          () => ({ method: m, ok: true }),
          (e) => ({ method: m, ok: false, msg: String(e.message) })
        )
      )
    );
    results.forEach((r) => assert(r.ok === false, r.method + " must be rejected (read-only)"));
    // GET is allowed.
    const getOk = await WlApi.rejectNonGet("GET").then(() => true, () => false);
    assert(getOk === true, "GET allowed");
  });

  t("rendered full+compact surfaces have no mutating controls", () => {
    const fx = loadFixture("cross-project-active-mixed.json");
    WlState.accept(fx, "FIXTURE");
    const html = WlRender.renderFull(fx) + WlRender.renderCompact(fx);
    // The strongest read-only guarantee: render produces NO <button>, NO <form>,
    // NO submit/execution controls at all. Status labels like "正在执行" are
    // legitimate prose, not controls, so we assert on interactive elements only.
    assert(!/<button\b/i.test(html), "render produces no <button> elements");
    assert(!/<form\b/i.test(html), "no <form> in rendered surface");
    assert(!/\bonclick\b/i.test(html), "no inline onclick handlers");
    assert(!/role=["']button["']/i.test(html), "no ARIA button roles");
    const lower = html.toLowerCase();
    FORBIDDEN_BUTTON_EN.forEach((w) => assert(!lower.includes(w), "forbidden english button word: " + w));
  });

  t("blocker evidence card offers NO retry control", () => {
    const fx = loadFixture("cross-project-active-mixed.json");
    const html = WlRender.renderBlocker(fx);
    // The word 重试 appears only inside the evidence disclaimer "不提供重试操作".
    // What must be absent is a retry *control* (button/link), not the word itself.
    assert(!/<button\b/i.test(html), "no retry button in blocker");
    assert(!/role=["']button["']/i.test(html), "no ARIA button in blocker");
    assert(!/\bonclick\b/i.test(html), "no click handler in blocker");
    assert(/证据卡|只读观察，不提供重试操作/.test(html), "blocker labeled evidence read-only");
  });

  t("index.html references no remote runtime/framework/CDN", () => {
    const html = fs.readFileSync(path.join(WEB, "index.html"), "utf-8");
    assert(!/react|vue|svelte|next|tailwind/i.test(html), "no framework");
    // Ignore the SVG xmlns attribute and code comments; only flag actual remote
    // runtime references (external <script>/<link>/fetch/@import/font URLs).
    const stripped = html.replace(/<!--[\s\S]*?-->/g, "").replace(/xmlns="[^"]*"/g, "");
    assert(!/https?:\/\/(?!127\.0\.0\.1|localhost|file)/.test(stripped), "no remote CDN/scripts/fonts");
    assert(!/cdn/i.test(stripped), "no CDN");
    // All scripts are local.
    ["formatters.js", "api.js", "state.js", "charts.js", "render.js", "accessibility.js", "app.js"]
      .forEach((s) => assert(html.includes("scripts/" + s), "loads " + s));
    // All styles local.
    ["tokens.css", "base.css", "layout.css", "components.css", "themes.css"]
      .forEach((s) => assert(html.includes("styles/" + s), "loads " + s));
  });

  t("no credentials/session/prompt/secret access in scripts", () => {
    const scriptsDir = path.join(WEB, "scripts");
    const src = fs.readdirSync(scriptsDir)
      .filter((f) => f.endsWith(".js"))
      .map((f) => fs.readFileSync(path.join(scriptsDir, f), "utf-8"))
      .join("\n");
    const lower = src.toLowerCase();
    ["localstorage", "sessionstorage", "cookies", "authorization", "x-api-key", "api[_-]?key",
      "password", "credential", "token =", "prompt body", "document.cookie"]
      .forEach((pat) => assert(!new RegExp(pat).test(lower), "forbidden access pattern: " + pat));
  });

  t("api layer never writes; only GET fetch exists", () => {
    const apiSrc = fs.readFileSync(path.join(WEB, "scripts", "api.js"), "utf-8");
    const fetchCalls = apiSrc.match(/fetch\s*\(/g) || [];
    assert(fetchCalls.length >= 1, "has fetch call(s)");
    assert(!/method:\s*["'](post|put|patch|delete)/i.test(apiSrc), "no non-GET fetch method");
    assert(/method:\s*["']GET["']/i.test(apiSrc), "GET method explicit");
  });

  t("dashboard endpoint accepts only explicit loopback read-only URL", () => {
    global.window = { location: { search: "?api=" + encodeURIComponent("http://127.0.0.1:43123/api/dashboard") } };
    try {
      assert(WlApi.dashboardEndpoint() === "http://127.0.0.1:43123/api/dashboard", "loopback endpoint accepted");
      global.window.location.search = "?api=" + encodeURIComponent("https://external.invalid/api/dashboard");
      let rejected = false;
      try { WlApi.dashboardEndpoint(); } catch (_) { rejected = true; }
      assert(rejected, "external endpoint rejected");
      global.window.location.search = "?api=" + encodeURIComponent("http://127.0.0.1:43123/api/dashboard?write=1");
      rejected = false;
      try { WlApi.dashboardEndpoint(); } catch (_) { rejected = true; }
      assert(rejected, "query-bearing endpoint rejected");
    } finally {
      delete global.window;
    }
  });

  t("theme toggle is memory-only (no server persistence, no storage)", () => {
    const appSrc = fs.readFileSync(path.join(WEB, "scripts", "app.js"), "utf-8");
    assert(!/localStorage|sessionStorage|document\.cookie/.test(appSrc), "no persistent storage");
    assert(/history\.replaceState/.test(appSrc), "theme persists only to URL history (memory)");
    // app.js may GET-read a bundled real snapshot (assets/live-snapshot.json), but never writes.
    assert(!/method:\s*["'](post|put|patch|delete)/i.test(appSrc), "app.js does not write via fetch");
  });

  t("state last-good survives refresh error (never clears to zero)", () => {
    WlState.accept(WlApi.FIXTURE, "FIXTURE");
    WlState.markRefreshError("network down");
    assert(WlState.get().lastGood !== null, "lastGood retained after error");
    assert(WlState.get().freshnessState === "stale", "refresh error marks stale");
    assert(WlState.get().data.freshness.state === "stale", "rendered projection is stale, not merely internal state");
    assert(WlState.get().lastGood.freshness.state === "fresh", "unmodified last-good source retained");
    WlState.markRefreshError("timeout");
    assert(WlState.get().lastGood !== null, "lastGood retained on second error");
  });

  t("bundled snapshot is always rendered stale rather than live", () => {
    const snapshot = loadFixture("empty-new-install.json");
    WlState.accept(snapshot, "SNAPSHOT");
    assert(WlState.get().mode === "SNAPSHOT", "snapshot mode explicit");
    assert(WlState.get().freshnessState === "stale", "snapshot freshness recomputed as stale");
    assert(WlState.get().data.freshness.state === "stale", "snapshot payload cannot retain a fresh badge");
  });

  t("SSE client accepts only loopback event endpoint and forwards named events", () => {
    let created = null;
    class FakeEventSource {
      constructor(url) { this.url = url; this.listeners = {}; created = this; }
      close() { this.closed = true; }
      addEventListener(name, cb) { (this.listeners[name] = this.listeners[name] || []).push(cb); }
    }
    global.EventSource = FakeEventSource;
    const events = [];
    let errors = 0;
    try {
      const source = WlApi.subscribeEvents("http://127.0.0.1:8766/api/v1/events", {
        onEvent: (event, id) => events.push({ event, id }),
        onError: () => { errors += 1; },
      });
      assert(source === created, "EventSource returned");
      // P0-4: named SSE events (observed/heartbeat/resync_required) must be
      // dispatched through addEventListener bindings.
      assert(source.listeners.observed && source.listeners.observed.length === 1, "observed listener bound");
      assert(source.listeners.heartbeat && source.listeners.heartbeat.length === 1, "heartbeat listener bound");
      assert(source.listeners.resync_required && source.listeners.resync_required.length === 1, "resync_required listener bound");
      source.listeners.observed[0]({ data: '{"event_id":"e1"}', lastEventId: "e1" });
      source.listeners.message[0]({ data: '{"event_id":"anon"}', lastEventId: "a1" });
      assert(events.length === 2 && events[0].id === "e1" && events[1].id === "a1", "named + anonymous events forwarded with Last-Event-ID");
      source.onerror();
      assert(errors === 1, "reconnect error surfaced as stale signal");
      let rejected = false;
      try { WlApi.subscribeEvents("http://127.0.0.1.evil.invalid/api/v1/events", {}); } catch (_) { rejected = true; }
      assert(rejected, "evil loopback-prefix host rejected");
    } finally {
      delete global.EventSource;
    }
  });

  t("web tree has no server/backoffice entry points", () => {
    const idx = fs.readFileSync(path.join(WEB, "index.html"), "utf-8");
    // Strip comments; only flag real fetch/script/src references to non-dashboard
    // API endpoints. "/api/dashboard" is the only documented read endpoint.
    const stripped = idx.replace(/<!--[\s\S]*?-->/g, "");
    assert(!/\/api\/(?!dashboard)/.test(stripped), "index does not hit other API endpoints");
    // api.js uses exactly GET /api/dashboard (already covered, explicit here too).
    const apiSrc = fs.readFileSync(path.join(WEB, "scripts", "api.js"), "utf-8");
    assert(/\/api\/dashboard/.test(apiSrc), "api.js targets /api/dashboard");
  });

  return { pass, fail };
}

module.exports = { run };
if (require.main === module) {
  const { pass, fail } = run();
  console.log(`\ntest_read_only_surface: ${pass} passed, ${fail} failed`);
  process.exit(fail ? 1 : 0);
}
