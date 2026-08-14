/* WORK-LAB Observer — tests/test_read_only_surface.js
   Read-only contract: no execution/retry/approve/submit/push/merge/publish/
   switch buttons in the rendered DOM, no POST/PUT/PATCH/DELETE success path in
   the API layer, no credentials/session/prompt access, theme switch is
   memory-only, and GET /api/v1/snapshot is the only network read. */

"use strict";

const fs = require("fs");
const path = require("path");
const { loadScripts, loadFixture, WEB, assert, test, asyncTest } = require("./helpers");

// Words that would imply a mutating control. Blocker/evidence card must NOT offer retry.
const FORBIDDEN_BUTTON_WORDS = [
  "执行", "暂停", "重试", "取消", "批准", "提交", "推送", "合并", "发布",
  "切换 Agent", "切换模型", "切换账号", "同步数据", "同步",
];
const FORBIDDEN_BUTTON_EN = [
  "execute", "retry", "approve", "submit", "push", "merge", "publish", "deploy", "sync",
];
const FORBIDDEN_WRITE_METHODS = ["POST", "PUT", "PATCH", "DELETE"];

async function run() {
  const { WlApi, WlRender, WlState } = loadScripts();
  let pass = 0, fail = 0;
  const t = (n, f) => { if (test(n, f)) pass++; else fail++; };

  if (await asyncTest("api layer exposes no success path for POST/PUT/PATCH/DELETE", async () => {
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
  })) pass++; else fail++;

  if (await asyncTest("snapshot fetch rejects legacy and partial LIVE success payloads", async () => {
    const originalFetch = global.fetch;
    const payloads = [
      { schemaVersion: "work-lab/observer-projection/v2", mode: "LIVE" },
      {
        schemaVersion: "workflow/snapshot/v3",
        revision: 1,
        generatedAt: "2026-08-15T00:00:00Z",
        projects: [], executions: [], ci: [], tasks: {}, tokenSummary: {},
        coverage: { numerator: 1, denominator: 1, scope: "collector_health" },
        transport: { transportState: "LIVE", eventStreamConnected: false },
      },
    ];
    try {
      for (const payload of payloads) {
        global.fetch = async () => ({ ok: true, json: async () => payload });
        let rejected = false;
        try { await WlApi.fetchSnapshot(); } catch (_) { rejected = true; }
        assert(rejected, "invalid/retired 200 payload must fail closed");
      }
    } finally {
      if (originalFetch === undefined) delete global.fetch;
      else global.fetch = originalFetch;
    }
  })) pass++; else fail++;

  t("v3 display mode cannot override the backend transport verdict", () => {
    const normalized = WlApi.normalizeV3({
      schemaVersion: "workflow/snapshot/v3",
      mode: "LIVE",
      transport: { transportState: "OFFLINE", freshnessState: "STALE" },
      projects: [], executions: [], tokenSummary: {}, tasks: {}, ci: [],
    });
    assert(normalized.mode === "OFFLINE", "top-level mode must not override OFFLINE transport");
  });

  t("LIVE v3 requires exact coverage, timestamps, and loopback events URL", () => {
    const valid = {
      schemaVersion: "workflow/snapshot/v3",
      revision: 1,
      generatedAt: "2026-08-15T00:00:00Z",
      projects: [], executions: [], ci: [], tasks: {}, tokenSummary: {},
      coverage: { numerator: 2, denominator: 2, scope: "collector_health" },
      transport: {
        transportState: "LIVE",
        freshnessState: "FRESH",
        eventStreamConnected: true,
        connectedSince: "2026-08-15T00:00:00Z",
        lastHeartbeatAt: "2026-08-15T00:00:01Z",
        writerWatermarkAt: "2026-08-15T00:00:01Z",
        eventsUrl: "http://127.0.0.1:57889/api/v1/events",
      },
    };
    assert(WlApi.validateSnapshotV3(valid) === true, "complete LIVE snapshot validates");

    const badTimestamp = JSON.parse(JSON.stringify(valid));
    badTimestamp.transport.writerWatermarkAt = "";
    assert(WlApi.validateSnapshotV3(badTimestamp) === false, "LIVE requires a valid writer timestamp");

    const overCompleteCoverage = JSON.parse(JSON.stringify(valid));
    overCompleteCoverage.coverage.numerator = 3;
    assert(WlApi.validateSnapshotV3(overCompleteCoverage) === false, "LIVE coverage must equal the expected denominator exactly");

    const remoteEvents = JSON.parse(JSON.stringify(valid));
    remoteEvents.transport.eventsUrl = "https://example.com/api/v1/events";
    assert(WlApi.validateSnapshotV3(remoteEvents) === false, "LIVE events URL must stay on the exact loopback endpoint");
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

  t("retired dashboard helper fails closed without a network request", () => {
    let rejected = false;
    try {
      WlApi.fetchDashboard();
    } catch (err) {
      rejected = /endpoint retired|fetchSnapshot/.test(String(err && err.message));
    }
    assert(rejected, "legacy fetchDashboard must reject synchronously");
  });

  t("snapshot endpoint accepts only explicit loopback read-only URL (v3)", () => {
    global.window = { location: { search: "?api=" + encodeURIComponent("http://127.0.0.1:43123/api/v1/snapshot") } };
    try {
      assert(WlApi.snapshotV3Endpoint() === "http://127.0.0.1:43123/api/v1/snapshot", "loopback v3 endpoint accepted");
      global.window.location.search = "?api=" + encodeURIComponent("https://external.invalid/api/v1/snapshot");
      let rejected = false;
      try { WlApi.snapshotV3Endpoint(); } catch (_) { rejected = true; }
      assert(rejected, "external endpoint rejected");
      global.window.location.search = "?api=" + encodeURIComponent("http://127.0.0.1:43123/api/v1/snapshot?write=1");
      rejected = false;
      try { WlApi.snapshotV3Endpoint(); } catch (_) { rejected = true; }
      assert(rejected, "query-bearing endpoint rejected");
      // R2 third batch: legacy /api/dashboard must be rejected as well.
      global.window.location.search = "?api=" + encodeURIComponent("http://127.0.0.1:43123/api/dashboard");
      rejected = false;
      try { WlApi.snapshotV3Endpoint(); } catch (_) { rejected = true; }
      assert(rejected, "legacy /api/dashboard rejected (retired)");
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

  t("EventSource open refreshes the read-only snapshot after sidecar reconnect", () => {
    const appSrc = fs.readFileSync(path.join(WEB, "scripts", "app.js"), "utf-8");
    assert(/onOpen:\s*async\s*\(\)\s*=>/.test(appSrc), "live subscription binds an async onOpen refresh");
    assert(/onOpen:[\s\S]{0,400}WlApi\.fetchSnapshot\(\)/.test(appSrc), "onOpen re-reads the canonical snapshot");
    assert(/scheduleLiveReconnect\(\)/.test(appSrc), "SSE errors schedule a fresh EventSource instance");
    assert(/onError:[\s\S]{0,300}markRefreshError\([^\n]+true\)[\s\S]{0,150}scheduleSnapshotRetry\(\)[\s\S]{0,150}scheduleLiveReconnect\(\)/.test(appSrc), "SSE failure overrides stale transport and retries both snapshot and stream");
    assert(/Math\.min\([^\n]+30000\)/.test(appSrc), "SSE reconnect backoff is capped at 30 seconds");
    assert(/function\s+scheduleSnapshotRetry\s*\(/.test(appSrc), "initial snapshot failures schedule a fresh GET");
    assert(/catch\s*\(err\)[\s\S]{0,500}scheduleSnapshotRetry\(\)/.test(appSrc), "initial GET failure enters the retry loop");
    assert(/function\s+closeEventSource\s*\(/.test(appSrc), "SSE reconnect closes only the current source without resetting backoff");
    assert(/if\s*\(eventSource\s*&&\s*eventSourceUrl\s*===\s*url\)\s*return true;[\s\S]{0,250}closeEventSource\(\);[\s\S]{0,100}eventSourceUrl\s*=\s*url/.test(appSrc), "starting a replacement EventSource closes the old source without resetting exponential backoff");
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

  t("refresh errors preserve string-valued v3 quality fields without throwing", () => {
    const v3 = {
      mode: "UNKNOWN",
      generatedAt: "2026-08-14T00:00:00Z",
      summary: { registeredProjects: 1 },
      quality: "UNKNOWN",
      projects: [{ projectId: "work-lab", quality: "UNKNOWN" }],
    };
    WlState.accept(v3, "UNKNOWN");
    WlState.markRefreshError("temporary SSE reconnect");
    assert(WlState.get().data.quality === "UNKNOWN", "top-level string quality preserved");
    assert(WlState.get().data.projects[0].quality === "UNKNOWN", "project string quality preserved");
    assert(WlState.get().freshnessState === "stale", "refresh error still marks retained data stale");
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
      // P0-4: named SSE events (snapshot/observed/heartbeat/resync_required) must be
      // dispatched through addEventListener bindings.
      assert(source.listeners.snapshot && source.listeners.snapshot.length === 1, "initial snapshot listener bound");
      assert(source.listeners.observed && source.listeners.observed.length === 1, "observed listener bound");
      assert(source.listeners.heartbeat && source.listeners.heartbeat.length === 1, "heartbeat listener bound");
      assert(source.listeners.resync_required && source.listeners.resync_required.length === 1, "resync_required listener bound");
      source.listeners.snapshot[0]({ data: '{"event_id":"s1"}', lastEventId: "s1" });
      source.listeners.observed[0]({ data: '{"event_id":"e1"}', lastEventId: "e1" });
      source.listeners.message[0]({ data: '{"event_id":"anon"}', lastEventId: "a1" });
      assert(events.length === 3 && events[0].id === "s1" && events[1].id === "e1" && events[2].id === "a1", "initial snapshot + named + anonymous events forwarded with Last-Event-ID");
      source.onerror();
      assert(errors === 1, "reconnect error surfaced as stale signal");
      let rejected = false;
      try { WlApi.subscribeEvents("http://127.0.0.1.evil.invalid/api/v1/events", {}); } catch (_) { rejected = true; }
      assert(rejected, "evil loopback-prefix host rejected");
      rejected = false;
      try { WlApi.subscribeEvents("http://user@127.0.0.1:8766/api/v1/events", {}); } catch (_) { rejected = true; }
      assert(rejected, "SSE userinfo rejected");
      rejected = false;
      try { WlApi.subscribeEvents("http://127.0.0.1:8766/api/v1/events?write=1", {}); } catch (_) { rejected = true; }
      assert(rejected, "query-bearing SSE endpoint rejected");
    } finally {
      delete global.EventSource;
    }
  });

  t("web tree has no server/backoffice entry points", () => {
    const idx = fs.readFileSync(path.join(WEB, "index.html"), "utf-8");
    // Strip comments; only flag real fetch/script/src references. The only
    // documented read endpoint is /api/v1/snapshot (R2 third batch: legacy
    // /api/dashboard is retired).
    const stripped = idx.replace(/<!--[\s\S]*?-->/g, "");
    assert(!/\/api\/(?!v1\/snapshot)/.test(stripped), "index does not hit non-v3 API endpoints");
    // api.js targets GET /api/v1/snapshot and never /api/dashboard.
    const apiSrc = fs.readFileSync(path.join(WEB, "scripts", "api.js"), "utf-8");
    assert(/\/api\/v1\/snapshot/.test(apiSrc), "api.js targets /api/v1/snapshot");
    assert(!/\/api\/dashboard/.test(apiSrc), "api.js no longer targets /api/dashboard");
  });

  return { pass, fail };
}

module.exports = { run };
if (require.main === module) {
  run().then(({ pass, fail }) => {
    console.log(`\ntest_read_only_surface: ${pass} passed, ${fail} failed`);
    process.exitCode = fail ? 1 : 0;
  });
}
